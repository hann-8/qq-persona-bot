"""Manage only recorded project processes. No process-name based shutdown."""
import argparse
import asyncio
from contextlib import closing
import json
import math
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
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from qqbot_gateway.config import load_settings, load_gate_config, configuration_lock
from qqbot_gateway.config_files import (read_project, create_snapshot, snapshot_environment, load_consumer, prune_snapshots)
from qqbot_gateway.lifecycle import atomic_json, stopping
from qqbot_gateway.napcat_login import child_environment
from qqbot_gateway.transport_owner import loaded_provider, loaded_settings, require_runtime, TransportBlocked
from qqbot_gateway.qq_transport import resolve_transport
from qqbot_gateway.transport_owner import prepare_stop_control, startup_unknown
from qqbot_gateway.config import require_configuration_lease
from qqbot_gateway.transport_launch import OwnerWriter, snow_specs
from qqbot_gateway import official_snowluma as desktop


def alive(entry):
    try:
        process = psutil.Process(entry['pid'])
        same=(round(process.create_time()*1000)==round(entry['created']*1000) if entry.get('component') in
              ('snowluma','qq_client','transport_watch',*desktop.COMPONENTS) else abs(process.create_time()-entry['created'])<.01)
        return process if same and process.is_running() else None
    except psutil.NoSuchProcess:
        return None


def read_state():
    if not STATE.exists():return []
    entries=json.loads(STATE.read_text(encoding='utf-8'))
    if not isinstance(entries,list) or any(not isinstance(e,dict) or type(e.get('pid')) is not int or
            type(e.get('created')) not in (int,float) or not math.isfinite(e['created']) or not isinstance(e.get('component'),str) for e in entries):
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


def status_report(*,disk_config=None):
    entries=read_state()
    mode_state=service_mode()
    try:provider=loaded_provider(ROOT,mode_state)
    except (ValueError,OSError):
        return dict(provider='unknown',process_state='unknown',mode=mode_state.get('mode','unknown'),
            processes={},channel={},channel_state='unknown',can_receive_group_messages=False,
            configuration={'loaded':None,'disk':'unknown'},model={},configured_profile={'state':'unavailable'},
            task_counts=task_counts(),napcat_login={'state':'unavailable'},qq_login_state='transport_unavailable',
            qq_login_observation={'state':'not_applicable'},autostart=None,transport_code='LOADED_SNAPSHOT_INVALID')
    # Desktop identities do not count toward framework readiness.
    components=() if provider=='snowluma' else ('napcat',)
    counts={name:sum(1 for e in entries if e['component']==name and alive(e) is not None)
            for name in ('astrbot','model','gate')+components}
    mode=mode_state.get('mode','text')
    expected=('astrbot','gate')+components+(('model',) if mode=='text' else ())
    model=fetch_health(8765) if counts['model'] else {'alive':False}
    gate=fetch_health(6200) if counts['gate'] else {'alive':False}
    required_ports=(6185,6199,6200)+((6099,) if provider=='napcat' else ())+((8765,) if mode=='text' else ())
    complete=all(counts[name] for name in expected) and all(port_open(p) for p in required_ports)
    if mode=='text':complete=complete and model.get('router_ready') is True and model.get('alive') is True
    phase='running' if complete else 'partial' if any(counts.values()) else 'stopped'
    if mode_state.get('phase')=='starting' and mode_state.get('owner') and alive(mode_state['owner']) is not None:
        phase='starting'
    channel=gate.get('channel_state','unknown') if counts['gate'] else 'disconnected'
    if phase=='stopped':channel='disconnected'
    try:
        from qqbot_gateway.backends import resolve_backend
        if disk_config is None:disk_config=read_project(ROOT)
        settings=disk_config.settings
        cfg=resolve_backend(settings)
        configured={'backend':cfg['backend'],'model':cfg['model']}
        from qqbot_gateway.napcat_login import credential_status
        login_status=credential_status(ROOT,settings['bot']['qq']) if provider=='napcat' else {'state':'not_applicable'}
    except (ValueError,OSError):configured={'state':'unavailable'};login_status={'state':'unavailable'};disk_config=False
    from qqbot_gateway.napcat_login_observer import gate_state, listener_identity, historical_status
    current_gate=(listener_identity(entries,'gate',6200) if provider=='napcat' else gate.get('channel_ready') is True) if counts['gate'] else None
    qq_state=gate_state(gate,paused=mode_state.get('login_check_only') is True) if current_gate else 'transport_unavailable'
    return {'provider':provider,'desktop':desktop_status(settings, entries) if provider=='snowluma' and disk_config is not False else None,
            'transport_task':gate.get('transport_monitor',{'running':False}) if provider=='snowluma' else None,
            'autostart':autostart_status(),'qq_login_observation':historical_status(ROOT,mode_state.get('instance_id')) if provider=='napcat' else {'state':'not_applicable'},'qq_login_state':qq_state,'process_state':phase,'mode':mode,'processes':counts,'channel':gate,'channel_state':channel,
            'can_receive_group_messages':bool(complete and gate.get('connected') is True and
                 gate.get('self_id_verified') is True and gate.get('online') is True and not gate.get('stopping') and
                 (provider=='napcat' or gate.get('channel_ready') is True)),
            'configuration':configuration_status(mode_state,disk_config=disk_config,running=phase!='stopped'),
            'model':model,'configured_profile':configured,'task_counts':task_counts(),'napcat_login':login_status}


