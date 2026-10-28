"""Deterministic six-zone paragraph excerpts, with original character ranges."""
import json
import re
from .public_http import WebFailure


def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')


STOP={'the','and','for','with','this','that','what','how','does','from','page','please','总结','概括','这页','网页','这个','如何','什么','请问','一下','介绍','search','latest','recent','news','today','current','stable','release','version','support','supports','official','status','currently','is','still','maintained','of','in','on','a','an','官方','新闻','版本','更新','支持','维护'}


def question_terms(question):
    # URL paths and hostnames are source identity, not target question terms.
    question=re.sub(r'https?://[^\s<>]+|(?i:site:)[a-zA-Z0-9.-]+|\d{4}-\d{2}-\d{2}',' ',question)
    question=re.sub(r'搜索|搜一下|最新|最近|近期|目前|现在|消息|动态|公告|过去24小时|今天|本周|(?:近|过去)\d+天',' ',question)
    question=re.sub(r'总结|概括|这页|网页|请看|请问|一下|(?i:please|summari[sz]e|summary|this page)',' ',question)
    result=[]
    for match in re.finditer(r'[A-Za-z0-9_]+(?:[.:-][A-Za-z0-9_]+)*|[\u4e00-\u9fff]+',question[:4096]):
        word=match.group().lower()
        words=[word[i:i+2] for i in range(len(word)-1)] if '\u4e00'<=word[0]<='\u9fff' else [word]
        for term in words:
            if term not in STOP and term not in result:result.append(term)
            if len(result)==32:return result
    return result


def term_hits(text,terms):
    text=text.lower()
    return sum(bool(re.search(r'(?<![A-Za-z0-9_.])'+re.escape(t)+r'(?![A-Za-z0-9_]|\.[A-Za-z0-9_])',text)) if t.isascii() else t in text for t in terms)


