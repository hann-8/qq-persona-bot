from .errors import GatewayError


def normalize_request(payload, char_limit=None, budget=None):
    from .token_budget import InputBudget, dialog_text
    budget = budget or InputBudget()
    fail = lambda: GatewayError('UNSUPPORTED_REQUEST')
    if not isinstance(payload, dict) or set(payload) - {'model', 'messages', 'stream','qqbot_request'}:
        raise fail()
    if 'qqbot_request' in payload:
        from .group_protocol import validate_request
        request=payload['qqbot_request']
        if isinstance(request,dict) and request.get('kind')=='media_turn':
            if set(request)!={'version','kind'} or type(request['version']) is not int or request['version']!=1:raise fail()
        else:validate_request(request)
    if payload.get('model') != 'workbuddy-local' or payload.get('stream', False) is not False:
        raise fail()
    messages = payload.get('messages')
    if not isinstance(messages, list) or not 1 <= len(messages) <= 2*budget.history_turns:
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
    if any(m['role'] != ('user' if index%2 == 0 else 'assistant') for index,m in enumerate(dialog)):
        raise fail()
    prompt = dialog_text(dialog)
    if 'qqbot_request' in payload and payload['qqbot_request'].get('kind')=='group_turn':
        from .reply_plan import digest
        if len(dialog)!=1 or payload['qqbot_request']['snapshot_digest']!=digest(dialog[0]['content']):raise fail()
        from .group_protocol import validate_snapshot
        validate_snapshot(dialog[0]['content'],payload['qqbot_request'])
    if char_limit is not None and len(system) + len(prompt) > char_limit:
        raise fail()
    budget.check(system, prompt)
    return system, prompt


def contract_shape(payload):
    return {'fields': {k: type(v).__name__ for k,v in payload.items()},
            'message_fields': [sorted(m) for m in payload.get('messages', []) if isinstance(m, dict)],
            'roles': [m.get('role') for m in payload.get('messages', []) if isinstance(m, dict)]}
