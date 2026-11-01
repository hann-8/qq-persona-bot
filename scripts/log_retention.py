"""Project-only daily logs and a current-user, metadata-only cleanup task."""
import argparse
from datetime import date, datetime, timedelta
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
COMPONENTS = ('model', 'gate', 'astrbot', 'napcat', 'snowluma', 'qq_client', 'transport_watch')
NAMES = {name+'.log' for name in COMPONENTS} | {'intake-'+name+'.log' for name in COMPONENTS} | {'snowluma-startup.local.log'}
TASK = 'QQbot-SnowLuma-LogRetention'


def policy(raw=None):
    from qqbot_gateway.config import normalize_logging
    return normalize_logging({} if raw is None else raw)


def read_policy(root=ROOT):
    from qqbot_gateway.config_files import read_project
    return policy(read_project(root).settings.get('logging',{}))


def checked(root, path, *, directory=False):
    from qqbot_gateway.config_files import plain_path
    return plain_path(root, path, directory=directory)


def mkdir(root, path):
    from qqbot_gateway.config_files import safe_mkdir
    return safe_mkdir(root, path)


def unlink_closed(path):
    if os.name != 'nt':return path.unlink()
    import _winapi
    # Share DELETE only: any existing reader/writer (including Node handles
    # that themselves allow deletion) prevents us from deleting an active log.
    handle=_winapi.CreateFile(str(path),_winapi.GENERIC_READ,4,0,_winapi.OPEN_EXISTING,0,0)
    try:path.unlink()
    finally:_winapi.CloseHandle(handle)


class Lease:
    """One writer per current log; sweepers never unlink a live current file."""
    def __init__(self, root, name):
        directory = mkdir(root, Path(root)/'state/log-retention/locks')
        path = directory/(name+'.lock')
        if os.path.lexists(path):checked(root, path)
        self.stream = path.open('a+b')
        if not path.stat().st_size:self.stream.write(b'\0');self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stream.close()
            raise

    def close(self):self.stream.close()


def _expired(root, directory, names, cutoff, *, current=False, native=False):
    result = dict(deleted_files=0, deleted_bytes=0, skipped=0)
    if not os.path.lexists(directory):return result
    checked(root, directory, directory=True)
    for entry in directory.iterdir():
        try:
            checked(root, entry)
            name = entry.name
            base = None
            if native:
                match = re.fullmatch(r'snowluma-(\d{4}-\d{2}-\d{2})(?:\.\d+)?\.log', name)
            else:
                base = next((value for value in names if name == value or name.startswith(value+'.')), None)
                if base is None:continue
                match = re.fullmatch(re.escape(base)+r'\.(\d{4}-\d{2}-\d{2})(?:\.\d+)?', name)
            lease = None
            if match:day = date.fromisoformat(match[1])
            elif current and name in names:
                day = datetime.fromtimestamp(entry.stat().st_mtime).date()
                if day >= cutoff:continue
                try:lease = Lease(root, name)
                except OSError:result['skipped'] += 1;continue
            else:continue
            try:
                if day < cutoff:
                    size = entry.stat().st_size
                    unlink_closed(entry)
                    result['deleted_files'] += 1;result['deleted_bytes'] += size
            finally:
                if lease:lease.close()
        except (OSError, ValueError):result['skipped'] += 1
    return result


def purge(root=ROOT, settings=None, today=None):
    root = Path(root).resolve();settings = read_policy(root) if settings is None else policy(settings)
    result = dict(deleted_files=0, deleted_bytes=0, skipped=0, enabled=settings['enabled'])
    if not settings['enabled']:return result
    cutoff = (today or datetime.now().date()) - timedelta(days=settings['retention_days']-1)
    targets = [(root/'logs', NAMES, False), (root/'runtime/astrbot', {'bootstrap.local.log', 'configure-error.log'}, False),
               (root/'runtime/snowluma/v2.1.1/logs', (), True)]
    for directory, names, native in targets:
        try:
            counts = _expired(root, directory, names, cutoff, current=True, native=native)
            for key in counts:result[key] += counts[key]
        except (OSError, ValueError):result['skipped'] += 1
    return result


class DailyHandler(TimedRotatingFileHandler):
    failed = False

    def handleError(self, record):
        # Never send a raw official log record into an exception traceback.
        self.failed = True

    def rotation_filename(self, default_name):
        path = Path(default_name);index = 0
        while path.exists():
            index += 1;path = Path(default_name+'.'+str(index))
        return str(path)


class LogSink:
    def __init__(self, root, name, settings, *, background=True):
        if name not in NAMES:raise ValueError('Unknown project log')
        self.root = Path(root).resolve();self.name = name;self.settings = policy(settings)
        directory = mkdir(self.root, self.root/'logs');path = directory/name
        if os.path.lexists(path):checked(self.root, path)
        self.lease = Lease(self.root, name)
        try:self.handler = DailyHandler(path, when='midnight', backupCount=0, encoding='utf-8', delay=True)
        except BaseException:self.lease.close();raise
        self.handler.terminator = '';self.closed = threading.Event();self.thread = None
        self.tick()
        if background:
            self.thread = threading.Thread(target=self._maintain, daemon=True);self.thread.start()

    def tick(self):
        if not self.settings['enabled']:return
        self.handler.acquire()
        try:
            if time.time() >= self.handler.rolloverAt:self.handler.doRollover()
            cutoff = datetime.now().date()-timedelta(days=self.settings['retention_days']-1)
            _expired(self.root, self.root/'logs', {self.name}, cutoff)
        finally:self.handler.release()

    def _maintain(self):
        while not self.closed.wait(60):
            try:self.tick()
            except (OSError, ValueError):pass  # locked file: retry, never interrupt the bot

    def write(self, text):
        failed=False
        self.handler.acquire()
        try:
            if self.settings['enabled'] and time.time() >= self.handler.rolloverAt:self.handler.doRollover()
            # Avoid TimedRotatingFileHandler's implicit rollover when disabled.
            self.handler.failed = False
            logging.FileHandler.emit(self.handler, logging.LogRecord('project', logging.INFO, '', 0, text, (), None))
            failed=self.handler.failed
        except (OSError,ValueError):failed=True
        finally:self.handler.release()
        if failed:
            try:
                from qqbot_gateway.lifecycle import atomic_json
                directory=mkdir(self.root,self.root/'state/log-retention/errors')
                atomic_json(directory/(self.name+'.json'),dict(code='LOG_WRITE_FAILED',time=datetime.now().astimezone().isoformat()))
            except (OSError,ValueError):pass
        return not failed

    def close(self):
        self.closed.set()
        if self.thread:self.thread.join(timeout=2)
        self.handler.close();self.lease.close()


