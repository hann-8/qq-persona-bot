"""Locked hosted contract with post-render system projection and bounded context."""
from copy import deepcopy

KIND = 'hosted_codebuddy_deepseek_v41_mod_v2'
RUNTIME = dict(version='2.168.0',
    artifact_sha256='13e6dd30a22d2f11857675193f909a2ccb935da67a067f580fcfe764e474ff60',
    node_sha256='ba93f9a70bd86fce3ebbb39ec758501458453467aa92a34a0a3602d1e3fc2b9c')
MODEL = 'deepseek-v4.1-flash'
REVISION = '314113f8a7dadb388215396ba5fbee2c610a04d6'
TYPES_HASH = '450476f6346507eb032a00a90c3a90c036e37ef57fbc442b52d5ec725a365a92'
FRAMEWORK_SPANS = {'composer': (4986189, 4987069, 'a46ede57030afae34423d73373ff98860df53a3edeee722d5970241a3eb88eda'), 'context_bridge': (5965415, 5969944, '1827d5126dd2be97a39ffbdf1d2408397b78ca1f136bd355c30911f6600a9f9b'), 'user_wrapper': (14096651, 14096715, '1d68621e1e8e4ba1de6f851849345a4c2207efe314066981739f97934b4957ef'), 'tool_enable_checker': (4873338, 4874369, 'f6394cad47e5c07534ab0fe975b9ae449f16acf642c4b7b80a6e8d4c802835b5'), 'sdk_enabled_tools': (19196392, 19196637, '35eac3fdb00d6c284f49817354d8ca5adba55354c469f0bf3960af69a36818a8'), 'catalog_context': (9736113, 9737113, '8057848afb9b46b0c67b6a1dafb280e7ab8b8e59c07cf7e0a0fe7f3437c7339a')}

SOURCE_HASHES = {
    'tokenizer.json': 'c90dfa01249db1be4245780a052ede752e1361c612ac6d08e2bdada7d599476b',
    'encoding/encoding.py': '13231c592e958fb39e2af6001dae69d90e7a36b265702b9b390236fb387599e2',
    'encoding/README.md': 'a34a5ca98c65e5b5b2bedd693cc2e18e732fe50192723fb6937ae07219c23739',
}


def matches_profile(cfg):
    return (cfg.get('backend') == 'codebuddy_cli' and cfg.get('model') == MODEL
            and cfg.get('reasoning_effort') == 'low')


def review_record():
    # These are source facts, never a locally editable eligibility switch.
    from .vision_mod_guard import assets_signature
    return dict(kind=KIND, backend='codebuddy_cli', model=MODEL, reasoning_effort='low',
        runtime=deepcopy(RUNTIME), vision_supported=True,
        sources=dict(revision=REVISION, hashes=deepcopy(SOURCE_HASHES),
                     audit='reports/lap-42-vision-closure-sources.json',
                     plugin_assets_sha256=assets_signature()),
        bounds=dict(text_tokens_per_byte=1, visual_max_tokens=1024,
                    native_window=1000000, max_width=1024, max_height=1024,
                    max_pixels=1000000, max_images=1),
        template_contract='post_render_single_session_system_dual_empty_context_v2')


def reviewed(record):
    if record != review_record():
        raise ValueError('HOSTED_REVIEW_RECORD_MISMATCH')
    return record


def positive(value):
    return type(value) is int and 0 < value <= 2**53-1


def effective_capacity(model, override=None):
    """Exact locked resolveEffectiveContextBudget semantics (not legacy default).

    An override/defaultLength is valid only with >=2 supported legal lengths.
    The CLI filters lengths above maxInputTokens before checking membership.
    """
    maximum = model.get('maxInputTokens')
    window = model.get('contextWindow') or {}
    if not isinstance(window, dict):
        raise ValueError('HOSTED_CONTEXT_STRUCTURE_CHANGED')
    lengths = window.get('supportedLengths') or []
    if not isinstance(lengths, list):
        raise ValueError('HOSTED_CONTEXT_STRUCTURE_CHANGED')
    lengths = sorted({n for n in lengths if positive(n) and
                      (maximum is None or (positive(maximum) and n <= maximum))})
    if len(lengths) >= 2:
        if positive(override) and override in lengths:
            return override
        default = window.get('defaultLength')
        return default if positive(default) and default in lengths else lengths[0]
    if not positive(maximum):
        raise ValueError('HOSTED_INPUT_CAPACITY_UNKNOWN')
    return maximum


def model_terms(model, output_reserve):
    if (model.get('id') != MODEL or model.get('supportsImages') is not True or
            'low' not in model.get('reasoning', {}).get('supportedEfforts', [])):
        raise ValueError('HOSTED_MODEL_VISION_OR_LOW_UNVERIFIED')
    output = model.get('maxOutputTokens')
    if not positive(output):
        raise ValueError('HOSTED_OUTPUT_CAPACITY_UNKNOWN')
    return min(effective_capacity(model), 1000000), max(output_reserve, output)


