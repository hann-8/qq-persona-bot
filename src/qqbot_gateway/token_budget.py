"""Conservative visible-text budget. UTF-8 bytes are not model token measurements."""
from dataclasses import dataclass
import json

from .errors import GatewayError
from .session_queue import trim_history


def dialog_text(dialog):
    return json.dumps(dialog, ensure_ascii=False, separators=(',', ':'))


def user_message(prompt):
    return {'type':'user', 'message':{'role':'user', 'content':prompt}}


@dataclass(frozen=True)
class InputBudget:
    limit: int = 16384
    overhead: int = 2048
    output: int = 2048
    history_turns: int = 8
    max_input: int | None = None
    window: int | None = None
    native_profile: dict | None = None
    vision_kind: str | None = None

    @classmethod
    def from_settings(cls, settings, metadata=None):
        from .backends import resolve_backend
        chat = resolve_backend(settings)['input_budget']
        metadata = metadata or {}
        cfg = resolve_backend(settings)
        return cls(chat['context_input_limit_tokens'], chat['context_overhead_reserve_tokens'],
                   chat['output_reserve_tokens'], settings['chat']['history_turns'], metadata.get('maxInputTokens'),
                   cfg.get('num_ctx'),cfg if cfg['backend']=='ollama_ssh' else None,
                   _vision_kind(cfg))

    @property
    def payload_limit(self):
        return min(8*1024*1024, max(512*1024, 8*self.limit))

    def validate_capacity(self):
        if ((self.max_input is not None and self.limit > self.max_input) or
                (self.window is not None and self.limit+self.output > self.window)):
            raise ValueError('Input budget/output reserve exceeds known model capacity')

    def usage(self, system, prompt):
        if self.native_profile is not None:
            from .ollama_ssh_runner import native_payload
            return len(json.dumps(native_payload(self.native_profile,system,prompt),ensure_ascii=False,allow_nan=False).encode('utf-8'))+self.overhead
        envelope = json.dumps(user_message(prompt), ensure_ascii=False, separators=(',', ':'))
        return len(system.encode('utf-8')) + len(envelope.encode('utf-8')) + self.overhead

    def check(self, system, prompt):
        self.validate_capacity()
        if self.usage(system, prompt) > self.limit:
            raise GatewayError('INPUT_TOO_LONG')

    def select_history(self, system, question, history):
        current = {'role':'user', 'content':question}
        self.check(system, dialog_text([current]))
        # Remove polluted/orphan turns first, then trim oldest whole pairs by exact wire size.
        pairs = trim_history(history, turns=self.history_turns-1, char_limit=self.payload_limit)
        while self.usage(system, dialog_text(pairs+[current])) > self.limit:
            pairs = pairs[2:]
        return pairs


def known_models():
    from pathlib import Path
    path = Path(__file__).resolve().parents[2]/'config/cli-capabilities.json'
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    lock=json.loads((path.parent/'versions.lock.json').read_text(encoding='utf-8'))
    if data.get('bundle_sha256') != lock['cli']['headless_sha256'] or data.get('cli_version') != lock['cli']['version']:
        return {}
    return {model['id']:model for model in data['models']}


def validate_model_settings(settings, models=None, backend=None):
    models = known_models() if models is None else models
    from .backends import resolve_backend
    llm = resolve_backend(settings,backend)
    if llm['backend'] == 'ollama_ssh':return {}
    model = models.get(llm['model'], {})
    if llm.get('context_window_tokens') is not None:
        raise ValueError('Native context window has not been verified for this CLI; use input budget')
    effort = llm.get('reasoning_effort', 'auto')
    if effort != 'auto' and effort not in model.get('reasoning', {}).get('supportedEfforts', []):
        raise ValueError('Requested effort is unsupported or capability is unknown for this model')
    cfg = dict(settings, llm=dict(settings['llm'],backend='codebuddy_cli'))
    InputBudget.from_settings(cfg, model).validate_capacity()
    return model


def _vision_kind(cfg):
    # Unit selection only; this does not grant source/identity/quality eligibility.
    from .hosted_cli_budget import KIND, matches_profile
    return KIND if matches_profile(cfg) else None
