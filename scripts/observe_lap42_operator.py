"""One supplemental large case after explicit operator waiver. Never retries."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('run','accept','reject'))
    parser.add_argument('--expected-binding',required=True)
    parser.add_argument('--answer-sha256')
    args=parser.parse_args()
    from scripts.activate_lap42_vision import current,atomic
    from scripts.observe_lap28 import observe
    from qqbot_gateway.config import configuration_lock,require_stopped
    from qqbot_gateway.vision_capabilities import read_json,offline_valid
    from qqbot_gateway.vision_mod_guard import probe_valid
    from qqbot_gateway.vision_operator_review import ATTEMPT,PATH,MODE,WAIVED,FIRST_BINDING,FIRST_ANSWER
    path=ROOT/ATTEMPT
    with configuration_lock(ROOT):
        require_stopped(ROOT)
        project,_,bound=current(ROOT)
        if bound!=args.expected_binding or project.settings['vision']['enabled']:
            raise ValueError('CURRENT_STATE_CHANGED')
        if args.action=='run':
            if not offline_valid(project.settings) or not probe_valid(ROOT,project.settings):
                raise ValueError('CURRENT_CONTRACT_PROOF_REQUIRED')
            spec=read_json(ROOT/'state/vision-evidence/iq-fixtures-lap42-v2/spec.json')
            sample=ROOT/'state/vision-evidence/iq-fixtures-lap42-v2/IQ-05.png'
            image_hash=hashlib.sha256(sample.read_bytes()).hexdigest()
            if image_hash!=spec['cases']['IQ-05']['sha256']:raise ValueError('FIXTURE_CHANGED')
            attempt=dict(binding=bound,case='IQ-05',attempts=1,state='attempt_reserved',fixture_hash=image_hash)
            # Exclusive creation is the irreversible attempt reservation. No replacement batch.
            with path.open('x',encoding='utf-8') as stream:json.dump(attempt,stream)
        else:
            attempt=read_json(path)
            if (attempt.get('binding')!=bound or attempt.get('state')!='awaiting_human' or
                attempt['result']['human_review']['answer_sha256']!=args.answer_sha256):
                raise ValueError('PENDING_REVIEW_MISMATCH')
            row=attempt['result'];accepted=args.action=='accept'
            row['human_passed']=accepted
            row['quality_passed']=bool(row['exact_facts'] and accepted)
            row['native_success']=row['quality_passed']
            row['human_review']['timestamp']=time.time()
            attempt['state']='scored';atomic(path,json.dumps(attempt).encode())
            if not accepted:return 1
            review=dict(mode=MODE,binding=bound,authorization=dict(source='conversation_explicit_feedback',
                waived_cases=WAIVED,prior_recorder_failure_acknowledged=True),
                first=dict(binding=FIRST_BINDING,case='IQ-01',answer_sha256=FIRST_ANSWER,
                    accepted=True,source='conversation_explicit_feedback'),large=row)
            from qqbot_gateway.vision_operator_review import diagnostics
            missing=diagnostics(review,bound)
            if missing:raise ValueError(','.join(missing))
            atomic(ROOT/PATH,json.dumps(review).encode())
            print('Operator two-case acceptance saved; four cases remain waived, not passed')
            return 0
    def pending(text):
        print('answer_sha256='+hashlib.sha256(text.encode()).hexdigest(),flush=True)
        print(text,flush=True)
        return dict(no_hallucination=False,visible_facts_correct=False,injection_safe=False)
    pending.review_source='conversation_explicit_feedback'
    try:
        result=asyncio.run(observe(ROOT,project.settings,sample,'IQ-05',spec['cases']['IQ-05']['truth'],bound,pending,image_hash))
        result['attempts']=1
        attempt.update(state='awaiting_human',result=result)
        atomic(path,json.dumps(attempt).encode())
        print('Saved native measurements awaiting explicit human feedback; no further generation')
        return 0
    except BaseException as exc:
        attempt.update(state='failed_or_unknown',failure=type(exc).__name__)
        atomic(path,json.dumps(attempt).encode())
        raise


if __name__=='__main__':raise SystemExit(main())
