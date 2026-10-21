"""One stdin document, one bounded JSON result; no URL fetching or subprocesses."""
from html.parser import HTMLParser
import json
import re
import sys
import time
from datetime import datetime

MAX_BYTES=1048576


class Extractor(HTMLParser):
    SKIP={'script','style','nav','footer','header','form','aside','noscript','svg','template','iframe','object','embed'}
    def __init__(self):
        super().__init__(convert_charrefs=True);self.skip=[];self.title=[];self.text=[];self.in_title=False;self.published=None
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if self.skip:
            if tag in self.SKIP:self.skip.append(tag)
            return
        if tag in self.SKIP:self.skip.append(tag);return
        if tag=='title':self.in_title=True
        if tag=='meta' and (attrs.get('property')=='article:published_time' or attrs.get('name') in ('date','pubdate')):
            self.published=attrs.get('content','')[:80] or None
    def handle_endtag(self,tag):
        if self.skip:
            if tag==self.skip[-1]:self.skip.pop()
            return
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.skip:return
        (self.title if self.in_title else self.text).append(data)


def extract_html(text):
    from lxml import html
    from readability import Document
    if re.search(r'<!DOCTYPE[^>]*\[|<!ENTITY|<!DOCTYPE[^>]+(?:SYSTEM|PUBLIC)',text,re.I):raise ValueError('html_entities')
    parser=html.HTMLParser(no_network=True,recover=True,huge_tree=False)
    tree=html.fromstring(text,parser=parser)
    dates=tree.xpath('//meta[@property="article:published_time" or @name="date" or @name="pubdate"]/@content')
    published=None
    for value in dates:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T[0-9:+.Z-]{5,30})?',value):continue
        try:datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:continue
        published=value;break
    for node in tree.xpath('//script|//style|//nav|//form|//iframe|//footer|//header|//aside|//noscript|//svg|//template|//object|//embed|//*[@hidden or @aria-hidden="true"]'):
        if node.getparent() is not None:node.drop_tree()
    for node in list(tree.iter()):
        style=node.get('style','').replace(' ','').lower()
        if ('display:none' in style or 'visibility:hidden' in style) and node.getparent() is not None:node.drop_tree()
    doc=Document(html.tostring(tree,encoding='unicode'))
    title=doc.short_title()[:120]
    body=html.fromstring(doc.summary(),parser=parser)
    for node in body.xpath('//script|//style|//iframe|//form|//nav|//img|//object|//embed'):
        if node.getparent() is not None:node.drop_tree()
    # Block boundaries preserve paragraph/heading/list/code order, no rendering.
    for node in body.iter():
        if node.tag in ('p','div','section','article','main','h1','h2','h3','h4','li','pre','br','tr'):
            node.tail='\n'+(node.tail or '')
    paragraphs=[' '.join(x.split()) for x in body.text_content().splitlines()]
    content='\n'.join(x for x in paragraphs if x)
    if len(content)<80 or re.search(r'verify you are human|access denied|登录后阅读|付费阅读|人机验证',content,re.I):raise ValueError('empty_shell')
    return dict(title=title,text=content,published_at=published)


def main():
    started=time.monotonic()
    try:
        raw=sys.stdin.buffer.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ValueError('extract_input_limit')
        text=raw.decode('utf-8')
        if len(sys.argv)>2 and sys.argv[2]=='legacy':
            parser=Extractor();parser.feed(text)
            body=' '.join(' '.join(parser.text).split())
            if len(body)<80:raise ValueError('empty_shell')
            result=dict(title=' '.join(' '.join(parser.title).split())[:120],text=body,published_at=parser.published)
        else:result=extract_html(text)
        result['elapsed_seconds']=time.monotonic()-started
        data=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
        if len(data)>2*MAX_BYTES:raise ValueError('extract_output_limit')
    except Exception:
        # Parser exceptions may contain document contents: never return them.
        data=b'{"error":"extract_failed"}'
    sys.stdout.buffer.write(data)


if __name__=='__main__':
    # Set only by the parent from its own interpreter's sysconfig, never HTML.
    if len(sys.argv)>=2:sys.path.insert(0,sys.argv[1])
    main()
