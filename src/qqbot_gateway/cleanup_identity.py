"""Request-owned CLI cleanup. No command lines or user data enter this ledger.

Observed descendants are not a containment proof. In particular a persisted
job_complete label is never accepted as a live Job handle after a restart.
"""
import asyncio
import json
import logging
import math
from pathlib import Path
import threading
import time
import uuid

import psutil

from .config import configuration_lock
from .errors import GatewayError, MESSAGES
from .lifecycle import atomic_json

LOG = logging.getLogger(__name__)
REASONS = {'access_denied', 'wait_timeout', 'identity_changed', 'observation_incomplete',
           'cleanup_in_progress', 'ledger_error', 'capacity_exceeded'}
OUTCOMES = {'active', 'observed_empty', 'owned_alive', 'identity_unknown'}
IDENTITY_RESULTS = {'pending', 'kill_sent', 'exited', 'access_denied', 'identity_changed', 'owned_alive', 'wait_timeout'}


def identity(process):
    return {'pid': process.pid, 'created': process.create_time()}


def inspect(entry):
    """Return only a same-creation process. Reused PIDs must never be killed."""
    try:
        process = psutil.Process(entry['pid'])
        if process.create_time() != entry['created']:
            return 'identity_changed', None
        return ('alive', process) if process.is_running() else ('exited', None)
    except psutil.NoSuchProcess:
        return 'exited', None
    except psutil.Error:
        return 'access_denied', None


def valid_record(value):
    if not isinstance(value, dict) or type(value.get('version')) is not int or value['version'] != 1:
        return False
    fields = {'version', 'trace', 'instance', 'owner', 'identities', 'generation_outcome',
              'cleanup_outcome', 'coverage', 'blocked', 'reasons', 'updated', 'elapsed_ms'}
    if not fields <= set(value) or set(value) - fields - {'checked_at'}:
        return False
    if type(value.get('cleanup_outcome')) is not str or value['cleanup_outcome'] not in OUTCOMES or value.get('coverage') not in ('observed_only', 'job_complete'):
        return False
    if type(value.get('generation_outcome')) is not str or value['generation_outcome'] not in {'pending', 'success', 'cancelled', *MESSAGES}:
        return False
    if not isinstance(value.get('reasons'), list) or len(value['reasons']) > len(REASONS) or any(type(r) is not str or r not in REASONS for r in value['reasons']):
        return False
    for field in ('trace', 'instance'):
        if not isinstance(value.get(field), str) or len(value[field]) != 10 or any(c not in '0123456789abcdef' for c in value[field]):
            return False
    entries = value.get('identities')
    if not isinstance(entries, list) or len(entries) > 128:
        return False
    if not isinstance(value.get('owner'), dict) or set(value['owner']) != {'pid', 'created'}:
        return False
    for entry in entries + [value.get('owner')]:
        if not isinstance(entry, dict) or set(entry) not in ({'pid', 'created'}, {'pid', 'created', 'outcome', 'root'}):
            return False
        if 'outcome' in entry and (type(entry['outcome']) is not str or entry['outcome'] not in IDENTITY_RESULTS or type(entry['root']) is not bool):
            return False
        if type(entry['pid']) is not int or not 0 < entry['pid'] <= 2**32 or type(entry['created']) not in (int, float) or not 0 < entry['created'] < 1e12:
            return False
    for field in ('updated', 'elapsed_ms', 'checked_at'):
        number = value.get(field, 0)
        if type(number) not in (int, float) or not 0 <= number < 1e15 or not math.isfinite(number):
            return False
    return type(value.get('blocked')) is bool


