"""Synthetic fixtures only; no sockets, QQ, credentials or original runtime."""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from qqbot_gateway.config import normalize_settings, read_settings
from qqbot_gateway.config_files import read_project, canonical, sha, create_snapshot, load_consumer
from qqbot_gateway.config_layout_ops import initialize, partition
from qqbot_gateway.qq_transport import (DEFAULTS, PROOF_FORMAT, RELEASE, TAG_SHA, BUNDLE_NAME,
    BUNDLE_SHA256, BUNDLE_SIZE, POLICY_VERSION, resolve_transport, validate_static_proof,
    inspect_transport, checked_path, provider_description)
from scripts import transport


def synthetic():
    data = yaml.safe_load((ROOT / 'config/settings.example.yaml').read_text(encoding='utf-8'))
    data.pop('qq_transport', None)
    data['bot']['qq'] = '222'
    data['access'].update(allowed_groups=['111'], admin_users=['333'], blocked_users=['999'])
    return data


def proof():
    value = dict(format=PROOF_FORMAT, release=RELEASE, tag_sha=TAG_SHA,
        bundle=dict(file=DEFAULTS['snowluma']['runtime_root']+'/'+BUNDLE_NAME,
                    sha256=BUNDLE_SHA256, size=BUNDLE_SIZE))
    for key in ('native_deployment', 'clean_qq', 'data_scope', 'private_build'):
        value[key] = dict(evidence_file='state/qq-transport/'+key+'.local.json', evidence_sha256='a'*64)
    value['clean_qq']['executable_sha256'] = 'b'*64
    value['private_build'].update(build_file='runtime/snowluma-private/build.mjs',
        policy_file='runtime/snowluma-private/project_policy.mjs',
        build_sha256='c'*64, policy_sha256='d'*64, policy_version=POLICY_VERSION)
    return value


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'config').mkdir()
        self.path = self.root/'config/settings.local.yaml'
        self.raw = synthetic()

    def write(self, data=None):
        self.path.write_text(yaml.safe_dump(self.raw if data is None else data, sort_keys=False), encoding='utf-8')

    def test_old_schemas_exact_semantic_digest_and_no_mutation(self):
        # Generated once from committed 6556b24 config.py, before LAP-40 edits.
        expected = '87b772031496d4601ced40978c0634ef6aedbd8f4c491aebeb177d58c1ed9a7e'
        for version in (1, 2, 3):
            raw = deepcopy(self.raw);raw['schema_version'] = version
            before = deepcopy(raw)
            data = normalize_settings(raw)
            self.assertEqual(sha(canonical(data)), expected)
            self.assertNotIn('qq_transport', data)
            self.assertEqual(raw, before)
            resolved = resolve_transport(data)
            resolved['snowluma']['control_port'] = 5000
            self.assertEqual(resolve_transport(data), DEFAULTS)
            self.assertEqual(provider_description(data).name, 'napcat')

    def test_legacy_split_snapshot_raw_and_semantic_compatibility(self):
        self.write();original = self.path.read_bytes()
        before = read_project(self.root)
        self.assertEqual(before.source_digest, hashlib.sha256(original).hexdigest())
        path, metadata = create_snapshot(before, 'a'*32)
        self.assertEqual(metadata['snapshot_digest'],
                         '1a36ae51af2d3c57318053033d6d79313244283a7bffd6ef533b309e9e3a16f4')
        # Existing consumer validates raw and semantic digests for old snapshots.
        with patch.dict(os.environ, {'QQBOT_CONFIG_SNAPSHOT': str(path)}, clear=False):
            from qqbot_gateway.config_files import snapshot_environment
            with patch.dict(os.environ, snapshot_environment(self.root, path, metadata), clear=False):
                self.assertEqual(load_consumer(self.root), before.settings)
        initialize(self.root, migrate=True)
        after = read_project(self.root)
        self.assertEqual(before.semantic_digest, after.semantic_digest)
        self.assertEqual(before.settings, after.settings)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertNotIn('qq_transport', partition(before.settings)['runtime.yaml'])

    def test_optional_present_partial_stays_partial(self):
        self.raw['qq_transport'] = {'provider': 'snowluma'}
        normalized = normalize_settings(self.raw)
        self.assertEqual(normalized['qq_transport'], {'provider': 'snowluma'})
        self.assertEqual(resolve_transport(normalized)['snowluma'], DEFAULTS['snowluma'])
        self.assertTrue(provider_description(normalized).independent_health)
        self.write();initialize(self.root, migrate=True)
        self.assertEqual(read_project(self.root).settings, normalized)

    def test_absent_section_does_not_reserve_new_ports_or_secret_reference(self):
        self.raw['llm']['port'] = 5098
        self.raw['secrets_file'] = DEFAULTS['snowluma']['control_secret_file']
        normalized = normalize_settings(self.raw)
        self.assertEqual(resolve_transport(normalized)['provider'], 'napcat')
        self.assertNotIn('qq_transport', normalized)

    def test_unknown_type_range_and_combination_reject(self):
        bad = [None, [], {'provider': []}, {'provider': 'other'}, {'bypass': True},
               {'snowluma': {'valid': True}}, {'recovery': {'enabled': 1}},
               {'trial': {'total_hours': 169}}]
        for key, val in [('control_port', True), ('control_port', 0), ('control_port', 65536),
                         ('health_poll_seconds', 4), ('health_poll_seconds', 11),
                         ('health_ttl_seconds', 31), ('ready_timeout_seconds', 59)]:
            bad.append({'snowluma': {key: val}})
        bad += [{'snowluma': {'health_poll_seconds': 10, 'health_ttl_seconds': 29}},
                {'recovery': {'drain_seconds': 149}}, {'recovery': {'max_qq_per_24h': 2}},
                {'recovery': {'max_snowluma_per_24h': 3}}, {'recovery': {'cooldown_seconds': 1799}}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_settings(self.raw | {'qq_transport': value})

    def test_port_collisions_include_custom_active_ports(self):
        for port in (6099, 3000, 3001, 6185, 6199, 6200, 8765, 7777, 7778):
            data = deepcopy(self.raw)
            data['onebot'].update(port=7777, upstream='ws://127.0.0.1:7778/ws')
            with self.subTest(port=port), self.assertRaises(ValueError):
                resolve_transport(data | {'qq_transport': {'snowluma': {'control_port': port}}})

    def test_scoped_paths_and_legacy_extension_collision(self):
        for name in ('../runtime/x', 'C:/runtime/x', 'runtime/../x', '/runtime/x',
                     'runtime\\x', 'secrets/x', 'runtime//x', 'runtime/x:stream',
                     'runtime/x.', 'runtime/x ', 'runtime/NUL', 'runtime/a?b'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                normalize_settings(self.raw | {'qq_transport': {'snowluma': {'runtime_root': name}}})
        with self.assertRaises(ValueError):normalize_settings(self.raw | {'legacy_extensions': {'qq_transport': {}}})
        for path in ('secrets/local-tokens.json', 'secrets/bilibili-session.local.json'):
            with self.assertRaises(ValueError):
                normalize_settings(self.raw | {'qq_transport': {'snowluma': {'control_secret_file': path}}})
        self.write();initialize(self.root, migrate=True)
        path = self.root/'config/local/runtime.yaml'
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        data['legacy_extensions'] = {'qq_transport': {'provider': 'snowluma'}}
        path.write_text(yaml.safe_dump(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '扩展字段冲突'):read_project(self.root)

    def test_existing_link_ancestor_rejects_even_missing_leaf(self):
        outside = self.root/'outside';outside.mkdir()
        (self.root/'runtime').mkdir()
        link = self.root/'runtime/link'
        try:link.symlink_to(outside, target_is_directory=True)
        except OSError:
            # NT junction needs no symlink privilege, and remains a real reparse test.
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)],
                           check=True, capture_output=True)
        self.addCleanup(lambda:link.rmdir() if link.exists() else None)
        with self.assertRaises(ValueError):checked_path(self.root, 'runtime/link/missing/file', 'runtime')
        data = self.raw | {'qq_transport': {'snowluma': {'runtime_root': 'runtime/link/missing'}}}
        self.write(data)
        with self.assertRaises(ValueError):read_settings(self.path)

    def test_reparse_point_rejected_without_symlink_privilege(self):
        (self.root/'runtime').mkdir()
        actual = Path.lstat
        def lstat(path, *args, **kwargs):
            value = actual(path, *args, **kwargs)
            if path == self.root/'runtime':
                from types import SimpleNamespace
                return SimpleNamespace(st_mode=value.st_mode, st_file_attributes=0x400)
            return value
        with patch.object(Path, 'lstat', lstat), self.assertRaises(ValueError):
            checked_path(self.root, 'runtime/missing', 'runtime')

    def test_strict_proof_fixed_release_and_no_true_bypass(self):
        valid = proof();self.assertEqual(validate_static_proof(valid), valid)
        for mutate in (lambda p:p.update(valid=True), lambda p:p.update(tag_sha='0'*40),
                       lambda p:p['bundle'].update(sha256='a'*64),
                       lambda p:p['bundle'].update(size=True),
                       lambda p:p['private_build'].update(policy_version='other'),
                       lambda p:p['clean_qq'].update(evidence_sha256='invalid'),
                       lambda p:p['data_scope'].update(evidence_file='secrets/private.json'),
                       lambda p:p.update(native_deployment=True)):
            value = proof();mutate(value)
            with self.assertRaises(ValueError):validate_static_proof(value)

    def test_inspect_read_only_redacted_no_secret_or_network(self):
        secret = self.root/'secrets/snowluma-control.local.json'
        secret.parent.mkdir();secret.write_text('PRIVATE_SECRET', encoding='utf-8')
        before = {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        original = Path.open
        def guard(path, *args, **kwargs):
            self.assertNotEqual(path, secret)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', guard), patch('socket.socket', side_effect=AssertionError('network')):
            result = inspect_transport(self.root, self.raw)
        self.assertFalse(result['channel_ready'])
        self.assertIn('official_bundle_missing', result['blockers'])
        self.assertIn('static_proof_missing', result['blockers'])
        self.assertNotIn('PRIVATE_SECRET', json.dumps(result))
        self.assertEqual(before, {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_invalid_duplicate_or_oversized_proof_no_payload_output(self):
        path = self.root/DEFAULTS['snowluma']['proof_file'];path.parent.mkdir(parents=True)
        for content in ('{"format":"PRIVATE_VALUE","format":true}', 'PRIVATE_VALUE', 'x'*16385):
            path.write_text(content, encoding='utf-8')
            result = inspect_transport(self.root, self.raw)
            self.assertIn('static_proof_invalid', result['blockers'])
            self.assertNotIn('PRIVATE_VALUE', json.dumps(result))

    def test_structurally_valid_proof_without_artifacts_never_ready(self):
        path = self.root/DEFAULTS['snowluma']['proof_file'];path.parent.mkdir(parents=True)
        path.write_text(json.dumps(proof()), encoding='utf-8')
        result = inspect_transport(self.root, self.raw)
        self.assertFalse(result['static_evidence_checked'])
        self.assertFalse(result['channel_ready'])
        self.assertIn('static_evidence_mismatch', result['blockers'])
        self.assertIn('clean_qq_unverified', result['blockers'])

    def test_actual_file_digest_binding_and_static_success_is_not_admission(self):
        # Synthetic release constants only inside this test. No official artifacts.
        value = proof()
        contents = {value['bundle']['file']: b'fixture-archive',
                    DEFAULTS['snowluma']['qq_executable']: b'fixture-QQ',
                    value['private_build']['build_file']: b'fixture-build',
                    value['private_build']['policy_file']: b'fixture-policy'}
        for key in ('native_deployment', 'clean_qq', 'data_scope', 'private_build'):
            record = value[key]
            contents[record['evidence_file']] = ('fixture-'+key).encode()
            record['evidence_sha256'] = sha(contents[record['evidence_file']])
        value['bundle'].update(sha256=sha(b'fixture-archive'), size=len(b'fixture-archive'))
        value['clean_qq']['executable_sha256'] = sha(b'fixture-QQ')
        value['private_build'].update(build_sha256=sha(b'fixture-build'), policy_sha256=sha(b'fixture-policy'))
        contents[DEFAULTS['snowluma']['proof_file']] = json.dumps(value).encode()
        for name, content in contents.items():
            path = self.root/name;path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(content)
        with patch('qqbot_gateway.qq_transport.BUNDLE_SHA256', sha(b'fixture-archive')), \
             patch('qqbot_gateway.qq_transport.BUNDLE_SIZE', len(b'fixture-archive')):
            result = inspect_transport(self.root, self.raw)
            self.assertTrue(result['static_evidence_checked'])
            self.assertFalse(result['channel_ready'])
            self.assertIn('private_build_unverified', result['blockers'])
            (self.root/value['private_build']['policy_file']).write_bytes(b'changed')
            self.assertIn('static_evidence_mismatch', inspect_transport(self.root, self.raw)['blockers'])

    def test_cli_missing_config_redacted_and_synthetic_config_only(self):
        output = StringIO()
        with redirect_stdout(output):self.assertEqual(transport.main(['--root', str(self.root), 'inspect']), 1)
        self.assertEqual(json.loads(output.getvalue())['error'], 'transport_config_invalid')
        self.write();before = self.path.read_bytes();output = StringIO()
        with redirect_stdout(output):self.assertEqual(transport.main(['--root', str(self.root), 'inspect', '--json']), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result['provider'], 'napcat')
        self.assertFalse(result['channel_ready'])
        self.assertNotIn('222', output.getvalue())
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':unittest.main()
