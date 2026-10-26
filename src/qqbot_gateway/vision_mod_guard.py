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
    def __init__(self, work, system, prompt, image, terms, *, mode='live',denied_tools=None,wire_message=None):
        import base64
        if wire_message is None:
            wire_message=dict(type='user',message=dict(role='user',content=[dict(type='text',text=prompt),
                dict(type='image',source=dict(type='base64',media_type=image.mime,data=base64.b64encode(image.data).decode()))]))
        wire=(json.dumps(wire_message,ensure_ascii=False,separators=(',',':'))+'\n').encode()
        wire_path=Path(work)/'native-user.json';wire_path.write_bytes(wire)
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
        self.receipt_root=Path(work)/'vision-receipts';self.receipt_root.mkdir()
        self.receipt = self.receipt_root / 'receipt.json'
        self.request = dict(schema=2, nonce=secrets.token_hex(32), root=str(self.root.resolve()),
            receipt=str(self.receipt.resolve()),receipt_root=str(self.receipt_root.resolve()), system=system, prompt=prompt,
            system_sha256=sha(system.encode()), system_bytes=len(system.encode()),
            prompt_sha256=sha(prompt.encode()), image_sha256=image.sha256,
            wire_path=str(wire_path.resolve()),wire_sha256=sha(wire),
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
        phase_names={'context_cleared','composed','refused','admitted','probe_short_circuit','next','completed'}
        phases=list(self.receipt_root.glob('phase-*.json'))
        if len(phases)>128:raise ValueError('VISION_PLUGIN_RECEIPT_COUNT')
        stages=['ready'];calls=0
        for path in phases:
            if path.is_symlink() or path.stat().st_size>16384:raise ValueError('VISION_PLUGIN_PHASE_INVALID')
            try:row=json.loads(path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:continue
            if row.get('nonce')!=self.request['nonce'] or row.get('stage') not in phase_names:
                raise ValueError('VISION_PLUGIN_PHASE_IDENTITY')
            stages.append(row['stage'])
            for key in ('reason','hook_error','diagnostic','registered_tools','catalog_tools','transcript_verified'):
                if key in row:value[key]=row[key]
            if row['stage']=='next':calls=1
        value['stages']=stages;value['next_calls']=calls
        keys = ('nonce', 'system_sha256', 'system_bytes', 'assets_sha256', 'model', 'effort', 'mode')
        mismatches=[k for k in keys if value.get(k) != self.request[k]]
        canonical=json.dumps(self.request,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        if value.get('request_sha256') != sha(canonical):mismatches.append('request_sha256')
        if mismatches:
            raise ValueError('VISION_PLUGIN_RECEIPT_MISMATCH:'+','.join(mismatches))
        if not isinstance(value.get('stages'), list) or 'ready' not in value['stages']:
            raise ValueError('VISION_PLUGIN_NOT_READY')
        if value.get('wire_verified') is not True:
            raise ValueError('VISION_PLUGIN_WIRE_UNVERIFIED')
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

    def preserve_probe(self, destination):
        import shutil
        destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
        total=0
        paths=[*(self.root/name for name in FILES),self.receipt,*(self.receipt_root.glob('phase-*.json'))]
        for path in paths:
            if not path.is_file() or path.is_symlink():continue
            total+=path.stat().st_size
            if total>4*1024*1024:raise ValueError('PROBE_EVIDENCE_TOO_LARGE')
            target=destination/('plugin' if path.is_relative_to(self.root) else 'receipts')/path.name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        return str(destination)


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
    """Only explicit fixed seven-total reauthorization accounts for the prior one.

    The original quarantine remains. A newly changed marker invalidates this
    accounting immediately; no log, config force flag or new batch can clear it.
    """
    from .vision_capabilities import read_json
    root=Path(root);marker=root/'state/vision-evidence/lap42-cli-probe-unknown.json'
    if not marker.exists():return False
    try:
        grant=read_json(root/'state/vision-evidence/lap42-native-authorization.json')
        expected=dict(schema_version=1,authorization='USER_CONFIRMED_7_TOTAL_WITH_SIX_FIXED_CASES',
            previous_real_requests=1,max_local_real_requests=7,fixed_batch='lap42-vision-closure-v2',
            max_group_generations=2,backend='codebuddy_cli',model='deepseek-v4.1-flash',effort='low',
            prior_marker_sha256=sha(marker.read_bytes()))
        fixed={k:v for k,v in expected.items() if k!='prior_marker_sha256'}
        if any(grant.get(k)!=v for k,v in fixed.items()) or grant.get('source')!='explicit_current_conversation':return True
        if grant.get('prior_marker_sha256')==expected['prior_marker_sha256']:return False
        resolution=read_json(root/'state/vision-evidence/lap42-zero-generation-resolution.json')
        if resolution.get('marker_sha256')!=expected['prior_marker_sha256']:return True
        marker_value=read_json(marker)
        journal=root/'state/lap42-vision-closure'/marker_value['journal']
        if sha(journal.read_bytes())!=resolution.get('journal_sha256'):return True
        rows=read_json(journal);proof=rows[0].get('guard_observed') or {}
        if proof:
            if proof.get('mode')!='probe' or proof.get('next_calls')!=0 or proof.get('wire_verified') is not True:return True
        elif rows[0].get('users')!=1 or rows[0].get('error')!='PROTOCOL_ERROR':return True
        log=Path(resolution['log_path']);text=log.read_text(encoding='utf-8')
        if not log.name.startswith('lap42-probe-None-') or sha(log.read_bytes())!=resolution.get('log_sha256'):return True
        return ('[ModelProvider]' in text or 'qua.enqueue:' in text or 'hook on turn.step throw' in text or
                'responses=0, items=0, input=1' not in text or '[ProcessExit] exit | code=0' not in text)
    except (OSError,ValueError,TypeError,KeyError):return True