class CleanupLedger:
    def __init__(self, root):
        self.root = Path(root)
        self.directory = Path(root) / 'state/cli-cleanup'
        self.path = self.directory / 'unresolved.json'

    def read(self):
        try:
            if self.path.stat().st_size > 32768:
                raise ValueError('bounded ledger')
            value = json.loads(self.path.read_text(encoding='utf-8'))
            if not valid_record(value):
                raise ValueError('ledger schema')
            return value
        except FileNotFoundError:
            return None

    def capacity(self):
        if self.directory.exists():
            files = list(self.directory.iterdir())
            if len(files) > 34 or sum(p.stat().st_size for p in files if p.is_file()) > 2 * 1024 * 1024 - 65536:
                raise ValueError('ledger capacity')

    def write(self, value):
        if not valid_record(value) or len(json.dumps(value).encode('utf-8')) > 30000:
            raise ValueError('ledger capacity')
        self.capacity()
        atomic_json(self.path, value)

    def resolve(self, value, deadline):
        # Unknown is never evicted to make space. Only resolved summaries rotate.
        summaries = sorted(self.directory.glob('resolved-*.json'), key=lambda p: p.name)
        while len(summaries) >= 32:
            summaries.pop(0).unlink()
        summary = {k: value[k] for k in ('version', 'trace', 'generation_outcome', 'cleanup_outcome', 'coverage', 'reasons', 'updated')}
        atomic_json(self.directory / ('resolved-' + str(time.time_ns()) + '-' + value['trace'] + '.json'), summary)
        if time.monotonic() >= deadline or value['blocked']:
            raise TimeoutError('cleanup deadline')
        self.path.unlink()


