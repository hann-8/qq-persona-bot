"""Discard upstream output; retain only explicit local transport/model metadata."""
import argparse
import re
import subprocess
import time


def safe_line(component,line):
    if component=='gate' and line.rstrip().endswith('CHANNEL_CONNECTED_SELF_ID_VERIFIED'):
        return 'CHANNEL_CONNECTED_SELF_ID_VERIFIED'
    if component=='model':
        match=re.search(r'\b(CLI_START|REQUEST_ACCEPTED|REQUEST_FAILED) request_id=([a-z0-9]{10})(?: (attempt=1|code=[A-Z_]+))?$',line.rstrip())
        if match:return match.group(0)
    return None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('component');parser.add_argument('command',nargs=argparse.REMAINDER);args=parser.parse_args()
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    print('HOST_START component='+args.component,flush=True)
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    buffer=b'';last_error=0
    while chunk:=process.stdout.read1(4096):
        buffer+=chunk
        while b'\n' in buffer:
            raw,buffer=buffer.split(b'\n',1)
            line=raw.decode('utf-8',errors='replace')
            safe=safe_line(args.component,line)
            if safe:print(time.strftime('%Y-%m-%d %H:%M:%S')+' '+safe,flush=True)
            elif ('ERROR' in line or '[ERRO]' in line) and time.monotonic()-last_error>30:
                print('COMPONENT_ERROR component='+args.component+' details_suppressed',flush=True);last_error=time.monotonic()
        if len(buffer)>16384:buffer=b''
    code=process.wait();print('HOST_EXIT component='+args.component+' code='+str(code),flush=True)
    raise SystemExit(code)


if __name__=='__main__':main()
