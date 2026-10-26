"""LAP-42 operator's explicitly shortened acceptance; never six-case proof."""
import re
from .vision_capabilities import read_json

MODE='lap42_first_plus_large_operator_acceptance'
WAIVED=['IQ-02','IQ-03','IQ-04','IQ-06']
FIRST_BINDING='4c131e1adf96f822fb75e4ec4aeb598363a767611616df1feb5f614f0f217e8a'
FIRST_ANSWER='30eea58651806c120aa7c512e273b0960bee1a9ae00481ebcf2956fe3992d592'
PATH='state/lap42-vision-closure/operator-review.json'
ATTEMPT='state/lap42-vision-closure/operator-large-attempt.json'


def diagnostics(value,bound):
    if not isinstance(value,dict):return ['OPERATOR_ACCEPTANCE_MISSING']
    authorization=value.get('authorization',{})
    first=value.get('first',{})
    large=value.get('large',{})
    checks=('exact_facts','human_passed','quality_passed','native_image_verified',
            'budget_passed','runtime_verified','no_truncation','no_tools')
    human=large.get('human_review',{})
    if (value.get('mode')!=MODE or value.get('binding')!=bound or
        authorization.get('source')!='conversation_explicit_feedback' or
        authorization.get('waived_cases')!=WAIVED or
        authorization.get('prior_recorder_failure_acknowledged') is not True or
        first.get('binding')!=FIRST_BINDING or first.get('case')!='IQ-01' or
        first.get('answer_sha256')!=FIRST_ANSWER or first.get('accepted') is not True or
        first.get('source')!='conversation_explicit_feedback'):
        return ['OPERATOR_ACCEPTANCE_INVALID']
    if (large.get('state')!='scored' or large.get('attempts')!=1 or large.get('case_id')!='IQ-05' or
        any(large.get(k) is not True for k in checks) or
        large.get('normalized',{}).get('width',0)*large.get('normalized',{}).get('height',0)<990000 or
        human.get('source')!='conversation_explicit_feedback' or human.get('case')!='IQ-05' or
        type(human.get('timestamp')) not in (int,float) or
        not re.fullmatch('[a-f0-9]{64}',str(human.get('answer_sha256','')))):
        return ['OPERATOR_LARGE_CASE_UNVERIFIED']
    return []


def durable_diagnostics(root,value,bound):
    missing=diagnostics(value,bound)
    try:
        saved=read_json(root/PATH);attempt=read_json(root/ATTEMPT)
        if saved!=value or attempt.get('binding')!=bound or attempt.get('result')!=value.get('large'):
            missing.append('OPERATOR_ACCEPTANCE_DURABLE_MISMATCH')
        # Preserve, and explicitly account for, the original failed recording.
        from .vision_quality import BatchLedger
        batch=BatchLedger(root/'state/vision-evidence/iq-batches.sqlite3').snapshot('lap42-vision-closure-v2')
        row=batch['cases']['IQ-01']
        pending=read_json(root/'state/lap42-vision-closure/pending-human-review.json')
        if (batch['selected_binding']!=FIRST_BINDING or row.get('attempts')!=1 or
            row.get('state')!='failed_or_unknown' or row.get('failure')!='NATIVE_OBSERVATION_FAILED' or
            pending.get('answer_sha256')!=FIRST_ANSWER or pending.get('human_accepted') is not True):
            missing.append('OPERATOR_PRIOR_RESULT_MISMATCH')
    except (OSError,ValueError,KeyError,TypeError):missing.append('OPERATOR_ACCEPTANCE_DURABLE_MISSING')
    return missing