def configuration_status(mode_state,*,disk_config=None,running=True):
    loaded=mode_state.get('configuration') if running else None
    try:
        if disk_config is False:raise ValueError()
        disk=read_project(ROOT) if disk_config is None else disk_config
        return dict(loaded=loaded, disk=dict(layout=disk.layout,source_digest=disk.source_digest,
                    semantic_digest=disk.semantic_digest,files=list(disk.files)),
                    pending_restart=bool(loaded and loaded['semantic_digest']!=disk.semantic_digest),
                    source_changed=bool(loaded and loaded['source_digest']!=disk.source_digest))
    except (ValueError,OSError):return dict(loaded=loaded,disk='invalid',pending_restart=None)


def task_counts():
    path=ROOT/'state/tasks.sqlite'
    if not path.exists():return {}
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.2)) as db:
            return dict(db.execute('SELECT status,count(*) FROM tasks GROUP BY status'))
    except sqlite3.Error:return {'unknown':None}


def autostart_status():
    from qqbot_gateway.napcat_login import bounded_read, strict_json
    from qqbot_gateway.napcat_login_observer import STATES
    try:
        value=strict_json(bounded_read(ROOT/'state/autostart-status.json',16384))
        if value.get('schema_version')!=1 or value.get('phase') not in ('failed','finished'):return None
        if value.get('reason') not in STATES | {'dependency_timeout','start_blocked','already_running'}:return None
        return dict(phase=value['phase'],reason=value['reason'],historical=True)
    except (OSError,ValueError,AttributeError,TypeError):return None


def show_status(report=None):
    report=report or status_report()
    phases={'stopped':'已停止','running':'组件在运行','partial':'组件不完整，请先关闭再启动'}
    channels={'waiting_login':'等待NapCat登录/QQ通道连接','connected':'QQ已连接',
              'disconnected':'QQ已断开或尚未连接','unknown':'登录状态未确认'}
    if report.get('provider')=='snowluma':channels['waiting_login']='OneBot未接通；QQ登录状态未确认'
    print('项目：'+phases.get(report['process_state'],'启动中'))
    print('QQ通道：'+channels.get(report['channel_state'],'登录状态未确认'))
    if report.get('provider')=='snowluma':
        state=report.get('desktop') or {}
        print('Snow管理页：'+('本机端口可达（不代表QQ已连接）' if state.get('webui_listening') else '尚未监听')+'；'+desktop.URL)
        print('官方Snow/专用QQ：'+str(state.get('snow','未确认'))+' / '+str(state.get('qq','未确认')))
        print('OneBot：'+('已连接且就绪' if report.get('channel',{}).get('channel_ready') is True else '未就绪'))
    print('登录层：'+report.get('qq_login_state','unknown'))
    startup=report.get('autostart')
    if startup:print('开机启动最近结果（历史）：'+startup['phase']+'/'+startup['reason'])
    historical=report.get('qq_login_observation')
    if historical and report.get('provider','napcat')=='napcat':print('最近登录观测（历史原因，以当前通道为准）：'+historical['state'])
    gate=report.get('channel',{})
    if 'silence_enabled' in gate:print('临时停言：'+('开启' if gate['silence_enabled'] else '关闭')+'；当前静默群数：'+str(gate.get('muted_groups',0)))
    login_status=report.get('napcat_login',{})
    if login_status and report.get('provider','napcat')=='napcat':print('密码回退：'+login_status.get('state','unavailable')+'；数据归属：'+login_status.get('data_scope','unverified')+'；本实例尝试：'+login_status.get('attempt_state','unavailable'))
    print('群消息：'+('可接收授权群真实@' if report['can_receive_group_messages'] else '尚未确认可接收'))
    model=report['model']
    configured=report.get('configured_profile',{})
    if configured.get('backend'):print('保存的后端（下次启动）：'+configured['backend']+'；模型：'+configured['model'])
    if model.get('backend'):print('当前后端：'+model['backend']+'；模型：'+str(model.get('model'))+'；元数据：'+str(model.get('metadata',{}).get('state'))+'；本次状态查询0生成')
    if not model.get('alive'):print('模型：网关未运行/不可达，本次未推理探测')
    else:
        print('模型活动：'+('处理中' if model.get('active') else '空闲' if model.get('active') is False else '未确认'))
        error=model.get('current_error')
        if error:print('模型：当前错误 '+error.get('code','UNKNOWN'))
        elif model.get('last_success'):print('模型：最近成功 '+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(model['last_success'])))
        else:print('模型：本次启动未推理（not_probed）')
        old=model.get('last_error')
        if old and old.get('historical'):print('历史模型错误：'+old.get('code','UNKNOWN')+'（后来已有成功，不代表当前故障）')
    configuration=report.get('configuration',{})
    if configuration.get('loaded'):print('当前实例配置快照：'+configuration['loaded']['snapshot_digest'])
    if configuration.get('pending_restart'):print('磁盘配置已改变，待关闭后正常启动加载。')
    if configuration.get('disk')=='invalid':print('磁盘配置无效；当前实例继续使用已加载快照。')
    print('任务状态计数：'+json.dumps(report['task_counts'],ensure_ascii=False))
    if report['process_state']!='stopped' and report['channel_state']!='connected':
        if report.get('provider','napcat')=='napcat':
            print(f'请在本机 {NAPCAT_URL} 完成登录，再查看状态；不会自动重启或调用模型。')
        else:print('OneBot尚未就绪；请打开SnowLuma管理页，确认条款、选择专用QQ并登录/扫码，再查看状态。')
    return report


