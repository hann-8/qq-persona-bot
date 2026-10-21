"""Discard upstream output; retain only explicit local transport/model metadata."""
import argparse
import re
import subprocess
import time


class BoundedLines:
    """Discard the entire oversized logical line, including later fragments."""
    def __init__(self):self.buffer=b'';self.discard=False
    def feed(self, chunk):
        for index, part in enumerate(chunk.split(b'\n')):
            if index:
                if not self.discard:yield self.buffer.decode('utf-8',errors='replace')
                self.buffer=b'';self.discard=False
            if not self.discard:
                if len(self.buffer)+len(part)>16384:self.buffer=b'';self.discard=True
                else:self.buffer+=part


def login_event(line):
    if len(line.encode('utf-8'))>16384:return None
    line=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',line).strip()
    line=re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[(?:info|warn|error)\] ?','',line,flags=re.I)
    patterns=[(r'需要验证码, proofWaterUrl: .*','verification_required'),
              (r'新设备需要扫码验证, jumpUrl: .*','verification_required'),
              (r'异常设备需要验证, jumpUrl: .*','verification_required'),
              (r'密码回退需要(?:验证码|新设备验证)，请在 WebUi 中继续完成验证.*','verification_required'),
              (r'正在快速登录 +[0-9]{5,20}', 'quick_login_started'),
              (r'快速登录错误：.*', 'quick_login_failed'),
              (r'快速登录异常：.*', 'quick_login_failed'),
              (r'快速登录失败，未找到该 QQ 历史登录记录，将尝试密码回退登录', 'native_history_missing_hint'),
              (r'没有 -q 指令指定快速登录，将使用二维码登录方式', 'quick_target_missing'),
              (r'\[NapCat\] \[WebUi\] 自动快速登录失败: .*','quick_login_failed'),
              (r'\[NapCat\] \[WebUi\] 自动快速登录成功: [0-9]{5,20}','quick_login_success_hint'),
              (r'\[NapCat\] 已通知主进程登录成功','login_success_hint')]
    for pattern,event in patterns:
        if re.fullmatch(pattern,line):
            code=re.search(r'错误码: (0|140022008|140022010|140022011)$',line)
            if code and code[1]!='0':event='verification_required'
            return 'NAPCAT_LOGIN_EVENT event='+event+((' code='+code[1]) if code else '')
    return None


def safe_line(component,line):
    if component=='napcat':return login_event(line)
    if component=='gate' and line.rstrip().endswith('CHANNEL_CONNECTED_SELF_ID_VERIFIED'):
        return 'CHANNEL_CONNECTED_SELF_ID_VERIFIED'
    if component=='gate' and line.rstrip().endswith('CHANNEL_DISCONNECTED'):
        return 'CHANNEL_DISCONNECTED'
    if component=='gate':
        match=re.search(r'\bCHANNEL_METADATA_WRITE_FAILED code=(?:ACCESS_DENIED|SHARING_VIOLATION|LOCK_VIOLATION|IO_ERROR)$',line.rstrip())
        if match:return match.group(0)
    if component=='model':
        match=re.search(r'\bCLI_CLEANUP_IO trace=[a-f0-9]{10} operation=(?:write_unresolved|rotate_summary|write_summary|remove_unresolved) error=(?:ACCESS_DENIED|SHARING_VIOLATION|LOCK_VIOLATION|INVALID_DATA|DISK_FULL|IO_ERROR) attempt=[1-3]$',line.rstrip())
        if match:return match.group(0)
        match=re.search(r'\bCLI_CLEANUP trace=[a-f0-9]{10} generation=(?:pending|success|cancelled|BACKEND_UNAVAILABLE|AUTH_REQUIRED|QUOTA_EXHAUSTED|RATE_LIMITED|INPUT_TOO_LONG|MODEL_CONFIG_UNSUPPORTED|TOOL_ISOLATION_FAILED|MODEL_TIMEOUT|PROTOCOL_ERROR|CLEANUP_FAILED) outcome=(?:active|observed_empty|owned_alive|identity_unknown) coverage=(?:observed_only|job_complete) reason=(?:none|access_denied|wait_timeout|identity_changed|observation_incomplete|cleanup_in_progress|ledger_error|capacity_exceeded) count=(?:[0-9]|[1-9][0-9]|1[01][0-9]|12[0-8]) elapsed_ms=[0-9]{1,10}$',line.rstrip())
        if match:return match.group(0)
        match=re.search(r'\b(CLI_START|REQUEST_ACCEPTED|REQUEST_FAILED) request_id=([a-z0-9]{10})(?: (attempt=1|code=[A-Z_]+))?$',line.rstrip())
        if match:return match.group(0)
    return None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('component');parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args()
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    print('HOST_START component='+args.component,flush=True)
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    lines=BoundedLines();last_error=0;events=set()
    while chunk:=process.stdout.read1(4096):
        for line in lines.feed(chunk):
            safe=safe_line(args.component,line)
            if safe and args.component=='napcat':
                if safe in events or len(events)>=32:continue
                events.add(safe)
            if safe:print(time.strftime('%Y-%m-%d %H:%M:%S')+' '+safe,flush=True)
            elif args.component!='napcat' and ('ERROR' in line or '[ERRO]' in line) and time.monotonic()-last_error>30:
                print('COMPONENT_ERROR component='+args.component+' details_suppressed',flush=True);last_error=time.monotonic()
    code=process.wait();print('HOST_EXIT component='+args.component+' code='+str(code),flush=True)
    raise SystemExit(code)


if __name__=='__main__':main()
