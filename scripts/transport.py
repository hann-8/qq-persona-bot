"""Explicit transport operator commands; production qualification remains closed."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main(argv=None):
    from qqbot_gateway.config_files import read_project
    from qqbot_gateway.qq_transport import inspect_transport
    parser = argparse.ArgumentParser(description='QQ传输受管操作；不安装或复制原生组件')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('command', choices=('inspect','prepare-policy','verify','activate','capability-probe','trial-start','trial-status','rollback'))
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--provider',choices=('snowluma',))
    parser.add_argument('--authorize-owned-qq',action='store_true')
    parser.add_argument('--timeout',type=int,default=240)
    parser.add_argument('--json', action='store_true', help='封闭JSON输出（当前默认）；不输出秘密或路径')
    args = parser.parse_args(argv)
    try:
        from qqbot_gateway import transport_cli as operations
        if args.command=='inspect':result=inspect_transport(args.root,read_project(args.root).settings)
        elif args.command=='prepare-policy':result=operations.prepare(args.root)
        elif args.command=='verify':
            if not args.offline:raise ValueError('VERIFY_REQUIRES_OFFLINE')
            result=operations.offline(args.root)
        elif args.command=='activate':
            if args.provider!='snowluma':raise ValueError('ACTIVATE_PROVIDER_REQUIRED')
            result=operations.activate(args.root)
        elif args.command=='capability-probe':
            if not args.authorize_owned_qq or not 1<=args.timeout<=240:raise ValueError('PROBE_AUTHORIZATION_REQUIRED')
            result=operations.blocked_runtime(args.root)
        elif args.command=='trial-start':result=operations.trial_start(args.root)
        elif args.command=='trial-status':
            from qqbot_gateway.transport_trial import status
            result=status(args.root)
        else:result=operations.rollback(args.root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, AttributeError, RecursionError) as error:
        # Neither malformed YAML nor arbitrary file names/values are diagnostics.
        from qqbot_gateway.transport_owner import TransportBlocked
        allowed={'PREPARE_ALREADY_STARTED','CONTROL_SECRET_EXISTS','CANDIDATE_SOURCE_CHANGED','CONFIG_SOURCE_CHANGED',
            'ACTIVATION_EXISTS','PROVIDER_ALREADY_SELECTED','CONFIG_EDIT_UNSUPPORTED','ROLLBACK_UNKNOWN','ROLLBACK_LAYOUT_CHANGED',
            'ROLLBACK_OWNED_FIELD_CHANGED','VERIFY_REQUIRES_OFFLINE','ACTIVATE_PROVIDER_REQUIRED','PROBE_AUTHORIZATION_REQUIRED',
            'TRIAL_PROVIDER_NOT_SELECTED','TRIAL_ALREADY_REQUESTED','TRIAL_MANAGEMENT_ROOT_UNKNOWN','OFFLINE_FIXTURE_FAILED',
            'RECOVERY_ALREADY_PREPARED','RECOVERY_LEDGER_UNKNOWN'}
        allowed|={'CONFIG_EDIT_SEMANTICS_CHANGED','TRIAL_START_SOURCE_CHANGED','TRIAL_START_UNKNOWN','TRIAL_STOP_UNKNOWN','TRIAL_STOP_INSTANCE_CHANGED'}
        reason=str(error) if str(error) in allowed else 'transport_config_invalid'
        if isinstance(error,TransportBlocked):
            reason='runtime_qualification_blocked'
        result=dict(error=reason,static_only=True,channel_ready=False)
        if isinstance(error,TransportBlocked):
            codes={'official_bundle_missing','clean_qq_missing','transport_path_unsafe','static_proof_missing','static_proof_invalid',
                'static_evidence_mismatch','native_deployment_unverified','clean_qq_unverified','data_scope_unverified',
                'private_build_unverified','operator_scan_required','private_runtime_entry_unavailable'}
            result['blockers']=[code for code in error.codes if code in codes]
            result['private_runtime_entry_available']=False
        print(json.dumps(result))
        return 1


if __name__ == '__main__':raise SystemExit(main())