def stop_project(grace=5,*,expected_instance=None):
    # Freeze identities and reserve command sequence under the unique writer lock.
    # Network never holds that lock; admission is already revoked by the marker.
    control=None;control_code=None
    with configuration_lock(ROOT) as lease:
        mode=service_mode()
        if expected_instance is not None and (mode.get('instance_id')!=expected_instance or mode.get('provider')!='snowluma'):
            raise ValueError('TRIAL_STOP_INSTANCE_CHANGED')
        # Revocation precedes cleanup and does not depend on a readable snapshot.
        # Only recorded PID/create identities authorize termination below.
        atomic_json(ROOT/'state/stop-request.json',{'instance_id':mode.get('instance_id'),'time':time.time()})
        entries=read_state()
        if not any(alive(e) is not None for e in entries):
            if startup_unknown(ROOT):raise RuntimeError('TRANSPORT_CREATION_UNKNOWN')
            save([]);print('已停止。');external_desktop_notice(mode);return
        if mode.get('provider')=='snowluma' and mode.get('transport_mode')!='official_onebot':
            try:control=prepare_stop_control(ROOT,mode,lease,process=psutil.Process)
            except (ValueError,OSError,KeyError,TypeError,psutil.Error):control_code='CONTROL_UNAVAILABLE'
    if control is not None:
        try:control_code=asyncio.run(control.run())
        except (ValueError,OSError,TimeoutError):control_code='ACK_UNKNOWN'
    with configuration_lock(ROOT):
        # A new instance/registry may have appeared while the network was awaited.
        if service_mode().get('instance_id')!=mode.get('instance_id') or read_state()!=entries:
            raise RuntimeError('TRANSPORT_STOP_OWNERSHIP_CHANGED')
        if control_code:print('TRANSPORT_STOP code='+control_code,flush=True)
        print('停止接收新任务，等待当前请求退出（最多5秒）……',flush=True)
        deadline=time.monotonic()+grace
        while time.monotonic()<deadline:
            model=fetch_health(8765) if any(e['component']=='model' and alive(e) is not None for e in entries) else {}
            tasks=task_counts()
            if model.get('active') is False and not model.get('queue') and not any(tasks.get(k,0) for k in ('accepted','running')):break
            time.sleep(.1)
        stop_in_order(entries)
        if startup_unknown(ROOT):raise RuntimeError('TRANSPORT_CREATION_UNKNOWN')
        # Terminated tasks must never be replayed; preserve completed/send_unknown.
        path=ROOT/'state/tasks.sqlite'
        if path.exists():
            try:
                with closing(sqlite3.connect(path,timeout=1)) as db, db:
                    db.execute("UPDATE tasks SET status='unknown',updated=unixepoch() WHERE status IN ('accepted','running')")
            except sqlite3.Error:
                raise RuntimeError('Project processes stopped, but interrupted task state update failed; inspect local task database before restarting') from None
        print('项目后台bot已关闭。')
        external_desktop_notice(mode)


def stop_in_order(entries):
    official=[e for e in entries if e['component'] in desktop.COMPONENTS]
    if not official:return stop(entries)
    framework=[e for e in entries if e['component'] not in desktop.COMPONENTS]
    try:stop(framework)
    finally:save(read_state()+official)
    # Snow exits before the interactive QQ instance. Preserve remaining QQ IDs
    # even if Snow cleanup fails.
    snow=[e for e in official if e['component']=='official_snow']
    qq=[e for e in official if e['component']=='official_qq']
    try:stop(snow)
    finally:save(read_state()+qq)
    stop(qq)


def external_desktop_notice(mode):
    if mode.get('provider')!='snowluma':return
    try:
        package,qq=desktop.paths(ROOT,loaded_settings(ROOT,mode))
        if any(desktop.discover(package,qq).values()):
            print('外部手动运行或身份未确认的Snow/QQ已保留；需要时请在其窗口正常退出。')
    except (ValueError,OSError,psutil.Error):
        print('未登记的Snow/QQ不会关闭；需要时请在其窗口正常退出。')


def desktop_status(settings, entries):
    package,qq=desktop.paths(ROOT,settings)
    found=desktop.discover(package,qq)
    def label(component):
        if any(e['component']==component and alive(e) is not None for e in entries):return '脚本创建，运行中'
        return '外部实例，保留' if found[component] else '未发现'
    return dict(webui_listening=port_open(5099),snow=label('official_snow'),qq=label('official_qq'))


