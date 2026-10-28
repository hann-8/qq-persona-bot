"""Code-owned native web policy. No network implementation or configurable tool names."""
import re
from urllib.parse import urlsplit
import ipaddress

TOOLS = ('WebSearch', 'WebFetch')
TOTAL_RESULT_BYTES = 12000


def allowed_tools(web):
    if web.get('engine') != 'codebuddy_cli' or not web.get('enabled'):return ()
    return TOOLS if web.get('search_enabled') else ('WebFetch',)


def public_url(value):
    try:
        u=urlsplit(value);host=(u.hostname or '').lower().rstrip('.')
        if u.scheme not in ('http','https') or not host or u.username or u.password:return False
        if u.port not in (None,80,443):return False
        if host in ('localhost','metadata.google.internal') or host.endswith(('.localhost','.local','.internal','.lan')):return False
        try:return ipaddress.ip_address(host).is_global
        except ValueError:return '.' in host and not re.fullmatch(r'[\d.]+',host)
    except (ValueError,TypeError):return False


def source_urls(text):
    return tuple(dict.fromkeys(u.rstrip('。，；！？、)]}') for u in re.findall(r'https?://[^\s<>"\u3000]+',text)
                              if public_url(u.rstrip('。，；！？、)]}'))))


def native_contract(web, private_ids, budget, question=''):
    tools=allowed_tools(web)
    if re.search(r'不要联网|别联网|不联网|禁止联网|只根据这段文字|只凭记忆',question):tools=()
    return dict(allowed_tools=list(tools),max_calls=web['cli_max_tool_calls'],max_turns=web['cli_max_turns'],
                result_bytes=web['cli_tool_result_bytes'],total_result_bytes=TOTAL_RESULT_BYTES,
                private_ids=[str(x) for x in private_ids if str(x)],visible_limit=budget.limit,overhead=budget.overhead,
                # Locked Zod parameter source + JSON schema field/escaping overhead.
                # Dynamic descriptions are separately measured by tool.describe.
                schema_bytes_per_tool=4096)


from contextvars import ContextVar
SCOPE=ContextVar('native_web_scope',default=(True,''))
PROOF_FILES=('scripts/revalidate_lap43_native_web.py','tests/test_cli_native_web.py',
             'tests/test_lap43.py','tests/test_vision_mod_guard.py','reports/lap-42-vision-closure-sources.json')
