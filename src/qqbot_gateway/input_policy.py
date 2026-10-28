"""Current-event facts supplied by the gate, never inferred from placeholders."""
SUPPORTED = {'text', 'at', 'reply', 'image'}


def facts(segments):
    text = ''.join(s.get('data', {}).get('text', '') for s in segments
                   if s.get('type') == 'text' and isinstance(s.get('data', {}).get('text'), str))
    kinds = sorted({s.get('type') for s in segments if s.get('type') not in ('text', 'at', 'reply')})
    return dict(text=text, has_direct_text=bool(text.strip()), media_types=[k if k in
                ('image', 'record', 'video', 'file', 'forward') else 'unknown' for k in kinds])


def notice(kinds, image_available, has_text):
    unsupported = set(kinds) - {'image'}
    if unsupported:
        names = {'record': '语音', 'video': '视频', 'file': '文件', 'forward': '转发', 'unknown': '这类媒体'}
        return '本条' + '、'.join(names.get(k, '这类媒体') for k in sorted(unsupported)) + '暂不能读取，请贴出需要讨论的文字。'
    if 'image' in kinds and not image_available:
        return '这张图片暂时无法读取，请重新发图或贴出需要讨论的文字。'
    if not has_text and not image_available:
        return '我在～'
    return None
