"""Default inspect is local-only; intake-only requires separate human authority."""
import argparse
import asyncio
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]


def inspect(root):
    """Only structure metadata, no locks/writes/ports/network/token read."""
    from qqbot_gateway.config_files import read_project
    cfg=read_project(root).settings
    bundle=root/'runtime/napcat/installer/NapCat.52230.Shell/versions/9.9.33-52230/resources/app/napcat/napcat.mjs'
    # No scan of logs, private credentials or message bodies.
    return dict(schema_version=1,mode='inspect',configuration_loaded=True,
        napcat_bundle_present=bundle.is_file(),vision_enabled=cfg['vision']['enabled'],
        ingress_diagnostics=cfg['vision']['ingress_diagnostics'],get_image_implemented=False,
        ingress_state='ingress_unverified',production_eligible=False,backend_calls=0,qq_outputs=0)


async def synthetic():
    from PIL import Image
    from qqbot_gateway.vision_ingress import observe
    output=io.BytesIO();Image.new('RGB',(12,8),'red').save(output,format='PNG');raw=output.getvalue()
    base=dict(self_id=222,group_id=111,user_id=333,message_id=1)
    async def fetch(url):return raw
    events=({'type':'image','data':{'file':'opaque-fixture'}},
            {'type':'image','data':{'url':'https://gchat.qpic.cn/synthetic'}},
            {'type':'text','data':{'text':'[图片]'}})
    return [await observe(dict(base,message=[segment]),'synthetic',lambda identity:True,fetch=fetch) for segment in events]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--inspect',action='store_true');modes.add_argument('--synthetic',action='store_true')
    modes.add_argument('--intake-only',action='store_true')
    parser.add_argument('--max-events',type=int);parser.add_argument('--timeout-seconds',type=int)
    parser.add_argument('--authorize',choices=('ONE_IMAGE_INGRESS',))
    parser.add_argument('--sample-group');parser.add_argument('--sample-sender')
    args=parser.parse_args(argv)
    if not args.intake_only:
        if any(v is not None for v in (args.authorize,args.sample_group,args.sample_sender,args.max_events,args.timeout_seconds)):
            parser.error('INTAKE_FLAGS_REQUIRE_INTAKE_ONLY')
        value=dict(mode='synthetic',records=asyncio.run(synthetic()),ingress_state='ingress_unverified',production_eligible=False) if args.synthetic else inspect(ROOT)
    else:
        if (args.authorize!='ONE_IMAGE_INGRESS' or args.max_events!=1 or args.timeout_seconds!=120 or
            not args.sample_group or not args.sample_sender):parser.error('EXPLICIT_ONE_SAMPLE_120_SECOND_AUTHORIZATION_REQUIRED')
        from scripts import manage
        value=manage.intake_only(authorize=args.authorize,group=args.sample_group,sender=args.sample_sender,
                                 max_events=args.max_events,timeout_seconds=args.timeout_seconds)
    print(json.dumps(value,ensure_ascii=False,sort_keys=True))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (Exception,KeyboardInterrupt):
        print(json.dumps(dict(state='failed_or_unknown',failure='INTAKE_FAILED',details_suppressed=True)))
        raise SystemExit(1) from None
