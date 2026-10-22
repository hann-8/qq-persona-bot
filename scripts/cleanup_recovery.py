"""Explicit, stopped-bot maintenance; never kill, infer, or replay a request.

This archives an observed-only ledger by operator choice, as in LAP-33.
It does not establish Job containment or the exit of unobserved descendants.
"""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import uuid

from qqbot_gateway.cleanup_identity import CleanupLedger, CleanupOwner, inspect
from qqbot_gateway.config import configuration_lock
from qqbot_gateway.config_files import exists, plain_path, safe_mkdir
from scripts import manage

PORTS = (6185, 6199, 6200, 6099, 8765)


def require_stopped(entries, record, port_open):
    identities = list(entries)
    if record is not None:
        identities += [record['owner'], *record['identities']]
    # Ambiguous/reused identities are left for a human; never touch replacements.
    if any(inspect(entry)[0] != 'exited' for entry in identities):
        raise ValueError('清理恢复已拒绝：仍有存活或无法确认退出的登记身份。请先关闭本项目bot。')
    if any(port_open(port) for port in PORTS):
        raise ValueError('清理恢复已拒绝：项目端口仍被占用。请先关闭本项目bot。')


def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def recover(root, *, read_state=None, port_open=None):
    root = Path(root).resolve()
    read_state = read_state or manage.read_state
    port_open = port_open or manage.port_open
    with configuration_lock(root):
        ledger = CleanupLedger(root)
        if exists(ledger.directory):
            plain_path(root, ledger.directory, directory=True)
        if exists(ledger.path):
            plain_path(root, ledger.path)
        value = ledger.read()  # Strict schema/size; corrupt evidence is not cleared.
        entries = read_state()
        require_stopped(entries, value, port_open)
        if value is None:
            return dict(state='not_needed', blocked=False, coverage='observed_only')
        original = ledger.path.read_bytes()
        if json.loads(original.decode('utf-8')) != value:
            raise ValueError('清理记录已变化，未执行恢复。')
        digest = hashlib.sha256(original).hexdigest()
        archive = root / 'state/cli-cleanup-manual-archive' / (
            'LAP-37-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:10])
        safe_mkdir(root, archive)
        write_new(archive / 'unresolved.backup.json', original)
        note = dict(schema_version=1, action='explicit_manual_archive', trace=value['trace'],
                    sha256=digest, coverage='observed_only', complete_descendant_exit_proven=False,
                    identities=len(value['identities']), ports_closed=list(PORTS),
                    reason='Operator requested stopped-bot recovery; all registered identities exited. '
                           'No kill, model call, request replay, or change to history/ACK/unknown.')
        write_new(archive / 'manual-recovery.json', json.dumps(note, indent=2).encode('utf-8'))
        # Recheck immediately before the sole mutation of the active ledger.
        require_stopped(read_state(), value, port_open)
        if ledger.path.read_bytes() != original or (archive / 'unresolved.backup.json').read_bytes() != original:
            raise ValueError('清理记录或备份已变化，未执行恢复。')
        ledger.path.rename(archive / 'unresolved.archived.json')
        report = CleanupOwner(root).status()
        if report['blocked']:
            raise ValueError('归档已保存，但独立状态仍阻断，请检查新的清理记录。')
        return dict(state='recovered', blocked=False, coverage='observed_only',
                    complete_descendant_exit_proven=False, archive=str(archive.relative_to(root)))
