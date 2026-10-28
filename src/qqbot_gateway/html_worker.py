"""One stdin document, one bounded JSON result; no URL fetching or subprocesses."""
from html.parser import HTMLParser
import json
import re
import sys
import time
from datetime import datetime

MAX_BYTES=1048576
FAILURES={
    'dependency':{'dependency_missing','internal_error'},
    'policy':{'entity_policy','internal_error'},
    'parse':{'parse_error','internal_error'},
    'body':{'empty_body','content_denied','internal_error'},
    'date':{'date_error','internal_error'},
    'serialize':{'output_limit','internal_error'},
}

class ExtractionFailure(Exception):
    def __init__(self,stage,reason):self.stage=stage;self.reason=reason


def phase(stage,reason,operation):
    try:return operation()
    except ExtractionFailure:raise
    except Exception:raise ExtractionFailure(stage,reason) from None



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
            if len(content.encode())>=20 and len(blocks)>=1 and density<.5:
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


def extract_dates(tree):
    rows=[]
    def add(kind,source,value):
        if isinstance(value,str) and len(value)<=80 and len(rows)<24:
            rows.append(dict(kind=kind,source=source,value=value))
    for kind in ('published','modified'):
        for value in tree.xpath('//meta[@property="article:'+kind+'_time"]/@content')[:8]:add(kind,'meta',value)
    count=0;nodes=0
    def walk(value,depth=0):
        nonlocal nodes
        nodes+=1
        if nodes>256 or depth>8:return
        if isinstance(value,list):
            for child in value:walk(child,depth+1)
        elif isinstance(value,dict):
            typ=value.get('@type',[]);typ=[typ] if isinstance(typ,str) else typ
            if isinstance(typ,list) and any(t in ('Article','NewsArticle','BlogPosting') for t in typ):
                # Only a unique article without an unrelated explicit URL is usable.
                canonical=tree.xpath('//link[@rel="canonical"]/@href')
                url=value.get('url')
                if url is None or canonical and url==canonical[0]:
                    add('published','jsonld',value.get('datePublished'))
                    add('modified','jsonld',value.get('dateModified'))
            for child in value.values():
                if isinstance(child,(dict,list)):walk(child,depth+1)
    for script in tree.xpath('//script[@type="application/ld+json"]')[:8]:
        text=script.text or '';count+=len(text.encode())
        if count>65536:break
        try:walk(json.loads(text))
        except (ValueError,RecursionError):continue
    if not any(r['kind']=='published' for r in rows):
        # A single article/main scope prevents recommendation dates being pooled.
        scopes=tree.xpath('//article') or tree.xpath('//main|//*[@role="main"]')
        if len(scopes)==1:
            for node in scopes[0].xpath('.//time[@datetime][not(ancestor::aside or ancestor::nav or ancestor::footer)]')[:8]:add('published','time',node.get('datetime'))
    return rows


def extract_html(text):
    def dependencies():
        from lxml import html
        from readability import Document
        return html,Document
    html,Document=phase('dependency','dependency_missing',dependencies)
    # External identifiers in ordinary XHTML declarations are inert with
    # no_network HTML parsing. Internal subsets/entities remain forbidden.
    if re.search(r'<!DOCTYPE[^>]*\[|<!ENTITY',text,re.I):raise ExtractionFailure('policy','entity_policy')
    parser=html.HTMLParser(no_network=True,recover=True,huge_tree=False)
    tree=phase('parse','parse_error',lambda:html.fromstring(text,parser=parser))
    dates=tree.xpath('//meta[@property="article:published_time" or @name="date" or @name="pubdate"]/@content')
    published=None
    for value in dates:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:T[0-9:+.Z-]{5,30})?',value):continue
        try:datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError:continue
        published=value;break
    date_candidates=phase('date','date_error',lambda:extract_dates(tree))
    description=' '.join((tree.xpath('//meta[@name="description" or @property="og:description"]/@content') or [''])[0].split())[:1000]
    for node in tree.xpath('//script|//style|//nav|//form|//iframe|//footer|//header[not(ancestor::main or ancestor::article or ancestor::section or ancestor::*[@role="main"])]|//aside|//noscript|//svg|//template|//object|//embed|//*[@hidden or @aria-hidden="true"]'):
        if node.getparent() is not None:node.drop_tree()
    for node in list(tree.iter()):
        style=node.get('style','').replace(' ','').lower()
        if ('display:none' in style or 'visibility:hidden' in style) and node.getparent() is not None:node.drop_tree()
    doc=phase('body','internal_error',lambda:Document(html.tostring(tree,encoding='unicode')))
    title=phase('body','internal_error',lambda:doc.short_title()[:120])
    body,method=phase('body','internal_error',lambda:semantic_body(tree))
    if body is None:
        body=phase('body','internal_error',lambda:html.fromstring(doc.summary(),parser=parser));method='readability'
    for node in body.xpath('//script|//style|//iframe|//form|//nav|//img|//object|//embed'):
        if node.getparent() is not None:node.drop_tree()
    content=phase('body','internal_error',lambda:body_text(body))
    if re.search(r'verify you are human|access denied|登录后阅读|付费阅读|人机验证',content,re.I):raise ExtractionFailure('body','content_denied')
    if len(content.encode())<20:
        if len(description.encode())>=80:
            return dict(title=title,text=description,published_at=published,date_candidates=date_candidates,body_method='metadata',body_scope='metadata')
        raise ExtractionFailure('body','empty_body')
    return dict(title=title,text=content,published_at=published,date_candidates=date_candidates,body_method=method,body_scope='extracted_main')


def main():
    started=time.monotonic()
    try:
        raw=sys.stdin.buffer.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ExtractionFailure('serialize','output_limit')
        text=phase('parse','parse_error',lambda:raw.decode('utf-8'))
        if len(sys.argv)>2 and sys.argv[2]=='legacy':
            parser=Extractor();parser.feed(text)
            body=' '.join(' '.join(parser.text).split())
            if len(body)<80:raise ExtractionFailure('body','empty_body')
            result=dict(title=' '.join(' '.join(parser.title).split())[:120],text=body,published_at=parser.published,date_candidates=[],body_method='legacy',body_scope='extracted_main')
        else:result=extract_html(text)
        result['elapsed_seconds']=time.monotonic()-started
        data=phase('serialize','internal_error',lambda:json.dumps(result,ensure_ascii=False,separators=(',',':')).encode())
        if len(data)>2*MAX_BYTES:raise ExtractionFailure('serialize','output_limit')
    except Exception as error:
        # Never include exception text or document content in the protocol.
        stage,reason=(error.stage,error.reason) if isinstance(error,ExtractionFailure) else ('body','internal_error')
        data=json.dumps(dict(error='extract_failed',stage=stage,reason=reason),separators=(',',':')).encode()
    sys.stdout.buffer.write(data)


if __name__=='__main__':
    # Set only by the parent from its own interpreter's sysconfig, never HTML.
    if len(sys.argv)>=2:sys.path.insert(0,sys.argv[1])
    main()
