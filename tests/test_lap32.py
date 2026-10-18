"""Cleanup ledger I/O regression; temporary files and fake model processes only."""
import errno
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'tests')]
from qqbot_gateway.cleanup_identity import CleanupOwner
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.lifecycle import atomic_json
from scripts.process_host import safe_line
import test_cli_runner as fixture


def locked(code=32):
    error = PermissionError('private filename and credential must never be logged')
    error.winerror = code
    return error


class LedgerIOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lap32-')
        self.root = Path(self.temp.name)
        self.owner = CleanupOwner(self.root)
        self.owner.reserve()

    def tearDown(self):
        self.temp.cleanup()

    def resolved(self):
        self.owner.record.update(blocked=False, generation_outcome='success', cleanup_outcome='observed_empty')
        return self.owner.record

    def test_transient_replace_preserves_ledger_and_reports_fixed_metadata(self):
        real = atomic_json
        calls = []
        def write(path, value):
            calls.append(1)
            if len(calls) < 3:
                raise locked(5)
            real(path, value)
        with patch('qqbot_gateway.cleanup_identity.atomic_json', side_effect=write), self.assertLogs('qqbot_gateway.cleanup_identity', level='WARNING') as logs:
            self.owner.ledger.write(self.resolved(), time.monotonic()+1)
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.owner.ledger.read()['generation_outcome'], 'success')
        for line in logs.output:
            safe = safe_line('model', line)
            self.assertIsNotNone(safe)
            self.assertNotIn('private', safe)
            self.assertIn('operation=write_unresolved error=ACCESS_DENIED', safe)

    def test_transient_rotation_and_unresolved_delete_both_recover(self):
        value = self.resolved()
        for i in range(32):
            value['trace'] = f'{i:010x}'
            self.owner.ledger.write(value)
            self.owner.ledger.resolve(value, time.monotonic()+1)
        self.owner.ledger.write(value)
        real = Path.unlink
        failures = set()
        def unlink(path, *args, **kwargs):
            category = 'unresolved' if path.name == 'unresolved.json' else 'summary'
            if path.suffix == '.json' and category not in failures:
                failures.add(category)
                raise locked()
            return real(path, *args, **kwargs)
        with patch.object(Path, 'unlink', unlink), self.assertLogs('qqbot_gateway.cleanup_identity', level='WARNING') as logs:
            self.owner.ledger.resolve(value, time.monotonic()+1)
        self.assertEqual(failures, {'unresolved', 'summary'})
        self.assertIsNone(self.owner.ledger.read())
        self.assertEqual(len(list(self.owner.ledger.directory.glob('resolved-*.json'))), 32)
        self.assertTrue(any('operation=rotate_summary' in line for line in logs.output))
        self.assertTrue(any('operation=remove_unresolved' in line for line in logs.output))

    def test_disk_full_and_deadline_do_not_retry_or_discard_unknown(self):
        for error, deadline in [(OSError(errno.ENOSPC, 'private disk'), time.monotonic()+1), (locked(), time.monotonic()-1)]:
            with patch('qqbot_gateway.cleanup_identity.atomic_json', side_effect=error) as write:
                with self.assertRaises(OSError):
                    self.owner.ledger.write(self.owner.record, deadline)
                self.assertEqual(write.call_count, 1)
            self.assertIsNotNone(self.owner.ledger.read())

    def test_summary_names_do_not_collide_when_system_clock_repeats(self):
        value = self.resolved()
        with patch('qqbot_gateway.cleanup_identity.time.time_ns', return_value=1):
            for _ in range(36):
                self.owner.ledger.write(value)
                self.owner.ledger.resolve(value, time.monotonic()+1)
        self.assertEqual(len(list(self.owner.ledger.directory.glob('resolved-*.json'))), 32)
        self.assertIsNone(self.owner.ledger.read())

    def test_retry_does_not_restart_after_sleep_uses_up_deadline(self):
        with patch('qqbot_gateway.cleanup_identity.atomic_json', side_effect=locked()) as write, patch('qqbot_gateway.cleanup_identity.time.monotonic', side_effect=[0., 0., .1]):
            with self.assertRaises(OSError):
                self.owner.ledger.write(self.owner.record, .02)
        self.assertEqual(write.call_count, 1)

    def test_permanent_sharing_failure_is_bounded_and_retains_unknown(self):
        with patch('qqbot_gateway.cleanup_identity.atomic_json', side_effect=locked()) as write:
            started = time.monotonic()
            self.owner.save()
        self.assertLess(time.monotonic()-started, .25)
        self.assertEqual(write.call_count, 3)
        self.assertTrue(self.owner.status()['blocked'])
        self.assertIn('ledger_error', self.owner.record['reasons'])
        self.assertIsNotNone(self.owner.ledger.read())

    def test_process_host_rejects_private_or_unrecognised_diagnostics(self):
        line = 'CLI_CLEANUP_IO trace=0123456789 operation=write_unresolved error=SHARING_VIOLATION attempt=1'
        self.assertEqual(safe_line('model', line), line)
        for bad in [line+' path=private', line.replace('SHARING_VIOLATION', 'PRIVATE'), line.replace('attempt=1','attempt=4'), line.replace('write_unresolved','read_password')]:
            self.assertIsNone(safe_line('model', bad))

    @unittest.skipUnless(os.name == 'nt', 'native Windows read-handle conflict')
    def test_native_reader_releases_during_atomic_replace_retry(self):
        reader = self.owner.ledger.path.open('r', encoding='utf-8')
        release = threading.Timer(.015, reader.close)
        real = atomic_json
        def write(path, value):
            try:
                real(path, value)
            except OSError:
                if release.ident is None:
                    release.start()
                raise
        try:
            with patch('qqbot_gateway.cleanup_identity.atomic_json', side_effect=write), self.assertLogs('qqbot_gateway.cleanup_identity', level='WARNING') as logs:
                self.owner.ledger.write(self.resolved(), time.monotonic()+1)
            self.assertTrue(any('error=ACCESS_DENIED' in line or 'error=SHARING_VIOLATION' in line for line in logs.output))
            self.assertFalse(self.owner.ledger.read()['blocked'])
        finally:
            reader.close()
            if release.ident is not None:
                release.join()


