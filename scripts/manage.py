"""Manage only recorded project processes. No process-name based shutdown."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'state/managed-processes.json'
NAPCAT = ROOT / 'runtime/napcat/installer/NapCat.52230.Shell'
sys.path.insert(0, str(ROOT / 'src'))
from qqbot_gateway.config import load_gate_config


def alive(entry):
    try:
        process = psutil.Process(entry['pid'])
        return process if abs(process.create_time() - entry['created']) < .01 and process.is_running() else None
    except psutil.NoSuchProcess:
        return None


def read_state():
    return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else []


def save(entries):
    STATE.parent.mkdir(exist_ok=True)
    temp = STATE.with_suffix('.tmp')
    temp.write_text(json.dumps(entries, indent=2), encoding='utf-8')
    temp.replace(STATE)


def remember(entries, process, component):
    try:
        if not any(e['pid'] == process.pid and e['created'] == process.create_time() for e in entries):
            entries.append({'pid':process.pid, 'created':process.create_time(), 'component':component})
            save(entries)
    except psutil.NoSuchProcess:
        pass


def capture(entries, root_process, component, started):
    try:
        remember(entries, root_process, component)
        for child in root_process.children(recursive=True):
            remember(entries, child, component)
    except psutil.NoSuchProcess:
        pass
    if component == 'napcat':
        # The launcher may exit after spawning QQ. Only this instance and launch time qualify.
        for process in psutil.process_iter(['exe','create_time']):
            try:
                if (process.info['exe'] and process.info['create_time'] >= started and
                        Path(process.info['exe']).resolve().is_relative_to(NAPCAT.resolve())):
                    remember(entries,process,component)
            except (psutil.NoSuchProcess,psutil.AccessDenied,OSError):
                continue


def stop(entries):
    targets=[]
    for entry in entries:
        process=alive(entry)
        if process is not None:
            try:
                targets.extend(process.children(recursive=True));targets.append(process)
            except psutil.NoSuchProcess:
                pass
    identities={}
    for process in targets:
        try:
            if process.is_running():identities[(process.pid,process.create_time())]=process
        except psutil.NoSuchProcess:pass
    targets=list(identities.values())
    for process in reversed(targets):
        try:process.terminate()
        except psutil.NoSuchProcess:pass
    _,pending=psutil.wait_procs(targets,timeout=3)
    for process in pending:
        try:process.kill()
        except psutil.NoSuchProcess:pass
    _,pending=psutil.wait_procs(pending,timeout=2)
    if pending:raise RuntimeError('Project process cleanup incomplete')
    save([])


def check_port(port):
    with socket.socket() as sock:
        try:sock.bind(('127.0.0.1',port))
        except OSError:
            owners=[c.pid for c in psutil.net_connections('tcp') if c.laddr and c.laddr.port==port and c.status=='LISTEN']
            raise RuntimeError(f'PORT_CONFLICT port={port} pid={owners}')


def start_channel(full=False):
    if any(alive(e) is not None for e in read_state()):
        raise RuntimeError('Project processes already running; inspect status first')
    gate=load_gate_config(ROOT/'config/settings.local.yaml')
    for port in ((6185,6199,6200,6099,8765) if full else (6185,6199,6200,6099)):check_port(port)
    if full:
        result=subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),str(ROOT/'scripts/configure_astrbot.py')],
                              cwd=ROOT/'runtime/astrbot',capture_output=True)
        if result.returncode:
            (ROOT/'runtime/astrbot/configure-error.log').write_bytes(result.stdout+result.stderr)
            raise RuntimeError('CONFIG_PREPARE_FAILED; local runtime/astrbot/configure-error.log')
    config_path=ROOT/'runtime/astrbot/data/cmd_config.json'
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    config['platform']=[{'id':'qqbot','type':'aiocqhttp','enable':True,'ws_reverse_host':'127.0.0.1',
                         'ws_reverse_port':6199,'ws_reverse_token':gate.upstream_token}]
    config['platform_settings'].update({'unique_session':True,'enable_id_white_list':True,
                                       'id_whitelist':sorted(gate.allowed_groups),
                                       'wl_ignore_admin_on_group':False,'wl_ignore_admin_on_friend':False,
                                       'ignore_bot_self_message':True,'ignore_at_all':True,
                                       'empty_mention_waiting':False,'empty_mention_waiting_need_reply':False})
    config['wake_prefix']=[]
    config['admins_id']=sorted(gate.admin_users)
    config['log_level']='ERROR'
    config['provider_settings']['enable']=full
    config['provider_settings']['streaming_response']=False
    config['provider_settings']['proactive_capability']['add_cron_tools']=False
    config['provider_settings']['computer_use_runtime']='none'
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8-sig')
    napcat_config=NAPCAT/'versions/9.9.33-52230/resources/app/napcat/config'
    logging={'fileLog':False,'consoleLog':True,'consoleLogLevel':'warn','fileLogLevel':'warn'}
    for name in ('napcat.json','napcat_'+gate.bot_qq+'.json'):
        (napcat_config/name).write_text(json.dumps(logging),encoding='utf-8')
    entries=[]
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src');env['PYTHONUTF8']='1';env['QQBOT_ROOT']=str(ROOT)
    specs=[('astrbot',[str(ROOT/'runtime/astrbot-bin/astrbot.exe'),'run'],ROOT/'runtime/astrbot',(6185,6199),25),
           ('gate',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.onebot_gate','--config',str(ROOT/'config/settings.local.yaml')],ROOT,(6200,),10),
           ('napcat',[str(NAPCAT/'NapCatWinBootMain.exe'),gate.bot_qq],NAPCAT,(6099,),30)]
    if full:specs.insert(1,('model',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.model_gateway','--config',str(ROOT/'config/settings.local.yaml')],ROOT,(8765,),10))
    try:
        for component,args,cwd,ports,timeout in specs:
            started=time.time()
            with (logs/(component+'.log')).open('ab') as output:
                hosted=[str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/process_host.py'),component,'--',*args]
                process=psutil.Popen(hosted,cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            ready=False
            while time.time()-started<timeout:
                capture(entries,process,component,started)
                results=[]
                for port in ports:
                    with socket.socket() as sock:
                        sock.settimeout(.2);results.append(sock.connect_ex(('127.0.0.1',port))==0)
                plugin_ready=not(full and component=='astrbot') or (ROOT/'state/router-ready.json').exists()
                if all(results) and plugin_ready:ready=True;break
                time.sleep(.2)
            if not ready:raise RuntimeError(f'{component.upper()}_STARTUP_NOT_READY; local logs/{component}.log')
            print(component.upper()+'_LOCAL_READY',flush=True)
    except BaseException:
        stop(entries)
        raise
    (ROOT/'state/service-mode.json').write_text(json.dumps({'mode':'text' if full else 'channel_only','started':time.time()}),encoding='utf-8')
    print('TEXT_READY: await real @ acceptance.' if full else 'CHANNEL_ONLY: LLM disabled. Await target QQ login.')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['start-channel','start-text','stop','status','test'])
    args=parser.parse_args()
    if args.command=='start-channel':start_channel()
    elif args.command=='start-text':start_channel(full=True)
    elif args.command=='stop':stop(read_state());print('Project processes stopped.')
    elif args.command=='status':
        entries=read_state()
        report={'processes':{name:sum(1 for e in entries if e['component']==name and alive(e) is not None) for name in ('astrbot','model','gate','napcat')}}
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open('http://127.0.0.1:8765/health',timeout=2) as response:report['model']=json.load(response)
        except OSError:report['model']={'alive':False}
        print(json.dumps(report,indent=2))
    else:
        raise SystemExit(subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT))


if __name__=='__main__':main()