def question_rows(paragraphs,cap,terms):
    scores=[term_hits(row[2],terms) for row in paragraphs]
    ranked=sorted((i for i,s in enumerate(scores) if s),key=lambda i:(-scores[i],-int(len(paragraphs[i][2])<=160),i))
    if not ranked:raise WebFailure('evidence_insufficient')
    chosen=set();used=0;matched=0
    def add(indices,limit):
        nonlocal used
        indices=set(indices)-chosen
        cost=sum(len(paragraphs[i][2].encode()) for i in indices)+len(indices)
        if indices and len(chosen|indices)<=512 and used+cost<=limit:
            chosen.update(indices);used+=cost;return True
        return False
    # Allocate at least 60% to complete matching blocks and local context.
    # Reserve this partition before adding global coverage; no paragraph clipping.
    for i in ranked:
        heading=next((j for j in range(i-1,-1,-1) if len(paragraphs[j][2])<=160),None)
        for neighbor in (i+1,i-1):
            if not 0<=neighbor<len(paragraphs):continue
            group=[i,neighbor]+([heading] if heading is not None and heading>=i-2 else [])
            if add(group,int(cap*.7)):
                matched+=1;break
    if not matched:raise WebFailure('evidence_insufficient')
    # Fill the reserved relevant partition before the remaining position coverage.
    for i in ranked:
        if used>=int(cap*.6):break
        add([i,i+1 if i+1<len(paragraphs) else i-1],int(cap*.7))
    for anchor in (0,len(paragraphs)//2,len(paragraphs)-1):
        for i in sorted(range(len(paragraphs)),key=lambda j:abs(j-anchor)):
            if add([i],cap):break
    rows=[paragraphs[i] for i in sorted(chosen)]
    if len(rows)<2 or not any(b==a+1 for a,b in zip(sorted(chosen),sorted(chosen)[1:])):raise WebFailure('evidence_insufficient')
    return rows


def select(text,cap,policy='excerpt',complete=False,selection_policy='coverage',question=''):
    total=len(text.encode('utf-8'))
    if total<=cap:return dict(text=text,coverage='full',ranges=[[0,len(text)]],input_bytes=total,selected_bytes=total,truncated=False)
    if policy=='reject' or complete:raise WebFailure('evidence_full_required')
    paragraphs=[(m.start(),m.end(),m.group()) for m in re.finditer(r'[^\n]+',text) if m.group().strip()]
    if selection_policy=='gist':
        terms=question_terms(question)
        ranked=sorted(range(len(paragraphs)),key=lambda i:(-term_hits(paragraphs[i][2],terms),i))
        chosen=set();used=0
        for i in [0]+ranked:
            for j in (i,i+1):
                if j>=len(paragraphs) or j in chosen:continue
                size=len(paragraphs[j][2].encode())+(1 if chosen else 0)
                if used+size<=cap:chosen.add(j);used+=size
            if len(chosen)>=32:break
        if not chosen:raise WebFailure('evidence_insufficient')
        rows=[paragraphs[i] for i in sorted(chosen)]
        body='\n'.join(row[2] for row in rows)
        if len(body.encode())<20:raise WebFailure('evidence_insufficient')
        return dict(text=body,coverage='excerpt',ranges=[[r[0],r[1]] for r in rows],input_bytes=total,selected_bytes=len(body.encode()),truncated=True)
    terms=question_terms(question) if selection_policy=='question' else []
    relevant=question_rows(paragraphs,cap,terms) if terms else None
    if relevant:
        body='\n'.join(row[2] for row in relevant);size=len(body.encode('utf-8'))
        if size<1200:raise WebFailure('evidence_insufficient')
        return dict(text=body,coverage='excerpt',ranges=[[row[0],row[1]] for row in relevant],input_bytes=total,selected_bytes=size,truncated=True)
    count=min(6,len(paragraphs));chosen=[];zones=0
    if not count:raise WebFailure('evidence_insufficient')
    # Even paragraph-position zones; each window is contiguous and whole.
    # A few long paragraphs cannot be represented honestly: reject, do not clip.
    for zone in range(count):
        rows=paragraphs[zone*len(paragraphs)//count:(zone+1)*len(paragraphs)//count]
        allowance=max(0,(cap-(count-1))//count);window=[];used=0
        for row in (reversed(rows) if zone==count-1 else rows):
            size=len(row[2].encode('utf-8'))+(1 if window else 0)
            if used+size>allowance:break
            window.append(row);used+=size
        if window:zones+=1;chosen.extend(window)
    chosen.sort();body='\n'.join(row[2] for row in chosen);size=len(body.encode('utf-8'))
    if zones<min(4,count) or size<1200:raise WebFailure('evidence_insufficient')
    return dict(text=body,coverage='excerpt',ranges=[[row[0],row[1]] for row in chosen],
                input_bytes=total,selected_bytes=size,truncated=True)


def sources_for_budget(sources,cap,page_cap,policy,question,selection_policy='coverage'):
    complete=bool(re.search(r'完整|逐项|逐条|不能遗漏|不得省略|不许省略|不遗漏|in full|complete|without omissions',question,re.I))
    prepared=[]
    for source in sources:
        if source.get('status')=='subtitle':
            from .bilibili_subtitles import select_source
            text_cap=cap
            while text_cap>=80:
                row=select_source(source,text_cap,policy,complete)
                if len(encoded(dict(partial=False,sources=[row])))<=cap:return [row]
                text_cap-=100
            raise WebFailure('evidence_insufficient')
        row={k:v for k,v in source.items() if not k.startswith('_')}
        body=source.get('_full_text',source['text'])
        try:
            identity=validate_material(source['material']) if 'material' in source else material() if source.get('status')=='body' else None
            if identity is None:raise ValueError('material missing')
        except (ValueError,TypeError,KeyError):raise WebFailure('material_identity') from None
        kind=identity['kind']
        if complete and kind!='page_excerpt':raise WebFailure('evidence_full_required')
        row.update(select(body,min(page_cap,cap),policy,complete,selection_policy,question))
        row['material']=material(kind,'metadata' if kind=='link_metadata' else 'summary' if kind=='search_snippet' else 'excerpt' if row['coverage']=='excerpt' else 'main',identity['reported_at'])
        prepared.append((row,body))
    # All fields, ranges, titles, source URLs and timestamps share one cap.
    text_cap=min(page_cap,cap)
    while text_cap>=80:
        rows=[]
        try:
            for original,body in prepared:
                row=dict(original);row.update(select(body,text_cap,policy,complete,selection_policy,question))
                row['material']=dict(row['material'])
                if row['material']['kind']=='page_excerpt':row['material']['scope']='excerpt' if row['coverage']=='excerpt' else 'main'
                rows.append(row)
        except WebFailure:
            raise
        if len(encoded(dict(partial=False,sources=rows)))<=cap:return rows
        text_cap-=100
    raise WebFailure('evidence_insufficient')


def manifest(sources):
    import hashlib
    result=[]
    for row in sources:
        item=dict(url=row['url'],coverage=row['coverage'],ranges=row['ranges'],input_bytes=row['input_bytes'],
                  selected_bytes=row['selected_bytes'],sha256=hashlib.sha256(row['text'].encode()).hexdigest())
        if row.get('material'):
            import hashlib
            item['material']=validate_material(row['material'])
            item['material_sha256']=hashlib.sha256(encoded(item['material'])).hexdigest()
        if row.get('time_policy'):
            if row['time_policy'] not in TIME_POLICIES:raise ValueError('time policy')
            item['time_policy']=row['time_policy']
        if row.get('freshness'):
            from .web_freshness import validate_facts
            item['freshness']=validate_facts(row['freshness'])
            item['freshness_sha256']=hashlib.sha256(encoded(item['freshness'])).hexdigest()
        if row.get('status')=='subtitle':
            item['subtitle']={k:row[k] for k in ('bvid','cid','page','language','subtitle_type','duration','time_ranges','time_gaps','time_coverage')}
        result.append(item)
    return result


def validate_manifest(rows,source):
    from .public_network import page_url
    if not source.get('web_anchor') or not isinstance(rows,list) or not 1<=len(rows)<=2:raise ValueError('web manifest')
    for row in rows:
        if not isinstance(row,dict) or set(row)-{'subtitle','freshness','freshness_sha256','material','material_sha256','time_policy'}!={'url','coverage','ranges','input_bytes','selected_bytes','sha256'}:raise ValueError('web fields')
        if 'time_policy' in row and (not isinstance(row['time_policy'],str) or row['time_policy'] not in TIME_POLICIES):raise ValueError('time policy')
        if ('material' in row)!=('material_sha256' in row):raise ValueError('material pairing')
        if 'material' in row:
            import hashlib
            validate_material(row['material'])
            if row['material_sha256']!=hashlib.sha256(encoded(row['material'])).hexdigest():raise ValueError('material hash')
            scope=row['material']['scope']
            if row['material']['kind']=='page_excerpt' and scope!=('main' if row['coverage']=='full' else 'excerpt'):raise ValueError('material scope')
        if ('freshness' in row)!=('freshness_sha256' in row):raise ValueError('web freshness pairing')
        if 'freshness' in row:
            import hashlib
            from .web_freshness import validate_facts
            validate_facts(row['freshness'])
            if row['freshness_sha256']!=hashlib.sha256(encoded(row['freshness'])).hexdigest():raise ValueError('web freshness hash')
        if not isinstance(row['url'],str):raise ValueError('web url')
        try:
            if '/video/' in row['url'] and row['url'].startswith('https://www.bilibili.com/'):
                if 'subtitle' not in row:raise ValueError('subtitle proof missing')
                from .bilibili_policy import locator
                locator(row['url'])
            else:page_url(row['url'])
        except WebFailure:raise ValueError('web url') from None
        if (row['coverage'] not in ('full','excerpt') or not isinstance(row['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',row['sha256']) or
            type(row['input_bytes']) is not int or not (20 if 'material' in row and row['material']['kind']=='page_excerpt' else 80)<=row['input_bytes']<=4194304 or
            type(row['selected_bytes']) is not int or not (20 if 'material' in row and row['material']['kind']=='page_excerpt' else 80)<=row['selected_bytes']<=min(6000,row['input_bytes'])):raise ValueError('web bounds')
        ranges=row['ranges'];previous=-1
        if not isinstance(ranges,list) or not 1<=len(ranges)<=512:raise ValueError('web ranges')
        for pair in ranges:
            if not isinstance(pair,list) or len(pair)!=2 or any(type(x) is not int for x in pair) or not previous<pair[0]<pair[1]<=row['input_bytes']:raise ValueError('web range')
            previous=pair[1]
        if row['coverage']=='full' and (len(ranges)!=1 or row['selected_bytes']!=row['input_bytes']):raise ValueError('web full')
        if row['coverage']=='excerpt' and (row['selected_bytes']<(20 if 'material' in row and row['material']['kind']=='page_excerpt' else 80 if 'material' in row else 1200) or row['selected_bytes']>=row['input_bytes']):raise ValueError('web excerpt')
        if 'subtitle' in row:
            from .bilibili_policy import locator,BV
            import math
            sub=row['subtitle']
            fields={'bvid','cid','page','language','subtitle_type','duration','time_ranges','time_gaps','time_coverage'}
            if not isinstance(sub,dict) or set(sub)!=fields:raise ValueError('subtitle fields')
            if (not isinstance(sub['bvid'],str) or not re.fullmatch(BV,sub['bvid']) or
                type(sub['cid']) is not int or not 1<=sub['cid']<2**63 or
                type(sub['page']) is not int or not 1<=sub['page']<=1000 or
                type(sub['duration']) is not int or not 1<=sub['duration']<=1200 or
                not isinstance(sub['language'],str) or not re.fullmatch(r'[A-Za-z0-9-]{1,32}',sub['language']) or
                sub['subtitle_type'] not in ('manual','automatic') or
                type(sub['time_coverage']) not in (int,float) or not math.isfinite(sub['time_coverage'])):raise ValueError('subtitle bounds')
            canonical='https://www.bilibili.com/video/'+sub['bvid']+(f'?p={sub["page"]}' if sub['page']!=1 else '')
            if row['url']!=canonical:raise ValueError('subtitle identity')
            intervals=sub['time_ranges'];last=0;gaps=[];covered=0
            if not isinstance(intervals,list) or not 1<=len(intervals)<=10000:raise ValueError('subtitle ranges')
            for pair in intervals:
                if (not isinstance(pair,list) or len(pair)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in pair)
                    or not last<=pair[0]<pair[1]<=sub['duration']):raise ValueError('subtitle times')
                if pair[0]>last:gaps.append([last,pair[0]])
                covered+=pair[1]-pair[0];last=pair[1]
            if last<sub['duration']:gaps.append([last,sub['duration']])
            if sub['time_gaps']!=gaps or sub['time_coverage']!=round(covered/sub['duration'],6):raise ValueError('subtitle coverage')


TIME_POLICIES={'none','recent_hint','current_status','strict_window'}

def material(kind='page_excerpt',scope='main',reported_at=None):
    return validate_material(dict(kind=kind,scope=scope,reported_at=reported_at,reported_date_source='rss_item' if reported_at else 'none'))


def validate_material(row):
    if not isinstance(row,dict) or set(row)!={'kind','scope','reported_at','reported_date_source'}:raise ValueError('material fields')
    scopes={'page_excerpt':{'main','excerpt'},'search_snippet':{'summary'},'link_metadata':{'metadata'}}
    if not isinstance(row['kind'],str) or row['kind'] not in scopes or not isinstance(row['scope'],str) or row['scope'] not in scopes[row['kind']]:raise ValueError('material identity')
    from .web_freshness import parse
    if row['reported_at'] is not None and parse(row['reported_at'])[0] is None:raise ValueError('material reported date')
    if row['reported_date_source']!=('rss_item' if row['reported_at'] else 'none'):raise ValueError('material date source')
    if row['kind']!='search_snippet' and row['reported_at'] is not None:raise ValueError('material date identity')
    return row
