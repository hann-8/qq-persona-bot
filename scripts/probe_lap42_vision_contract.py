"""Actual locked CLI Mod contract probe. One local user, zero remote generations.

Requires stopped project. Negative cases withhold user. No IQ/production gate.
"""
import argparse
import asyncio
import io
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]


async def probe(root,settings,journal):
    from PIL import Image
    from qqbot_gateway.backends import create_runner
    from qqbot_gateway.token_budget import InputBudget
    from qqbot_gateway.vision import CURRENT, NativeImage, normalize, binding
    from qqbot_gateway.vision_capabilities import runtime_identity, static_diagnostics
    from qqbot_gateway.vision_mod_guard import assets_signature
    from qqbot_gateway.errors import GatewayError
    missing=static_diagnostics(settings,runtime_identity(root,settings))
    if missing:raise ValueError(','.join(missing))
    out=io.BytesIO();Image.new('RGB',(24,16),'red').save(out,format='PNG')
    blob=normalize(out.getvalue());rows=[]
    from scripts.activate_lap42_vision import atomic
    for fault in (None,'missing_plugin','wrong_receipt'):
        row=dict(fault=fault,state='started',users=0)
        rows.append(row);atomic(journal,json.dumps(rows).encode())
        runner=create_runner(root,settings,InputBudget.from_settings(settings))
        token=CURRENT.set(NativeImage(blob,4096,time.monotonic()+60,time.monotonic()+15))
        try:
            try:
                result=await runner.probe_image_contract('Project policy 中文🙂 {{literal}}\nDo not generate.',
                    'Synthetic local image probe.', 'lap42-probe-'+str(fault),fault=fault)
            except GatewayError as error:
                row.update(state='failed',users=runner.user_messages_sent,error=error.code)
                atomic(journal,json.dumps(rows).encode())
                if runner.user_messages_sent:
                    atomic(root/'state/vision-evidence/lap42-cli-probe-unknown.json',json.dumps(dict(
                        state='unknown',users=runner.user_messages_sent,timestamp=time.time(),journal=journal.name)).encode())
                if not fault or runner.user_messages_sent or runner.last_parameters.get('vision_rejection')!='VISION_PLUGIN_NOT_READY_OR_MISMATCH':
                    raise ValueError('CLI_PROBE_FAILED_OR_GENERATION_UNKNOWN') from error
                result={'rejected':True}
            if fault is None and (not result.get('local_probe') or result['guard']['next_calls']!=0):
                raise ValueError('CLI_PROBE_GENERATION_UNKNOWN')
            row.update(state='verified',users=runner.user_messages_sent,result=result)
            atomic(journal,json.dumps(rows).encode())
        finally:
            CURRENT.reset(token);await runner.cleanup_close()
    value=dict(schema_version=2,binding=binding(settings,runtime_identity(root,settings)),
        assets_signature=assets_signature(),passed=True,positive_local_users=rows[0]['users'],
        positive_next_calls=rows[0]['result']['guard']['next_calls'],negative_users=[r['users'] for r in rows[1:]],
        real_generations=0,stages=rows[0]['result']['guard']['stages'],timestamp=time.time(),
        journal=journal.name,journal_sha256=__import__('hashlib').sha256(journal.read_bytes()).hexdigest())
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true',help='Explicitly run real CLI processes; no remote generation')
    args=parser.parse_args()
    if not args.run:parser.error('--run is required')
    from qqbot_gateway.config import configuration_lock, require_stopped
    from qqbot_gateway.config_files import read_project
    from qqbot_gateway.vision import binding
    from qqbot_gateway.vision_capabilities import runtime_identity
    root=ROOT
    with configuration_lock(root):
        require_stopped(root);settings=read_project(root).settings
        before=binding(settings,runtime_identity(root,settings))
        if (root/'state/vision-evidence/lap42-cli-probe-unknown.json').exists():
            raise ValueError('UNRESOLVED_PROBE_GENERATION')
    # Never hold config lock across runner I/O.
    import uuid
    value=asyncio.run(probe(root,settings,root/'state/lap42-vision-closure'/('probe-'+uuid.uuid4().hex+'.json')))
    with configuration_lock(root):
        require_stopped(root)
        now=read_project(root).settings
        if binding(now,runtime_identity(root,now))!=before:raise ValueError('PROBE_BINDING_CHANGED')
        from scripts.activate_lap42_vision import atomic
        atomic(root/'state/vision-evidence/lap42-cli-probe.json',json.dumps(value).encode())
    print(json.dumps(value,ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
