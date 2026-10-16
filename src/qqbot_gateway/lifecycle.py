"""Instance-bound admission pause; files alone never identify a process to kill."""
import json
import os
from pathlib import Path
import uuid


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def stopping(root, instance_id=None):
    instance_id = instance_id if instance_id is not None else os.environ.get('QQBOT_INSTANCE_ID')
    if not instance_id:
        return False  # Legacy processes do not pretend to support the new pause protocol.
    try:
        value = json.loads((Path(root) / 'state/stop-request.json').read_text(encoding='utf-8'))
        if not isinstance(value, dict):return True
        return value.get('instance_id') == instance_id
    except FileNotFoundError:
        return False
    except (OSError, ValueError, TypeError):
        return True  # A corrupt current stop marker must not open admission.
