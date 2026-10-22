"""Capacity churn and explicit recovery, only synthetic state/processes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from qqbot_gateway.cleanup_identity import CleanupOwner
from qqbot_gateway.config import configuration_lock
from scripts.cleanup_recovery import recover


class CapacityTests(unittest.TestCase):
    def test_hundreds_of_retired_helpers_do_not_exhaust_request(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = CleanupOwner(directory)
            owner.reserve()
            current = {'pid': 1}
            def probe(entry):
                return ('alive', Mock()) if entry['pid'] == current['pid'] else ('exited', None)
            with patch('qqbot_gateway.cleanup_identity.inspect', side_effect=probe):
                for pid in range(1, 401):
                    current['pid'] = pid
                    process = Mock(pid=pid)
                    process.create_time.return_value = 1.
                    self.assertTrue(owner.add(process, root=pid == 1))
                    self.assertLessEqual(len(owner.ledger.read()['identities']), 128)
            self.assertEqual(owner.record['reasons'], [])
            self.assertIn(400, [e['pid'] for e in owner.ledger.read()['identities']])

    def test_only_os_confirmed_exit_releases_slot(self):
        for state in ('alive', 'access_denied', 'identity_changed'):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as directory:
                owner = CleanupOwner(directory)
                owner.reserve()
                owner.record['identities'] = [dict(pid=i, created=1., outcome='exited', root=False)
                                              for i in range(1, 129)]
                extra = Mock(pid=999)
                extra.create_time.return_value = 1.
                with patch('qqbot_gateway.cleanup_identity.inspect', return_value=(state, None)):
                    self.assertFalse(owner.add(extra))
                self.assertEqual(len(owner.record['identities']), 128)
                self.assertIn('capacity_exceeded', owner.record['reasons'])

    def test_expired_cleanup_deadline_does_not_start_extra_probes(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = CleanupOwner(directory)
            owner.reserve()
            owner.record['identities'] = [dict(pid=i, created=1., outcome='pending', root=False)
                                          for i in range(1, 129)]
            owner.deadline = time.monotonic() - 1
            extra = Mock(pid=999)
            extra.create_time.return_value = 1.
            with patch('qqbot_gateway.cleanup_identity.inspect') as probe:
                self.assertFalse(owner.add(extra))
            probe.assert_not_called()
            self.assertEqual(len(owner.record['identities']), 128)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        owner = CleanupOwner(self.root)
        owner.reserve('0123456789')
        owner.record.update(generation_outcome='success', reasons=['capacity_exceeded'],
                            cleanup_outcome='observed_empty')
        owner.record['identities'] = [dict(pid=123, created=1., outcome='pending', root=True)]
        owner.save()
        self.path = owner.ledger.path
        self.original = self.path.read_bytes()
        self.probe = patch('scripts.cleanup_recovery.inspect', return_value=('exited', None))
        self.inspect = self.probe.start()

    def tearDown(self):
        self.probe.stop()
        self.temp.cleanup()

    def recover(self, **kwargs):
        return recover(self.root, read_state=kwargs.pop('read_state', lambda: []),
                       port_open=kwargs.pop('port_open', lambda port: False), **kwargs)

    def test_archive_exact_bytes_note_and_idempotence(self):
        marker = self.root / 'state/tasks-untouched'
        marker.write_bytes(b'unknown/history/ACK')
        result = self.recover()
        self.assertFalse(result['blocked'])
        self.assertFalse(self.path.exists())
        archive = self.root / result['archive']
        for name in ('unresolved.backup.json', 'unresolved.archived.json'):
            self.assertEqual((archive / name).read_bytes(), self.original)
        note = json.loads((archive / 'manual-recovery.json').read_text())
        self.assertEqual(note['sha256'], hashlib.sha256(self.original).hexdigest())
        self.assertFalse(note['complete_descendant_exit_proven'])
        self.assertEqual(self.recover()['state'], 'not_needed')
        self.assertEqual(marker.read_bytes(), b'unknown/history/ACK')

    def test_live_owner_child_or_managed_identity_refuses_without_mutation(self):
        for index in range(3):
            with self.subTest(index=index):
                self.inspect.side_effect = lambda entry: ('alive', Mock()) if entry.get('pid') == (100 + index) else ('exited', None)
                value = json.loads(self.original)
                value['owner']['pid'] = 100
                value['identities'][0]['pid'] = 101
                self.path.write_text(json.dumps(value), encoding='utf-8')
                before = self.path.read_bytes()
                with self.assertRaises(ValueError):
                    self.recover(read_state=lambda: [dict(pid=102, created=1., component='model')])
                self.assertEqual(self.path.read_bytes(), before)
                self.assertFalse((self.root / 'state/cli-cleanup-manual-archive').exists())

    def test_unknown_reused_identity_or_busy_port_refuses(self):
        for state in ('access_denied', 'identity_changed'):
            self.inspect.return_value = (state, None)
            with self.assertRaises(ValueError):
                self.recover()
        self.inspect.return_value = ('exited', None)
        with self.assertRaises(ValueError):
            self.recover(port_open=lambda port: port == 6099)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_second_check_catches_new_process(self):
        self.inspect.side_effect = lambda entry: ('alive', Mock()) if entry['pid'] == 999 else ('exited', None)
        with self.assertRaises(ValueError):
            self.recover(read_state=Mock(side_effect=[[], [dict(pid=999, created=1.)]]))
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_corrupt_ledger_and_lock_conflict_preserve_source(self):
        with configuration_lock(self.root), self.assertRaises(ValueError):
            self.recover()
        self.path.write_bytes(b'{bad')
        with self.assertRaises(ValueError):
            self.recover()
        self.assertEqual(self.path.read_bytes(), b'{bad')

    def test_backup_io_failure_keeps_active_ledger(self):
        with patch('scripts.cleanup_recovery.write_new', side_effect=OSError('synthetic')):
            with self.assertRaises(OSError):
                self.recover()
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_changed_ledger_before_archive_is_preserved(self):
        calls = 0
        def state():
            nonlocal calls
            calls += 1
            if calls == 2:
                self.path.write_bytes(self.original + b' ')
            return []
        with self.assertRaises(ValueError):
            self.recover(read_state=state)
        self.assertTrue(self.path.exists())


if __name__ == '__main__':
    unittest.main()