def start_desktop(channel_only=False):
    with configuration_lock(ROOT) as lease:
        project=read_project(ROOT)
        existing=read_state()
        live=any(alive(e) is not None for e in existing)
        # An existing framework keeps its actual loaded account/token/paths.
        settings=loaded_settings(ROOT,service_mode()) if live else project.settings
        if resolve_transport(settings)['provider']!=resolve_transport(project.settings)['provider']:
            raise RuntimeError('运行实例与磁盘provider不同；请先关闭本根实例再启动。')
        if resolve_transport(settings)['provider']=='napcat':
            try:return _start_channel(full=not channel_only,lease=lease)
            finally:print(f'\nNapCat 登录/管理：{NAPCAT_URL}')
        package,qq=desktop.paths(ROOT,settings)
        desktop.validate_package(package,qq)
        gate=load_gate_config(root=ROOT,settings=settings)
        plan=desktop.connection_plan(ROOT,settings,gate)
        found=desktop.discover(package,qq)
        # A registry identity remains decisive when command-line inspection is denied.
        for component in desktop.COMPONENTS:
            for entry in existing:
                if entry['component']==component:
                    process=alive(entry)
                    if process is not None and all(p.pid!=process.pid for p in found[component]):found[component].append(process)
        if found['official_snow'] and plan[3]:
            raise RuntimeError('Snow已运行，目标OneBot连接需同步。请先在Snow窗口/管理页正常退出Snow（QQ可保留），再双击启动机器人.cmd；脚本会自动备份并同步，无需手填JSON/token。现有项目组件保持运行。')
        if port_open(5099):
            permitted=set()
            for process in found['official_snow']:
                permitted.add(process.pid)
                permitted.update(p.pid for p in process.children(recursive=True))
            listeners=[c for c in psutil.net_connections('tcp') if c.laddr and c.laddr.port==5099 and c.status=='LISTEN']
            if not listeners or any(c.pid not in permitted or c.laddr.ip not in ('127.0.0.1','::1') for c in listeners):
                raise RuntimeError('5099端口被未确认或非回环实例占用；请正常退出冲突程序后重试，脚本不会终止它。')
        try:
            desktop.publish_connection(plan)
            _start_channel(full=not channel_only,lease=lease)
            entries=read_state()
            for component in ('official_qq','official_snow'):
                if found[component]:
                    print(('Snow' if component=='official_snow' else '专用QQ')+'已存在，复用且不接管外部身份。')
                    continue
                process=desktop.launch(component,package,qq,ROOT)
                remember(entries,process,component)
                capture(entries,process,component,time.time())
                if component=='official_snow':
                    desktop.wait_ready(process,lambda:port_open(5099),
                        lambda:capture(entries,process,component,time.time()))
            show_status()
        except BaseException:
            new=[e for e in read_state() if e not in existing]
            try:stop_in_order(new)
            finally:
                survivors=[e for e in read_state() if e not in existing]
                save(existing+survivors)
            raise
    desktop.open_page()
    print('首次请在官方页面阅读/确认条款、登录管理页、选择本根专用QQ进程并扫码。')
    print('管理账号/初始密码请双击“查看Snow本机日志.cmd”在本机查看；统一状态不显示密码。')
    print('关闭此窗口不会停止机器人；请使用“关闭机器人.cmd”。')


def check_port(port):
    with socket.socket() as sock:
        try:sock.bind(('127.0.0.1',port))
        except OSError:
            owners=[c.pid for c in psutil.net_connections('tcp') if c.laddr and c.laddr.port==port and c.status=='LISTEN']
            component={6185:'astrbot',6199:'astrbot',6200:'gate',6099:'napcat',8765:'model'}.get(port,'unknown')
            raise RuntimeError(f'PORT_CONFLICT component={component} port={port} pid={owners}')


def _snow_framework_specs(snapshot,full,settings):
    specs=[('astrbot',[str(ROOT/'runtime/astrbot-bin/astrbot.exe'),'run'],ROOT/'runtime/astrbot',(6185,6199),25),
        ('gate',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.onebot_gate','--root',str(ROOT),'--config',str(snapshot)],ROOT,(6200,),10)]
    if full:specs.insert(1,('model',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.model_gateway',
        '--root',str(ROOT),'--config',str(snapshot)],ROOT,(8765,),30 if settings['llm']['backend']=='ollama_ssh' else 10))
    return specs


def _configure_snow_framework(gate,full,env):
    """Same restricted AstrBot platform contract as the existing NapCat path."""
    if full:
        result=subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),str(ROOT/'scripts/configure_astrbot.py')],
            cwd=ROOT/'runtime/astrbot',capture_output=True,env=env)
        if result.returncode:raise RuntimeError('CONFIG_PREPARE_FAILED')
    path=ROOT/'runtime/astrbot/data/cmd_config.json'
    config=json.loads(path.read_text(encoding='utf-8-sig'))
    config['platform']=[dict(id='qqbot',type='aiocqhttp',enable=True,ws_reverse_host='127.0.0.1',ws_reverse_port=6199,ws_reverse_token=gate.upstream_token)]
    config['platform_settings'].update(dict(unique_session=True,enable_id_white_list=True,id_whitelist=sorted(gate.allowed_groups),
        wl_ignore_admin_on_group=False,wl_ignore_admin_on_friend=False,ignore_bot_self_message=True,ignore_at_all=True,
        empty_mention_waiting=False,empty_mention_waiting_need_reply=False))
    config['wake_prefix']=[];config['admins_id']=sorted(gate.admin_users);config['log_level']='ERROR'
    config['provider_settings']['enable']=full;config['provider_settings']['streaming_response']=False
    config['provider_settings']['proactive_capability']['add_cron_tools']=False
    config['provider_settings']['computer_use_runtime']='none'
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8-sig')


