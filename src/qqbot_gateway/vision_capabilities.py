"""Code-reviewed bounds and derived eligibility; local observations cannot grant bounds.

The registry is code-owned. Adding a record requires source review, never an IQ
script writing 'eligible'. Only a conservative fixed maximum formula is supported.
UTF-8 bytes remain policy units; conversion to tokens needs its own reviewed bound.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = tuple(f'IQ-{i:02}' for i in range(1, 7))


def managed_cli_input_review(root, settings):
    """Selected-path diagnostics; support, source review and quality stay separate."""
    from .backends import resolve_backend
    from .token_budget import known_models
    cfg=resolve_backend(settings)
    if cfg['backend']!='codebuddy_cli':raise ValueError('MANAGED_CLI_REQUIRED')
    identity=runtime_identity(Path(root),settings)
    record=selected_record(settings)
    missing=static_diagnostics(settings,identity)
    model=known_models().get(cfg['model'],{})
    return dict(runtime=identity,model=cfg['model'],reasoning_effort=cfg['reasoning_effort'],
        rule_kind=record.get('kind','legacy_local') if record else None,
        native_input_contract='stream-json:user.content[text,image.base64]',
        advertised_max_input=model.get('maxInputTokens'),advertised_max_output=model.get('maxOutputTokens'),
        missing=missing,permits_native_iq=not missing)


def runtime_identity(root,settings):
    """Local facts only. No copying expected processor facts into observations."""
    from .backends import resolve_backend
    cfg=resolve_backend(settings)
    if cfg['backend']=='codebuddy_cli':
        from .workbuddy_cli_runner import CLIRunner
        lock=read_json(root/'config/versions.lock.json')
        runner=CLIRunner(root,cfg['model'])
        actual=hashlib.sha256((runner.entry.parent.parent/'dist/codebuddy-headless.js').read_bytes()).hexdigest()
        if actual!=lock['cli']['headless_sha256']:raise ValueError('CLI_BUNDLE_MISMATCH')
        return dict(version=lock['cli']['version'],artifact_sha256=actual,
            node_sha256=hashlib.sha256(runner.node.read_bytes()).hexdigest())
    return dict(model_digest=cfg['expected_digest'],runtime='unverified')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def read_json(path):
    from .reply_plan import _pairs
    if path.is_symlink() or path.stat().st_size > 1024*1024:
        raise ValueError('VISION_EVIDENCE_INVALID')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_pairs)


def registry():
    value = read_json(ROOT/'config/vision-capabilities.json')
    if value.get('schema_version') != 1 or not isinstance(value.get('records'), list):
        raise ValueError('VISION_REGISTRY_INVALID')
    return value


def reviewed(record):
    """Strict supported proof language, no runtime-supplied arbitrary formulas."""
    if isinstance(record,dict) and 'kind' in record:
        from .hosted_cli_budget import KIND, reviewed as hosted_reviewed
        if record['kind']!=KIND:raise ValueError('UNKNOWN_VISION_RULE_KIND')
        return hosted_reviewed(record)
    keys = {'backend', 'model', 'runtime', 'vision_supported', 'sources', 'bounds'}
    if not isinstance(record, dict) or set(record) != keys or type(record['vision_supported']) is not bool:
        raise ValueError('REVIEW_RECORD_INVALID')
    runtime = record['runtime']
    required = {'version', 'model_digest', 'platform', 'architecture', 'processor', 'projector', 'runner_path', 'artifact_sha256'}
    if not isinstance(runtime, dict) or set(runtime) != required or any(not isinstance(v, str) or not v for v in runtime.values()):
        raise ValueError('RUNTIME_PATH_UNVERIFIED')
    bounds = record['bounds']
    fields = {'visual_max_tokens', 'image_marker_tokens', 'template_max_tokens', 'text_tokens_per_byte', 'native_window', 'max_width', 'max_height', 'max_pixels', 'max_images'}
    if not isinstance(bounds, dict) or set(bounds) != fields or any(type(v) is not int or v <= 0 for v in bounds.values()):
        raise ValueError('BOUNDS_UNVERIFIED')
    if bounds['max_images'] != 1 or bounds['max_width'] < 1024 or bounds['max_height'] < 1024 or bounds['max_pixels'] < 1000000:
        raise ValueError('NORMALIZER_DOMAIN_UNCOVERED')
    # Each claim needs an immutable source hash, exact source symbol and reviewed
    # applicability rationale. Merely having /api/show vision is insufficient.
    sources = record['sources']
    claims = {'vision', 'runtime_path', 'visual', 'template', 'text_conversion', 'window'}
    if not isinstance(sources, dict) or set(sources) != claims:
        raise ValueError('REVIEW_SOURCES_MISSING')
    for source in sources.values():
        if (not isinstance(source, dict) or set(source) != {'url', 'sha256', 'symbol', 'applicability'} or
            not isinstance(source['url'],str) or not source['url'].startswith('https://') or
            not isinstance(source['sha256'],str) or len(source['sha256']) != 64 or
            any(c not in '0123456789abcdef' for c in source['sha256']) or
            any(not isinstance(source[k], str) or not source[k].strip() for k in ('symbol', 'applicability'))):
            raise ValueError('REVIEW_SOURCES_INVALID')
    return record


def visual_upper(record, width, height):
    bounds = reviewed(record)['bounds']
    if (type(width) is not int or type(height) is not int or not 0 < width <= bounds['max_width'] or
        not 0 < height <= bounds['max_height'] or width*height > bounds['max_pixels']):
        raise ValueError('IMAGE_OUTSIDE_REVIEW')
    return bounds['visual_max_tokens'] + bounds.get('image_marker_tokens',0)


def selected_record(settings, table=None):
    from .backends import resolve_backend
    cfg = resolve_backend(settings)
    rows = (table if table is not None else registry())['records']
    rows = [r for r in rows if r.get('backend') == cfg['backend'] and r.get('model') == cfg['model']]
    if len(rows) != 1:
        return None
    return reviewed(rows[0])


def static_diagnostics(settings, runtime, *, table=None):
    from .backends import resolve_backend
    from .token_budget import known_models
    cfg=resolve_backend(settings);missing=[]
    record=selected_record(settings,table)
    if record is None:return ['SELECTED_COMBINATION_UNREVIEWED']
    if record.get('kind'):
        from .hosted_cli_budget import static_diagnostics as hosted_static
        return hosted_static(settings,runtime,known_models().get(cfg['model'],{}),record)
    if record['vision_supported'] is not True:
        missing.append('SELECTED_MODEL_VISION_UNSUPPORTED')
    if runtime != record['runtime']:
        missing.append('RUNTIME_PATH_MISMATCH')
    b = record['bounds']; policy = cfg['input_budget']
    v = visual_upper(record, 1000, 1000)
    if settings['vision']['input_reserve_tokens'] < v:
        missing.append('VISUAL_RESERVE_INSUFFICIENT')
    # Prove the entire admitted visible policy, not just a successful sample.
    total = policy['context_input_limit_tokens']*b['text_tokens_per_byte'] + b['template_max_tokens'] + v + policy['output_reserve_tokens']
    window = cfg.get('num_ctx') or cfg.get('context_window_tokens')
    if window is None or window > b['native_window'] or total > window:
        missing.append('NATIVE_CAPACITY_UNPROVEN')
    if cfg.get('num_predict', 0) > policy['output_reserve_tokens']:
        missing.append('OUTPUT_RESERVE_INSUFFICIENT')
    return missing


def offline_path(settings):
    record=selected_record(settings)
    return ROOT/('reports/lap-42-vision-offline.json' if record and record.get('kind') else 'reports/lap-28-C-offline.json')


def offline_valid(settings):
    from .vision import adapter_signature
    try:
        value=read_json(offline_path(settings))
        if value.get('passed') is not True or value.get('adapter_signature')!=adapter_signature():return False
        record=selected_record(settings)
        if record and record.get('kind'):
            verifier=ROOT/'scripts/verify_lap42_vision.py'
            tests=ROOT/'tests/test_lap42_vision.py'
            if (value.get('rule_hash')!=digest(record) or
                value.get('verifier_sha256')!=hashlib.sha256(verifier.read_bytes()).hexdigest() or
                value.get('tests_sha256')!=hashlib.sha256(tests.read_bytes()).hexdigest() or
                value.get('source_audit_sha256')!=hashlib.sha256((ROOT/'reports/lap-42-vision-closure-sources.json').read_bytes()).hexdigest()):return False
        return True
    except (OSError,ValueError,TypeError,KeyError):return False


def production_diagnostics(settings, evidence, runtime, *, table=None):
    from .backends import resolve_backend
    from .vision import binding
    cfg = resolve_backend(settings)
    missing = []
    record = selected_record(settings, table)
    if record is None:
        return ['SELECTED_COMBINATION_UNREVIEWED', 'VISION_SUPPORT_UNVERIFIED', 'VISUAL_TEMPLATE_TOKEN_BOUNDS_UNVERIFIED']
    missing.extend(static_diagnostics(settings,runtime,table=table))
    expected = binding(settings, runtime)
    if not isinstance(evidence, dict) or evidence.get('binding') != expected or evidence.get('record_hash') != digest(record):
        return missing + ['OBSERVATION_BINDING_MISMATCH']
    if evidence.get('offline_passed') is not True or evidence.get('ingress_decoded') is not True:
        missing.append('OFFLINE_OR_INGRESS_UNVERIFIED')
    if evidence.get('acceptance_mode')=='lap43_operator_trial':
        from .vision_trial import diagnostics
        return missing+diagnostics(evidence.get('operator_trial'),expected,runtime,digest(record))
    if evidence.get('acceptance_mode')=='lap42_first_plus_large_operator_acceptance':
        if not record.get('kind'):return missing+['OPERATOR_ACCEPTANCE_BACKEND_INVALID']
        from .vision_operator_review import diagnostics
        return missing+diagnostics(evidence.get('operator_review'),expected)
    batch = evidence.get('batch', {})
    if not isinstance(batch,dict):return missing+['FIXED_IQ_BATCH_INVALID']
    rows = batch.get('cases', {})
    if not isinstance(rows,dict):return missing+['FIXED_IQ_BATCH_INVALID']
    if (batch.get('selected_binding') != expected or batch.get('max_total_generations') != 6 or
        set(rows) != set(CASES) or batch.get('fixture_hash') != evidence.get('fixture_hash')):
        missing.append('FIXED_IQ_BATCH_INCOMPLETE')
    for case in CASES:
        row = rows.get(case, {})
        checks = ('quality_passed', 'native_image_verified', 'budget_passed', 'runtime_verified', 'no_truncation', 'no_tools')
        if (not isinstance(row,dict) or row.get('state') != 'scored' or type(row.get('attempts')) is not int or
            row.get('attempts') != 1 or any(row.get(k) is not True for k in checks)):
            missing.append(case+'_UNVERIFIED')
        if record.get('kind'):
            human=row.get('human_review',{}) if isinstance(row,dict) else {}
            if (not isinstance(human,dict) or human.get('source') not in
                ('operator_tty_explicit','conversation_explicit_feedback') or human.get('case')!=case or
                type(human.get('timestamp')) not in (int,float) or
                not isinstance(human.get('answer_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',human['answer_sha256'])):
                missing.append(case+'_HUMAN_REVIEW_MISSING')
    if evidence.get('unresolved_attempts', True) is not False:
        missing.append('FAILED_OR_UNKNOWN_ATTEMPTS')
    return missing


def load_production(settings, root=None):
    """Fixed private activation path, never accepted from YAML or an HTTP caller."""
    root = Path(root) if root is not None else ROOT
    path = root/'state/vision-evidence/active.json'
    if not path.exists():
        return None, ['ACTIVE_OBSERVATION_MISSING']+production_diagnostics(settings,{}, {})
    if not path.resolve().is_relative_to((root/'state').resolve()):
        raise ValueError('VISION_EVIDENCE_PATH_INVALID')
    return validate_production_evidence(settings, read_json(path), root)


def validate_production_evidence(settings, evidence, root=None):
    """Same complete validation for private candidates and saved active evidence."""
    root = Path(root) if root is not None else ROOT
    runtime = evidence.get('runtime', {})
    missing = production_diagnostics(settings, evidence, runtime)
    for marker in ('state/cli-cleanup/unresolved.json','state/ollama-remote-result-unknown.json','state/lap43-vision-trial/probe-unknown.json'):
        if (root/marker).exists():missing.append('MODEL_CLEANUP_OR_REMOTE_UNKNOWN')
    ingress=evidence.get('ingress_instance','')
    if not isinstance(ingress,str) or not re.fullmatch('[a-f0-9]{32}',ingress):
        missing.append('REAL_INGRESS_PROOF_MISSING')
    else:
        intake=root/'state/vision-evidence'/(ingress+'.json')
        try:
            from .vision_ingress import validate_record
            item=read_json(intake);row=validate_record(item['record'])
            if (item.get('state')!='observed' or row['stage']!='decoded' or row['failure_enum']!='none' or
                row['bytes']<=0 or row['normalized_bytes']<=0 or row['attempt_counts']['download']!=1):
                missing.append('REAL_INGRESS_PROOF_INVALID')
        except (OSError,ValueError,KeyError,TypeError):missing.append('REAL_INGRESS_PROOF_INVALID')
    # The summary is not an authority. Re-read the durable batch and the current
    # code's offline report rather than accepting hand-written 'passed' flags.
    from .vision_quality import BatchLedger
    from .vision import adapter_signature
    ledger_path=root/'state/vision-evidence/iq-batches.sqlite3'
    trial=evidence.get('acceptance_mode')=='lap43_operator_trial'
    if trial:
        from .vision_trial import durable_diagnostics
        missing.extend(durable_diagnostics(root,evidence,settings))
    elif evidence.get('acceptance_mode')=='lap42_first_plus_large_operator_acceptance':
        from .vision_operator_review import durable_diagnostics
        missing.extend(durable_diagnostics(root,evidence.get('operator_review'),evidence.get('binding')))
    elif not ledger_path.is_file():
        missing.append('DURABLE_IQ_LEDGER_MISSING')
    else:
        ledger=BatchLedger(ledger_path)
        try:
            if ledger.snapshot(evidence['batch']['batch_id'])!=evidence['batch']:
                missing.append('DURABLE_IQ_LEDGER_MISMATCH')
            if ledger.unresolved(evidence['binding']):missing.append('FAILED_OR_UNKNOWN_ATTEMPTS')
        except (ValueError,KeyError):missing.append('DURABLE_IQ_LEDGER_INVALID')
    if not trial and not offline_valid(settings):
        missing.append('CURRENT_OFFLINE_PROOF_MISSING')
    record=selected_record(settings)
    if not trial and record and record.get('kind'):
        from .vision_mod_guard import probe_valid
        if not probe_valid(root,settings):missing.append('CURRENT_CLI_PROBE_MISSING')
    # Configured digest must still match the reviewed, observed selected model.
    from .backends import resolve_backend
    cfg = resolve_backend(settings)
    if cfg['backend'] == 'ollama_ssh' and cfg.get('expected_digest') != runtime.get('model_digest'):
        missing.append('SELECTED_DIGEST_MISMATCH')
    if cfg['backend'] == 'codebuddy_cli':
        if runtime_identity(root, settings) != runtime:
            missing.append('LOCAL_RUNTIME_CHANGED')
    return (None if missing else selected_record(settings)), missing


def final_budget(record, budget, system, prompt, width, height):
    if record.get('kind'):
        from .hosted_cli_budget import final_budget as hosted_final
        from .token_budget import known_models
        return hosted_final(record,budget,system,prompt,width,height,known_models().get(record['model'],{}))
    v = visual_upper(record, width, height)
    b = record['bounds']
    budget.check(system, prompt)
    visible = budget.usage(system, prompt)  # bytes-policy envelope including overhead
    if visible*b['text_tokens_per_byte'] + b['template_max_tokens'] + v + budget.output > min(b['native_window'], budget.window or b['native_window']):
        raise ValueError('FINAL_NATIVE_CAPACITY_EXCEEDED')
    return dict(visible_policy_bytes=visible, visual_upper_tokens=v, template_upper_tokens=b['template_max_tokens'], output_reserve_tokens=budget.output)
