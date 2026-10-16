import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from qqbot_gateway.config import (configuration_lock, load_settings, normalize_settings,
                                  read_settings, require_stopped, save_settings)
from scripts.configure_bot import execute


def fixture():
    data = yaml.safe_load((ROOT / 'config/settings.example.yaml').read_text(encoding='utf-8'))
    data.pop('schema_version')
    data['bot']['qq'] = 222
    data['access']['allowed_groups'] = [111, '111', '444']
    data['access']['admin_users'] = [333]
    data['access'].pop('blocked_users')
    data.pop('chat')
    data.pop('output')
    data['extension'] = {'preserve': ['future', 42]}
    return data


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        self.path = self.root / 'config/settings.local.yaml'
        self.path.write_text(yaml.safe_dump(fixture()), encoding='utf-8-sig')
        self.original = self.path.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def test_v1_bom_normalization_is_read_only(self):
        data = load_settings(self.path)
        self.assertEqual(data['schema_version'], 2)
        self.assertEqual(data['access']['allowed_groups'], ['111', '444'])
        self.assertEqual(data['access']['admin_users'], ['333'])
        self.assertEqual(data['access']['blocked_users'], [])
        self.assertEqual(data['llm']['reasoning_effort'], 'auto')
        self.assertIsNone(data['llm']['context_window_tokens'])
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_rejects_invalid_ids_and_empty_authorization(self):
        for field in ('allowed_groups', 'admin_users', 'blocked_users'):
            for value in (True, -1, '', '1e3', '1x', None, 1.5, '001', 0):
                data = fixture(); data['access'][field] = [value]
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    normalize_settings(data)
        for field in ('allowed_groups', 'admin_users'):
            data = fixture(); data['access'][field] = []
            with self.assertRaises(ValueError): normalize_settings(data)

    def test_invalid_complete_config_and_unimplemented_controls(self):
        for section, key, value in [('access', 'private_enabled', True), ('onebot', 'port', True),
                                    ('llm', 'model', '--model injected'), ('llm', 'reasoning_effort', 'medium'),
                                    ('llm', 'context_window_tokens', 32768), ('chat', 'history_turns', 65),
                                    ('output', 'mode', 'markdown')]:
            data = fixture(); data.setdefault(section, {})[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): normalize_settings(data)
        for raw in (None, [], {'schema_version': True}, {'schema_version': 3}):
            with self.assertRaises(ValueError): normalize_settings(raw)

    def test_atomic_backup_unknown_fields_and_stale_digest(self):
        data, digest = read_settings(self.path)
        data['access']['blocked_users'] = [333, '333']
        save_settings(self.path, data, digest)
        saved = load_settings(self.path)
        self.assertEqual(saved['access']['blocked_users'], ['333'])
        self.assertEqual(saved['extension'], fixture()['extension'])
        self.assertEqual(saved['llm']['model'], fixture()['llm']['model'])
        self.assertEqual(next((self.root / 'state/config-backups').glob('*.yaml')).read_bytes(), self.original)
        changed = self.path.read_bytes()
        with self.assertRaises(ValueError): save_settings(self.path, data, digest)
        self.assertEqual(self.path.read_bytes(), changed)

    def test_replace_failure_keeps_original_and_cleans_temporary(self):
        data, digest = read_settings(self.path)
        data['access']['blocked_users'] = ['555']
        with patch('qqbot_gateway.config.os.replace', side_effect=OSError('simulated')):
            with self.assertRaises(OSError): save_settings(self.path, data, digest)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_external_edit_during_save_is_not_overwritten(self):
        data, digest = read_settings(self.path)
        original_check = require_stopped
        calls = 0
        external = self.original + b'\n# external edit\n'
        def check(root):
            nonlocal calls
            calls += 1
            if calls == 2: self.path.write_bytes(external)
            original_check(root)
        with patch('qqbot_gateway.config.require_stopped', side_effect=check):
            with self.assertRaises(ValueError): save_settings(self.path, data, digest)
        self.assertEqual(self.path.read_bytes(), external)

    def test_live_identity_denies_write_and_reused_pid_is_safe(self):
        state = self.root / 'state'; state.mkdir()
        identity = {'pid': os.getpid(), 'created': psutil.Process().create_time()}
        for filename, payload in [('managed-processes.json', [identity]), ('router-ready.json', identity)]:
            file = state / filename
            file.write_text(json.dumps(payload), encoding='utf-8')
            data, digest = read_settings(self.path)
            with self.assertRaises(ValueError): save_settings(self.path, data, digest)
            self.assertEqual(self.path.read_bytes(), self.original)
            file.unlink()
        identity['created'] -= 100
        (state / 'managed-processes.json').write_text(json.dumps([identity]), encoding='utf-8')
        save_settings(self.path, data, digest)
        self.assertEqual(load_settings(self.path)['access']['allowed_groups'], ['111', '444'])

    def test_unreadable_or_malformed_state_fails_closed(self):
        state = self.root / 'state'; state.mkdir()
        for content in ('not json', '{}', '[{}]'):
            (state / 'managed-processes.json').write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError): require_stopped(self.root)

    def test_stopped_edit_is_seen_by_gate_model_and_router_loaders(self):
        from qqbot_gateway.config import load_gate_config
        (self.root / 'secrets').mkdir()
        (self.root / 'secrets/local-tokens.json').write_text(json.dumps({
            'onebot_inbound': 'a'*40, 'onebot_upstream': 'b'*40}), encoding='utf-8')
        old_gate = load_gate_config(self.path)
        execute(self.path, 'groups', 'add', '777')
        execute(self.path, 'blacklist', 'add', '333')
        new_gate = load_gate_config(self.path)
        # Router and model both call load_settings at construction/startup.
        router_snapshot = load_settings(self.path)
        model_snapshot = load_settings(self.path)
        self.assertEqual(new_gate.allowed_groups, frozenset(router_snapshot['access']['allowed_groups']))
        self.assertEqual(new_gate.blocked_users, frozenset(model_snapshot['access']['blocked_users']))
        self.assertNotIn('777', old_gate.allowed_groups)
        self.assertNotIn('333', old_gate.blocked_users)

    def test_parameter_commands_validate_and_preserve_existing_identity(self):
        before=load_settings(self.path)
        execute(self.path,'context','set','32768')
        execute(self.path,'history','set','12')
        execute(self.path,'effort','set','high')
        snapshot=self.path.read_bytes()
        for section,value in [('effort','medium'),('context-window','200000'),('context','1048577'),('context','1e5')]:
            with self.subTest(section=section), self.assertRaises(ValueError):execute(self.path,section,'set',value)
            self.assertEqual(self.path.read_bytes(),snapshot)
        execute(self.path,'effort','set','auto')
        execute(self.path,'model','set','unknown-model')
        with self.assertRaises(ValueError):execute(self.path,'effort','set','high')
        after=load_settings(self.path)
        self.assertEqual(before['bot'],after['bot']);self.assertEqual(before['access'],after['access'])
        self.assertEqual(after['chat']['context_input_limit_tokens'],32768)

    def test_os_lock_blocks_other_process_and_releases(self):
        code = ('import sys; from pathlib import Path; '
                f'sys.path.insert(0, {str(ROOT / "src")!r}); '
                'from qqbot_gateway.config import configuration_lock; '
                'ctx=configuration_lock(Path(sys.argv[1])); ctx.__enter__(); ctx.__exit__(None,None,None)')
        with configuration_lock(self.root):
            result = subprocess.run([sys.executable, '-c', code, str(self.root)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        result = subprocess.run([sys.executable, '-c', code, str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_commands_apply_one_snapshot_and_no_duplicate_backup(self):
        execute(self.path, 'blacklist', 'add', '333')
        backups = list((self.root / 'state/config-backups').glob('*'))
        execute(self.path, 'blacklist', 'add', '333')
        self.assertEqual(backups, list((self.root / 'state/config-backups').glob('*')))
        execute(self.path, 'groups', 'remove', '111')
        with self.assertRaises(ValueError): execute(self.path, 'groups', 'remove', '444')
        execute(self.path, 'blacklist', 'remove', '333')
        self.assertEqual(load_settings(self.path)['access']['allowed_groups'], ['444'])
        self.assertEqual(load_settings(self.path)['access']['blocked_users'], [])

    def test_invalid_config_prevents_starting_any_child(self):
        from scripts import manage
        self.path.write_text('access: {allowed_groups: []}', encoding='utf-8')
        with patch.object(manage, 'ROOT', self.root), patch.object(manage, 'read_state', return_value=[]), \
             patch.object(manage.subprocess, 'run') as child, patch.object(manage, 'check_port') as port:
            with self.assertRaises(ValueError): manage.start_channel(full=True)
            child.assert_not_called(); port.assert_not_called()


if __name__ == '__main__': unittest.main()
