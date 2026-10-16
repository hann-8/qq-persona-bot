import json
from .errors import GatewayError


def normalize_request(payload, char_limit=24000):
    fail = lambda: GatewayError('UNSUPPORTED_REQUEST')
    if not isinstance(payload, dict) or set(payload) - {'model', 'messages', 'stream'}:
        raise fail()
    if payload.get('model') != 'workbuddy-local' or payload.get('stream', False) is not False:
        raise fail()
    messages = payload.get('messages')
    if not isinstance(messages, list) or not 1 <= len(messages) <= 40:
        raise fail()
    normalized = []
    for message in messages:
        if not isinstance(message, dict) or set(message) != {'role', 'content'}:
            raise fail()
        role, content = message['role'], message['content']
        if role not in ('system', 'user', 'assistant'):
            raise fail()
        if isinstance(content, list):
            parts = []
            for part in content:
                if (not isinstance(part, dict) or set(part) != {'type', 'text'} or
                        part['type'] != 'text' or not isinstance(part['text'], str)):
                    raise fail()
                parts.append(part['text'])
            content = ''.join(parts)
        if not isinstance(content, str):
            raise fail()
        normalized.append({'role': role, 'content': content})
    seen_dialog = False
    systems, dialog = [], []
    for message in normalized:
        if message['role'] == 'system':
            if seen_dialog:
                raise fail()
            systems.append(message['content'])
        else:
            seen_dialog = True
            dialog.append(message)
    if not dialog or dialog[-1]['role'] != 'user' or not dialog[-1]['content'].strip():
        raise fail()
    system = '\n\n'.join(systems)
    prompt = json.dumps(dialog, ensure_ascii=False, separators=(',', ':'))
    if len(system) + len(prompt) > char_limit:
        raise fail()
    return system, prompt


def contract_shape(payload):
    return {'fields': {k: type(v).__name__ for k,v in payload.items()},
            'message_fields': [sorted(m) for m in payload.get('messages', []) if isinstance(m, dict)],
            'roles': [m.get('role') for m in payload.get('messages', []) if isinstance(m, dict)]}
