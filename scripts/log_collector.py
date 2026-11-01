"""Private official stdout collector; the Node/QQ process remains directly owned."""
import argparse
import codecs
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.log_retention import LogSink, mkdir, policy


class CollectorPipe:
    def __init__(self, root, settings, *, python_executable=None):
        import msvcrt
        import psutil
        root=Path(root).resolve();settings=policy(settings)
        directory=mkdir(root,root/'state/log-retention')
        ready=directory/('collector-'+uuid.uuid4().hex+'.json')
        read_fd,self.write_fd=os.pipe();self.process=None
        try:
            handle=msvcrt.get_osfhandle(read_fd);os.set_inheritable(read_fd,True)
            startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':[handle]}
            args=[str(python_executable or root/'.venv/Scripts/python.exe'),str(ROOT/'scripts/log_collector.py'),
                  '--handle',str(handle),'--ready',str(ready),'--root',str(root),
                  '--retention-days',str(settings['retention_days'])]
            if not settings['enabled']:args.append('--disabled')
            self.process=psutil.Popen(args,cwd=root,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,close_fds=True,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
        except BaseException:
            self.close();raise
        finally:os.close(read_fd)
        try:
            deadline=time.monotonic()+5
            while time.monotonic()<deadline and self.process.poll() is None:
                if ready.exists():
                    value=json.loads(ready.read_text())
                    owned={self.process.pid,*(child.pid for child in self.process.children(recursive=True))}
                    if value.get('ready') is True and type(value.get('pid')) is int and value['pid'] in owned:return
                time.sleep(.05)
            raise RuntimeError('LOG_COLLECTOR_NOT_READY')
        except BaseException:
            self.close()
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=3)
            raise

    def close(self):
        if self.write_fd is not None:os.close(self.write_fd);self.write_fd=None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--handle',type=int,required=True);parser.add_argument('--ready',type=Path,required=True)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--retention-days',type=int,required=True);parser.add_argument('--disabled',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    from qqbot_gateway.config_files import plain_path
    from qqbot_gateway.lifecycle import atomic_json
    if args.ready.parent != root/'state/log-retention' or not args.ready.name.startswith('collector-'):raise ValueError('Invalid collector ready path')
    plain_path(root,args.ready.parent,directory=True)
    import msvcrt
    descriptor=msvcrt.open_osfhandle(args.handle,os.O_RDONLY|os.O_BINARY)
    sink=LogSink(root,'snowluma-startup.local.log',dict(enabled=not args.disabled,retention_days=args.retention_days))
    try:
        atomic_json(args.ready,dict(pid=os.getpid(),ready=True))
        decoder=codecs.getincrementaldecoder('utf-8')(errors='replace')
        with os.fdopen(descriptor,'rb',buffering=0) as stream:
            while chunk:=stream.read(4096):sink.write(decoder.decode(chunk))
            tail=decoder.decode(b'',final=True)
            if tail:sink.write(tail)
    finally:
        sink.close();args.ready.unlink(missing_ok=True)


if __name__=='__main__':main()
