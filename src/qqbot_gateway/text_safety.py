"""Reject serialized tool instructions emitted as plain text by a backend."""
import re


_TOOL_MARKUP = re.compile(
    r'<[^<>\n]{0,24}DSML[^<>\n]{0,24}>|'
    r'<\s*/?\s*(?:tool_call|tool_calls|function_calls|function_call)\b|'
    r'<\s*(?:invoke|function)\s+(?:name\s*=)|<\s*function\s*=',
    re.IGNORECASE,
)


def has_tool_markup(text):
    return bool(_TOOL_MARKUP.search(text))
