"""Retired subtitle compatibility: pure legacy material selection only. No I/O."""
from .public_http import WebFailure

def select_source(source,cap,policy,complete):
    cues=source['_cues'];body=source['_full_text'];total=len(body.encode())
    rows=[];pos=0
    for a,b,text in cues:
        rows.append((a,b,text,pos,pos+len(text)));pos+=len(text)+1
    if total<=cap:chosen=rows;coverage='full'
    else:
        if policy=='reject' or complete:raise WebFailure('evidence_full_required')
        zones=[[] for _ in range(6)]
        for row in rows:zones[min(5,int(row[0]*6/source['duration']))].append(row)
        populated=sum(bool(z) for z in zones);chosen=[];used_zones=0
        for i,zone in enumerate(zones):
            used=0;window=[]
            for row in (reversed(zone) if i==5 else zone):
                size=len(row[2].encode())+1
                if used+size>(cap-6)//6:break
                window.append(row);used+=size
            if window:used_zones+=1;chosen.extend(window)
        chosen.sort(key=lambda r:r[3])
        if used_zones<min(4,populated) or populated<min(4,len(rows)):raise WebFailure('evidence_insufficient')
        coverage='excerpt'
    text='\n'.join(r[2] for r in chosen);size=len(text.encode())
    if coverage=='excerpt' and size<1200:raise WebFailure('evidence_insufficient')
    intervals=[]
    for a,b,*_ in chosen:
        if intervals and a<=intervals[-1][1]:intervals[-1][1]=max(b,intervals[-1][1])
        else:intervals.append([a,b])
    gaps=[];last=0
    for a,b in intervals:
        if a>last:gaps.append([last,a])
        last=b
    if last<source['duration']:gaps.append([last,source['duration']])
    ranges=[]
    for r in chosen:
        if ranges and r[3]==ranges[-1][1]+1:ranges[-1][1]=r[4]
        else:ranges.append([r[3],r[4]])
    row={k:v for k,v in source.items() if not k.startswith('_')}
    row.update(text=text,coverage=coverage,ranges=[[0,len(body)]] if coverage=='full' else ranges,
               input_bytes=total,selected_bytes=size,truncated=coverage=='excerpt',time_ranges=intervals,time_gaps=gaps,
               time_coverage=round(sum(b-a for a,b in intervals)/source['duration'],6))
    return row