def known_template_parts():
    # Fixed official encoder render_message/_process_image_blocks; byte bound
    # also covers special tokens without claiming exact tokenization counts.
    # CLI UserQueryWrapper adds the two literal tags for the single text block.
    return ('<｜begin▁of▁sentence｜>', '<｜System｜>',
            'Reasoning Effort: 50 (range 1-100, the higher the value, the more thorough the reasoning)\n\n',
            '<｜User｜>', '<user_query>', '</user_query>', '\n\n',
            '<｜deepseek_image｜>', '<｜Assistant｜>', '<think>')


def template_diagnostics():
    try:
        framework_upper()
        return []
    except (OSError,ValueError,KeyError,TypeError):
        return ['CLI_MOD_FRAMEWORK_SOURCE_CHANGED']


def framework_upper():
    """Whole reviewed source spans overcount fixed text, once per guarded request.

    Dynamic composer/context text is replaced, never bounded by source length.
    The plugin independently rejects transcript expansion before next().
    """
    import hashlib
    from pathlib import Path
    from .vision_capabilities import read_json
    root=Path(__file__).resolve().parents[2]
    audit=read_json(root/'reports/lap-42-vision-closure-sources.json')
    lock=read_json(root/'config/versions.lock.json')
    bundle=Path(lock['cli']['entry']).parent.parent/'dist/codebuddy-headless.js'
    raw=bundle.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=RUNTIME['artifact_sha256'] or audit['bundle_sha256']!=RUNTIME['artifact_sha256']:
        raise ValueError('CLI_MOD_FRAMEWORK_SOURCE_CHANGED')
    source=raw.decode('utf-8')
    if (set(audit['framework_parts'])!=set(FRAMEWORK_SPANS) or audit['types_sha256']!=TYPES_HASH or
        hashlib.sha256((bundle.parent.parent/'types/codebuddy-code.d.ts').read_bytes()).hexdigest()!=TYPES_HASH):
        raise ValueError('CLI_MOD_FRAMEWORK_SOURCE_CHANGED')
    total=sum(len(p.encode('utf-8')) for p in known_template_parts())
    for name,row in audit['framework_parts'].items():
        if (row['start'],row['end'],row['sha256'])!=FRAMEWORK_SPANS[name]:
            raise ValueError('CLI_MOD_FRAMEWORK_SOURCE_CHANGED')
        data=source[row['start']:row['end']].encode('utf-8')
        if (row['multiplicity']!=1 or len(data)!=row['source_bytes'] or
            hashlib.sha256(data).hexdigest()!=row['sha256']):
            raise ValueError('CLI_MOD_FRAMEWORK_SOURCE_CHANGED')
        total+=len(data)
    if total!=audit['framework_upper_bytes']:raise ValueError('CLI_MOD_FRAMEWORK_SOURCE_CHANGED')
    return total


def static_diagnostics(settings, runtime, model, record):
    from .backends import resolve_backend
    reviewed(record)
    cfg = resolve_backend(settings)
    missing = []
    if not matches_profile(cfg): missing.append('HOSTED_PROFILE_MISMATCH')
    if runtime != RUNTIME: missing.append('HOSTED_RUNTIME_MISMATCH')
    if cfg.get('context_window_tokens') is not None:
        missing.append('HOSTED_SESSION_OVERRIDE_NOT_REVIEWED')
    if settings['vision']['input_reserve_tokens'] < 1024:
        missing.append('VISUAL_RESERVE_INSUFFICIENT')
    try:
        capacity, output = model_terms(model, cfg['input_budget']['output_reserve_tokens'])
        if cfg['input_budget']['context_input_limit_tokens'] + framework_upper() + 1024 + output > capacity:
            missing.append('HOSTED_NATIVE_CAPACITY_EXCEEDED')
    except ValueError as error:
        missing.append(str(error))
    return missing + template_diagnostics()


def final_budget(record, budget, system, prompt, width, height, model):
    reviewed(record)
    if budget.vision_kind != KIND: raise ValueError('HOSTED_BUDGET_KIND_MISMATCH')
    if not (type(width) is int and type(height) is int and
            0 < width <= 1024 and 0 < height <= 1024 and width*height <= 1000000):
        raise ValueError('IMAGE_OUTSIDE_REVIEW')
    budget.check(system, prompt)
    capacity, output = model_terms(model, budget.output)
    text = len(system.encode('utf-8')) + len(prompt.encode('utf-8'))
    framework = framework_upper()
    if text + framework + 1024 + output > capacity:
        raise ValueError('FINAL_NATIVE_CAPACITY_EXCEEDED')
    return dict(T=text,F=framework,V=1024,O=output,C=capacity)