def _launch_snow_component(spec,env):
    # No upstream stdout/stderr ever reaches a log file, including startup errors.
    return psutil.Popen(list(spec.argv),cwd=spec.cwd,env=env,stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)


def _snow_environment(environment):
    """Per-child policy, never a global/user environment mutation or override."""
    env={key:value for key,value in child_environment(environment).items()
        if not key.upper().startswith('SNOWLUMA_') and key.upper() not in ('NODE_OPTIONS','NODE_PATH')}
    env.update(SNOWLUMA_HOOK_AUTOLOAD='0',SNOWLUMA_TELEMETRY='0')
    return env


def _wait_snow_owner(owner,timeout):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if stopping(ROOT,owner.binding.instance_id):raise RuntimeError('TRANSPORT_STOP_REQUESTED')
        if owner.identity_current(owner.binding):return
        time.sleep(.2)
    raise RuntimeError('TRANSPORT_OWNER_NOT_READY')


def _launch_snow_framework(specs,env,entries,snapshot,full):
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    for component,args,cwd,ports,timeout in specs:
        load_consumer(ROOT,snapshot,environ=env)
        with (logs/(component+'.log')).open('ab') as output:
            process=psutil.Popen([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/process_host.py'),component,'--',*args],
                cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        started=time.time();deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            capture(entries,process,component,started)
            ready=all(port_open(port) for port in ports)
            if full and component=='astrbot':
                try:
                    identity=json.loads((ROOT/'state/router-ready.json').read_text(encoding='utf-8'))
                    mode=service_mode()
                    ready=ready and identity.get('instance_id')==mode['instance_id'] and identity.get('config_digest')==mode['configuration']['snapshot_digest'] and alive(identity) is not None
                except (OSError,ValueError,KeyError):ready=False
            if ready:break
            time.sleep(.2)
        else:raise RuntimeError('TRANSPORT_FRAMEWORK_NOT_READY')


def _start_snow_channel(project,layout,full,paused,lease):
    """Called only after qualification; tests inject a synthetic qualification.

    No CLI/config bypass exists: require_runtime currently always rejects before
    this function can write an instance or invoke the creation callback.
    """
    require_configuration_lease(ROOT,lease)
    if read_state():raise RuntimeError('TRANSPORT_REGISTRY_NOT_EMPTY')
    from qqbot_gateway.transport_owner import read_control_key
    from qqbot_gateway.vision import require_production
    from qqbot_gateway.vision import context_token
    from qqbot_gateway.meme_import import admin_token
    settings=project.settings;require_production(settings,root=ROOT)
    gate=load_gate_config(root=ROOT,settings=settings)
    read_control_key(ROOT,settings,(gate.inbound_token,gate.upstream_token,admin_token(ROOT),context_token(ROOT)))
    instance=uuid.uuid4().hex;epoch=uuid.uuid4().hex+uuid.uuid4().hex
    snapshot,metadata=create_snapshot(project,instance)
    specs=snow_specs(ROOT,settings,snapshot,metadata,layout)
    cfg=resolve_transport(settings)['snowluma']
    for port in (6185,6199,6200,cfg['control_port'])+((8765,) if full else ()):check_port(port)
    env=child_environment(os.environ);env.update(snapshot_environment(ROOT,snapshot,metadata))
    env.update(PYTHONPATH=str(ROOT/'src'),PYTHONUTF8='1')
    transport_env=_snow_environment(env)
    previous=ROOT/'runtime/astrbot/data/cmd_config.json'
    if previous.exists():
        backup=ROOT/'state/config-backups'/('startup-'+str(time.time_ns()))
        backup.mkdir(parents=True,exist_ok=False)
        (backup/'astrbot-cmd-config.json').write_bytes(previous.read_bytes())
    _configure_snow_framework(gate,full,env)
    mode=dict(mode='text' if full else 'channel_only',provider='snowluma',instance_id=instance,
        configuration=metadata,phase='starting',login_check_only=paused)
    atomic_json(ROOT/'state/service-mode.json',mode)
    (ROOT/'state/stop-request.json').unlink(missing_ok=True)
    writer=OwnerWriter(ROOT,lease,instance,process=psutil.Process)
    try:
        for spec in specs:writer.create(spec,lambda item:_launch_snow_component(item,transport_env))
        owner=writer.register(settings,metadata,snapshot,layout,epoch)
        _wait_snow_owner(owner,cfg['ready_timeout_seconds'])
        if paused:atomic_json(ROOT/'state/stop-request.json',dict(instance_id=instance,time=time.time()))
        _launch_snow_framework(_snow_framework_specs(snapshot,full,settings),env,read_state(),snapshot,full)
    except BaseException:
        atomic_json(ROOT/'state/stop-request.json',dict(instance_id=instance,time=time.time()))
        mode['phase']='failed';atomic_json(ROOT/'state/service-mode.json',mode)
        stop(read_state());raise
    mode['phase']='running';atomic_json(ROOT/'state/service-mode.json',mode)
    return dict(provider='snowluma',instance_id=instance,state='starting')


def start_channel(full=False, paused=False, *, login_diagnostics=False, wait_login_seconds=0, expected_source_digest=None):
    completed = False
    snow_blocked=False
    try:
        with configuration_lock(ROOT) as lease:
            if expected_source_digest is not None:
                project=read_project(ROOT)
                if project.source_digest!=expected_source_digest or resolve_transport(project.settings)['provider']!='snowluma':
                    raise ValueError('TRIAL_START_SOURCE_CHANGED')
            observation = _start_channel(full, paused, lease=lease)
            observer=None
            if observation and not isinstance(observation,dict) and service_mode().get('provider')=='napcat' and (login_diagnostics or wait_login_seconds):
                from qqbot_gateway.napcat_login_observer import Observation
                instance,account=observation
                observer=Observation(ROOT,instance,account,entries=read_state,mode=service_mode,
                                     gate_health=lambda:fetch_health(6200),paused=paused)
        completed = True
        if isinstance(observation,dict):return observation
        # Only a new instance is returned; polling is outside the lifecycle lock.
        if observer is not None:
            result=observer.run(wait_login_seconds or 120,diagnostics=login_diagnostics)
            print('QQ_LOGIN_STATE '+result['state'],flush=True)
            return dict(state=result['state'],instance_id=instance)
        return {'state':'already_running' if observation is None else 'starting'}
    except TransportBlocked:
        snow_blocked=True
        raise
    finally:
        try:snow_mode=snow_blocked or service_mode().get('provider')=='snowluma'
        except (ValueError,OSError,AttributeError):snow_mode=snow_blocked
        if not snow_mode:print(f'\nNapCat 登录/管理：{NAPCAT_URL}')
        if not completed:print('本次启动未完成，页面可能暂不可访问。')


def _start_channel(full=False, paused=False, *, lease=None):
    if startup_unknown(ROOT):raise RuntimeError('TRANSPORT_CREATION_UNKNOWN')
    if any(alive(e) is not None for e in read_state()):
        report=status_report()
        if report['process_state']=='running' and (not full or report['mode']=='text') and service_mode().get('login_check_only',False)==paused:
            print('已运行，无需重复启动。');show_status(report);return
        raise RuntimeError('PARTIAL_RUNNING: 组件不完整或运行模式不同，请先关闭再启动')
    project_config=read_project(ROOT)
    from qqbot_gateway.qq_transport import resolve_transport
    transport=resolve_transport(project_config.settings)
    if project_config.extensions:print('已保留旧顶层扩展字段；不保证扩展具有运行功能。')
    from qqbot_gateway.vision import require_production
    require_production(project_config.settings,root=ROOT)
    instance_id=uuid.uuid4().hex
    prune_snapshots(ROOT,keep=2)
    snapshot,metadata=create_snapshot(project_config,instance_id)
    config_env=snapshot_environment(ROOT,snapshot,metadata)
    env=child_environment(os.environ);env.update(config_env)
    env['PYTHONPATH']=str(ROOT/'src');env['PYTHONUTF8']='1'
    gate=load_gate_config(root=ROOT,settings=project_config.settings)
    ports=(6185,6199,6200)+((6099,) if transport['provider']=='napcat' else ())+((8765,) if full else ())
    for port in ports:check_port(port)
    backup=ROOT/'state/config-backups'/('startup-'+str(time.time_ns()))
    backup.mkdir(parents=True,exist_ok=True)
    config_before=ROOT/'runtime/astrbot/data/cmd_config.json'
    if config_before.exists():(backup/'astrbot-cmd-config.json').write_bytes(config_before.read_bytes())
    if full:
        result=subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),str(ROOT/'scripts/configure_astrbot.py')],
                              cwd=ROOT/'runtime/astrbot',capture_output=True,env=env)
        if result.returncode:
            (ROOT/'runtime/astrbot/configure-error.log').write_bytes(result.stdout+result.stderr)
            raise RuntimeError('CONFIG_PREPARE_FAILED; local runtime/astrbot/configure-error.log')
    load_consumer(ROOT,snapshot,environ=env)
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
    # WebUI owns core settings. Back up existing files without rewriting them;
    # NapCat initializes missing files using its own defaults.
    for name in ('napcat.json','napcat_'+gate.bot_qq+'.json'):
        if transport['provider']=='napcat' and (napcat_config/name).exists():(backup/name).write_bytes((napcat_config/name).read_bytes())
    entries=[]
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    mode_record={'mode':'text' if full else 'channel_only','started':time.time(),'instance_id':instance_id,
                 'provider':transport['provider'],
                 'transport_mode':'official_onebot' if transport['provider']=='snowluma' else 'managed_napcat',
                 'login_check_only':paused and not full,'configuration':metadata,'phase':'starting','owner':{'pid':os.getpid(),'created':psutil.Process().create_time()}}
    atomic_json(ROOT/'state/service-mode.json',mode_record)
    if paused:
        # Verification uses the ordinary stop marker from the first child onward.
        atomic_json(ROOT/'state/stop-request.json',{'instance_id':instance_id,'time':time.time()})
    else:
        (ROOT/'state/stop-request.json').unlink(missing_ok=True)
    specs=_snow_framework_specs(snapshot,full,project_config.settings)
    if transport['provider']=='napcat':
        specs.append(('napcat',[str(NAPCAT/'NapCatWinBootMain.exe'),gate.bot_qq],NAPCAT,(6099,),30))
    try:
        for component,args,cwd,ports,timeout in specs:
            load_consumer(ROOT,snapshot,environ=env)
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
                        plugin_ready=(identity.get('instance_id')==instance_id and
                                      identity.get('config_digest')==metadata['snapshot_digest'] and alive(identity) is not None)
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
    if not paused and transport['provider']=='napcat':
        from qqbot_gateway.napcat_login_client import startup_fallback
        def ready_channel():
            value=fetch_health(6200)
            return (value.get('connected') is True and value.get('self_id_verified') is True and
                    value.get('online') is True and not value.get('stopping'))
        reason=startup_fallback(ROOT,NAPCAT,instance_id,gate.bot_qq,entries=read_state,channel_ready=ready_channel)
        print('NAPCAT_LOGIN_FALLBACK '+reason,flush=True)
    show_status(status_report(disk_config=project_config))
    print('关闭此启动窗口不会停止后台bot；请使用关闭机器人.cmd。')
    return instance_id,gate.bot_qq


