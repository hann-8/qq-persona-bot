"""On-demand owned leaf worker, bounded pipes/deadline/RSS and confirmed cleanup."""
import asyncio
import json
import os
from pathlib import Path
import sys
import sysconfig
import tempfile
import time
import psutil
from .public_http import WebFailure
from .errors import GatewayError
from .cleanup_identity import CleanupOwner
from .extractor_limits import WorkerLimit


class WebExtractor:
    def __init__(self,root=None):
        self.temporary=tempfile.TemporaryDirectory(prefix='qqbot-extract-') if root is None else None
        self.owner=CleanupOwner(root or self.temporary.name)
        self.lock=asyncio.Lock();self.last_metrics={};self.active_pid=None

    async def extract(self,text,mode='readability'):
        if mode not in ('readability','legacy'):raise WebFailure('extract_mode')
        data=text.encode('utf-8')
        if len(data)>1048576:raise WebFailure('extract_input_limit')
        async with self.lock:
            self.owner.reserve();process=None;owned=None;limit=None;tasks=[]
            started=time.monotonic();self.last_metrics={'peak_rss':0,'elapsed_seconds':0,'exited':False}
            spawn=None
            try:
                # Isolated interpreter, explicit script, no shell/user env/PYTHONPATH.
                env={k:v for k,v in os.environ.items() if k.upper() in ('SYSTEMROOT','WINDIR','TEMP','TMP')}
                # Windows venv python.exe is a redirector that creates a second
                # process. Use the base interpreter directly and our fixed site
                # directory, so the one-process Job contains the actual parser.
                executable=Path(sys._base_executable)
                if os.name=='nt':executable=executable.with_name('pythonw.exe')
                spawn=asyncio.create_task(asyncio.create_subprocess_exec(str(executable),'-I',str(Path(__file__).with_name('html_worker.py')),sysconfig.get_path('purelib'),mode,
                    stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,env=env,
                    creationflags=0x08000000 if os.name=='nt' else 0))
                process=await asyncio.shield(spawn)
                self.active_pid=process.pid;owned=psutil.Process(process.pid);self.owner.add(owned,root=True)
                limit=WorkerLimit(process.pid)
                async def feed():
                    process.stdin.write(data);await process.stdin.drain();process.stdin.close();await process.stdin.wait_closed()
                async def read():
                    output=bytearray()
                    while chunk:=await process.stdout.read(16384):
                        output.extend(chunk)
                        if len(output)>2097152:raise WebFailure('extract_output_limit')
                    return output
                async def monitor():
                    while process.returncode is None:
                        try:
                            memory=owned.memory_info();rss=max(memory.rss,getattr(memory,'peak_wset',0))
                            self.last_metrics['peak_rss']=max(self.last_metrics['peak_rss'],rss)
                            if rss>256*1024*1024:raise WebFailure('extract_rss_limit')
                            if owned.children():raise WebFailure('extract_child_denied')
                        except psutil.NoSuchProcess:return
                        await asyncio.sleep(.01)
                async with asyncio.timeout(max(.001,2-(time.monotonic()-started))):
                    tasks=[asyncio.create_task(feed()),asyncio.create_task(read()),asyncio.create_task(monitor())]
                    _,output,_=await asyncio.gather(*tasks)
                    await process.wait()
                if process.returncode:raise WebFailure('extract_exit')
                try:result=json.loads(output)
                except (ValueError,UnicodeError):raise WebFailure('extract_protocol') from None
                if not isinstance(result,dict) or 'error' in result:raise WebFailure('extract_failed')
                if set(result)!={'title','text','published_at','elapsed_seconds'} or not all(isinstance(result[k],str) for k in ('title','text')):raise WebFailure('extract_protocol')
                return result
            except TimeoutError:raise WebFailure('extract_timeout') from None
            except (OSError,psutil.Error):raise WebFailure('extract_worker') from None
            finally:
                if spawn and process is None:
                    # A cancellation during spawn still owns and reaps the child.
                    while not spawn.done():
                        try:await asyncio.shield(spawn)
                        except asyncio.CancelledError:continue
                    if not spawn.cancelled() and spawn.exception() is None:
                        process=spawn.result();owned=psutil.Process(process.pid);self.owner.add(owned,root=True)
                watcher=asyncio.create_task(asyncio.sleep(0))
                self.owner.begin(process,tasks,watcher,owned,'success' if process and process.returncode==0 else 'cancelled',2)
                clean=await self.owner.join()
                if limit:limit.close()
                self.last_metrics.update(elapsed_seconds=round(time.monotonic()-started,4),exited=bool(process and process.returncode is not None),cleanup=clean)
                self.active_pid=None
                if not clean:raise GatewayError('CLEANUP_FAILED')
