"""Deterministic six-zone paragraph excerpts, with original character ranges."""
import json
import re
from .public_http import WebFailure


def encoded(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')


def select(text,cap,policy='excerpt',complete=False):
    total=len(text.encode('utf-8'))
    if total<=cap:return dict(text=text,coverage='full',ranges=[[0,len(text)]],input_bytes=total,selected_bytes=total,truncated=False)
    if policy=='reject' or complete:raise WebFailure('evidence_full_required')
    paragraphs=[(m.start(),m.end(),m.group()) for m in re.finditer(r'[^\n]+',text) if m.group().strip()]
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


def sources_for_budget(sources,cap,page_cap,policy,question):
    complete=bool(re.search(r'完整|逐项|不得省略|不许省略|不遗漏|in full|complete|without omissions',question,re.I))
    prepared=[]
    for source in sources:
        row={k:v for k,v in source.items() if not k.startswith('_')}
        body=source.get('_full_text',source['text'])
        row.update(select(body,min(page_cap,cap),policy,complete));prepared.append((row,body))
    # All fields, ranges, titles, source URLs and timestamps share one cap.
    text_cap=min(page_cap,cap)
    while text_cap>=80:
        rows=[]
        try:
            for original,body in prepared:
                row=dict(original);row.update(select(body,text_cap,policy,complete));rows.append(row)
        except WebFailure:
            raise
        if len(encoded(dict(partial=False,sources=rows)))<=cap:return rows
        text_cap-=100
    raise WebFailure('evidence_insufficient')


def manifest(sources):
    import hashlib
    return [dict(url=row['url'],coverage=row['coverage'],ranges=row['ranges'],input_bytes=row['input_bytes'],
                 selected_bytes=row['selected_bytes'],sha256=hashlib.sha256(row['text'].encode()).hexdigest()) for row in sources]


def validate_manifest(rows,source):
    from .public_network import page_url
    if not source.get('web_anchor') or not isinstance(rows,list) or not 1<=len(rows)<=2:raise ValueError('web manifest')
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'url','coverage','ranges','input_bytes','selected_bytes','sha256'}:raise ValueError('web fields')
        try:page_url(row['url'])
        except WebFailure:raise ValueError('web url') from None
        if (row['coverage'] not in ('full','excerpt') or not isinstance(row['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',row['sha256']) or
            type(row['input_bytes']) is not int or not 80<=row['input_bytes']<=4194304 or
            type(row['selected_bytes']) is not int or not 80<=row['selected_bytes']<=min(6000,row['input_bytes'])):raise ValueError('web bounds')
        ranges=row['ranges'];previous=-1
        if not isinstance(ranges,list) or not 1<=len(ranges)<=512:raise ValueError('web ranges')
        for pair in ranges:
            if not isinstance(pair,list) or len(pair)!=2 or any(type(x) is not int for x in pair) or not previous<pair[0]<pair[1]<=row['input_bytes']:raise ValueError('web range')
            previous=pair[1]
        if row['coverage']=='full' and (len(ranges)!=1 or row['selected_bytes']!=row['input_bytes']):raise ValueError('web full')
        if row['coverage']=='excerpt' and (row['selected_bytes']<1200 or row['selected_bytes']>=row['input_bytes']):raise ValueError('web excerpt')
