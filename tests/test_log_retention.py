"""Synthetic files/clocks and real Windows pipes, without models or messaging."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts.log_retention import LogSink, Lease, policy, purge, task_xml, task_action
from scripts.log_collector import CollectorPipe


class LogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='log 中文 ');self.root=Path(self.temp.name)
        (self.root/'logs').mkdir();self.today=datetime.now().date()
    def tearDown(self):self.temp.cleanup()
    def put(self, name, days=0):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('synthetic-only',encoding='utf-8')
        stamp=time.time()-days*86400;os.utime(path,(stamp,stamp));return path

    def test_date_cutoff_sparse_archives_and_narrow_scope(self):
        old=self.put('logs/model.log.'+str(self.today-timedelta(days=7)))
        keep=self.put('logs/model.log.'+str(self.today-timedelta(days=6)))
        older=self.put('logs/gate.log.'+str(self.today-timedelta(days=70))+'.1')
        foreign=self.put('logs/user-report.log.2000-01-01')
        state=self.put('state/evidence.log',days=100)
        native=self.put('runtime/snowluma/v2.1.1/logs/snowluma-'+str(self.today-timedelta(days=8))+'.log')
        result=purge(self.root,{},self.today)
        self.assertEqual(result['deleted_files'],3)
        self.assertFalse(any(p.exists() for p in (old,older,native)))
        self.assertTrue(all(p.exists() for p in (keep,foreign,state)))

    def test_active_current_log_locked_then_expired_after_close(self):
        path=self.put('logs/gate.log',days=9);lease=Lease(self.root,'gate.log')
        try:
            self.assertEqual(purge(self.root,{},self.today)['deleted_files'],0);self.assertTrue(path.exists())
        finally:lease.close()
        self.assertEqual(purge(self.root,{},self.today)['deleted_files'],1)

    @unittest.skipUnless(os.name=='nt','Windows sharing modes')
    def test_native_open_file_is_preserved_even_with_delete_sharing(self):
        import _winapi
        path=self.put('runtime/snowluma/v2.1.1/logs/snowluma-2000-01-01.log')
        handle=_winapi.CreateFile(str(path),_winapi.GENERIC_READ,7,0,_winapi.OPEN_EXISTING,0,0)
        try:
            self.assertEqual(purge(self.root,{})['deleted_files'],0);self.assertTrue(path.exists())
        finally:_winapi.CloseHandle(handle)
        self.assertEqual(purge(self.root,{})['deleted_files'],1)

    def test_quiet_rollover_and_archive_collision_preserve_both_files(self):
        path=self.put('logs/model.log',days=1)
        archive=self.put('logs/model.log.'+str(self.today-timedelta(days=1)));archive.write_text('previous archive')
        sink=LogSink(self.root,'model.log',{},background=False)
        try:
            self.assertEqual(archive.read_text(),'previous archive')
            self.assertEqual(Path(str(archive)+'.1').read_text(),'synthetic-only')
            sink.write('new today\n');sink.handler.rolloverAt=int(time.time())-1
            sink.tick()  # no new output is needed to rotate
            self.assertFalse(path.exists());sink.write('after quiet rollover\n')
            self.assertEqual(path.read_text(),'after quiet rollover\n')
        finally:sink.close()

    def test_disabled_and_invalid_policies_do_not_delete(self):
        path=self.put('logs/model.log',days=90)
        self.assertEqual(purge(self.root,{'enabled':False})['deleted_files'],0);self.assertTrue(path.exists())
        for bad in [dict(retention_days=0),dict(retention_days=True),dict(enabled=1),dict(sweep_interval_minutes=-1),dict(extra=True)]:
            with self.assertRaises(ValueError):purge(self.root,bad)

    def test_locked_rotation_reports_safe_error_without_stopping_the_host(self):
        sink=LogSink(self.root,'model.log',{},background=False)
        try:
            sink.handler.rolloverAt=0
            with patch.object(sink.handler,'doRollover',side_effect=PermissionError('synthetic')):
                self.assertFalse(sink.write('private synthetic record'))
            marker=self.root/'state/log-retention/errors/model.log.json'
            self.assertEqual(json.loads(marker.read_text())['code'],'LOG_WRITE_FAILED')
            self.assertNotIn('private',marker.read_text())
        finally:sink.close()

    def test_symlink_file_is_not_followed(self):
        target=self.put('secret.txt',days=100);link=self.root/'logs/model.log.2000-01-01'
        try:link.symlink_to(target)
        except OSError:self.skipTest('File symlink privilege unavailable')
        purge(self.root,{})
        self.assertTrue(target.exists());self.assertTrue(link.is_symlink())

    @unittest.skipUnless(os.name=='nt','Windows junction')
    def test_directory_junction_is_not_followed(self):
        logs=self.root/'logs';logs.rmdir();target=self.root/'unrelated';target.mkdir()
        secret=target/'model.log.2000-01-01';secret.write_text('keep')
        result=subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(logs),str(target)],capture_output=True)
        self.assertEqual(result.returncode,0)
        try:
            self.assertEqual(purge(self.root,{})['deleted_files'],0);self.assertTrue(secret.exists())
        finally:os.rmdir(logs)  # unlink this exact junction, never its target

    def test_process_host_keeps_only_existing_safe_events(self):
        import yaml
        raw=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        raw['bot']['qq']='222';raw['access'].update(allowed_groups=['111'],admin_users=['333'])
        directory=self.root/'config';directory.mkdir();(directory/'settings.local.yaml').write_text(yaml.safe_dump(raw),encoding='utf-8')
        env={key:value for key,value in os.environ.items() if not key.startswith('QQBOT_')}
        env.update(QQBOT_ROOT=str(self.root),PYTHONPATH=str(ROOT/'src'),PYTHONUTF8='1')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/process_host.py'),'model','--',sys.executable,'-c',
            "print('private synthetic text');print('REQUEST_ACCEPTED request_id=abcdefghij')"],env=env,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
        text=(self.root/'logs/model.log').read_text();self.assertIn('REQUEST_ACCEPTED',text);self.assertNotIn('private synthetic text',text)
        self.assertEqual(result.stdout,b'')

    @unittest.skipUnless(os.name=='nt','Windows handle inheritance')
    def test_one_collector_two_direct_children_and_eof_no_inherited_writer(self):
        pipe=CollectorPipe(self.root,{},python_executable=sys.executable)
        children=[]
        try:
            for word in ['synthetic-initial-credentials','synthetic-second-stream']:
                children.append(subprocess.Popen([sys.executable,'-c',f'print({word!r},flush=True)'],
                    stdout=pipe.write_fd,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW))
            pipe.close()
            for child in children:self.assertEqual(child.wait(timeout=10),0)
            self.assertEqual(pipe.process.wait(timeout=10),0)
            text=(self.root/'logs/snowluma-startup.local.log').read_text()
            self.assertIn('synthetic-initial-credentials',text);self.assertIn('synthetic-second-stream',text)
        finally:
            pipe.close()
            for child in children:
                if child.poll() is None:child.kill();child.wait(timeout=3)
            if pipe.process.poll() is None:pipe.process.kill();pipe.process.wait(timeout=3)

    def test_task_xml_is_current_user_hourly_logon_and_fixed_action(self):
        import xml.etree.ElementTree as ET
        value=ET.fromstring(task_xml(self.root,policy(), 'S-1-5-21-123'))
        ns={'t':'http://schemas.microsoft.com/windows/2004/02/mit/task'}
        self.assertEqual(value.find('.//t:Interval',ns).text,'PT60M')
        self.assertIsNotNone(value.find('.//t:LogonTrigger',ns))
        self.assertEqual(value.find('.//t:LogonType',ns).text,'InteractiveToken')
        command,args=task_action(self.root)
        self.assertEqual(value.find('.//t:Command',ns).text,command);self.assertEqual(value.find('.//t:Arguments',ns).text,args)


if __name__=='__main__':unittest.main()
