import copy
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from qqbot_gateway.config import read_settings, save_settings, export_legacy_config, activate_legacy_config, normalize_settings
from qqbot_gateway.config_files import (LAYOUT, ConfigError, read_project, create_snapshot,
    snapshot_environment, load_consumer, sha, canonical, management_root, prune_snapshots)
from qqbot_gateway.config_layout_ops import initialize, export_legacy, rollback_layout, partition, render
from qqbot_gateway.persona import session_version
from scripts import configure_bot, manage, config_files


def synthetic():
    data = yaml.safe_load((ROOT / 'config/settings.example.yaml').read_text(encoding='utf-8'))
    data['bot']['qq'] = '222'
    data['access'].update(allowed_groups=['111'], admin_users=['333'], blocked_users=['999'])
    return normalize_settings(data)


class ConfigFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='分层 config ')
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        self.legacy = self.root / 'config/settings.local.yaml'
        self.data = synthetic()
        self.legacy.write_text(yaml.safe_dump(self.data, allow_unicode=True), encoding='utf-8-sig')
        self.original = self.legacy.read_bytes()

    def tearDown(self):self.temp.cleanup()

    def split(self):
        initialize(self.root, migrate=True)
        return read_project(self.root)

    def write(self, name, content):
        (self.root / 'config/local' / name).write_text(content, encoding='utf-8')

    def capture(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_CF01_templates_match_example_and_placeholders_reject(self):
        self.legacy.unlink()
        initialize(self.root)
        with self.assertRaises(ConfigError):read_project(self.root)
        path = self.root / 'config/local/bot.yaml'
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        data['bot']['qq'] = '222'
        data['access'].update(allowed_groups=['111'], admin_users=['333'], blocked_users=['999'])
        path.write_text(yaml.safe_dump(data), encoding='utf-8')
        self.assertEqual(read_project(self.root).settings, self.data)
        for name in LAYOUT:
            template = (ROOT / 'config/examples' / name).read_text(encoding='utf-8')
            self.assertIn('下次正常启动', template)
            self.assertIn('新装默认', template)

    def test_CF01_migration_preserves_free_profiles_extensions_and_raw_backup(self):
        self.data['participation']['mode'] = 'free'
        self.data['llm']['profiles']['ollama_ssh']['expected_digest'] = 'a' * 64
        self.data['llm']['profiles']['ollama_ssh']['num_ctx'] = 24576
        self.data['custom'] = {'value': '换行\n冒号: \'引号\'\naccess: injected', 'list': [True, None, 4]}
        self.data['chat']['unknown_future'] = {'nested': 5}
        shared = {'items': ['legacy alias expands without changing values']}
        self.data['custom_alias'] = {'first': shared, 'second': shared}
        self.legacy.write_text('# 保留旧注释\n' + yaml.safe_dump(self.data, allow_unicode=True), encoding='utf-8-sig')
        original = self.legacy.read_bytes()
        before = read_settings(self.legacy)[0]
        result = initialize(self.root, migrate=True)
        after = read_project(self.root).settings
        self.assertEqual(before, after)
        self.assertEqual(session_version('合成', before), session_version('合成', after))
        self.assertEqual(self.legacy.read_bytes(), original)
        self.assertEqual((Path(result['backup']) / 'settings.original.yaml').read_bytes(), original)
        with self.assertRaises(ConfigError):initialize(self.root, migrate=True)

    def test_CF02_fixed_ownership_and_single_file_effect(self):
        before = self.split()
        path = self.root / 'config/local/chat.yaml'
        path.write_text(path.read_text(encoding='utf-8').replace('history_turns: 8', 'history_turns: 9'), encoding='utf-8')
        after = read_project(self.root)
        expected = copy.deepcopy(before.settings);expected['chat']['history_turns'] = 9
        self.assertEqual(after.settings, expected)
        self.write('bot.yaml', 'bot: {qq: "222"}\nllm: {}')
        with self.assertRaisesRegex(ConfigError, 'bot.yaml'):read_project(self.root)

    def test_CF02_parser_rejects_unsafe_yaml_without_values(self):
        self.split()
        for content in ('bot: {}\nbot: {}', 'bot: &x {}\naccess: *x',
                        'bot: {<<: {qq: 222}}', 'bot: !!python/object:PRIVATE {}',
                        'bot: !!str SECRET', '[]', '', 'bot: [SECRET', '? [a,b]\n: SECRET',
                        'SECRET_UNKNOWN: 999999999999999999'):
            with self.subTest(content=content):
                self.write('bot.yaml', content)
                with self.assertRaises(ConfigError) as caught:read_project(self.root)
                message = str(caught.exception)
                self.assertIn('bot.yaml', message)
                for secret in ('SECRET', 'PRIVATE', '999999999999999999'):self.assertNotIn(secret, message)

    def test_CF02_no_legacy_fallback_missing_corrupt_size_version(self):
        self.split()
        path = self.root / 'config/local/runtime.yaml'
        original = path.read_bytes()
        for content in (b'layout_version: 2', b'layout_version: true', b'\xff', b'#' * (128 * 1024 + 1)):
            path.write_bytes(content)
            with self.assertRaises(ConfigError):read_project(self.root)
        path.write_bytes(original);path.unlink()
        with self.assertRaises(ConfigError):read_project(self.root)
        self.assertEqual(self.legacy.read_bytes(), self.original)

    def test_CF02_total_limit(self):
        self.split()
        for name in LAYOUT:
            path = self.root / 'config/local' / name
            value = path.read_bytes();path.write_bytes(value + b'\n#' + b' ' * (110000 - len(value)))
        with self.assertRaisesRegex(ConfigError, '512KiB'):read_project(self.root)

    def test_CF02_extension_collision_and_schema(self):
        self.split()
        for content in ('layout_version: 1\nschema_version: 3\nlegacy_extensions: {bot: {}}',
                        'layout_version: 1\nschema_version: 4',
                        'layout_version: 1\nschema_version: 3\nlegacy_extensions: []'):
            self.write('runtime.yaml', content)
            with self.assertRaises(ConfigError):read_project(self.root)

    def test_CF02_junction_and_file_link_rejected(self):
        self.split()
        path = self.root / 'config/local/bot.yaml'
        target = self.root / 'bot-copy.yaml';target.write_bytes(path.read_bytes());path.unlink()
        try:path.symlink_to(target)
        except OSError:
            # Windows without symlink privilege: exercise the actual NT junction.
            local = self.root / 'config/local'
            retired = self.root / 'config/retired';local.rename(retired)
            (retired / 'bot.yaml').write_bytes(target.read_bytes())
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(local), str(retired)], check=True, capture_output=True)
            try:
                with self.assertRaises(ConfigError):read_project(self.root)
            finally:local.rmdir()
        else:
            with self.assertRaises(ConfigError):read_project(self.root)

    def test_CF03_check_has_no_side_effect_or_secret_read(self):
        config = self.split()
        self.write('extra.yaml', 'THIS_CONTENT_MUST_NOT_BE_LOADED: secret')
        before = self.capture()
        original_read = Path.open
        def guarded(path, *args, **kwargs):
            if path.is_relative_to(self.root / 'secrets'):raise AssertionError('secret opened')
            if args and any(c in args[0] for c in 'wax+'):raise AssertionError('write attempted')
            return original_read(path, *args, **kwargs)
        output = StringIO()
        with patch.object(Path, 'open', guarded), patch('socket.socket', side_effect=AssertionError('network')), redirect_stdout(output):
            self.assertEqual(config_files.main(['--root', str(self.root), 'check']), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result['unloaded'], ['extra.yaml'])
        self.assertNotIn('THIS_CONTENT', output.getvalue())
        self.assertEqual(self.capture(), before)
        self.assertEqual(config.source_digest, read_project(self.root).source_digest)

    def test_CF03_safe_validation_and_location(self):
        self.split()
        self.write('bot.yaml', 'bot: {qq: PRIVATE_ID}\naccess: {}')
        opened = Path.open
        def no_fallback(path,*args,**kwargs):
            if path.name in ('settings.example.yaml','settings.local.yaml'):raise AssertionError('fallback read')
            return opened(path,*args,**kwargs)
        with patch.object(Path,'open',no_fallback),self.assertRaisesRegex(ConfigError, 'bot.yaml.*bot') as caught:read_project(self.root)
        self.assertNotIn('PRIVATE_ID', str(caught.exception))
        self.write('bot.yaml', 'bot: [PRIVATE_ID')
        with self.assertRaisesRegex(ConfigError, '行1列'):read_project(self.root)

    def test_CF04_publish_failure_keeps_original_and_no_local(self):
        with patch('qqbot_gateway.config_layout_ops.os.rename', side_effect=OSError('disk')):
            with self.assertRaises(OSError):initialize(self.root, migrate=True)
        self.assertFalse((self.root / 'config/local').exists())
        self.assertEqual(self.legacy.read_bytes(), self.original)
        self.assertEqual(list((self.root / 'config').glob('.local-*')), [])
        self.assertEqual(len(list((self.root / 'state/config-backups').glob('*/settings.original.yaml'))), 1)

    def test_CF04_stop_unknown_and_active_reject(self):
        state = self.root / 'state';state.mkdir()
        path = state / 'managed-processes.json'
        for content in ('broken', json.dumps([{'pid': os.getpid(), 'created': psutil.Process().create_time()}])):
            path.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):initialize(self.root, migrate=True)
            self.assertFalse((self.root / 'config/local').exists())

    def test_CF04_concurrent_legacy_and_target_edits(self):
        import qqbot_gateway.config_layout_ops as ops
        real = ops.read_split
        def changed(*args):
            result = real(*args);self.legacy.write_bytes(self.original + b'\n# concurrent')
            return result
        with patch.object(ops, 'read_split', side_effect=changed):
            with self.assertRaises(ConfigError):initialize(self.root, migrate=True)
        self.assertFalse((self.root / 'config/local').exists())
        self.legacy.write_bytes(self.original)
        def target_created(*args):
            result = real(*args);target = self.root / 'config/local';target.mkdir()
            (target / 'user-file').write_text('preserve')
            return result
        with patch.object(ops, 'read_split', side_effect=target_created):
            with self.assertRaises(ConfigError):initialize(self.root, migrate=True)
        self.assertEqual((self.root / 'config/local/user-file').read_text(), 'preserve')

    def test_CF04_post_publication_failure_is_identified(self):
        import qqbot_gateway.config_layout_ops as ops
        real = ops.record
        def record(*args, **kwargs):
            if kwargs['stage'] == 'published':raise OSError()
            return real(*args, **kwargs)
        with patch.object(ops, 'record', side_effect=record):
            with self.assertRaisesRegex(ConfigError, '已完整发布'):initialize(self.root, migrate=True)
        self.assertEqual(read_project(self.root).settings, self.data)

    def test_CF04_read_race_and_disk_failure_do_not_publish(self):
        self.split()
        from qqbot_gateway import config_files as loader
        validate = loader.validate
        def concurrent(root, data):
            result = validate(root, data)
            path = self.root/'config/local/bot.yaml';path.write_bytes(path.read_bytes()+b'\n# race')
            return result
        with patch.object(loader, 'validate', side_effect=concurrent):
            with self.assertRaisesRegex(ConfigError, '读取期间文件改变'):read_project(self.root)
        # A failure in temporary generation must retain byte-exact legacy.
        import shutil
        shutil.rmtree(self.root/'config/local')
        import qqbot_gateway.config_layout_ops as ops
        writer = ops.write_new
        def disk_failure(path, content):
            if path.name == 'models.yaml':raise OSError('synthetic disk full')
            return writer(path, content)
        with patch.object(ops, 'write_new', side_effect=disk_failure):
            with self.assertRaises(OSError):initialize(self.root,migrate=True)
        self.assertFalse((self.root/'config/local').exists())
        self.assertEqual(self.legacy.read_bytes(),self.original)

    def test_CF04_atomic_publish_does_not_replace_even_empty_target(self):
        from qqbot_gateway.config_layout_ops import publish_directory
        source=self.root/'config/source';source.mkdir();(source/'value').write_bytes(b'synthetic')
        target=self.root/'config/target';target.mkdir()
        with self.assertRaises(OSError):publish_directory(source,target)
        self.assertEqual((source/'value').read_bytes(),b'synthetic')
        self.assertEqual(list(target.iterdir()),[])

    def test_CF05_snapshot_isolated_from_source_edits_and_deep_root(self):
        config = self.split()
        path, meta = create_snapshot(config, 'a' * 32)
        env = snapshot_environment(self.root, path, meta)
        self.write('chat.yaml', 'chat: {history_turns: 9}')
        self.assertEqual(load_consumer(self.root, path, environ=env), self.data)
        self.assertEqual(read_project(self.root).settings['chat']['history_turns'], 9)
        with self.assertRaises(ConfigError):management_root(path)
        self.assertEqual(management_root(path, self.root), self.root)
        bad_env = os.environ.copy() | env | {'QQBOT_CONFIG_DIGEST': 'incorrect', 'PYTHONPATH': str(ROOT/'src'), 'PYTHONUTF8': '1'}
        for command in (['-m','qqbot_gateway.model_gateway','--root',str(self.root),'--config',str(path)],
                        ['-m','qqbot_gateway.onebot_gate','--root',str(self.root),'--config',str(path)],
                        [str(ROOT/'scripts/configure_astrbot.py')]):
            result = subprocess.run([sys.executable,*command],cwd=self.root,env=bad_env,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,1)
            self.assertNotIn(b'Traceback',result.stderr)
            self.assertIn('快照',result.stderr.decode('utf-8'))
        for key in ('QQBOT_CONFIG_DIGEST', 'QQBOT_INSTANCE_ID', 'QQBOT_CONFIG_SNAPSHOT'):
            bad = dict(env);bad[key] = 'incorrect'
            with self.assertRaises(ConfigError):load_consumer(self.root, path, environ=bad)
        path.write_bytes(path.read_bytes() + b'\n# tampered')
        with self.assertRaises(ConfigError):load_consumer(self.root, path, environ=env)
        path.unlink()
        with self.assertRaises(ConfigError):load_consumer(self.root, path, environ=env)

    def test_CF05_normal_start_resolves_once_and_preparation_and_children_share_snapshot(self):
        self.split()
        napcat = self.root / 'napcat'
        (napcat / 'versions/9.9.33-52230/resources/app/napcat/config').mkdir(parents=True)
        path = self.root / 'runtime/astrbot/data/cmd_config.json';path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'platform_settings': {}, 'provider_settings': {'proactive_capability': {}}}))
        gate = Mock(upstream_token='synthetic', allowed_groups={'111'}, admin_users={'333'}, bot_qq='222')
        loaded = []
        identities = []
        def prepare(*args, **kwargs):
            data = load_consumer(self.root, environ=kwargs['env'])
            loaded.append(('prepare', data, dict(kwargs['env'])))
            # Editing disk during startup must not affect any consumer.
            self.write('chat.yaml', 'chat: {history_turns: 9}')
            return Mock(returncode=0)
        def popen(args, **kwargs):
            component = args[2]
            data = load_consumer(self.root, environ=kwargs['env'])
            loaded.append((component, data, dict(kwargs['env'])))
            return Mock()
        def capture(entries, process, component, started):
            entry = {'pid': 123, 'created': 1., 'component': component}
            entries.append(entry);identities.append(entry)
        with ExitStack() as stack:
            for name, value in (('ROOT',self.root), ('STATE',self.root/'state/managed-processes.json'), ('NAPCAT',napcat)):
                stack.enter_context(patch.object(manage, name, value))
            read = stack.enter_context(patch.object(manage, 'read_project', wraps=read_project))
            stack.enter_context(patch.object(manage, 'load_gate_config', return_value=gate))
            stack.enter_context(patch.object(manage.subprocess, 'run', side_effect=prepare))
            stack.enter_context(patch.object(manage.psutil, 'Popen', side_effect=popen))
            stack.enter_context(patch.object(manage, 'check_port'))
            stack.enter_context(patch.object(manage.socket.socket, 'connect_ex', return_value=0))
            stack.enter_context(patch.object(manage, 'capture', side_effect=capture))
            stack.enter_context(patch.object(manage, 'alive', return_value=True))
            stack.enter_context(patch.object(manage, 'show_status'))
            # Produce the ready identity from a consumer, without launching a process.
            original = popen
            def ready(args, **kwargs):
                process = original(args, **kwargs)
                if args[2] == 'astrbot':
                    (self.root/'state/router-ready.json').write_text(json.dumps(dict(instance_id=kwargs['env']['QQBOT_INSTANCE_ID'],config_digest=kwargs['env']['QQBOT_CONFIG_DIGEST'])))
                return process
            manage.psutil.Popen.side_effect = ready
            manage.start_channel(full=True, paused=True)
            self.assertEqual(read.call_count, 1)
        self.assertEqual({name for name, _, _ in loaded}, {'prepare','astrbot','gate','model','napcat'})
        self.assertTrue(all(data == self.data for _, data, _ in loaded))
        self.assertEqual(len({env['QQBOT_CONFIG_DIGEST'] for _, _, env in loaded}), 1)
        self.assertEqual(read_project(self.root).settings['chat']['history_turns'], 9)

    def test_CF05_tamper_after_preparation_prevents_process_creation(self):
        self.split()
        path = self.root / 'runtime/astrbot/data/cmd_config.json';path.parent.mkdir(parents=True)
        path.write_text('{}')
        def prepare(*args, **kwargs):
            Path(kwargs['env']['QQBOT_CONFIG_SNAPSHOT']).write_text('tampered',encoding='utf-8')
            return Mock(returncode=0)
        with patch.object(manage,'ROOT',self.root),patch.object(manage,'STATE',self.root/'state/managed-processes.json'), \
                patch.object(manage,'load_gate_config'),patch.object(manage,'check_port'), \
                patch.object(manage.subprocess,'run',side_effect=prepare),patch.object(manage.psutil,'Popen') as spawn:
            with self.assertRaises(ConfigError):manage.start_channel(full=True)
            spawn.assert_not_called()

    def test_CF06_semantic_source_and_session_version_separate(self):
        before = self.split()
        path = self.root / 'config/local/models.yaml'
        path.write_bytes(path.read_bytes() + b'\n# comment only\n')
        after = read_project(self.root)
        self.assertNotEqual(before.source_digest, after.source_digest)
        self.assertEqual(before.semantic_digest, after.semantic_digest)
        self.assertEqual(session_version('合成', before.settings), session_version('合成', after.settings))
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        data['llm']['profiles']['ollama_ssh']['num_ctx'] = 24576
        path.write_text(yaml.safe_dump(data), encoding='utf-8')
        other = read_project(self.root)
        self.assertEqual(session_version('合成', before.settings), session_version('合成', other.settings))
        data['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'] = 15000
        path.write_text(yaml.safe_dump(data), encoding='utf-8')
        self.assertNotEqual(session_version('合成', before.settings), session_version('合成', read_project(self.root).settings))
        with patch.object(manage, 'ROOT', self.root):
            self.assertTrue(manage.configuration_status({'configuration': {'source_digest': before.source_digest, 'semantic_digest': before.semantic_digest}})['pending_restart'])

    def test_CF05_snapshot_retention_preserves_unknown_and_referenced(self):
        config=self.split()
        paths=[]
        for number in range(5):
            path=create_snapshot(config,f'{number:032x}')[0];paths.append(path)
            os.utime(path.parent,(1000+number,1000+number))
        unknown=self.root/'state/config-runtime/unknown';unknown.mkdir();(unknown/'private').write_bytes(b'preserve')
        (self.root/'state/service-mode.json').write_text(json.dumps(dict(instance_id=paths[0].parent.name)))
        prune_snapshots(self.root,keep=3)
        self.assertTrue(paths[0].exists())
        self.assertTrue((unknown/'private').exists())
        self.assertFalse(paths[1].exists())
        # Unverifiable registry prevents all further cleanup.
        (self.root/'state/managed-processes.json').write_text('broken')
        before=self.capture();prune_snapshots(self.root,keep=0);self.assertEqual(before,self.capture())
        (self.root/'state/managed-processes.json').unlink()
        marker=self.root/'state/cli-cleanup/unresolved.json';marker.parent.mkdir();marker.write_text('{}')
        before=self.capture();prune_snapshots(self.root,keep=0);self.assertEqual(before,self.capture())

    def test_CF07_old_writes_and_feature_rollback_refuse_split(self):
        config = self.split();before = self.capture()
        for call in (lambda: save_settings(self.legacy, config.settings, config.source_digest),
                     lambda: export_legacy_config(self.legacy),
                     lambda: activate_legacy_config(self.legacy, 'x', 'a'*64, 'b'*64, '已核对'),
                     lambda: configure_bot.execute(self.legacy, 'groups', 'add', '111'),
                     lambda: configure_bot.execute(self.legacy, 'model', 'set', 'deepseek-v4.1-flash'),
                     lambda: save_settings(self.root/'state/config-runtime/x/settings.yaml', self.data, config.source_digest)):
            with self.assertRaises(ConfigError):call()
        self.assertEqual(self.capture(), before)

    def test_CF07_no_argument_index_does_not_read_config(self):
        output = StringIO()
        with patch.object(sys, 'argv', ['configure_bot.py']), patch.object(configure_bot, 'ROOT', self.root), \
                patch.object(configure_bot, 'read_settings', side_effect=AssertionError('read')), redirect_stdout(output):
            self.assertEqual(configure_bot.main(), 0)
        self.assertIn('config/README.md', output.getvalue())

    def test_CF07_admin_actions_keep_source_and_authorization_guards(self):
        self.data['memory'].update(enabled=True,learning_enabled=True)
        self.legacy.write_text(yaml.safe_dump(self.data),encoding='utf-8')
        config=self.split()
        store=Mock();store.manage.return_value={'records':0}
        with patch('qqbot_gateway.group_memory.MemoryStore',return_value=store) as factory, \
                patch.object(configure_bot,'_MEMORY_MANAGER',None):
            configure_bot.memory_action(self.legacy,'111','inspect',config_digest=config.source_digest)
            self.assertEqual(factory.call_args.args[0],self.root)
            with self.assertRaisesRegex(ValueError,'Unauthorized'):
                configure_bot.memory_action(self.legacy,'444','inspect',config_digest=config.source_digest)
            self.write('chat.yaml','chat: {history_turns: 9}')
            with self.assertRaisesRegex(ValueError,'Configuration changed'):
                configure_bot.memory_action(self.legacy,'111','clear',config_digest=config.source_digest)
            self.assertEqual(store.manage.call_count,1)
        from qqbot_gateway import napcat_login
        with patch.object(napcat_login,'credential_status',return_value={'state':'not_configured'}) as status:
            napcat_login.configure_credentials(self.legacy,'status',root=self.root)
            status.assert_called_once_with(self.root,'222')
        # Existing admin action can read split source without writing any settings.
        from qqbot_gateway.meme_catalog import MemeCatalog
        before=self.capture()
        catalog=MemeCatalog(self.root,config.settings['memes'],config_guard=configure_bot.ConfigMenu(self.legacy).config_guard(config.source_digest))
        with self.assertRaisesRegex(ValueError,'Configuration changed'):catalog.save()
        self.assertEqual(before,self.capture())

    def test_CF07_admin_pages_offer_only_management_choices(self):
        self.split()
        console=Mock();console.choose.return_value='0'
        page=configure_bot.ConfigMenu(self.legacy,console)
        page.memes_group(admin_only=True)
        self.assertEqual(console.choose.call_args.args[0],set('01234567'))
        page.memory_group(admin_only=True)
        self.assertEqual(console.choose.call_args.args[0],{'0','3'})

    def test_CF08_existing_safety_constraints(self):
        self.split()
        local = self.root / 'config/local'
        for section, key, value in (('access','private_enabled',True), ('onebot','host','0.0.0.0'),
                                    ('secrets_file',None,'../outside.json')):
            data = copy.deepcopy(self.data)
            if key:data[section][key] = value
            else:data[section] = value
            name = next(name for name, keys in LAYOUT.items() if section in keys)
            original = (local / name).read_bytes()
            self.write(name, render(name, partition(data)[name]))
            with self.assertRaises(ConfigError):read_project(self.root)
            (local / name).write_bytes(original)
        from qqbot_gateway.vision import require_production
        from qqbot_gateway.members import suspend_unverified
        data = copy.deepcopy(self.data);data['vision']['enabled'] = True
        with self.assertRaises(ValueError):require_production(data)
        data['members'].update(enabled=True, mentions_enabled=True)
        self.assertFalse(suspend_unverified(data)['enabled'])

    def test_CF09_complete_export_and_rollback_keep_other_state(self):
        self.data['participation']['mode'] = 'free'
        self.legacy.write_text(yaml.safe_dump(self.data), encoding='utf-8')
        config = self.split()
        extra = self.root / 'state/remote-unknown';extra.write_bytes(b'synthetic unresolved')
        result = export_legacy(self.root)
        self.assertFalse(result['activated'])
        self.assertEqual(yaml.safe_load(Path(result['export']).read_text(encoding='utf-8')), config.settings)
        self.assertTrue((self.root / 'config/local').is_dir())
        for source, digest, confirm in (('a'*64,result['export_digest'],'已核对'),
                                        (result['source_digest'],'b'*64,'已核对'),
                                        (result['source_digest'],result['export_digest'],'')):
            with self.assertRaises(ConfigError):rollback_layout(self.root, result['export'], source, digest, confirm)
        output = rollback_layout(self.root, result['export'], result['source_digest'], result['export_digest'], '已核对')
        self.assertEqual(read_project(self.root).settings, config.settings)
        self.assertEqual(extra.read_bytes(), b'synthetic unresolved')
        self.assertFalse((self.root / 'config/local').exists())
        self.assertEqual(len(list((Path(output['backup']) / 'local-archived').glob('*.yaml'))), 5)

    def test_CF09_interruption_after_legacy_write_retains_split_and_can_retry(self):
        self.split();result = export_legacy(self.root)
        import qqbot_gateway.config_layout_ops as ops
        rename = ops.os.rename
        with patch.object(ops.os, 'rename', side_effect=OSError('archive failure')):
            with self.assertRaisesRegex(ConfigError,'config/local仍优先'):rollback_layout(self.root, result['export'], result['source_digest'], result['export_digest'], '已核对')
        self.assertEqual(read_project(self.root).layout, 'split')
        self.assertEqual(self.legacy.read_bytes(), Path(result['export']).read_bytes())
        output = rollback_layout(self.root, result['export'], result['source_digest'], result['export_digest'], '已核对')
        self.assertTrue(output['completed'])

    def test_CF09_source_and_export_race_leave_split_in_charge(self):
        self.split();result=export_legacy(self.root)
        import qqbot_gateway.config_layout_ops as ops
        writer=ops.record
        def race(directory,**fields):
            value=writer(directory,**fields)
            if fields['stage']=='legacy-written':Path(result['export']).write_bytes(b'changed')
            return value
        with patch.object(ops,'record',side_effect=race):
            with self.assertRaisesRegex(ConfigError,'布局回滚未完成'):
                rollback_layout(self.root,result['export'],result['source_digest'],result['export_digest'],'已核对')
        self.assertEqual(read_project(self.root).layout,'split')
        outside=self.root/'outside.yaml';outside.write_bytes(b'preserve')
        with self.assertRaises(ConfigError):rollback_layout(self.root,outside,result['source_digest'],sha(b'preserve'),'已核对')
        self.assertEqual(outside.read_bytes(),b'preserve')

    def test_CF10_ignore_and_template_index(self):
        paths = ['config/local/bot.yaml', 'state/config-runtime/x/settings.yaml', 'state/config-backups/x/settings.export.yaml', 'secrets/fixture.json']
        result = subprocess.run(['git', 'check-ignore', '-z', '--stdin'], input=('\0'.join(paths)+'\0').encode(), cwd=ROOT, capture_output=True, check=True)
        self.assertEqual(result.stdout.decode().strip('\0').split('\0'), paths)
        index = (ROOT / 'config/README.md').read_text(encoding='utf-8')
        for name in LAYOUT:self.assertIn(name, index)
