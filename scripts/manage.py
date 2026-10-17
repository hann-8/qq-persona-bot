"""Manage only recorded project processes. No process-name based shutdown."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import socket
import sqlite3
import uuid
import subprocess
import sys
import time
import urllib.request

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'state/managed-processes.json'
NAPCAT = ROOT / 'runtime/napcat/installer/NapCat.52230.Shell'
NAPCAT_URL = 'http://127.0.0.1:6099'
sys.path.insert(0, str(ROOT / 'src'))
from qqbot_gateway.config import load_settings, load_gate_config, configuration_lock
from qqbot_gateway.lifecycle import atomic_json


def alive(entry):
    try:
        process = psutil.Process(entry['pid'])
        return process if abs(process.create_time() - entry['created']) < .01 and process.is_running() else None
    except psutil.NoSuchProcess:
        return None


def read_state():
    if not STATE.exists():return []
    entries=json.loads(STATE.read_text(encoding='utf-8'))
    if not isinstance(entries,list) or any(not isinstance(e,dict) or type(e.get('pid')) is not int or
            type(e.get('created')) not in (int,float) or not isinstance(e.get('component'),str) for e in entries):
        raise ValueError('Invalid managed process identities; inspect local state')
    return entries


def save(entries):
    atomic_json(STATE,entries)


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
    """Capture fresh descendants before parents exit; persist every surviving identity."""
    targets={(e['pid'],e['created']):dict(e) for e in entries}
    # Every round discovers children generated since the previous snapshot.
    for round_index in range(3):
        for entry in list(targets.values()):
            try:
                process=alive(entry)
                if process is None:continue
                for child in process.children(recursive=True):
                    identity={'pid':child.pid,'created':child.create_time(),'component':entry['component']}
                    targets[(identity['pid'],identity['created'])]=identity
            except psutil.NoSuchProcess:continue
            except psutil.AccessDenied:
                save(list(targets.values()))
                raise RuntimeError('Cannot inspect owned descendants; identities preserved, cleanup not confirmed') from None
        save(list(targets.values()))
        live=[]
        for entry in reversed(list(targets.values())):
            try:
                process=alive(entry)
                if process is not None:
                    # A request child can appear after the first snapshot. Save
                    # its identity before letting this parent exit/orphan it.
                    for child in process.children(recursive=True):
                        identity={'pid':child.pid,'created':child.create_time(),'component':entry['component']}
                        targets[(identity['pid'],identity['created'])]=identity
                    save(list(targets.values()))
                    live.append(process)
                    process.terminate() if round_index==0 else process.kill()
            except psutil.NoSuchProcess:pass
            except psutil.AccessDenied:pass
        if live:psutil.wait_procs(live,timeout=2)
        survivors=[]
        for entry in targets.values():
            try:
                if alive(entry) is not None:survivors.append(entry)
            except psutil.AccessDenied:survivors.append(entry)
        save(survivors)
        if not survivors:return
    raise RuntimeError('Project cleanup incomplete; surviving identities preserved in state')


def service_mode():
    path=ROOT/'state/service-mode.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def fetch_health(port):
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/health',timeout=1) as response:
            data=json.load(response)
        return data if isinstance(data,dict) else {'alive':False}
    except (OSError,ValueError):return {'alive':False}


def port_open(port):
    with socket.socket() as sock:
        sock.settimeout(.2)
        return sock.connect_ex(('127.0.0.1',port))==0


def status_report():
    entries=read_state()
    counts={name:sum(1 for e in entries if e['component']==name and alive(e) is not None)
            for name in ('astrbot','model','gate','napcat')}
    mode_state=service_mode()
    mode=mode_state.get('mode','text')
    expected=('astrbot','gate','napcat','model') if mode=='text' else ('astrbot','gate','napcat')
    model=fetch_health(8765) if counts['model'] else {'alive':False}
    gate=fetch_health(6200) if counts['gate'] else {'alive':False}
    required_ports=(6185,6199,6200,6099,8765) if mode=='text' else (6185,6199,6200,6099)
    complete=all(counts[name] for name in expected) and all(port_open(p) for p in required_ports)
    if mode=='text':complete=complete and model.get('router_ready') is True and model.get('alive') is True
    phase='running' if complete else 'partial' if any(counts.values()) else 'stopped'
    if mode_state.get('phase')=='starting' and mode_state.get('owner') and alive(mode_state['owner']) is not None:
        phase='starting'
    channel=gate.get('channel_state','unknown') if counts['gate'] else 'disconnected'
    if phase=='stopped':channel='disconnected'
    try:
        from qqbot_gateway.backends import resolve_backend
        cfg=resolve_backend(load_settings(ROOT/'config/settings.local.yaml'))
        configured={'backend':cfg['backend'],'model':cfg['model']}
    except (ValueError,OSError):configured={'state':'unavailable'}
    return {'process_state':phase,'mode':mode,'processes':counts,'channel':gate,'channel_state':channel,
            'can_receive_group_messages':bool(complete and gate.get('connected') is True and
                 gate.get('self_id_verified') is True and gate.get('online') is True and not gate.get('stopping')),
            'model':model,'configured_profile':configured,'task_counts':task_counts()}


def task_counts():
    path=ROOT/'state/tasks.sqlite'
    if not path.exists():return {}
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.2)) as db:
            return dict(db.execute('SELECT status,count(*) FROM tasks GROUP BY status'))
    except sqlite3.Error:return {'unknown':None}


def show_status(report=None):
    report=report or status_report()
    phases={'stopped':'已停止','running':'组件在运行','partial':'组件不完整，请先关闭再启动'}
    channels={'waiting_login':'等待NapCat登录/QQ通道连接','connected':'QQ已连接',
              'disconnected':'QQ已断开或尚未连接','unknown':'登录状态未确认'}
    print('项目：'+phases.get(report['process_state'],'启动中'))
    print('QQ通道：'+channels.get(report['channel_state'],'登录状态未确认'))
    print('群消息：'+('可接收授权群真实@' if report['can_receive_group_messages'] else '尚未确认可接收'))
    model=report['model']
    configured=report.get('configured_profile',{})
    if configured.get('backend'):print('保存的后端（下次启动）：'+configured['backend']+'；模型：'+configured['model'])
    if model.get('backend'):print('当前后端：'+model['backend']+'；模型：'+str(model.get('model'))+'；元数据：'+str(model.get('metadata',{}).get('state'))+'；本次状态查询0生成')
    if not model.get('alive'):print('模型：网关未运行/不可达，本次未推理探测')
    else:
        error=model.get('current_error')
        if error:print('模型：当前错误 '+error.get('code','UNKNOWN'))
        elif model.get('last_success'):print('模型：最近成功 '+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(model['last_success'])))
        else:print('模型：本次启动未推理（not_probed）')
        old=model.get('last_error')
        if old and old.get('historical'):print('历史模型错误：'+old.get('code','UNKNOWN')+'（后来已有成功，不代表当前故障）')
    print('任务状态计数：'+json.dumps(report['task_counts'],ensure_ascii=False))
    if report['process_state']!='stopped' and report['channel_state']!='connected':
        print(f'请在本机 {NAPCAT_URL} 完成登录，再查看状态；不会自动重启或调用模型。')
    return report


def stop_project(grace=5):
    # Same OS lock as start and configuration writes, held through all cleanup.
    with configuration_lock(ROOT):
        entries=read_state()
        if not any(alive(e) is not None for e in entries):
            save([]);print('已停止。');return
        mode=service_mode()
        atomic_json(ROOT/'state/stop-request.json',{'instance_id':mode.get('instance_id'), 'time':time.time()})
        print('停止接收新任务，等待当前请求退出（最多5秒）……',flush=True)
        deadline=time.monotonic()+grace
        while time.monotonic()<deadline:
            model=fetch_health(8765) if any(e['component']=='model' and alive(e) is not None for e in entries) else {}
            tasks=task_counts()
            if model.get('active') is False and not model.get('queue') and not any(tasks.get(k,0) for k in ('accepted','running')):break
            time.sleep(.1)
        stop(entries)
        # Terminated tasks must never be replayed; preserve completed/send_unknown.
        path=ROOT/'state/tasks.sqlite'
        if path.exists():
            try:
                with closing(sqlite3.connect(path,timeout=1)) as db, db:
                    db.execute("UPDATE tasks SET status='unknown',updated=unixepoch() WHERE status IN ('accepted','running')")
            except sqlite3.Error:
                raise RuntimeError('Project processes stopped, but interrupted task state update failed; inspect local task database before restarting') from None
        print('项目后台bot已关闭。')


def check_port(port):
    with socket.socket() as sock:
        try:sock.bind(('127.0.0.1',port))
        except OSError:
            owners=[c.pid for c in psutil.net_connections('tcp') if c.laddr and c.laddr.port==port and c.status=='LISTEN']
            component={6185:'astrbot',6199:'astrbot',6200:'gate',6099:'napcat',8765:'model'}.get(port,'unknown')
            raise RuntimeError(f'PORT_CONFLICT component={component} port={port} pid={owners}')


def start_channel(full=False, paused=False):
    completed = False
    try:
        with configuration_lock(ROOT):
            _start_channel(full, paused)
        completed = True
    finally:
        print(f'\nNapCat 登录/管理：{NAPCAT_URL}')
        if not completed:print('本次启动未完成，页面可能暂不可访问。')


def _start_channel(full=False, paused=False):
    if any(alive(e) is not None for e in read_state()):
        report=status_report()
        if report['process_state']=='running' and (not full or report['mode']=='text'):
            print('已运行，无需重复启动。');show_status(report);return
        raise RuntimeError('PARTIAL_RUNNING: 组件不完整或运行模式不同，请先关闭再启动')
    gate=load_gate_config(ROOT/'config/settings.local.yaml')
    for port in ((6185,6199,6200,6099,8765) if full else (6185,6199,6200,6099)):check_port(port)
    backup=ROOT/'state/config-backups'/('startup-'+str(time.time_ns()))
    backup.mkdir(parents=True,exist_ok=True)
    config_before=ROOT/'runtime/astrbot/data/cmd_config.json'
    if config_before.exists():(backup/'astrbot-cmd-config.json').write_bytes(config_before.read_bytes())
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
        if (napcat_config/name).exists():(backup/name).write_bytes((napcat_config/name).read_bytes())
        (napcat_config/name).write_text(json.dumps(logging),encoding='utf-8')
    entries=[]
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    instance_id=uuid.uuid4().hex
    mode_record={'mode':'text' if full else 'channel_only','started':time.time(),'instance_id':instance_id,
                 'phase':'starting','owner':{'pid':os.getpid(),'created':psutil.Process().create_time()}}
    atomic_json(ROOT/'state/service-mode.json',mode_record)
    if paused:
        # Verification uses the ordinary stop marker from the first child onward.
        atomic_json(ROOT/'state/stop-request.json',{'instance_id':instance_id,'time':time.time()})
    else:
        (ROOT/'state/stop-request.json').unlink(missing_ok=True)
    env=os.environ.copy();env['QQBOT_INSTANCE_ID']=instance_id;env['PYTHONPATH']=str(ROOT/'src');env['PYTHONUTF8']='1';env['QQBOT_ROOT']=str(ROOT)
    specs=[('astrbot',[str(ROOT/'runtime/astrbot-bin/astrbot.exe'),'run'],ROOT/'runtime/astrbot',(6185,6199),25),
           ('gate',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.onebot_gate','--config',str(ROOT/'config/settings.local.yaml')],ROOT,(6200,),10),
           ('napcat',[str(NAPCAT/'NapCatWinBootMain.exe'),gate.bot_qq],NAPCAT,(6099,),30)]
    if full:specs.insert(1,('model',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.model_gateway','--config',str(ROOT/'config/settings.local.yaml')],ROOT,(8765,),30 if load_settings(ROOT/'config/settings.local.yaml')['llm']['backend']=='ollama_ssh' else 10))
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
                plugin_ready=True
                if full and component=='astrbot':
                    ready_file=ROOT/'state/router-ready.json'
                    try:
                        identity=json.loads(ready_file.read_text(encoding='utf-8'))
                        plugin_ready=identity.get('instance_id')==instance_id and alive(identity) is not None
                    except (OSError,ValueError,KeyError):plugin_ready=False
                if all(results) and plugin_ready:ready=True;break
                time.sleep(.2)
            if not ready:raise RuntimeError(f'{component.upper()}_STARTUP_NOT_READY; local logs/{component}.log')
            print(component.upper()+'_LOCAL_READY',flush=True)
    except BaseException:
        try:stop(entries)
        finally:
            mode_record['phase']='failed'
            atomic_json(ROOT/'state/service-mode.json',mode_record)
        raise
    mode_record['phase']='running'
    atomic_json(ROOT/'state/service-mode.json',mode_record)
    show_status()
    print('关闭此启动窗口不会停止后台bot；请使用关闭机器人.cmd。')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['start-channel','start-text','stop','status','test'])
    parser.add_argument('--no-pause',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--json',action='store_true',help='metadata status as JSON')
    args=parser.parse_args()
    try:
        if args.command=='start-channel':start_channel()
        elif args.command=='start-text':start_channel(full=True)
        elif args.command=='stop':stop_project()
        elif args.command=='status':
            report=status_report()
            print(json.dumps(report,ensure_ascii=False,indent=2)) if args.json else show_status(report)
        else:
            return subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
        return 0
    except (ValueError,RuntimeError,OSError,psutil.Error) as error:
        # Never print upstream command/config payloads or raw model errors.
        if isinstance(error,(ValueError,RuntimeError)):print(str(error))
        else:print('本机进程/文件操作失败，请检查项目状态和文件权限。')
        return 1


if __name__=='__main__':raise SystemExit(main())
