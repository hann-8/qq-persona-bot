"""One-way Markdown to chat text conversion. Never run on downstream text."""
from markdown_it import MarkdownIt

from .errors import GatewayError
from .text_safety import has_tool_markup


def _literal_star(state, silent):
    """Protect arithmetic/identifier stars and path globs before emphasis parsing."""
    pos = state.pos
    source = state.src
    if source[pos] != '*':
        return False
    before = source[pos - 1] if pos else ''
    after = source[pos + 1] if pos + 1 < state.posMax else ''
    identifier = lambda char: bool(char) and char.isascii() and (char.isalnum() or char == '_')
    literal = (identifier(before) and identifier(after)) or after in ('.', '/')
    if before == '*' or after == '*' or not literal:
        return False
    if not silent:
        state.pending += '*'
    state.pos += 1
    return True


def _inline(tokens):
    parts = []
    links = []
    for token in tokens or []:
        if token.type in ('text', 'code_inline', 'html_inline'):
            parts.append(token.content)
        elif token.type in ('softbreak', 'hardbreak'):
            parts.append('\n')
        elif token.type == 'image':
            parts.append(_inline(token.children) or token.content)
            parts.append('（' + (token.attrGet('src') or '') + '）')
        elif token.type == 'link_open':
            links.append((token.attrGet('href') or '', len(parts)))
        elif token.type == 'link_close' and links:
            url, start = links.pop()
            if url and ''.join(parts[start:]) != url:
                parts.append('（' + url + '）')
    return ''.join(parts)


def plain_chat(text):
    # Check before parsing: markup must never be laundered into a valid answer.
    if has_tool_markup(text):
        raise GatewayError('TOOL_ISOLATION_FAILED')
    parser = MarkdownIt('commonmark', {'html': False, 'linkify': False}).enable(['table', 'strikethrough'])
    parser.inline.ruler.before('emphasis', 'literal_star', _literal_star)
    tokens = parser.parse(text)
    blocks = []
    row = None
    headers = []
    in_header = False
    table_has_rows = False
    for token in tokens:
        if token.type == 'table_open':
            headers = []
            table_has_rows = False
        elif token.type == 'thead_open':
            in_header = True
        elif token.type == 'thead_close':
            in_header = False
        elif token.type == 'tr_open':
            row = []
        elif token.type == 'tr_close':
            if in_header:
                headers = row
            else:
                table_has_rows = True
                blocks.append('；'.join((headers[i] + '：' + cell) if i < len(headers) and headers[i]
                                       else cell for i, cell in enumerate(row)))
            row = None
        elif token.type == 'inline':
            value = _inline(token.children)
            if row is not None:
                row.append(value)
            else:
                blocks.append(value)
        elif token.type in ('fence', 'code_block'):
            blocks.append(token.content.rstrip('\n'))
        elif token.type == 'table_close' and headers and not table_has_rows:
            blocks.append('；'.join(headers))
    result = '\n'.join(blocks).strip('\n')
    if has_tool_markup(result):
        raise GatewayError('TOOL_ISOLATION_FAILED')
    if not result.strip():
        raise GatewayError('EMPTY_REPLY')
    return result


def prepare_reply(text, max_chars=1200):
    result = plain_chat(text)
    if len(result) <= max_chars:
        return result, False
    notice = '……（内容未展示完）'
    available = max_chars - len(notice)
    prefix = result[:available]
    # Prefer a nearby sentence/line boundary without discarding most of the reply.
    boundary = max((i + 1 for i, c in enumerate(prefix) if c in '\n。！？；.!?'), default=0)
    if boundary >= available // 2:
        prefix = prefix[:boundary]
    return prefix.rstrip() + notice, True
