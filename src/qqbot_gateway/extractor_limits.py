"""A dedicated leaf worker Job: 256MiB/process, one process, kill on close.

This does not grant the CLI's unrelated LAP-31B full-tree capability.
"""
import os


class WorkerLimit:
    def __init__(self,pid):
        self.handle=None
        if os.name!='nt':return
        import ctypes as c
        from ctypes import wintypes as w
        class Basic(c.Structure):
            _fields_=[('process_time',c.c_int64),('job_time',c.c_int64),('flags',w.DWORD),
                      ('minimum',c.c_size_t),('maximum',c.c_size_t),('active',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
        class IO(c.Structure):
            _fields_=[(key,c.c_uint64) for key in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
        class Extended(c.Structure):
            _fields_=[('basic',Basic),('io',IO),('process_memory',c.c_size_t),('job_memory',c.c_size_t),('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
        k=c.WinDLL('kernel32',use_last_error=True);self.kernel=k
        k.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
        k.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];k.SetInformationJobObject.restype=w.BOOL
        k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
        k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];k.AssignProcessToJobObject.restype=w.BOOL
        k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
        job=k.CreateJobObjectW(None,None)
        if not job:raise OSError('worker_job_create')
        process=None
        try:
            info=Extended();info.basic.flags=0x2000|0x100|0x8;info.basic.active=1;info.process_memory=256*1024*1024
            if not k.SetInformationJobObject(job,9,c.byref(info),c.sizeof(info)):raise OSError('worker_job_limit')
            process=k.OpenProcess(0x100|0x1,False,pid)
            if not process or not k.AssignProcessToJobObject(job,process):raise OSError('worker_job_assign')
            self.handle=job
        except BaseException:
            k.CloseHandle(job);raise
        finally:
            if process:k.CloseHandle(process)
    def close(self):
        if self.handle:self.kernel.CloseHandle(self.handle);self.handle=None
