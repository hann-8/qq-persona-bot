"""Desktop launcher checks: temp roots, fake identities and mocked OS/UI only."""
from contextlib import ExitStack, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from scripts import manage
from qqbot_gateway import official_snowluma as desktop
from qqbot_gateway.lifecycle import atomic_json


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='Snow 中文 path ')
        self.root=Path(self.temp.name)
        self.settings={'qq_transport':{'provider':'snowluma'}}
        self.gate=SimpleNamespace(bot_qq='222',host='127.0.0.1',port=6200,inbound_token='synthetic-secret-ONLY')
        self.package,self.qq=desktop.paths(self.root,self.settings)
        for p in (self.package/'node.exe',self.package/'index.mjs',self.package/'check-node-version.cjs',self.qq):
            p.parent.mkdir(parents=True,exist_ok=True);p.touch()
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(manage,'ROOT',self.root))
        self.stack.enter_context(patch.object(manage,'STATE',self.root/'state/managed-processes.json'))
        self.output=StringIO();self.stack.enter_context(redirect_stdout(self.output))
    def tearDown(self):self.stack.close();self.temp.cleanup()
    def plan(self):return desktop.connection_plan(self.root,self.settings,self.gate)

    def test_create_idempotent_and_only_target(self):
        other=self.package/'config/onebot_333.json';atomic_json(other,{'other':True})
        before=other.read_bytes()
        plan=self.plan();desktop.publish_connection(plan)
        value=json.loads(plan[0].read_text())
        self.assertEqual(value['mode'],'snapshot')
        self.assertEqual(value['networks']['httpServers'],[])
        self.assertEqual(value['networks']['wsClients'][0]['accessToken'],self.gate.inbound_token)
        self.assertEqual(value['networks']['wsClients'][0]['url'],'ws://127.0.0.1:6200/ws')
        stat=plan[0].stat();self.assertFalse(self.plan()[3]);desktop.publish_connection(self.plan())
        self.assertEqual(stat.st_mtime_ns,plan[0].stat().st_mtime_ns)
        self.assertEqual(other.read_bytes(),before);self.assertEqual(list(plan[0].parent.glob('*.bak')),[])
        self.assertNotIn(self.gate.inbound_token,self.output.getvalue())

    def test_update_preserves_bytes_backup_unrelated_fields_and_mode(self):
        path=self.plan()[0]
        value={'mode':'overlay','custom':{'keep':1},'networks':{'wsClients':[
            {'name':'unrelated','accessToken':'unrelated-secret'},
            {'name':'qqbot-gate','url':'ws://old','custom':'keep'}],'httpClients':[{'name':'keep'}]}}
        atomic_json(path,value);before=path.read_bytes()
        desktop.publish_connection(self.plan())
        updated=json.loads(path.read_text())
        self.assertEqual(updated['mode'],'overlay');self.assertEqual(updated['custom'],value['custom'])
        self.assertEqual(updated['networks']['wsClients'][0],value['networks']['wsClients'][0])
        self.assertEqual(updated['networks']['httpClients'],value['networks']['httpClients'])
        self.assertEqual(updated['networks']['wsClients'][1]['custom'],'keep')
        self.assertEqual(next(path.parent.glob('*.bak')).read_bytes(),before)

    def test_corrupt_duplicate_and_concurrent_edits_preserved(self):
        path=self.plan()[0];path.parent.mkdir(parents=True)
        for raw in (b'bad JSON',b'{"networks":{"wsClients":[{"name":"qqbot-gate"},{"name":"qqbot-gate"}]}}'):
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'OneBot'):self.plan()
            self.assertEqual(path.read_bytes(),raw)
        path.unlink();plan=self.plan();path.write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'其他程序'):desktop.publish_connection(plan)
        self.assertEqual(path.read_text(),'{}')

    def test_atomic_failure_keeps_original_and_backup(self):
        path=self.plan()[0];atomic_json(path,{'networks':{'wsClients':[]}});before=path.read_bytes()
        with patch('qqbot_gateway.lifecycle.os.replace',side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):desktop.publish_connection(self.plan())
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(next(path.parent.glob('*.bak')).read_bytes(),before)

    def process(self,pid,exe=None,args=None):
        p=Mock();p.pid=pid;p.create_time.return_value=float(pid);p.children.return_value=[]
        p.is_running.return_value=True;p.info={'exe':str(exe) if exe else None,'cmdline':args or []}
        p.cwd.return_value=str(self.package);return p

    def orchestration(self,existing=()):
        self.actual_start=manage._start_channel
        manage.save(list(existing))
        self.stack.enter_context(patch.object(manage,'read_project',return_value=SimpleNamespace(settings=self.settings)))
        self.stack.enter_context(patch.object(manage,'loaded_settings',return_value=self.settings))
        self.stack.enter_context(patch.object(manage,'alive',side_effect=lambda e:self.process(e['pid'])))
        self.stack.enter_context(patch.object(manage,'load_gate_config',return_value=self.gate))
        self.stack.enter_context(patch.object(manage,'show_status'))
        self.stack.enter_context(patch.object(manage,'port_open',return_value=False))
        self.found={c:[] for c in desktop.COMPONENTS}
        self.stack.enter_context(patch.object(desktop,'discover',side_effect=lambda *a:self.found))
        self.page=self.stack.enter_context(patch.object(desktop,'open_page'))
        self.wait=self.stack.enter_context(patch.object(desktop,'wait_ready'))
        self.launch=self.stack.enter_context(patch.object(desktop,'launch',side_effect=[self.process(21),self.process(22)]))
        def start(**kwargs):
            if any(e['component']=='gate' for e in manage.read_state()):return
            manage.save(manage.read_state()+[{'pid':11,'created':11.,'component':'gate'}])
        self.framework=self.stack.enter_context(patch.object(manage,'_start_channel',side_effect=start))

    def test_existing_framework_adds_only_desktop_repeated_click_no_duplicate(self):
        original={'pid':11,'created':11.,'component':'gate'}
        self.orchestration([original]);manage.start_desktop();manage.start_desktop()
        self.assertEqual(self.launch.call_count,2);self.assertEqual(self.page.call_count,2)
        self.assertEqual(manage.read_state()[0],original)
        self.assertEqual(len(manage.read_state()),3)
        self.assertEqual(len(json.loads(self.plan()[0].read_text())['networks']['wsClients']),1)

    def test_external_instances_not_registered(self):
        self.orchestration();desktop.publish_connection(self.plan())
        self.found.update(official_qq=[self.process(31)],official_snow=[self.process(32)])
        manage.start_desktop();self.launch.assert_not_called()
        self.assertEqual([e['component'] for e in manage.read_state()],['gate'])

    def test_real_framework_entry_reuses_running_components_and_still_adds_desktop(self):
        self.orchestration([{'pid':11,'created':11.,'component':'gate'}])
        self.framework.side_effect=self.actual_start
        with patch.object(manage,'status_report',return_value={'process_state':'running','mode':'text'}):
            manage.start_desktop()
        self.assertEqual(self.launch.call_count,2)
        self.assertEqual([e['component'] for e in manage.read_state()],['gate','official_qq','official_snow'])

    def test_verified_external_listener_reused_but_public_listener_rejected(self):
        self.orchestration();desktop.publish_connection(self.plan())
        self.found.update(official_qq=[self.process(31)],official_snow=[self.process(32)])
        connection=SimpleNamespace(laddr=SimpleNamespace(port=5099,ip='127.0.0.1'),pid=32,status='LISTEN')
        with patch.object(manage,'port_open',return_value=True),patch.object(manage.psutil,'net_connections',return_value=[connection]):
            manage.start_desktop();self.launch.assert_not_called()
            connection.laddr.ip='0.0.0.0'
            with self.assertRaisesRegex(RuntimeError,'5099'):manage.start_desktop()

    def test_failed_snow_readiness_keeps_existing_framework_and_records_only_new_cleanup(self):
        original={'pid':11,'created':11.,'component':'gate'}
        self.orchestration([original]);self.wait.side_effect=RuntimeError('synthetic timeout')
        removed=[]
        def cleanup(entries):removed.extend(entries);manage.save([])
        with patch.object(manage,'stop',side_effect=cleanup):
            with self.assertRaisesRegex(RuntimeError,'timeout'):manage.start_desktop()
        self.assertEqual([e['component'] for e in removed],['official_snow','official_qq'])
        self.assertEqual(manage.read_state(),[original])

    def test_running_snow_requires_normal_exit_before_sync_no_writes(self):
        self.orchestration();self.found['official_snow']=[self.process(32)]
        with self.assertRaisesRegex(RuntimeError,'正常退出Snow'):manage.start_desktop()
        self.framework.assert_not_called();self.launch.assert_not_called();self.assertFalse(self.plan()[0].exists())

    def test_unknown_port_conflict_preserves_everything(self):
        self.orchestration()
        with patch.object(manage,'port_open',return_value=True),patch.object(manage.psutil,'net_connections',return_value=[]):
            with self.assertRaisesRegex(RuntimeError,'5099'):manage.start_desktop()
        self.framework.assert_not_called();self.launch.assert_not_called();self.assertFalse(self.plan()[0].exists())

    def test_partial_launch_failure_rolls_back_only_new_keeps_original(self):
        original={'pid':11,'created':11.,'component':'gate'}
        self.orchestration([original]);self.launch.side_effect=[self.process(21),OSError('synthetic')]
        removed=[]
        def cleanup(entries):removed.extend(entries);manage.save([])
        with patch.object(manage,'stop',side_effect=cleanup):
            with self.assertRaises(OSError):manage.start_desktop()
        self.assertEqual([e['component'] for e in removed],['official_qq'])
        self.assertEqual(manage.read_state(),[original]);self.page.assert_not_called()

    def test_fresh_launch_failure_also_cleans_new_framework(self):
        self.orchestration();self.launch.side_effect=OSError('synthetic')
        removed=[]
        def cleanup(entries):removed.extend(entries);manage.save([])
        with patch.object(manage,'stop',side_effect=cleanup):
            with self.assertRaises(OSError):manage.start_desktop()
        self.assertEqual([e['component'] for e in removed],['gate']);self.assertEqual(manage.read_state(),[])

    def test_napcat_delegates_without_desktop_or_config(self):
        self.settings={'qq_transport':{'provider':'napcat'}};self.orchestration()
        manage.start_desktop(channel_only=True)
        self.assertFalse(self.framework.call_args.kwargs['full']);self.launch.assert_not_called();self.page.assert_not_called()
        self.assertFalse((self.package/'config').exists())

    def test_missing_material_before_framework(self):
        self.orchestration();(self.package/'node.exe').unlink()
        with self.assertRaisesRegex(RuntimeError,'缺少官方启动材料'):manage.start_desktop()
        self.framework.assert_not_called()

    def test_launch_uses_bundled_node_cwd_hidden_and_sanitized_environment(self):
        with patch.dict(os.environ,{'SNOWLUMA_ACCEPT_EULA':'1','SNOWLUMA_ACCEPT_PRIVACY':'1',
                'SNOWLUMA_HOOK_AUTOLOAD_ALL':'1','SNOWLUMA_WEBUI_BOOTSTRAP_PASSWORD':'hidden'}), \
             patch.object(desktop.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as check, \
             patch.object(desktop.psutil,'Popen') as popen:
            desktop.launch('official_snow',self.package,self.qq,self.root)
            self.assertEqual(check.call_args.args[0],[str(self.package/'node.exe'),str(self.package/'check-node-version.cjs')])
            self.assertEqual(popen.call_args.args[0],[str(self.package/'node.exe'),str(self.package/'index.mjs')])
            self.assertEqual(popen.call_args.kwargs['cwd'],self.package)
            env=popen.call_args.kwargs['env']
            self.assertEqual(env['SNOWLUMA_WEBUI_HOST'],'127.0.0.1');self.assertEqual(env['SNOWLUMA_HOOK_AUTOLOAD'],'0')
            self.assertNotIn('SNOWLUMA_ACCEPT_EULA',env);self.assertNotIn('SNOWLUMA_HOOK_AUTOLOAD_ALL',env)
            self.assertEqual(popen.call_args.kwargs['creationflags'],subprocess.CREATE_NO_WINDOW)
            desktop.launch('official_qq',self.package,self.qq,self.root)
            self.assertEqual(popen.call_args.args[0],[str(self.qq)]);self.assertEqual(popen.call_args.kwargs['creationflags'],0)

    def test_exact_path_discovery_does_not_claim_other_qq_or_node(self):
        qq=self.process(1,self.qq);snow=self.process(2,self.package/'node.exe',['node','index.mjs'])
        wrong=self.process(3,self.qq.parent.parent/'daily/QQ.exe')
        node=self.process(4,self.package/'node.exe',['node','unrelated.mjs'])
        with patch.object(desktop.psutil,'process_iter',return_value=[qq,snow,wrong,node]):
            found=desktop.discover(self.package,self.qq)
        self.assertEqual(found['official_qq'],[qq]);self.assertEqual(found['official_snow'],[snow])

    def test_external_official_bat_system_node_detected_before_listener_exists(self):
        p=self.process(9,self.root/'system/node.exe',['node',str(self.package/'index.mjs')])
        with patch.object(desktop.psutil,'process_iter',return_value=[p]):
            self.assertEqual(desktop.discover(self.package,self.qq)['official_snow'],[p])

    def test_stop_orders_framework_snow_qq_and_preserves_not_yet_stopped_ids(self):
        rows=[{'pid':i,'created':float(i),'component':c} for i,c in enumerate(('gate','official_snow','official_qq'),1)]
        manage.save(rows);calls=[]
        def cleanup(entries):
            calls.append([e['component'] for e in entries]);manage.save([])
        with patch.object(manage,'stop',side_effect=cleanup):manage.stop_in_order(rows)
        self.assertEqual(calls,[['gate'],['official_snow'],['official_qq']]);self.assertEqual(manage.read_state(),[])
        manage.save(rows)
        def fail(entries):manage.save(entries);raise RuntimeError('synthetic')
        with patch.object(manage,'stop',side_effect=fail):
            with self.assertRaises(RuntimeError):manage.stop_in_order(rows)
        self.assertEqual(manage.read_state(),rows)

    def test_pid_reuse_not_killed_even_for_official_component(self):
        row={'pid':55,'created':1.,'component':'official_snow'}
        p=self.process(55)
        with patch.object(manage.psutil,'Process',return_value=p):
            self.assertIsNone(manage.alive(row));manage.stop([row])
        p.terminate.assert_not_called();p.kill.assert_not_called()

    def test_page_log_fallback_never_print_log_contents(self):
        with patch.object(desktop.webbrowser,'open',return_value=False):self.assertFalse(desktop.open_page())
        self.assertIn(desktop.URL,self.output.getvalue())
        self.assertFalse(desktop.open_log(self.root))
        path=self.root/'logs/snowluma-startup.local.log';path.parent.mkdir();path.write_text('password-do-not-print')
        with patch.object(desktop.os,'startfile',side_effect=OSError()):self.assertFalse(desktop.open_log(self.root))
        self.assertNotIn('password-do-not-print',self.output.getvalue())

    def test_snow_status_chinese_no_napcat_or_private_prerequisite(self):
        report=dict(provider='snowluma',process_state='running',channel_state='waiting_login',
                    can_receive_group_messages=False,model={},task_counts={},desktop={})
        manage.show_status(report)
        text=self.output.getvalue();self.assertNotIn('NapCat',text);self.assertNotIn('私有',text)
        self.assertIn('OneBot未接通',text);self.assertIn('选择专用QQ',text)

    def test_cmd_encoding_crlf_root_relative_and_actions(self):
        for name,action in [('启动机器人.cmd','start-desktop'),('打开SnowLuma管理页.cmd','open-snow'),
                            ('查看Snow本机日志.cmd','snow-log'),('查看状态.cmd','status'),('关闭机器人.cmd','stop')]:
            raw=(ROOT/name).read_bytes();text=raw.decode('utf-8')
            self.assertNotIn(b'\n',raw.replace(b'\r\n',b''));self.assertIn('%~dp0scripts\\manage.py',text)
            self.assertIn(action,text);self.assertIn('--no-pause',text);self.assertIn('%bot_manage_exit%',text)


if __name__=='__main__':unittest.main()