class RunnerIOTests(unittest.IsolatedAsyncioTestCase):
    setUp = fixture.RunnerTests.setUp
    tearDown = fixture.RunnerTests.tearDown
    runner = fixture.RunnerTests.runner

    async def test_success_with_transient_summary_delete_accepts_next_request(self):
        runner = self.runner()
        real = Path.unlink
        attempts = []
        def unlink(path, *args, **kwargs):
            if path.name == 'unresolved.json':
                attempts.append(1)
                if len(attempts) == 1:
                    raise locked()
            return real(path, *args, **kwargs)
        with patch.object(Path, 'unlink', unlink):
            first = await runner.run('system', 'prompt', 'first')
            second = await runner.run('system', 'prompt', 'second')
        self.assertEqual(first, second)
        self.assertEqual(runner.attempts, 2)
        self.assertFalse(runner.cleanup_status()['blocked'])
        self.assertIsNone(runner.cleanup_owner().ledger.read())

    async def test_permanent_summary_delete_failure_blocks_restart_without_new_model_attempt(self):
        runner = self.runner()
        real = Path.unlink
        def unlink(path, *args, **kwargs):
            if path.name == 'unresolved.json':
                raise locked()
            return real(path, *args, **kwargs)
        with patch.object(Path, 'unlink', unlink):
            with self.assertRaises(GatewayError) as caught:
                await runner.run('system', 'prompt', 'first')
        self.assertEqual(caught.exception.code, 'CLEANUP_FAILED')
        record = runner.cleanup_owner().ledger.read()
        self.assertEqual(record['generation_outcome'], 'success')
        self.assertIn('ledger_error', record['reasons'])
        restarted = self.runner()
        with self.assertRaises(GatewayError):
            await restarted.run('', '', 'new')
        self.assertEqual(restarted.attempts, 0)
        self.assertTrue(restarted.cleanup_status()['blocked'])