class CleanupOwner:
    def __init__(self, root):
        self.ledger = CleanupLedger(root)
        self.task = None
        self.check_task = None
        self.check_thread = None
        self.lock = threading.RLock()
        self.record = None
        self.deadline = None
        self.last_check = 0.
        self.io_failed = False
        self.timed_out = False
        self.instance = uuid.uuid4().hex[:10]

    def reserve(self, request_id=None):
        try:
            with configuration_lock(self.ledger.root):
                self._reserve(request_id)
        except (OSError, ValueError):
            self.io_failed = True
            raise GatewayError('CLEANUP_FAILED') from None

    def _reserve(self, request_id):
        with self.lock:
            try:
                if self.task and not self.task.done() or self.ledger.read() is not None or self.io_failed or self.record and self.record['blocked']:
                    raise GatewayError('CLEANUP_FAILED')
                self.ledger.capacity()
                trace = request_id if isinstance(request_id, str) and len(request_id) == 10 and all(c in '0123456789abcdef' for c in request_id) else uuid.uuid4().hex[:10]
                self.record = dict(version=1, trace=trace, instance=self.instance,
                    owner=identity(psutil.Process()), identities=[], generation_outcome='pending',
                    cleanup_outcome='active', coverage='observed_only', blocked=True,
                    reasons=[], updated=time.time(), elapsed_ms=0)
                self.ledger.write(self.record)
            except (OSError, ValueError, psutil.Error):
                self.io_failed = True
                raise GatewayError('CLEANUP_FAILED') from None

    def reason(self, reason):
        with self.lock:
            if reason not in self.record['reasons']:
                self.record['reasons'].append(reason)

    def add(self, process, root=False):
        entry = identity(process) | {'outcome': 'pending', 'root': root}
        with self.lock:
            if not any(e['pid'] == entry['pid'] and e['created'] == entry['created'] for e in self.record['identities']):
                if len(self.record['identities']) >= 128:
                    self.reason('capacity_exceeded')
                    return False
                self.record['identities'].append(entry)
                self.save()
        return True

    def save(self):
        self.record['updated'] = time.time()
        try:
            self.ledger.write(self.record)
        except (OSError, ValueError):
            self.io_failed = True
            self.reason('ledger_error')

    def observe(self, root):
        try:
            if root is not None and root.is_running():
                # children() may race short-lived intermediate parents: no Job proof.
                for child in root.children(recursive=True):
                    try:
                        self.add(child)
                    except psutil.NoSuchProcess:
                        pass
                    except psutil.Error:
                        self.reason('observation_incomplete')
        except psutil.NoSuchProcess:
            pass
        except psutil.Error:
            self.reason('observation_incomplete')

    def sweep(self, deadline, kill=True):
        alive = unknown = 0
        waiting = []
        with self.lock:
            entries = list(reversed(self.record['identities']))
        # Signal every inspectable owned identity before waiting on any one.
        for entry in entries:
            if time.monotonic() >= deadline:
                self.reason('wait_timeout')
                entry['outcome'] = 'wait_timeout'
                unknown += 1
                continue
            state, process = inspect(entry)
            entry['outcome'] = state if state != 'alive' else 'owned_alive'
            if state == 'access_denied':
                unknown += 1
                self.reason(state)
            elif state == 'identity_changed':
                self.reason(state)
            elif process is not None:
                if kill:
                    try:
                        process.kill()
                        entry['outcome'] = 'kill_sent'
                        waiting.append((entry, process))
                    except psutil.NoSuchProcess:
                        entry['outcome'] = 'exited'
                    except psutil.Error:
                        entry['outcome'] = 'access_denied'
                        unknown += 1
                        self.reason('access_denied')
                else:
                    alive += 1
        for entry, process in waiting:
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
                entry['outcome'] = 'exited'
            except psutil.NoSuchProcess:
                entry['outcome'] = 'exited'
            except psutil.TimeoutExpired:
                entry['outcome'] = 'wait_timeout'
                alive += 1
                self.reason('wait_timeout')
            except psutil.Error:
                entry['outcome'] = 'access_denied'
                unknown += 1
                self.reason('access_denied')
        return 'identity_unknown' if unknown else 'owned_alive' if alive else 'observed_empty'

    def begin(self, process, io, watcher, root, generation, seconds):
        """One strong task owns all finalization, even if callers cancel repeatedly."""
        if self.task and not self.task.done():
            return
        started = time.monotonic()
        self.deadline = started + seconds
        self.record['generation_outcome'] = generation

        async def finish():
            watcher.cancel()
            for task in io:
                task.cancel()
            await asyncio.gather(watcher, *io, return_exceptions=True)
            def work():
                self.save()
                self.observe(root)
                outcome = self.sweep(self.deadline)
                return outcome
            outcome = await asyncio.to_thread(work)
            remaining = self.deadline - time.monotonic()
            if process is not None:
                try:
                    if remaining <= 0:
                        raise TimeoutError
                    await asyncio.wait_for(process.wait(), timeout=remaining)
                except TimeoutError:
                    outcome = 'identity_unknown'
                    self.reason('wait_timeout')
            if time.monotonic() >= self.deadline:
                outcome = 'identity_unknown'
                self.reason('wait_timeout')
            def persist():
                self.record['cleanup_outcome'] = outcome
                bad = set(self.record['reasons']) - {'identity_changed'}
                self.record['blocked'] = bool(outcome != 'observed_empty' or bad or self.io_failed or self.timed_out)
                self.record['elapsed_ms'] = int((time.monotonic() - started) * 1000)
                self.save()
                # A late or failed write cannot turn a deadline breach into ready.
                if time.monotonic() >= self.deadline or self.io_failed:
                    self.record['blocked'] = True
                    self.reason('wait_timeout' if not self.io_failed else 'ledger_error')
                    self.save()
                if not self.record['blocked']:
                    try:
                        self.ledger.resolve(self.record, self.deadline)
                    except (OSError, ValueError):
                        self.io_failed = True
                        self.record['blocked'] = True
                        self.reason('ledger_error')
                        self.save()
                if time.monotonic() >= self.deadline:
                    self.record['blocked'] = True
                    self.reason('wait_timeout')
                    self.save()
                self.event()
            await asyncio.to_thread(persist)
        self.task = asyncio.create_task(finish())
        def consume(task):
            if task.cancelled() or task.exception() is not None:
                self.io_failed = True
                self.reason('ledger_error')
        self.task.add_done_callback(consume)

    async def join(self):
        # Repeated cancellation only cancels the waiter, never the owning task.
        while self.task and not self.task.done():
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                self.timed_out = True
                self.record['blocked'] = True
                self.reason('cleanup_in_progress')
                return False
            try:
                await asyncio.wait_for(asyncio.shield(self.task), remaining)
            except asyncio.CancelledError:
                continue
            except TimeoutError:
                self.timed_out = True
                self.record['blocked'] = True
                self.reason('cleanup_in_progress')
                return False
        if self.task:
            try:
                self.task.result()
            except (Exception, asyncio.CancelledError):
                self.io_failed = True
                self.reason('ledger_error')
                return False
        return bool(self.record and not self.record['blocked'] and not self.io_failed)

    def status(self):
        if self.io_failed and self.record is None:
            return {'blocked': True, 'cleanup_outcome': 'identity_unknown', 'reasons': ['ledger_error']}
        try:
            value = self.record or self.ledger.read()
            from_disk = self.record is None and value is not None
        except (OSError, ValueError):
            return {'blocked': True, 'cleanup_outcome': 'identity_unknown', 'reasons': ['ledger_error']}
        if value is None:
            return {'blocked': self.io_failed, 'cleanup_outcome': 'observed_empty', 'coverage': 'observed_only', 'reasons': []}
        result = {k: value[k] for k in ('trace', 'generation_outcome', 'cleanup_outcome', 'coverage', 'blocked', 'reasons', 'updated', 'elapsed_ms') if k in value}
        result['reasons'] = list(result['reasons'])
        result['owned_count'] = len(value['identities'])
        result['last_check'] = value.get('checked_at')
        if from_disk:
            result['blocked'] = True
        if self.task and not self.task.done():
            result.update(blocked=True, cleanup_outcome='identity_unknown', reasons=sorted(set(result['reasons']) | {'cleanup_in_progress'}))
        if self.io_failed or self.timed_out:
            result['blocked'] = True
        return result

    def event(self):
        value = dict(self.record)
        value['owned_count'] = len(value['identities'])
        LOG.info('CLI_CLEANUP trace=%s generation=%s outcome=%s coverage=%s reason=%s count=%d elapsed_ms=%d',
                 value['trace'], value['generation_outcome'], value['cleanup_outcome'], value['coverage'],
                 next(iter(sorted(value['reasons'])), 'none'), value.get('owned_count', 0), value.get('elapsed_ms', 0))

    async def check(self):
        # This phase intentionally has no kill or inference. observed_only can
        # diagnose exits but cannot unlock a failed request. No historical Job
        # label is a substitute for a currently held, verified containment handle.
        if self.task and not self.task.done() or self.io_failed:
            return self.status()
        if time.monotonic() - self.last_check < 5:
            return self.status()
        self.last_check = time.monotonic()
        if self.check_task and not self.check_task.done():
            return self.status()
        def passive():
            try:
                with configuration_lock(self.ledger.root):
                    inspect_ledger()
            except (OSError, ValueError):
                self.io_failed = True
        def inspect_ledger():
            try:
                value = self.ledger.read()
                if value is None:
                    return
                value['blocked'] = True
                # Another live owner may still be creating/cleaning this request.
                state, _ = inspect(value['owner'])
                if value['owner'] != identity(psutil.Process()) and state in ('alive', 'access_denied'):
                    self.record = value
                    return
                if time.time() - value.get('checked_at', 0) < 5:
                    self.record = value
                    return
                self.record = value
                self.record['checked_at'] = time.time()
                self.record['cleanup_outcome'] = self.sweep(time.monotonic() + 1.8, kill=False)
                self.record['blocked'] = True
                self.reason('observation_incomplete')
                self.save()
            except (OSError, ValueError):
                self.io_failed = True
        # A standalone `cleanup check` must also exit within the check bound.
        # asyncio.run joins default-executor threads on shutdown; a stuck OS
        # inspection there would make the supposedly bounded CLI wait forever.
        # This separately retained daemon only inspects/saves blocked metadata.
        completed = threading.Event()
        def passive_thread():
            try:passive()
            finally:completed.set()
        self.check_thread = threading.Thread(target=passive_thread, daemon=True)
        self.check_thread.start()
        async def completion():
            while not completed.is_set():await asyncio.sleep(.01)
        self.check_task = asyncio.create_task(completion())
        try:
            await asyncio.wait_for(asyncio.shield(self.check_task), 2)
        except TimeoutError:
            self.io_failed = True
        return self.status()
