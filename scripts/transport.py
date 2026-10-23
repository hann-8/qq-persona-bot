"""Read-only transport evidence diagnostics; no installation or activation."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main(argv=None):
    from qqbot_gateway.config_files import read_project
    from qqbot_gateway.qq_transport import inspect_transport
    parser = argparse.ArgumentParser(description='QQ传输静态检查；不启停、不联网、不读凭据')
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('command', choices=('inspect',))
    parser.add_argument('--json', action='store_true', help='封闭JSON输出（当前默认）；不输出秘密或路径')
    args = parser.parse_args(argv)
    try:
        config = read_project(args.root)
        result = inspect_transport(args.root, config.settings)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, AttributeError, RecursionError):
        # Neither malformed YAML nor arbitrary file names/values are diagnostics.
        print(json.dumps(dict(error='transport_config_invalid', static_only=True, channel_ready=False)))
        return 1


if __name__ == '__main__':raise SystemExit(main())