def require_intake_logging(bot):
    """No logging reconfiguration: refuse unsafe/unknown existing file logs."""
    from qqbot_gateway.napcat_login import bounded_read, strict_json
    base=NAPCAT/'versions/9.9.33-52230/resources/app/napcat/config'
    for name in ('napcat.json','napcat_'+bot+'.json'):
        path=base/name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):raise ValueError('INTAKE_LOGGING_UNVERIFIED')
        try:value=strict_json(bounded_read(path,16384))
        except (OSError,ValueError):raise ValueError('INTAKE_LOGGING_UNVERIFIED') from None
        if not isinstance(value,dict) or value.get('fileLog') is not False:raise ValueError('INTAKE_FILE_LOGGING_DENIED')


def intake_only(*, authorize, group, sender, max_events=1, timeout_seconds=120):
    """Separate opt-in transaction. Never calls normal start/login/fallback.

    Reuses this manager's lock, snapshots, process creation ledger, capture and
    identity-checked cleanup. The lock covers the entire short diagnostic lease.
    """
    from qqbot_gateway.config import require_stopped
    from qqbot_gateway.cleanup_identity import CleanupOwner
    from qqbot_gateway.vision_ingress import validate_record
    if authorize!='ONE_IMAGE_INGRESS' or max_events!=1 or type(timeout_seconds) is not int or not 1<=timeout_seconds<=120:
        raise ValueError('INTAKE_AUTHORIZATION_REQUIRED')
    with configuration_lock(ROOT):
        require_stopped(ROOT)
        if CleanupOwner(ROOT).status()['blocked']:raise ValueError('INTAKE_CLEANUP_UNRESOLVED')
        if any(v for k,v in task_counts().items() if k in ('accepted','running','unknown','send_unknown')):
            raise ValueError('INTAKE_TASK_UNRESOLVED')
        for port in (6185,6199,6200,6099,8765):check_port(port)
        project=read_project(ROOT)
        from qqbot_gateway.vision import require_production
        require_production(project.settings,root=ROOT)
        gate=load_gate_config(root=ROOT,settings=project.settings)
        if group not in gate.allowed_groups or not group or not sender or sender in gate.blocked_users or sender==gate.bot_qq:
            raise ValueError('INTAKE_TARGET_DENIED')
        from qqbot_gateway.config import qq_id
        if qq_id(sender)!=sender:raise ValueError('INTAKE_TARGET_DENIED')
        require_intake_logging(gate.bot_qq)
        instance=uuid.uuid4().hex
        snapshot,metadata=create_snapshot(project,instance)
        env=child_environment(os.environ);env.update(snapshot_environment(ROOT,snapshot,metadata))
        env.update(PYTHONPATH=str(ROOT/'src'),PYTHONUTF8='1',QQBOT_INTAKE_GROUP=group,QQBOT_INTAKE_SENDER=sender)
        mode=dict(mode='intake_only',instance_id=instance,phase='starting',configuration=metadata,
                  owner=dict(pid=os.getpid(),created=psutil.Process().create_time()))
        atomic_json(ROOT/'state/service-mode.json',mode)
        evidence=ROOT/'state/vision-evidence'/(instance+'.json')
        logs=ROOT/'logs';logs.mkdir(exist_ok=True)
        entries=[];result=dict(state='failed_or_unknown',record=None)
        # Deliberately no account/quick-login argument, credentials or password
        # fallback. Manual login is a separately authorized operator action.
        specs=(('gate',[str(ROOT/'.venv/Scripts/python.exe'),'-m','qqbot_gateway.vision_intake_gate',
                       '--root',str(ROOT),'--config',str(snapshot),'--instance',instance,'--timeout',str(timeout_seconds)],ROOT),
               ('napcat',[str(NAPCAT/'NapCatWinBootMain.exe')],NAPCAT))
        owners=[];deadline=time.monotonic()+timeout_seconds
        try:
            for component,args,cwd in specs:
                started=time.time()
                with (logs/('intake-'+component+'.log')).open('ab') as output:
                    process=psutil.Popen([str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'scripts/process_host.py'),component,'--',*args],
                        cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                owners.append((process,component,started))
                capture(entries,process,component,started)
                if not entries:raise RuntimeError('INTAKE_IDENTITY_UNVERIFIED')
                if component=='gate':
                    gate_deadline=min(deadline,time.monotonic()+10)
                    while time.monotonic()<gate_deadline:
                        capture(entries,process,component,started)
                        health=fetch_health(gate.port)
                        if (health.get('intake_only') is True and health.get('instance_id')==instance and
                            any(e['component']=='gate' and e['pid']==health.get('pid') and
                                e['created']==health.get('created') and alive(e) is not None for e in entries)):break
                        if process.poll() is not None:raise RuntimeError('INTAKE_GATE_FAILED')
                        time.sleep(.1)
                    else:raise RuntimeError('INTAKE_GATE_TIMEOUT')
            mode['phase']='running';atomic_json(ROOT/'state/service-mode.json',mode)
            while time.monotonic()<deadline:
                for process,component,started in owners:capture(entries,process,component,started)
                if evidence.exists():
                    raw=evidence.read_bytes()
                    if len(raw)>4096:raise ValueError('INTAKE_EVIDENCE_INVALID')
                    from qqbot_gateway.reply_plan import _pairs
                    value=json.loads(raw,object_pairs_hook=_pairs)
                    if (not isinstance(value,dict) or set(value)!={'state','record'} or
                        value['state'] not in ('observed','cancelled','timeout','login_required')):raise ValueError('INTAKE_EVIDENCE_INVALID')
                    if value['record'] is not None:validate_record(value['record'])
                    result=value;break
                if any(process.poll() is not None for process,_,_ in owners[:1]):break
                time.sleep(.1)
            else:
                result=dict(state='timeout' if fetch_health(gate.port).get('online') else 'login_required',record=None)
        except KeyboardInterrupt:result=dict(state='cancelled',record=None)
        finally:
            # Final discovery precedes termination, including launcher children.
            # No pre-existing identities are ever handed to stop().
            mode['phase']='cleanup_failed'
            try:
                try:
                    for process,component,started in owners:capture(entries,process,component,started)
                finally:stop(entries)
                mode['phase']='finished'
            finally:
                atomic_json(ROOT/'state/service-mode.json',mode)
        return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['start-desktop','open-snow','snow-log','start-channel','start-text','stop','status','test','cleanup'])
    parser.add_argument('cleanup_action',nargs='?',choices=['status','check','recover'])
    parser.add_argument('--no-pause',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--json',action='store_true',help='metadata status as JSON')
    parser.add_argument('--channel-only',action='store_true')
    parser.add_argument('--login-check-only',action='store_true')
    parser.add_argument('--login-diagnostics',action='store_true')
    parser.add_argument('--wait-login-seconds',type=int,default=0)
    args=parser.parse_args()
    if args.channel_only and args.command!='start-desktop':parser.error('--channel-only requires start-desktop')
    if args.login_check_only and args.command!='start-channel':parser.error('--login-check-only requires start-channel')
    if not 0<=args.wait_login_seconds<=300:parser.error('--wait-login-seconds must be 0..300')
    if (args.login_diagnostics or args.wait_login_seconds) and args.command not in ('start-channel','start-text'):
        parser.error('login observation requires a start command')
    try:
        if args.command=='start-desktop':start_desktop(channel_only=args.channel_only)
        elif args.command=='open-snow':return 0 if desktop.open_page() else 1
        elif args.command=='snow-log':return 0 if desktop.open_log(ROOT) else 1
        elif args.command in ('start-channel','start-text'):
            start_channel(full=args.command=='start-text',paused=args.login_check_only,
                          login_diagnostics=args.login_diagnostics,wait_login_seconds=args.wait_login_seconds)
        elif args.command=='stop':stop_project()
        elif args.command=='status':
            report=status_report()
            print(json.dumps(report,ensure_ascii=False,indent=2)) if args.json else show_status(report)
        elif args.command=='cleanup':
            # No model calls or bot start/stop. Recovery is explicit maintenance.
            import asyncio
            from qqbot_gateway.cleanup_identity import CleanupOwner
            if args.cleanup_action=='recover':
                from scripts.cleanup_recovery import recover
                report=recover(ROOT)
            else:
                owner=CleanupOwner(ROOT)
                report=asyncio.run(owner.check()) if args.cleanup_action=='check' else owner.status()
            print(json.dumps(report,ensure_ascii=False,indent=2))
        else:
            return subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
        return 0
    except (ValueError,RuntimeError,OSError,psutil.Error) as error:
        # Never print upstream command/config payloads or raw model errors.
        if isinstance(error,(ValueError,RuntimeError)):print(str(error))
        else:print('本机进程/文件操作失败，请检查项目状态和文件权限。')
        return 1


if __name__=='__main__':raise SystemExit(main())