def task_action(root=ROOT):
    root = Path(root).resolve()
    return str(root/'.venv/Scripts/python.exe'), '"'+str(root/'scripts/log_retention.py')+'" purge'


def task_xml(root, settings, sid):
    ns = 'http://schemas.microsoft.com/windows/2004/02/mit/task'
    task = ET.Element('Task', version='1.2', xmlns=ns)
    triggers = ET.SubElement(task, 'Triggers');trigger = ET.SubElement(triggers, 'TimeTrigger')
    repetition = ET.SubElement(trigger, 'Repetition');ET.SubElement(repetition, 'Interval').text = f"PT{settings['sweep_interval_minutes']}M"
    ET.SubElement(repetition, 'StopAtDurationEnd').text = 'false'
    ET.SubElement(trigger, 'StartBoundary').text = datetime.now().astimezone().isoformat(timespec='seconds')
    ET.SubElement(trigger, 'Enabled').text = 'true'
    login = ET.SubElement(triggers, 'LogonTrigger');ET.SubElement(login, 'Enabled').text = 'true';ET.SubElement(login, 'UserId').text = sid
    principal = ET.SubElement(ET.SubElement(task, 'Principals'), 'Principal', id='Author')
    for key, value in [('UserId',sid),('LogonType','InteractiveToken'),('RunLevel','LeastPrivilege')]:ET.SubElement(principal,key).text=value
    section = ET.SubElement(task,'Settings')
    for key,value in [('MultipleInstancesPolicy','IgnoreNew'),('DisallowStartIfOnBatteries','false'),('StopIfGoingOnBatteries','false'),('StartWhenAvailable','true'),('ExecutionTimeLimit','PT5M')]:ET.SubElement(section,key).text=value
    command, arguments = task_action(root);action = ET.SubElement(ET.SubElement(task,'Actions',Context='Author'),'Exec')
    ET.SubElement(action,'Command').text=command;ET.SubElement(action,'Arguments').text=arguments
    ET.SubElement(action,'WorkingDirectory').text=str(root)
    return ET.tostring(task,encoding='unicode')


def scheduled_task(operation, root=ROOT):
    settings = read_policy(root);directory = mkdir(root,Path(root)/'state/log-retention')
    command, arguments = task_action(root)
    script = directory/'task-control.ps1'
    script.write_text('''param($Operation,$TaskName,$TaskXml,$ExpectedExe,$ExpectedArgs)
$ErrorActionPreference='Stop'
$existing=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Count -ne 1 -or $existing.Actions[0].Execute -ine $ExpectedExe -or $existing.Actions[0].Arguments -cne $ExpectedArgs)) { throw 'TASK_IDENTITY_MISMATCH' }
if ($Operation -eq 'install') { Register-ScheduledTask -TaskName $TaskName -Xml ([IO.File]::ReadAllText($TaskXml)) -Force | Out-Null }
elseif ($Operation -eq 'remove' -and $existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
$value=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
@{installed=($null -ne $value);state=if($value){[string]$value.State}else{'Absent'}} | ConvertTo-Json -Compress
''',encoding='utf-8-sig')
    xml = directory/'task.xml'
    if operation == 'install' and settings['enabled']:
        identity = subprocess.check_output(['whoami','/user','/fo','csv','/nh'],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).decode('ascii',errors='ignore')
        match = re.search(r'S-1-\d+(?:-\d+)+',identity)
        if not match:raise ValueError('Current user SID unavailable')
        xml.write_text(task_xml(root,settings,match[0]),encoding='utf-16')
    if operation == 'install' and not settings['enabled']:operation = 'remove'
    result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(script),operation,TASK,str(xml),command,arguments],capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise RuntimeError('Project log task operation failed; inspect current-user Task Scheduler permissions')
    return json.loads(result.stdout.lstrip('\ufeff').strip())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('purge','install','status','remove'));parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args();root=args.root.resolve()
    if args.command!='purge' and root!=ROOT:parser.error('Task operations require the actual project root')
    try:
        if args.command=='purge':
            result=purge(root)
            from qqbot_gateway.lifecycle import atomic_json
            directory=mkdir(root,root/'state/log-retention');atomic_json(directory/'last-sweep.json',dict(time=datetime.now().astimezone().isoformat(),**result))
        else:result=scheduled_task(args.command,root)
        print(json.dumps(result))
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
        print('LOG_RETENTION_FAILED',file=sys.stderr);raise SystemExit(1)


if __name__=='__main__':main()
