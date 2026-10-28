"""Explicit LAP-43 runtime permission, always pending user quality testing."""
import hashlib
import re
from pathlib import Path

MODE='lap43_operator_trial'
OFFLINE='reports/lap-43-vision-offline.json'
PROBE='state/lap43-vision-trial/cli-probe.json'
JOURNALS='state/lap43-vision-trial'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def offline_valid(settings,root):
    from .vision_capabilities import read_json,digest,selected_record
    from .vision import adapter_signature,binding
    from .vision_capabilities import runtime_identity
    try:
        value=read_json(root/OFFLINE)
        files=('scripts/revalidate_lap43_vision.py','tests/test_lap43.py','tests/test_web_freshness.py',
               'tests/test_lap42_vision.py','tests/test_vision_mod_guard.py','reports/lap-42-vision-closure-sources.json')
        return (value.get('passed') is True and value.get('adapter_signature')==adapter_signature() and
            value.get('binding')==binding(settings,runtime_identity(root,settings)) and
            value.get('rule_hash')==digest(selected_record(settings)) and value.get('files')=={p:sha(root/p) for p in files} and
            value.get('real_model_calls')==0 and value.get('real_qq_outputs')==0 and
            value.get('budget',{}).get('passed') is True and value.get('static_missing')==[] and
            type(value.get('tests_run')) is int and value['tests_run']>0)
    except (OSError,ValueError,TypeError,KeyError):return False


def diagnostics(value,bound,runtime,record_hash):
    if not isinstance(value,dict) or set(value)!={'binding','runtime','record_hash','authorized_at','authorization_source',
            'quality_state','previous_active_sha256','technical_report_sha256'}:return ['OPERATOR_TRIAL_INVALID']
    from .web_freshness import parse_date
    if (value['binding']!=bound or value['runtime']!=runtime or value['record_hash']!=record_hash or
        value['authorization_source']!='operator_submitted_prompt' or value['quality_state']!='pending_user_test' or
        parse_date(value['authorized_at'])[1]!='instant' or any(not isinstance(value[k],str) or not re.fullmatch('[a-f0-9]{64}',value[k])
            for k in ('previous_active_sha256','technical_report_sha256'))):return ['OPERATOR_TRIAL_INVALID']
    return []


def durable_diagnostics(root,evidence,settings):
    from .vision_capabilities import read_json
    from .vision_quality import BatchLedger
    from .vision_mod_guard import probe_valid,probe_unknown_unresolved
    missing=[];bound=evidence['binding'];folder=root/JOURNALS/bound
    try:
        from .config_files import plain_path
        for path in (folder/'authorization.json',folder/'active.before',root/OFFLINE):plain_path(root,path)
        value=evidence['operator_trial']
        if read_json(folder/'authorization.json')!=value or sha(folder/'active.before')!=value['previous_active_sha256']:
            missing.append('OPERATOR_TRIAL_DURABLE_MISMATCH')
        if sha(root/OFFLINE)!=value['technical_report_sha256'] or not offline_valid(settings,root):missing.append('CURRENT_OFFLINE_PROOF_MISSING')
        ledger=root/'state/vision-evidence/iq-batches.sqlite3'
        if not ledger.is_file() or BatchLedger(ledger).unresolved(bound):missing.append('FAILED_OR_UNKNOWN_ATTEMPTS')
        if probe_unknown_unresolved(root) or not probe_valid(root,settings,trial=True):missing.append('CURRENT_CLI_PROBE_MISSING')
    except (OSError,ValueError,TypeError,KeyError):missing.append('OPERATOR_TRIAL_DURABLE_MISSING')
    return missing
