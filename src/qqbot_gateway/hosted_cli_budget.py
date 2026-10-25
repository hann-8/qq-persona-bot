"""Code-owned hosted review. Policy bytes and native tokens are separate.

The reviewed encoder bounds text and the image, but the locked CLI still
renders provider prompts *after* reading a custom system file. Do not invent
a finite bound for that extra text. This partial review cannot authorize IQ.
"""
from copy import deepcopy

KIND = 'hosted_codebuddy_deepseek_v41_v1'
RUNTIME = dict(version='2.168.0',
    artifact_sha256='13e6dd30a22d2f11857675193f909a2ccb935da67a067f580fcfe764e474ff60',
    node_sha256='ba93f9a70bd86fce3ebbb39ec758501458453467aa92a34a0a3602d1e3fc2b9c')
MODEL = 'deepseek-v4.1-flash'
REVISION = '314113f8a7dadb388215396ba5fbee2c610a04d6'
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
    return dict(kind=KIND, backend='codebuddy_cli', model=MODEL, reasoning_effort='low',
        runtime=deepcopy(RUNTIME), vision_supported=True,
        sources=dict(revision=REVISION, hashes=deepcopy(SOURCE_HASHES),
                     audit='reports/lap-42-vision-sources.json'),
        bounds=dict(text_tokens_per_byte=1, visual_max_tokens=1024,
                    native_window=1000000, max_width=1024, max_height=1024,
                    max_pixels=1000000, max_images=1),
        template_contract='partial_encoder_only_cli_post_override_unbounded')


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
    # Source audit gives exact symbols and offsets. get_available_models
    # returns model data, not rendered instructions or agent.appendInstructions.
    return ['CLI_POST_OVERRIDE_TEMPLATE_UNBOUNDED']


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
        # F is incomplete: this is a necessary check only, never a passing proof.
        if cfg['input_budget']['context_input_limit_tokens'] + 1024 + output > capacity:
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
    known_f = sum(len(part.encode('utf-8')) for part in known_template_parts())
    if text + known_f + 1024 + output > capacity:
        raise ValueError('FINAL_NATIVE_CAPACITY_EXCEEDED')
    # Never substitute policy.overhead=2048, a guessed F, or base64 byte count.
    raise ValueError(template_diagnostics()[0])
