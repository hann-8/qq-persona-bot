"""LAP-31 independent verifier. Never invokes old verify main/report writers."""
import asyncio
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests')]
os.environ['ASTRBOT_DISABLE_METRICS']='1'


async def job_probe(root, failure=None, close_only=False):
    """Capability experiment only: native suspended launch, no CLI or production pipes.

    This intentionally does not activate production containment or recovery.
    Handles are owned by one finalizer, including each injected failure branch.
    """
    if os.name!='nt':return {'state':'unverified_non_windows'}
    import _winapi
    from ctypes import wintypes as W
    import psutil
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    class Limits(ctypes.Structure):
        _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),
                  ('flags',W.DWORD),('minimum',ctypes.c_size_t),('maximum',ctypes.c_size_t),
                  ('active_limit',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
    class IO(ctypes.Structure):_fields_=[('counts',ctypes.c_ulonglong*6)]
    class Extended(ctypes.Structure):
        _fields_=[('basic',Limits),('io',IO),('process_memory',ctypes.c_size_t),
                  ('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
    class Accounting(ctypes.Structure):
        _fields_=[('times',ctypes.c_longlong*4),('faults',W.DWORD),('total',W.DWORD),('active',W.DWORD),('terminated',W.DWORD)]
    signatures={
        'CreateJobObjectW':([ctypes.c_void_p,W.LPCWSTR],W.HANDLE),
        'SetInformationJobObject':([W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD],W.BOOL),
        'AssignProcessToJobObject':([W.HANDLE,W.HANDLE],W.BOOL),
        'QueryInformationJobObject':([W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p],W.BOOL),
        'IsProcessInJob':([W.HANDLE,W.HANDLE,ctypes.POINTER(W.BOOL)],W.BOOL),
        'ResumeThread':([W.HANDLE],W.DWORD),
        'TerminateJobObject':([W.HANDLE,W.UINT],W.BOOL),
        'TerminateProcess':([W.HANDLE,W.UINT],W.BOOL),
        'WaitForSingleObject':([W.HANDLE,W.DWORD],W.DWORD),
        'CloseHandle':([W.HANDLE],W.BOOL),
    }
    for name,(args,result) in signatures.items():
        method=getattr(kernel,name);method.argtypes=args;method.restype=result
    def require(value):
        if not value:raise OSError(ctypes.get_last_error(),'native capability failed')
        return value
    def accounting():
        value=Accounting();require(kernel.QueryInformationJobObject(job,1,ctypes.byref(value),ctypes.sizeof(value),None));return value
    marker=root/'executed'
    child_marker=root/'child'
    grand_marker=root/'grand'
    breakaway_marker=root/'breakaway'
    grand_code='import time; time.sleep(60)'
    child_code='import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,"-c",'+repr(grand_code)+']); Path('+repr(str(grand_marker))+').write_text(str(p.pid)); time.sleep(60)'
    code='import subprocess,sys,time; from pathlib import Path; Path('+repr(str(marker))+').write_text("yes")\ntry:\n subprocess.Popen([sys.executable,"-c","raise SystemExit(0)"],creationflags=0x01000000)\n Path('+repr(str(breakaway_marker))+').write_text("allowed")\nexcept OSError:\n Path('+repr(str(breakaway_marker))+').write_text("denied")\np=subprocess.Popen([sys.executable,"-c",'+repr(child_code)+']); Path('+repr(str(child_marker))+').write_text(str(p.pid)); time.sleep(.5)'
    outside=psutil.Popen([sys.executable,'-c','import time; time.sleep(60)'],creationflags=subprocess.CREATE_NO_WINDOW)
    external_identity=outside.create_time()
    job=process=thread=None;assigned=False;finalizer=None;known=[];result={}
    async def cleanup():
        def work():
            nonlocal job
            deadline=time.monotonic()+3
            if job and assigned and not close_only:
                require(kernel.TerminateJobObject(job,1))
                while accounting().active and time.monotonic()<deadline:time.sleep(.01)
                result['active_zero']=accounting().active==0
            if job and close_only:
                require(kernel.CloseHandle(job));job=None
            if process:
                # Native process handle is creation-bound, even on Assign failure.
                if not assigned:require(kernel.TerminateProcess(process,1))
                result['root_exited']=kernel.WaitForSingleObject(process,2000)==0
            for entry in known:
                try:
                    p=psutil.Process(entry['pid'])
                    if p.create_time()==entry['created']:p.wait(timeout=max(0,deadline-time.monotonic()))
                except psutil.NoSuchProcess:pass
            result['known_descendants_exited']=all(not psutil.pid_exists(e['pid']) or psutil.Process(e['pid']).create_time()!=e['created'] for e in known)
            for handle in (thread,process,job):
                if handle:require(kernel.CloseHandle(handle))
            job=None
        await asyncio.to_thread(work)
    try:
        job=require(kernel.CreateJobObjectW(None,None))
        limits=Extended();limits.basic.flags=0x2000
        require(kernel.SetInformationJobObject(job,9,ctypes.byref(limits),ctypes.sizeof(limits)))
        if failure=='create':raise RuntimeError('injected_create')
        process,thread,_,_=_winapi.CreateProcess(sys.executable,subprocess.list2cmdline([sys.executable,'-c',code]),None,None,False,0x4|subprocess.CREATE_NO_WINDOW,None,str(root),subprocess.STARTUPINFO())
        assert not marker.exists()
        if failure=='assign':raise RuntimeError('injected_assign')
        require(kernel.AssignProcessToJobObject(job,process));assigned=True
        inside=W.BOOL();require(kernel.IsProcessInJob(process,job,ctypes.byref(inside)))
        assert inside.value and accounting().active==1 and not marker.exists()
        result.update(assigned_before_execution=True,no_breakaway_flags=True)
        if failure=='resume':raise RuntimeError('injected_resume')
        if kernel.ResumeThread(thread)==0xffffffff:raise OSError('resume failed')
        for _ in range(200):
            if grand_marker.exists():break
            await asyncio.sleep(.01)
        assert grand_marker.exists()
        assert breakaway_marker.read_text()=='denied'
        result['breakaway_denied']=True
        for path in (child_marker,grand_marker):
            p=psutil.Process(int(path.read_text()));known.append({'pid':p.pid,'created':p.create_time()})
        # Root exits first; the Job still accounts for descendants.
        assert await asyncio.to_thread(kernel.WaitForSingleObject,process,2000)==0
        assert accounting().active>=2
        result['root_first_descendants_accounted']=True
    except RuntimeError as error:
        if str(error)!='injected_'+str(failure):raise
        result['injected_failure']=failure
    except AssertionError:
        # Accepted breakaway creation does not by itself prove an escape (it
        # may remain in an enclosing/nested Job). It does fail this probe's
        # strict no-breakaway gate. Preserve the gap; never enable production.
        if not breakaway_marker.exists() or breakaway_marker.read_text()!='allowed':raise
        result['capability_gap']='breakaway_request_accepted_membership_unverified'
    finally:
        finalizer=asyncio.create_task(cleanup())
        try:
            await asyncio.wait_for(asyncio.shield(finalizer),4)
            assert outside.is_running() and outside.create_time()==external_identity
            result['external_untouched']=True
        finally:
            # Only this verifier's independently created external fixture.
            if outside.is_running() and outside.create_time()==external_identity:outside.kill()
            outside.wait(timeout=3)
    assert result.get('root_exited',True)
    assert result.get('active_zero',True)
    assert result.get('known_descendants_exited',True)
    result.update(state='unverified_capability_gap' if result.get('capability_gap') else 'synthetic_only_passed',
                  handles_finalized=True,production_cli_verified=False)
    return result


async def frameworks(root):
    from scripts.verify_lap20 import verify as group_verify
    from scripts.verify_lap21 import verify as media_verify
    results=[]
    for backend in ('codebuddy_cli','ollama_ssh'):
        for mode in ('single','adaptive'):
            work=root/(backend+'-'+mode+'-group');work.mkdir()
            value=await group_verify(work,backend,mode,full_lifecycle=True,lap24=True,lap25=True)
            results.append(value)
            print('PASS group',backend,mode,len(value['cases']),flush=True)
            for participation in ('mentions','free'):
                work=root/(backend+'-'+mode+'-'+participation+'-media');work.mkdir()
                value=await media_verify(work,backend,mode,participation,full_lifecycle=True,lap24=True,lap25=True)
                results.append(value)
                print('PASS media',backend,mode,participation,len(value['cases']),flush=True)
    return results


def main():
    if sys.argv[1:]==['--frameworks-only']:
        previous=Path.cwd()
        with tempfile.TemporaryDirectory(prefix='qqbot-lap31-framework-',ignore_cleanup_errors=True) as directory:
            os.chdir(directory)
            try:result=asyncio.run(frameworks(Path(directory)))
            finally:os.chdir(previous)
        (ROOT/'reports/lap-31-framework-offline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        return 0
    # Discover once: imports in the dedicated tests must not duplicate fixtures.
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    tests=unittest.TextTestRunner(verbosity=1).run(suite)
    if not tests.wasSuccessful():return 1
    previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap31-',ignore_cleanup_errors=True) as directory:
        root=Path(directory);os.chdir(root)
        try:
            probes=[]
            for failure,close in ((None,False),('create',False),('assign',False),('resume',False),(None,True)):
                work=root/('job-'+str(failure)+'-'+str(close));work.mkdir()
                probes.append(asyncio.run(job_probe(work,failure,close)))
        finally:os.chdir(previous)
    # The installed framework and gateway have separate dependency environments.
    # Neither subprocess runs a bot entry point or an old report-writing main.
    framework_python=ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'
    subprocess.run([str(framework_python),'-X','utf8',str(Path(__file__).resolve()),'--frameworks-only'],cwd=ROOT/'runtime/astrbot',check=True)
    result=json.loads((ROOT/'reports/lap-31-framework-offline.json').read_text(encoding='utf-8'))
    report={'unit_tests':tests.testsRun,'real_model_calls':0,'real_qq_calls':0,
            '31A':'offline_passed','31B':'synthetic_probe_incomplete_no_production_containment' if any(p.get('capability_gap') for p in probes) else 'synthetic_probe_only_no_production_containment',
            'job_probes':probes,'frameworks':result}
    path=ROOT/'reports/lap-31-offline.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS LAP-31 offline; 31B production integration/recovery remains unverified',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
