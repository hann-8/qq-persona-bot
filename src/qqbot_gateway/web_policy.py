"""Deterministic current-turn policy; never send conversation history to search."""
from dataclasses import dataclass
import re
from urllib.parse import urlsplit

DEFAULTS = dict(enabled=False, trigger='auto', provider='bing_rss', max_searches=1,
                max_results=5, max_pages=2, timeout_seconds=15, max_redirects=2,
                max_response_bytes=1048576, max_page_text_bytes=4000,
                max_evidence_bytes=6000, max_sources=2, extractor='readability', long_text_policy='excerpt', selection_policy='coverage')
# Candidate has not passed the public quality gate. This is code-owned, not config.
SEARCH_QUALITY_PASSED = False
URL = re.compile(r'https?://[^\s<>"\u3000，。！？；、（）]+', re.I)
VIDEO = re.compile(r'(^|\.)(bilibili\.com|b23\.tv|youtube\.com|youtu\.be|douyin\.com)$', re.I)


def validate_web(raw):
    if not isinstance(raw, dict):raise ValueError('web must be a mapping')
    cfg = DEFAULTS | raw
    if cfg['selection_policy'] not in ('coverage','question'):raise ValueError('Invalid web.selection_policy')
    if cfg['extractor'] not in ('readability','legacy') or cfg['long_text_policy'] not in ('excerpt','reject'):raise ValueError('Invalid web extraction policy')
    if type(cfg['enabled']) is not bool or cfg['trigger'] not in ('auto','explicit') or cfg['provider'] != 'bing_rss':
        raise ValueError('Invalid web mode/provider')
    for key, lo, hi in [('max_searches',1,1),('max_results',1,5),('max_pages',1,2),
                        ('timeout_seconds',5,15),('max_redirects',0,2),
                        ('max_response_bytes',65536,1048576),('max_page_text_bytes',1000,8000),
                        ('max_evidence_bytes',1000,12000),('max_sources',1,2)]:
        if type(cfg[key]) is not int or not lo <= cfg[key] <= hi:raise ValueError('Invalid web.'+key)
    return cfg


@dataclass(frozen=True)
class Intent:
    kind: str = 'none'
    query: str = ''
    urls: tuple = ()


def intent(question, cfg, private_ids=()):
    if re.search(r'不要联网|别联网|不联网|禁止联网|只根据这段文字|只凭记忆',question):return Intent()
    from .bilibili_policy import LINK, BARE
    if LINK.search(question) or BARE.search(question):return Intent('video')
    urls=tuple(dict.fromkeys(x.rstrip('。，；！？、）)]') for x in URL.findall(question)))
    if urls:
        if not cfg['enabled']:return Intent('disabled')
        try:
            if any(VIDEO.search(urlsplit(x).hostname or '') for x in urls):return Intent('video')
        except ValueError:return Intent('blocked')
        return Intent('read',urls=urls[:cfg['max_pages']])
    if not cfg['enabled']:return Intent()
    explicit=bool(re.search(r'搜索|搜一下|联网查|帮我查|查一下',question))
    temporal=bool(re.search(r'现在|今天|最新|最近|目前|当日',question) and re.search(r'新闻|版本|价格|天气|赛程|在任|发布|汇率|股价',question))
    if not explicit and not (cfg['trigger']=='auto' and temporal):return Intent()
    if re.search(r'记不记得|口令|我的代码|这段代码|陪我|开心',question):return Intent()
    if re.search(r'刚才|那个|上述|上面|这个',question):return Intent('clarify')
    # Reject instead of guessing how to redact sensitive or oversized text.
    if (len(question)>240 or re.search(r'\d{5,}|QQ|群号|密码|口令|token|secret|api.?key|[A-Za-z]:[\\/]|\\\\|@[\w]+|[\w.+-]+@[\w.-]+',question,re.I)
            or any(str(x) in question for x in private_ids if str(x))):return Intent('sensitive')
    return Intent('search',query=question.strip())
