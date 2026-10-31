"""Backend-neutral results and explicitly selected profile views."""
from copy import deepcopy
from dataclasses import dataclass, field

BUDGET_DEFAULTS = dict(context_input_limit_tokens=16384,
                       context_overhead_reserve_tokens=2048, output_reserve_tokens=2048)
CLI_DEFAULTS = dict(model='deepseek-v4.1-flash', reasoning_effort='auto',
                    context_window_tokens=None, run_timeout_seconds=90,
                    input_budget=BUDGET_DEFAULTS)
OLLAMA_DEFAULTS = dict(model='qwen3.5:9b-q4_K_M', expected_digest=None,
    access_file='secrets/home-5070-runtime.local.json', num_ctx=16384, think=False,
    num_predict=1024, keep_alive_seconds=300, temperature=0.7, top_p=0.8, top_k=20,
    run_timeout_seconds=120, input_budget=BUDGET_DEFAULTS | dict(context_input_limit_tokens=12288))


def resolve_backend(settings, backend=None):
    llm = settings['llm']
    name = backend or llm.get('backend','codebuddy_cli')
    if 'profiles' not in llm:  # Legacy snapshots used by offline tools.
        return deepcopy(llm | {'backend':name,'input_budget': BUDGET_DEFAULTS | settings.get('chat', {})})
    return deepcopy({k:v for k,v in llm.items() if k != 'profiles'} | llm['profiles'][name] | {'backend':name})


@dataclass(frozen=True)
class BackendResult:
    text: str
    usage: dict = field(default_factory=dict)
    parameters: dict = field(default_factory=dict)
    finish_reason: str = 'stop'
    prepared_plan: object = None
    generation_performed: bool = True
    web_expired: bool = False
    response_to_seq: int | None = None
    memory_proposals: tuple = ()
    memory_aux: dict = field(default_factory=dict)
    web_evidence: tuple = ()


def numeric_usage(value):
    allowed = ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens',
               'inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens',
               'prompt_eval_count','eval_count','total_duration','load_duration','prompt_eval_duration','eval_duration')
    return {k:v for k,v in value.items() if k in allowed and type(v) is int and 0 <= v <= 2**63-1} if isinstance(value,dict) else {}


def create_runner(root, settings, budget):
    cfg = resolve_backend(settings)
    if cfg['backend'] == 'codebuddy_cli':
        from .workbuddy_cli_runner import CLIRunner
        runner = CLIRunner(root,cfg['model'],cfg['run_timeout_seconds'],cfg['cleanup_seconds'],cfg['reasoning_effort'],budget)
    else:
        from .ollama_ssh_runner import OllamaSSHRunner
        runner = OllamaSSHRunner(root,cfg,budget,settings['output'])
    runner.native_web=cfg['backend']=='codebuddy_cli' and settings.get('web',{}).get('engine')=='codebuddy_cli'
    runner.web_config=deepcopy(settings.get('web',{}))
    runner.web_private_ids=[settings['bot']['qq']]+sum((settings['access'][k] for k in ('allowed_groups','admin_users','blocked_users')),[]) if runner.native_web else []
    if runner.native_web:
        from .wechat_materials import private_ids
        runner.web_private_ids+=private_ids()
    runner.vision_settings = deepcopy(settings)
    return runner
