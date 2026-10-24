"""Actual CLI and finite transaction paths, exclusively synthetic temp roots."""
from contextlib import redirect_stdout
from io import StringIO
import json
import base64
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml

from scripts import transport
from qqbot_gateway import transport_cli as ops
from qqbot_gateway.config_files import read_project
from qqbot_gateway.config_layout_ops import initialize
from qqbot_gateway.transport_supervisor import RecoveryLedger
from test_qq_transport import synthetic


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'config').mkdir();self.path=self.root/'config/settings.local.yaml'
        self.path.write_text('# untouched header\n'+yaml.safe_dump(synthetic(),sort_keys=False)+'# untouched tail\n',encoding='utf-8')

    def cli(self,*args):
        output=StringIO()
        with redirect_stdout(output):code=transport.main(['--root',str(self.root),*args])
        return code,json.loads(output.getvalue())

    def prepared(self):
        with patch('qqbot_gateway.transport_cli.require_stopped'),patch('qqbot_gateway.transport_supervisor.require_stopped'):
            return ops.prepare(self.root)

    def activated(self):
        self.prepared()
        with patch('qqbot_gateway.transport_cli.require_stopped'):return ops.activate(self.root,qualify=lambda *_:None)

    def test_actual_cli_offline_inspect_and_blocked_commands_no_writes(self):
        original=self.path.read_bytes()
        self.assertEqual(self.cli('inspect','--json')[0],0)
        code,result=self.cli('verify','--offline');self.assertEqual(code,0);self.assertTrue(result['offline_passed']);self.assertFalse(result['real_verified'])
        for command in [('activate','--provider','snowluma'),('capability-probe','--authorize-owned-qq','--timeout','240')]:
            code,result=self.cli(*command);self.assertEqual(code,1);self.assertEqual(result['error'],'runtime_qualification_blocked');self.assertFalse(result['private_runtime_entry_available'])
        self.assertEqual(self.path.read_bytes(),original)
        self.assertFalse((self.root/'state/qq-transport').exists())

    def test_prepare_actual_cli_and_partial_failure_cannot_reset_budget(self):
        with patch('qqbot_gateway.transport_cli.require_stopped'),patch('qqbot_gateway.transport_supervisor.require_stopped'):
            self.assertEqual(self.cli('prepare-policy')[0],0)
        key=json.loads((self.root/'secrets/snowluma-control.local.json').read_text())
        self.assertEqual(len(bytes.fromhex(key['key'])),32)
        ledger=(self.root/'state/qq-transport/recovery.local.json');before=ledger.read_bytes()
        (self.root/'state/qq-transport/candidate.local.json').unlink()
        with self.assertRaisesRegex(ValueError,'PREPARE_ALREADY_STARTED'):self.prepared()
        self.assertEqual(ledger.read_bytes(),before)

    def test_prepare_failure_after_budget_leaves_closed_intent(self):
        original=ops._new
        def fail(path,data):
            if path.suffix=='.mjs':raise OSError('synthetic')
            return original(path,data)
        with patch.object(ops,'_new',side_effect=fail):
            with self.assertRaises(OSError):self.prepared()
        before=RecoveryLedger(self.root).read()
        with self.assertRaisesRegex(ValueError,'PREPARE_ALREADY_STARTED'):self.prepared()
        self.assertEqual(RecoveryLedger(self.root).read(),before)

    def test_legacy_bytes_comments_unknown_and_unrelated_later_edit_survive_rollback(self):
        original=self.path.read_bytes();self.activated()
        self.assertTrue(self.path.read_bytes().startswith(original))
        content=self.path.read_bytes().replace(b'# untouched header',b'# changed later header')
        content+=b'custom_extension: later\n';self.path.write_bytes(content)
        with patch('qqbot_gateway.transport_cli.require_stopped'):ops.rollback(self.root)
        self.assertEqual(self.path.read_bytes(),original.replace(b'# untouched header',b'# changed later header')+b'custom_extension: later\n')

    def test_split_only_runtime_changed_and_unrelated_provider_subfield_survives(self):
        initialize(self.root,migrate=True)
        files={p.name:p.read_bytes() for p in (self.root/'config/local').iterdir()}
        self.activated();runtime=self.root/'config/local/runtime.yaml'
        runtime.write_bytes(runtime.read_bytes()+b'  snowluma:\n    health_ttl_seconds: 30 # later\n')
        with patch('qqbot_gateway.transport_cli.require_stopped'):ops.rollback(self.root)
        self.assertIn(b'health_ttl_seconds: 30 # later',runtime.read_bytes())
        for name,content in files.items():
            if name!='runtime.yaml':self.assertEqual((runtime.parent/name).read_bytes(),content)

    def test_source_race_and_owned_field_conflict_are_closed(self):
        self.prepared()
        def race():self.path.write_bytes(self.path.read_bytes()+b'# concurrent\n')
        with patch('qqbot_gateway.transport_cli.require_stopped'):
            with self.assertRaisesRegex(ValueError,'CONFIG_SOURCE_CHANGED'):ops.activate(self.root,qualify=lambda *_:None,before_publish=race)
            with self.assertRaisesRegex(ValueError,'ROLLBACK_UNKNOWN'):ops.rollback(self.root)
        self.assertNotIn('qq_transport',read_project(self.root).settings)

    def test_rollback_refuses_later_owned_change(self):
        self.activated();self.path.write_bytes(self.path.read_bytes().replace(b'provider: snowluma',b'provider: napcat'))
        before=self.path.read_bytes()
        with patch('qqbot_gateway.transport_cli.require_stopped'):
            with self.assertRaisesRegex(ValueError,'ROLLBACK_OWNED_FIELD_CHANGED'):ops.rollback(self.root)
        self.assertEqual(self.path.read_bytes(),before)

    def test_trial_production_refuses_before_request_or_start_and_fake_calls_once_outside_lock(self):
        self.activated()
        with patch('qqbot_gateway.transport_cli.require_stopped'):
            code,result=self.cli('trial-start');self.assertEqual(code,1);self.assertEqual(result['error'],'runtime_qualification_blocked')
            self.assertFalse((self.root/'state/qq-transport/trial-request.local.json').exists())
            calls=[]
            def start(**kwargs):
                self.assertTrue(kwargs['full'])
                from qqbot_gateway.config import configuration_lock
                with configuration_lock(self.root):calls.append(1)
                return dict(provider='snowluma',instance_id='a'*32)
            ops.trial_start(self.root,qualify=lambda *_:None,start=start)
            with self.assertRaisesRegex(ValueError,'TRIAL_ALREADY_REQUESTED'):ops.trial_start(self.root,qualify=lambda *_:None,start=start)
            self.assertEqual(calls,[1])
            stopped=[]
            ops.rollback(self.root,stop=lambda **kwargs:stopped.append(kwargs['expected_instance']))
            self.assertEqual(stopped,['a'*32])

    def test_actual_management_rechecks_source_before_any_creation(self):
        from scripts import manage
        self.activated();digest=read_project(self.root).source_digest
        self.path.write_bytes(self.path.read_bytes()+b'# raced after trial lock\n')
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'_start_channel') as create,redirect_stdout(StringIO()):
            with self.assertRaisesRegex(ValueError,'TRIAL_START_SOURCE_CHANGED'):manage.start_channel(expected_source_digest=digest)
            create.assert_not_called()

    def test_management_stop_instance_race_refuses_before_marker_and_cleanup(self):
        from scripts import manage
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'service_mode',return_value=dict(provider='snowluma',instance_id='b'*32)),patch.object(manage,'stop') as kill:
            with self.assertRaisesRegex(ValueError,'TRIAL_STOP_INSTANCE_CHANGED'):manage.stop_project(expected_instance='a'*32)
            kill.assert_not_called();self.assertFalse((self.root/'state/stop-request.json').exists())

    def test_partial_trial_request_cannot_choose_stop_target(self):
        self.activated()
        (self.root/'state/qq-transport/trial-request.local.json').write_text(json.dumps(dict(format='qqbot-trial-request-v1',source_digest='a'*64,instance_id=None)))
        stop=__import__('unittest.mock',fromlist=['Mock']).Mock()
        with self.assertRaisesRegex(ValueError,'TRIAL_STOP_UNKNOWN'):ops.rollback(self.root,stop=stop)
        stop.assert_not_called();self.assertEqual(read_project(self.root).settings['qq_transport']['provider'],'snowluma')

    def test_exact_rollback_bom_no_final_newline_quoted_provider(self):
        for prefix,section in [(b'\xef\xbb\xbf',b''),(b'',b'\nqq_transport:\n  provider: "napcat" # original')]:
            with self.subTest(prefix=prefix,section=section):
                # Each independent transaction has its own isolated ledger.
                with tempfile.TemporaryDirectory() as directory:
                    oldroot,oldpath=self.root,self.path
                    self.root=Path(directory);(self.root/'config').mkdir();self.path=self.root/'config/settings.local.yaml'
                    original=prefix+yaml.safe_dump(synthetic(),sort_keys=False).rstrip().encode()+section
                    self.path.write_bytes(original);self.activated()
                    with patch('qqbot_gateway.transport_cli.require_stopped'):ops.rollback(self.root)
                    self.assertEqual(self.path.read_bytes(),original)
                    self.root,self.path=oldroot,oldpath

    def test_editor_wrong_semantics_refused_before_config_write(self):
        self.prepared();before=self.path.read_bytes()
        with patch('qqbot_gateway.transport_cli.require_stopped'),patch.object(ops,'_provider',return_value=before):
            with self.assertRaisesRegex(ValueError,'CONFIG_EDIT_SEMANTICS_CHANGED'):ops.activate(self.root,qualify=lambda *_:None)
        self.assertEqual(self.path.read_bytes(),before)

    def test_private_corrupt_backup_and_alias_are_closed_at_actual_cli(self):
        self.activated();path=self.root/'state/qq-transport/activation.local.json';record=json.loads(path.read_text())
        for content in (b'PRIVATE_MARKER: [unterminated',b'PRIVATE_MARKER: &a [1]\nother: *a\n'):
            record['original']=base64.b64encode(content).decode();path.write_text(json.dumps(record))
            with patch('qqbot_gateway.transport_cli.require_stopped'):
                code,result=self.cli('rollback')
            self.assertEqual(code,1);self.assertNotIn('PRIVATE_MARKER',json.dumps(result));self.assertEqual(result['error'],'transport_config_invalid')


