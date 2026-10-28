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


def body_text(body):
    """Render content blocks in DOM order, preserving pre and table structure."""
    chunks=[]
    blocks={'p','div','section','article','main','header','h1','h2','h3','h4','h5','h6','li','dt','dd','pre','tr','blockquote'}
    def walk(node,pre=False):
        tag=node.tag
        if not isinstance(tag,str):return
        if tag in blocks:chunks.append('\n')
        if tag in ('h2','h3','h4','h5','h6'):chunks.append('  '*(int(tag[1])-1))
        if tag=='br':chunks.append('\n')
        if tag in ('td','th') and chunks and not chunks[-1].endswith('\n'):chunks.append(' | ')
        pre=pre or tag=='pre'
        if node.text:chunks.append(node.text if pre else re.sub(r'\s+',' ',node.text))
        for child in node:
            walk(child,pre)
            if child.tail:chunks.append(child.tail if pre else re.sub(r'\s+',' ',child.tail))
        if tag in blocks:chunks.append('\n')
    walk(body)
    return '\n'.join(line.rstrip() for line in ''.join(chunks).splitlines() if line.strip())


def semantic_body(tree):
    # Prefer explicit document containers. Drop contained roots, never stitch
    # parallel articles or duplicate nested article/main trees together.
    for expression,method in (('//main|//*[@role="main"]','semantic_main'),('//article','semantic_article')):
        candidates=tree.xpath(expression);roots=[];seen=set()
        for node in candidates:
            if any(parent in candidates for parent in node.iterancestors()):continue
            content=body_text(node)
            size=len(content.strip())
            blocks=node.xpath('.//p|.//pre|.//li|.//tr|.//dt|.//dd|.//h1|.//h2|.//h3|.//h4')
            blocks=[x for x in blocks if x.text_content().strip()]
            links=sum(len(' '.join(x.text_content().split())) for x in node.xpath('.//a'))
            density=min(1,links/max(1,size))
            if size>=80 and len(blocks)>=2 and density<.5:
                if content in seen:continue
                seen.add(content)
                score=size*(1-density)+min(len(blocks),100)*20
                roots.append((score,node))
        if roots:
            # DOM order resolves equal scores; near ties are ambiguous.
            roots.sort(key=lambda x:x[0],reverse=True)
            if len(roots)>1 and roots[1][0]>=roots[0][0]*.95:return None,None
            return roots[0][1],method
    return None,None


def extract_html(text):
    from lxml import html
    from readability import Document
    if re.search(r'<!DOCTYPE[^>]*\[|<!ENTITY|<!DOCTYPE[^>]+(?:SYSTEM|PUBLIC)',text,re.I):raise ValueError('html_entities')
    parser=html.HTMLParser(no_network=True,recover=True,huge_tree=False)
    tree=html.fromstring(text,parser=parser)
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).parent))
    from web_freshness import page_dates
    mains=tree.xpath('//main|//article|//*[@role="main"]')
    date_info=page_dates(tree,mains[0] if mains else None)
    for node in tree.xpath('//script|//style|//nav|//form|//iframe|//footer|//header[not(ancestor::main or ancestor::article or ancestor::section or ancestor::*[@role="main"])]|//aside|//noscript|//svg|//template|//object|//embed|//*[@hidden or @aria-hidden="true"]'):
        if node.getparent() is not None:node.drop_tree()
    for node in list(tree.iter()):
        style=node.get('style','').replace(' ','').lower()
        if ('display:none' in style or 'visibility:hidden' in style) and node.getparent() is not None:node.drop_tree()
    doc=Document(html.tostring(tree,encoding='unicode'))
    title=doc.short_title()[:120]
    body,method=semantic_body(tree)
    if body is None:
        body=html.fromstring(doc.summary(),parser=parser);method='readability'
    for node in body.xpath('//script|//style|//iframe|//form|//nav|//img|//object|//embed'):
        if node.getparent() is not None:node.drop_tree()
    content=body_text(body)
    if len(content)<80 or re.search(r'verify you are human|access denied|登录后阅读|付费阅读|人机验证',content,re.I):raise ValueError('empty_shell')
    return dict(title=title,text=content,body_method=method,body_scope='extracted_main',**date_info)


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
            from pathlib import Path
            sys.path.insert(0,str(Path(__file__).parent))
            from web_freshness import parse_date
            result=dict(title=' '.join(' '.join(parser.title).split())[:120],text=body,published_at=parser.published if parse_date(parser.published)[0] else None,
                modified_at=None,date_source='legacy',date_conflict=False,body_method='legacy',body_scope='extracted_main')
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
