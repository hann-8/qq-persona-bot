"""Code-owned LAP-43 evidence namespace; old LAP-42 facts remain immutable."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from .vision_capabilities import read_json
MODE='lap43_current_regression'
BASE='state/lap43-vision-regression'

def directory(root,bound):
    if not isinstance(bound,str) or not re.fullmatch('[a-f0-9]{64}',bound):raise ValueError('BINDING_INVALID')
    from .meme_catalog import controlled_path
    return controlled_path(Path(root),BASE+'/'+bound)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def unknown(root):
    from .vision_mod_guard import probe_unknown_unresolved
    if probe_unknown_unresolved(root) or not old_attempts_clean(root):return True
    base=Path(root)/BASE
    if base.exists():
        for p in base.glob('*/attempt.json'):
            try:
                if read_json(p).get('state')!='scored':return True
            except (OSError,ValueError):return True
        for p in base.glob('*/probe-attempt.json'):
            try:
                if read_json(p).get('state')!='verified':return True
            except (OSError,ValueError):return True
        if any(base.glob('*/probe-unknown.json')):return True
    return False

def old_attempts_clean(root):
    ledger=Path(root)/'state/vision-evidence/iq-batches.sqlite3'
    if not ledger.exists():return True
    try:
        import sqlite3
        with sqlite3.connect('file:'+ledger.as_posix()+'?mode=ro',uri=True) as db:
            rows=db.execute('SELECT batches.id,attempts.case_id,attempts.result FROM attempts JOIN batches ON batches.id=attempts.batch').fetchall()
        for batch,case,raw in rows:
            result=json.loads(raw)
            if result.get('state')=='scored' and result.get('quality_passed') is True and result.get('no_truncation') is True:continue
            if batch=='lap42-vision-closure-v2' and case=='IQ-01' and historical(root):continue
            return False
        return True
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error):return False


def authorized(root,bound):
    try:
        grant=read_json(directory(root,bound)/'authorization.json')
        return (grant==dict(mode=MODE,binding=bound,source='explicit_current_conversation',max_local_real_requests=1,
            case='IQ-05',historical_case='IQ-01',prior_failures_preserved=True))
    except (OSError,ValueError):return False

def historical(root):
    """Check accepted IQ-01 and the retained recorder failure, not current IQ-01."""
    from .vision_operator_review import PATH,FIRST_BINDING,FIRST_ANSWER,diagnostics
    try:
        old=read_json(Path(root)/PATH)
        from .vision_operator_review import ATTEMPT
        attempt=read_json(Path(root)/ATTEMPT)
        if attempt.get('state')!='scored' or attempt.get('result')!=old.get('large'):return False
        if diagnostics(old,old['binding']):return False
        pending=read_json(Path(root)/'state/lap42-vision-closure/pending-human-review.json')
        ledger=Path(root)/'state/vision-evidence/iq-batches.sqlite3'
        if not ledger.is_file():return False
        import sqlite3
        with sqlite3.connect('file:'+ledger.as_posix()+'?mode=ro',uri=True) as db:
            plan=db.execute('SELECT plan FROM batches WHERE id=?',('lap42-vision-closure-v2',)).fetchone()
            saved=db.execute('SELECT result FROM attempts WHERE batch=? AND case_id=?',('lap42-vision-closure-v2','IQ-01')).fetchone()
        if not plan or not saved:return False
        batch=json.loads(plan[0]);row=json.loads(saved[0])
        return (batch['selected_binding']==FIRST_BINDING and row['attempts']==1 and row['state']=='failed_or_unknown' and
                row['failure']=='NATIVE_OBSERVATION_FAILED' and pending['answer_sha256']==FIRST_ANSWER and pending['human_accepted'] is True)
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error):return False

def diagnostics(value,bound):
    if not isinstance(value,dict) or value.get('mode')!=MODE or value.get('binding')!=bound:return ['LAP43_REVIEW_MISSING']
    from .vision_operator_review import FIRST_BINDING,FIRST_ANSWER
    if value.get('historical_first')!=dict(binding=FIRST_BINDING,answer_sha256=FIRST_ANSWER,case='IQ-01',current_rerun=False):return ['LAP43_HISTORICAL_ACCEPTANCE_MISSING']
    row=value.get('large',{});human=row.get('human_review',{})
    if (row.get('case_id')!='IQ-05' or row.get('attempts')!=1 or row.get('state')!='scored' or
        any(row.get(k) is not True for k in ('exact_facts','human_passed','quality_passed','native_image_verified','budget_passed','runtime_verified','no_truncation','no_tools')) or
        row.get('normalized',{}).get('width',0)*row.get('normalized',{}).get('height',0)<990000 or
        human.get('source')!='conversation_explicit_feedback' or human.get('case')!='IQ-05' or
        type(human.get('timestamp')) not in (int,float) or not re.fullmatch('[a-f0-9]{64}',str(human.get('answer_sha256','')))):
        return ['LAP43_CURRENT_LARGE_UNVERIFIED']
    return []

def durable(root,value,bound):
    missing=diagnostics(value,bound)
    try:
        d=directory(root,bound);attempt=read_json(d/'attempt.json')
        if (read_json(d/'review.json')!=value or attempt.get('binding')!=bound or attempt.get('state')!='scored' or
            attempt.get('attempts')!=1 or attempt.get('result')!=value.get('large')):missing.append('LAP43_ATTEMPT_MISMATCH')
        if not authorized(root,bound):missing.append('LAP43_AUTHORIZATION_MISSING')
        if not historical(root):missing.append('LAP43_HISTORICAL_FACT_MISSING')
        if unknown(root):missing.append('LAP43_UNRESOLVED_ATTEMPTS')
    except (OSError,ValueError,KeyError,TypeError):missing.append('LAP43_DURABLE_MISSING')
    return missing

from contextvars import ContextVar
PROBE_BASE=ContextVar('lap43_probe_base',default=None)
