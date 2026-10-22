"""Inspect by default. Explicit fixed public batch, never models/bot/config/secrets."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

# Predeclared fact anchors for human review, not substring-based quality approval.
# Positions and selection retention are reported independently; no passed gate.
SAMPLES=(
    ('article','https://www.python.org/doc/essays/blurb/',('interpreted','dynamic typing','high-level')),
    ('documentation','https://docs.python.org/3/library/json.html',('json.loads','json.dumps','JSONDecodeError')),
    ('long_text','https://www.rfc-editor.org/rfc/rfc8259.txt',('UTF-8','false','unordered')),
    ('restricted_shell','https://app.slack.com/',()),
)


def inspect():
    from qqbot_gateway.web_policy import DEFAULTS,SEARCH_QUALITY_PASSED
    return dict(mode='inspect',sample_count=len(SAMPLES),selection_policy=DEFAULTS['selection_policy'],
                search_quality_passed=SEARCH_QUALITY_PASSED,network_calls=0,model_calls=0,bot_outputs=0)


async def public_samples():
    from qqbot_gateway.web_retrieval import Retriever,PublicHTTP,Audit
    from qqbot_gateway.web_policy import DEFAULTS
    from qqbot_gateway.evidence_selection import sources_for_budget
    rows=[]
    with tempfile.TemporaryDirectory(prefix='lap18C-public-') as directory:
        reader=Retriever(DEFAULTS,root=directory)
        for kind,url,facts in SAMPLES:
            audit=Audit();started=time.monotonic();row=dict(kind=kind,attempts=1,status='transport_failed',failure='none')
            try:
                # One entry per sample, no retry/provider changes/credentials.
                text,final,mime=await PublicHTTP(reader.cfg,audit).get(url)
                row.update(status='body_failed',response_bytes=len(text.encode()))
                source=await reader.extract(text,final,mime)
                body=source['_full_text']
                row.update(status='selection_failed',body_method=source['body_method'],body_bytes=len(body.encode()),
                           blocks=len(body.splitlines()),fact_positions=[body.find(f) for f in facts])
                selected=sources_for_budget([source],6000,4000,'excerpt',' '.join(facts),'question')[0]
                row.update(status='selected_unreviewed',coverage=selected['coverage'],selected_bytes=selected['selected_bytes'],
                           selected_fact_flags=[f in selected['text'] for f in facts])
                if kind=='restricted_shell':row['status']='restriction_requires_review'
            except asyncio.CancelledError:raise
            except Exception as error:
                # Never serialize exception messages, source URLs or body.
                row['failure']='timeout' if isinstance(error,TimeoutError) else row['status']
            row['elapsed_ms']=int((time.monotonic()-started)*1000)
            rows.append(row)
    return dict(mode='public_samples',samples=rows,model_calls=0,bot_outputs=0,quality_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-samples',action='store_true',help='explicit fixed public batch; requires separate operator authorization')
    args=parser.parse_args()
    print(json.dumps(asyncio.run(public_samples()) if args.public_samples else inspect(),separators=(',',':')))


if __name__=='__main__':main()