class TrialManagementTests(unittest.TestCase):
    def setUp(self):
        import test_transport_lifecycle as fixture
        fixture.Fixture.setUp(self);fixture.Fixture.fresh(self)

    def test_trial_calls_actual_management_text_mode_and_preserves_model_settings(self):
        from scripts import manage
        from qqbot_gateway.config import configuration_lock
        from qqbot_gateway.transport_launch import OwnerWriter
        with configuration_lock(self.root) as lease,patch('qqbot_gateway.transport_supervisor.require_stopped'):
            RecoveryLedger(self.root).initialize(lease)
        framework=[];configured=[]
        def writer(root,lease,instance,**kwargs):return OwnerWriter(root,lease,instance,process=self.procs.__getitem__,clock=lambda:1700000000.)
        before=read_project(self.root).settings['llm']
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
             patch.object(manage,'require_runtime',return_value=self.layout),patch.object(manage,'OwnerWriter',side_effect=writer), \
             patch.object(manage.psutil,'Process',side_effect=self.procs.__getitem__),patch.object(manage.psutil,'Popen') as real_spawn, \
             patch.object(manage,'check_port'),patch.object(manage,'_configure_snow_framework',side_effect=lambda gate,full,env:configured.append(full)), \
             patch.object(manage,'_launch_snow_component',side_effect=lambda spec,env:self.procs[13 if spec.component=='qq_client' else 12]), \
             patch.object(manage,'_launch_snow_framework',side_effect=lambda *args:framework.append(args)), \
             patch('qqbot_gateway.transport_cli.require_stopped'),redirect_stdout(StringIO()):
            ops.trial_start(self.root,qualify=lambda *_:None)
            self.assertEqual(manage.service_mode()['mode'],'text');self.assertEqual(configured,[True])
            self.assertEqual([item[0] for item in framework[0][0]],['astrbot','model','gate'])
            self.assertEqual(read_project(self.root).settings['llm'],before);real_spawn.assert_not_called()
