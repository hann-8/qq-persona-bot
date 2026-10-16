from dataclasses import dataclass
from pathlib import Path
import json
import re
from urllib.parse import urlparse

import yaml


def qq_id(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value)
    return text if re.fullmatch(r'[1-9][0-9]{0,19}', text) else None


@dataclass(frozen=True)
class GateConfig:
    bot_qq: str
    allowed_groups: frozenset[str]
    admin_users: frozenset[str]
    inbound_token: str
    upstream_token: str
    database: Path
    upstream: str = 'ws://127.0.0.1:6199/ws'
    host: str = '127.0.0.1'
    port: int = 6200

    def __post_init__(self):
        if not qq_id(self.bot_qq) or not self.allowed_groups or not self.admin_users:
            raise ValueError('Bot, allowed groups and admins must be nonempty')
        if any(not qq_id(x) for x in self.allowed_groups | self.admin_users):
            raise ValueError('Invalid QQ/group ID')
        if self.host != '127.0.0.1' or not 0 < self.port < 65536:
            raise ValueError('Gate must listen on loopback')
        url = urlparse(self.upstream)
        if (url.scheme != 'ws' or url.hostname != '127.0.0.1' or
                url.path != '/ws' or not url.port or url.username or url.password or url.query or url.fragment):
            raise ValueError('Upstream must be a loopback WS /ws endpoint')
        if any(not isinstance(t, str) or len(t) < 32 for t in (self.inbound_token, self.upstream_token)):
            raise ValueError('Missing local transport token')


def load_gate_config(path):
    path = Path(path).resolve()
    root = path.parent.parent
    data = yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    token_path = (root / data['secrets_file']).resolve()
    if not token_path.is_relative_to(root / 'secrets'):
        raise ValueError('Secrets file must remain in project secrets directory')
    tokens = json.loads(token_path.read_text(encoding='utf-8'))
    if data['access'].get('private_enabled') is not False:
        raise ValueError('Private messages must be disabled')
    groups, admins = data['access']['allowed_groups'], data['access']['admin_users']
    if not isinstance(groups, list) or not isinstance(admins, list):
        raise ValueError('Groups/admins must be explicit lists')
    return GateConfig(
        bot_qq=data['bot']['qq'], allowed_groups=frozenset(groups), admin_users=frozenset(admins),
        inbound_token=tokens['onebot_inbound'], upstream_token=tokens['onebot_upstream'],
        database=root / 'state/gate.sqlite', upstream=data['onebot']['upstream'],
        host=data['onebot']['host'], port=data['onebot']['port'],
    )
