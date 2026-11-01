"""Small official desktop adapter. No private Snow API or login automation."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import webbrowser

import psutil

from .lifecycle import atomic_json
from .qq_transport import checked_path, resolve_transport

URL = 'http://127.0.0.1:5099'
COMPONENTS = ('official_snow', 'official_qq')
_LOG_PIPES = {}


def webui_port(root=None):
    root=Path(root or Path(__file__).resolve().parents[2])
    try:
        value=json.loads((root/'state/snowluma-webui.local.json').read_text(encoding='utf-8'))
        process=psutil.Process(value['pid'])
        if type(value['port']) is int and 1<=value['port']<=65535 and abs(process.create_time()-value['created'])<.01:
            return value['port']
    except (OSError,ValueError,KeyError,TypeError,psutil.Error):pass
    return 5099


def webui_url(root=None):return 'http://127.0.0.1:'+str(webui_port(root))


def actual_webui_port(process):
    """Follow official automatic port fallback, using only this created tree."""
    owned={process.pid,*(child.pid for child in process.children(recursive=True))}
    ports={c.laddr.port for c in psutil.net_connections('tcp') if c.pid in owned and c.status=='LISTEN'
           and c.laddr and c.laddr.ip in ('127.0.0.1','::1')}
    return next(iter(ports)) if len(ports)==1 else None


def log_pipe(root):
    root=Path(root).resolve()
    if root not in _LOG_PIPES:
        from scripts.log_collector import CollectorPipe
        from .config_files import read_project
        _LOG_PIPES[root]=CollectorPipe(root,read_project(root).settings.get('logging',{}))
    return _LOG_PIPES[root]


def close_log_pipe(root):
    pipe=_LOG_PIPES.pop(Path(root).resolve(),None)
    if pipe is not None:pipe.close()


def paths(root, settings):
    config = resolve_transport(settings)['snowluma']
    return (checked_path(root, config['runtime_root'], 'runtime'),
            checked_path(root, config['qq_executable'], 'runtime'))


def validate_package(package, qq):
    for path in (package/'node.exe', package/'index.mjs', package/'check-node-version.cjs', qq):
        if not path.is_file():
            raise RuntimeError('缺少官方启动材料：'+str(path)+'；请恢复本根材料后重试，不会自动安装。')


def connection_plan(root, settings, gate):
    package, _ = paths(root, settings)
    if not re.fullmatch(r'[0-9]+', str(gate.bot_qq)):
        raise ValueError('目标QQ账号配置无效。')
    if gate.host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('OneBot入口必须为本机回环地址。')
    path = checked_path(root, f'{package.relative_to(root).as_posix()}/config/onebot_{gate.bot_qq}.json', 'runtime')
    original = path.read_bytes() if path.exists() else None
    try:
        value = json.loads(original.decode('utf-8-sig')) if original is not None else dict(
            mode='snapshot', networks=dict(httpServers=[], httpClients=[], wsServers=[], wsClients=[]))
        networks = value.setdefault('networks', {})
        clients = networks.setdefault('wsClients', [])
        if not isinstance(clients, list) or any(not isinstance(c, dict) for c in clients):raise ValueError()
        matches = [c for c in clients if c.get('name') == 'qqbot-gate']
        if len(matches) > 1:raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError('目标OneBot配置无效或有重复qqbot-gate；请在本机检查该账号配置，原文件保留。') from None
    host = '[::1]' if gate.host == '::1' else gate.host
    desired = dict(name='qqbot-gate', enabled=True, url=f'ws://{host}:{gate.port}/ws',
                   role='Universal', messageFormat='array', reportSelfMessage=False,
                   reconnectIntervalMs=5000, accessToken=gate.inbound_token)
    # Preserve unknown fields on the managed connection as well as other networks.
    updated = deepcopy(matches[0]) if matches else {}
    updated.update(desired)
    changed = not matches or matches[0] != updated
    if matches:clients[clients.index(matches[0])] = updated
    else:clients.append(updated)
    return path, original, value, changed


def publish_connection(plan):
    path, original, value, changed = plan
    if not changed:return
    if (path.read_bytes() if path.exists() else None) != original:
        raise RuntimeError('OneBot配置已被其他程序修改，请重试；未覆盖。')
    if original is not None:
        backup = path.with_name(path.name+'.'+uuid.uuid4().hex+'.bak')
        with backup.open('xb') as stream:stream.write(original)
    atomic_json(path, value)


def discover(package, qq):
    """Read exact executable/entry paths; never infer ownership from a name."""
    result = {name: [] for name in COMPONENTS}
    for process in psutil.process_iter(['exe', 'cmdline']):
        try:
            exe = Path(process.info['exe']).resolve() if process.info['exe'] else None
            if exe == qq.resolve():result['official_qq'].append(process)
            elif exe and exe.name.casefold() in ('node.exe', 'node'):
                # The official bat can use a system Node. Exact entry/cwd still
                # identifies an external instance; it never grants ownership.
                args = process.info['cmdline'] or []
                cwd = None
                for arg in args[1:]:
                    candidate = Path(arg)
                    if not candidate.is_absolute():
                        cwd = cwd or Path(process.cwd())
                        candidate = cwd/candidate
                    if candidate.resolve() == (package/'index.mjs').resolve():
                        result['official_snow'].append(process);break
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):continue
    return result


def environment():
    # Do not inherit consent, auto-injection, bootstrap passwords or dev switches.
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith('SNOWLUMA_')}
    env.update(SNOWLUMA_WEBUI_HOST='127.0.0.1', SNOWLUMA_WEBUI_PORT='5099', SNOWLUMA_HOOK_AUTOLOAD='0')
    return env


def launch(component, package, qq, root):
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if component == 'official_snow' else 0
    env = environment()
    pipe = log_pipe(root)
    output = pipe.write_fd
    try:
        if component == 'official_snow':
            try:
                result = subprocess.run([str(package/'node.exe'), str(package/'check-node-version.cjs')],
                                        cwd=package, env=env, stdout=output, stderr=subprocess.STDOUT,
                                        creationflags=flags, timeout=30)
            except subprocess.TimeoutExpired:
                raise RuntimeError('官方Node版本检查超时，请查看Snow本机日志。') from None
            if result.returncode:raise RuntimeError('官方Node版本检查失败，请查看Snow本机日志；未启动Snow。')
        args = [str(package/'node.exe'), str(package/'index.mjs')] if component == 'official_snow' else [str(qq)]
        process = psutil.Popen(args, cwd=package if component == 'official_snow' else qq.parent,
                            env=env, stdout=output, stderr=subprocess.STDOUT, creationflags=flags)
        process._qqbot_log_collector = pipe.process
        return process
    except BaseException:
        close_log_pipe(root)
        raise


def open_page(root=None):
    url=webui_url(root)
    try:
        if webbrowser.open(url):return True
    except (OSError, webbrowser.Error):pass
    print('浏览器未打开，请手动打开：'+url)
    return False


def open_log(root):
    path = Path(root)/'logs/snowluma-startup.local.log'
    if not path.exists():
        print('本机启动日志尚未产生：'+str(path));return False
    try:os.startfile(str(path));return True
    except OSError:
        print('无法打开本机日志，请手动查看：'+str(path));return False


def wait_ready(process, ready, capture, timeout=20, *, root=None):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        capture()
        if root is None:
            if ready():return
        else:
            try:port=actual_webui_port(process)
            except (psutil.Error,OSError):port=None
            if port is not None:
                atomic_json(Path(root)/'state/snowluma-webui.local.json',dict(port=port,pid=process.pid,created=process.create_time()))
                return
        if not process.is_running():break
        time.sleep(.2)
    raise RuntimeError('Snow管理页未就绪，请查看Snow本机日志；仅回收本次新增进程。')
