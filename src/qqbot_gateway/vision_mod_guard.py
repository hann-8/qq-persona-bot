"""Project-owned, per-process Mod assets and private request attestations."""
import asyncio
import hashlib
import json
from pathlib import Path
import secrets
import time

ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = 'adapters/codebuddy_vision_guard'
FILES = ('.codebuddy-plugin/plugin.json', 'hooks/hooks.json', 'hooks/register.ts')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def assets():
    return {name: sha((ROOT / ASSET_ROOT / name).read_bytes()) for name in FILES}


def assets_signature():
    return sha(json.dumps(assets(), sort_keys=True, separators=(',', ':')).encode())


class Guard:
    def __init__(self, work, system, prompt, image, terms, *, mode='live',denied_tools=None):
        self.root = Path(work) / 'vision-plugin'
        self.root.mkdir()
        source = assets()
        for name, expected in source.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            data = (ROOT / ASSET_ROOT / name).read_bytes()
            if sha(data) != expected:
                raise ValueError('VISION_PLUGIN_ASSET_CHANGED')
            target.write_bytes(data)
        self.receipt = self.root / 'receipt.json'
        self.request = dict(schema=2, nonce=secrets.token_hex(32), root=str(self.root.resolve()),
            receipt=str(self.receipt.resolve()), system=system, prompt=prompt,
            system_sha256=sha(system.encode()), system_bytes=len(system.encode()),
            prompt_sha256=sha(prompt.encode()), image_sha256=image.sha256,
            assets={k:v for k,v in source.items() if k != FILES[0]}, assets_sha256=assets_signature(), model='deepseek-v4.1-flash',
            denied_tools=denied_tools if denied_tools is not None else json.loads((ROOT/'config/cli-tools-denied.json').read_text(encoding='utf-8')),
            effort='low', mode=mode, deadline=int((time.time()+180)*1000), **terms)
        self.serialized = json.dumps(self.request, ensure_ascii=False, separators=(',', ':'))
        manifest_path = self.root / FILES[0]
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        # A per-request default, never user/global settings; static source hashes
        # exclude this derived manifest, whose independent hash is also checked.
        manifest['userConfig']['request']['default'] = self.serialized
        manifest['options'] = {'request': self.serialized}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        self.manifest_hash = sha(manifest_path.read_bytes())

    def read(self):
        if sha((self.root / FILES[0]).read_bytes()) != self.manifest_hash:
            raise ValueError('VISION_PLUGIN_MANIFEST_CHANGED')
        for name, expected in self.request['assets'].items():
            if name != FILES[0] and sha((self.root / name).read_bytes()) != expected:
                raise ValueError('VISION_PLUGIN_ASSET_CHANGED')
        if self.receipt.is_symlink() or self.receipt.stat().st_size > 16384:
            raise ValueError('VISION_PLUGIN_RECEIPT_INVALID')
        value = json.loads(self.receipt.read_text(encoding='utf-8'))
        keys = ('nonce', 'system_sha256', 'system_bytes', 'assets_sha256', 'model', 'effort', 'mode')
        mismatches=[k for k in keys if value.get(k) != self.request[k]]
        canonical=json.dumps(self.request,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        if value.get('request_sha256') != sha(canonical):mismatches.append('request_sha256')
        if mismatches:
            raise ValueError('VISION_PLUGIN_RECEIPT_MISMATCH:'+','.join(mismatches))
        if not isinstance(value.get('stages'), list) or 'ready' not in value['stages']:
            raise ValueError('VISION_PLUGIN_NOT_READY')
        return value

    async def ready(self, timeout):
        async with asyncio.timeout(timeout):
            while True:
                if self.receipt.exists():
                    try:return self.read()
                    except json.JSONDecodeError:pass  # host fs.write may still be completing
                await asyncio.sleep(.025)

    def finish(self):
        value = self.read()
        required = {'ready', 'composed', 'context_cleared',
                    'probe_short_circuit' if self.request['mode'] == 'probe' else 'completed'}
        calls = 0 if self.request['mode'] == 'probe' else 1
        if (not required.issubset(value['stages']) or 'refused' in value['stages'] or
                value.get('next_calls') != calls or value.get('transcript_verified') is not True):
            raise ValueError('VISION_PLUGIN_TURN_REJECTED')
        return value


def probe_valid(root, settings):
    """A real CLI probe is a separate prerequisite, never an IQ prerequisite of itself."""
    from .vision import binding
    from .vision_capabilities import read_json, runtime_identity
    try:
        item = read_json(Path(root)/'state/vision-evidence/lap42-cli-probe.json')
        import re
        name=item.get('journal','')
        if not isinstance(name,str) or not re.fullmatch('probe-[a-f0-9]{32}\\.json',name):return False
        journal=Path(root)/'state/lap42-vision-closure'/name
        rows=read_json(journal)
        if sha(journal.read_bytes())!=item.get('journal_sha256') or not isinstance(rows,list) or len(rows)!=3:return False
        if ([r.get('fault') for r in rows]!=[None,'missing_plugin','wrong_receipt'] or
            any(r.get('state')!='verified' for r in rows) or
            [r.get('users') for r in rows]!=[1,0,0]):return False
        proof=rows[0]['result']['guard']
        if (proof.get('mode')!='probe' or proof.get('next_calls')!=0 or proof.get('transcript_verified') is not True or
            not {'ready','composed','context_cleared','probe_short_circuit'}.issubset(proof.get('stages',[])) or
            'refused' in proof.get('stages',[]) or proof.get('assets_sha256')!=assets_signature()):return False
        return (not probe_unknown_unresolved(root) and
                item.get('binding') == binding(settings, runtime_identity(Path(root), settings)) and
                item.get('assets_signature') == assets_signature() and item.get('passed') is True and
                item.get('positive_local_users') == 1 and item.get('positive_next_calls') == 0 and
                item.get('negative_users') == [0, 0] and item.get('real_generations') == 0)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def probe_unknown_unresolved(root):
    """Unexpected generation is quarantined; never auto-clear it from other logs."""
    return (Path(root)/'state/vision-evidence/lap42-cli-probe-unknown.json').exists()
