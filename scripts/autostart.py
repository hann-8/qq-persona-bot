"""One-shot current-user startup. No credentials, login actions, or model probes."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts import manage
from qqbot_gateway.config import configuration_lock
from qqbot_gateway.lifecycle import atomic_json
from qqbot_gateway.napcat_login import bounded_read, strict_json

LINK_NAME='QQbot-managed-startup.lnk'


def network_available():
    # Local interface metadata only. No DNS, Internet, SSH, or model requests.
    import ipaddress
    import psutil
    stats=psutil.net_if_stats()
    for name,addresses in psutil.net_if_addrs().items():
        if name not in stats or not stats[name].isup:continue
        for item in addresses:
            if item.family not in (socket.AF_INET,socket.AF_INET6):continue
            try:
                ip=ipaddress.ip_address(item.address.split('%')[0])
                if not ip.is_loopback and not ip.is_unspecified and not ip.is_link_local:return True
            except ValueError:continue
    return False


def write_status(root, instance, started, phase, reason, ready=False):
    with configuration_lock(root):
        mode_path=Path(root)/'state/service-mode.json'
        mode=strict_json(bounded_read(mode_path,16384)) if mode_path.exists() else {}
        if mode.get('instance_id')!=instance:return False
        marker=Path(root)/'state/stop-request.json'
        if phase=='finished' and marker.exists():
            if strict_json(bounded_read(marker,16384)).get('instance_id')==instance:return False
        atomic_json(Path(root)/'state/autostart-status.json',dict(schema_version=1,
            instance_id=instance,started=started,finished=time.time(),phase=phase,reason=reason,qq_ready=ready))
        return True


def run(root=ROOT, delay=30, network_wait=120, *, start=None, network=network_available,
        sleep=time.sleep, clock=time.monotonic):
    if type(delay) is not int or not 0<=delay<=120 or type(network_wait) is not int or not 0<=network_wait<=300:
        raise ValueError('AUTOSTART_INVALID')
    root=Path(root);started=time.time()
    # A separate wrapper singleton is held over waits; the shared configuration lock is NOT.
    # manage.start_channel still owns the existing lifecycle lock and immutable snapshot.
    with configuration_lock(root/'state/autostart-wrapper'):
        initial=manage.service_mode().get('instance_id')
        sleep(delay)
        end=clock()+network_wait
        while not network():
            if clock()>=end:
                write_status(root,initial,started,'failed','dependency_timeout')
                return {'state':'dependency_timeout'}
            sleep(min(1,end-clock()))
        try:
            result=(start or manage.start_channel)(full=True,login_diagnostics=True,wait_login_seconds=120)
        except (OSError,ValueError,RuntimeError):
            # Do not repair partial instances, kill, clear ledgers, or change backend.
            write_status(root,initial,started,'failed','start_blocked')
            return {'state':'start_blocked'}
        instance=result.get('instance_id')
        if instance:
            write_status(root,instance,started,'finished',result['state'],result['state']=='qq_ready')
        return result


def current_startup():
    if os.name!='nt' or not os.environ.get('APPDATA'):raise ValueError('STARTUP_UNAVAILABLE')
    return Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup'


def shortcut(path, target, arguments, working):
    subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-File',
        str(ROOT/'scripts/startup_shortcut.ps1'),str(path),str(target),arguments,str(working)],
        check=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW)


def link_digest(path):
    if path.is_symlink() or path.is_junction() or not path.is_file():raise ValueError('STARTUP_FOREIGN_LINK')
    return hashlib.sha256(bounded_read(path,65536)).hexdigest()


def registration(root, action, *, startup=None, create=shortcut, delay=30, network_wait=120):
    root=Path(root).resolve()
    startup=(current_startup() if startup is None else Path(startup)).resolve()
    link=startup/LINK_NAME
    ledger=root/'state/autostart-registration.json'
    if action not in ('install','status','remove'):raise ValueError('AUTOSTART_INVALID')
    if type(delay) is not int or not 0<=delay<=120 or type(network_wait) is not int or not 0<=network_wait<=300:
        raise ValueError('AUTOSTART_INVALID')
    expected=dict(root=str(root),target=str(root/'开机启动机器人.cmd'),
                  arguments=f'--delay-seconds {delay} --network-wait-seconds {network_wait}',
                  working_directory=str(root),shortcut=str(link))
    def inspect():
        if ledger.is_symlink() or ledger.is_junction():raise ValueError('STARTUP_OWNERSHIP_UNKNOWN')
        if not ledger.exists():return None
        value=strict_json(bounded_read(ledger,16384))
        if (not isinstance(value,dict) or set(value)!={'schema_version','owner','link_sha256'} or
            value.get('schema_version')!=1 or not isinstance(value.get('owner'),dict) or
            value['owner'].get('root')!=str(root) or value['owner'].get('shortcut')!=str(link)):
            raise ValueError('STARTUP_OWNERSHIP_UNKNOWN')
        owner=value['owner']
        if (set(owner)!=set(expected) or owner.get('target')!=expected['target'] or
            owner.get('working_directory')!=str(root) or not isinstance(owner.get('arguments'),str)):
            raise ValueError('STARTUP_OWNERSHIP_UNKNOWN')
        arguments=re.fullmatch(r'--delay-seconds ([0-9]{1,3}) --network-wait-seconds ([0-9]{1,3})',owner['arguments'])
        if not arguments or int(arguments[1])>120 or int(arguments[2])>300:raise ValueError('STARTUP_OWNERSHIP_UNKNOWN')
        if not link.exists() or link_digest(link)!=value.get('link_sha256'):raise ValueError('STARTUP_FOREIGN_LINK')
        return value
    if action=='status':
        try:
            value=inspect()
            return {'state':'installed' if value else 'foreign' if os.path.lexists(link) else 'not_installed'}
        except (OSError,ValueError):return {'state':'ownership_unknown'}
    with configuration_lock(root):
        value=inspect()
        if action=='remove':
            if not value:
                if os.path.lexists(link):raise ValueError('STARTUP_FOREIGN_LINK')
                return {'state':'not_installed'}
            # A matching ledger alone is insufficient: inspect verified the link's exact bytes.
            link.unlink();ledger.unlink();return {'state':'removed'}
        if value:
            if value['owner']!=expected:raise ValueError('STARTUP_CONFIGURATION_CHANGED_REMOVE_FIRST')
            return {'state':'installed'}
        if os.path.lexists(link):raise ValueError('STARTUP_FOREIGN_LINK')
        startup.mkdir(parents=True,exist_ok=True)
        temporary=startup/('QQbot-'+uuid.uuid4().hex+'.lnk')
        installed=False;digest=None
        try:
            create(temporary,Path(expected['target']),expected['arguments'],root)
            digest=link_digest(temporary)
            # Windows rename refuses an existing destination; no foreign overwrite.
            if os.path.lexists(link):raise ValueError('STARTUP_FOREIGN_LINK')
            temporary.rename(link);installed=True
            atomic_json(ledger,dict(schema_version=1,owner=expected,link_sha256=digest))
        except BaseException:
            if installed and link_digest(link)==digest:link.unlink()
            raise
        finally:temporary.unlink(missing_ok=True)
        return {'state':'installed'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['run','install','status','remove'])
    parser.add_argument('--delay-seconds',type=int,default=30)
    parser.add_argument('--network-wait-seconds',type=int,default=120)
    args=parser.parse_args()
    try:
        result=run(delay=args.delay_seconds,network_wait=args.network_wait_seconds) if args.action=='run' else registration(
            ROOT,args.action,delay=args.delay_seconds,network_wait=args.network_wait_seconds)
        print(json.dumps(result,ensure_ascii=False))
        return 0 if result['state'] in ('installed','removed','not_installed','already_running','qq_ready') else 1
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
        print('AUTOSTART_OPERATION_BLOCKED');return 1


if __name__=='__main__':raise SystemExit(main())
