"""Bounded independent Snow health protocol. No listeners or process mutations.

The owner supplies an already verified binding and an identity/registry/listener
check. A signed boolean alone never establishes ownership or runtime readiness.
"""
from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import secrets
import time

LIMIT = 8192
FIELDS = frozenset(('schema', 'instance_id', 'transport_epoch', 'config_digest', 'policy_digest',
    'build_hash', 'node', 'qq', 'listener_port', 'account_match', 'phase', 'pipe_connected',
    'logged_in', 'rx_watch_armed', 'receive_healthy', 'outbound_healthy', 'last_rx_age_ms',
    'seq', 'nonce', 'mac'))
FLAGS = ('account_match', 'pipe_connected', 'logged_in', 'rx_watch_armed', 'receive_healthy', 'outbound_healthy')
PHASES = ('starting', 'ready', 'draining', 'stopped', 'failed')


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')


def strict_json(content, limit=LIMIT):
    if not isinstance(content, (bytes, str)) or len(content.encode() if isinstance(content, str) else content) > limit:
        raise ValueError('HEALTH_INVALID')
    def pairs(rows):
        obj = {}
        for key, value in rows:
            if key in obj:raise ValueError('HEALTH_INVALID')
            obj[key] = value
        return obj
    def constant(_):raise ValueError('HEALTH_INVALID')
    return json.loads(content, object_pairs_hook=pairs, parse_constant=constant)


def _hex(value, length):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{'+str(length)+'}', value) is not None


def identity(value):
    if (not isinstance(value, dict) or set(value) != {'pid', 'created'} or
        type(value['pid']) is not int or not 0 < value['pid'] <= 2147483647 or
        type(value['created']) is not int or not 0 < value['created'] <= 9007199254740991):
        raise ValueError('HEALTH_INVALID')
    # Unix creation time in integer milliseconds: stable cross-language canonical JSON.
    return dict(value)


@dataclass(frozen=True)
class HealthBinding:
    instance_id: str
    transport_epoch: str
    config_digest: str
    policy_digest: str
    build_hash: str
    node_pid: int
    node_created: int
    qq_pid: int
    qq_created: int
    listener_port: int

    def __post_init__(self):
        if not _hex(self.instance_id, 32) or any(not _hex(getattr(self, f), 64) for f in
            ('transport_epoch', 'config_digest', 'policy_digest', 'build_hash')):raise ValueError('HEALTH_BINDING_INVALID')
        identity(self.node);identity(self.qq)
        if type(self.listener_port) is not int or not 1 <= self.listener_port <= 65535:raise ValueError('HEALTH_BINDING_INVALID')

    @property
    def node(self):return dict(pid=self.node_pid, created=self.node_created)

    @property
    def qq(self):return dict(pid=self.qq_pid, created=self.qq_created)

    def fields(self):
        return dict(schema=1, instance_id=self.instance_id, transport_epoch=self.transport_epoch,
            config_digest=self.config_digest, policy_digest=self.policy_digest, build_hash=self.build_hash,
            node=self.node, qq=self.qq, listener_port=self.listener_port)


def validate_message(obj):
    if not isinstance(obj, dict) or set(obj) != FIELDS or type(obj['schema']) is not int or obj['schema'] != 1:
        raise ValueError('HEALTH_INVALID')
    if not _hex(obj['nonce'], 64) or not _hex(obj['mac'], 64):raise ValueError('HEALTH_INVALID')
    if not _hex(obj['instance_id'],32) or any(not _hex(obj[k],64) for k in
        ('transport_epoch','config_digest','policy_digest','build_hash')):raise ValueError('HEALTH_INVALID')
    if type(obj['listener_port']) is not int or not 1<=obj['listener_port']<=65535:raise ValueError('HEALTH_INVALID')
    for flag in FLAGS:
        if type(obj[flag]) is not bool:raise ValueError('HEALTH_INVALID')
    if obj['phase'] not in PHASES:raise ValueError('HEALTH_INVALID')
    if type(obj['seq']) is not int or not 0 < obj['seq'] <= 9007199254740991:raise ValueError('HEALTH_INVALID')
    if type(obj['last_rx_age_ms']) is not int or not 0 <= obj['last_rx_age_ms'] <= 2147483647:raise ValueError('HEALTH_INVALID')
    identity(obj['node']);identity(obj['qq'])
    return obj


class HealthProducer:
    """Fixed producer interface; observations must come from private early wiring."""
    def __init__(self, binding, key):
        if not isinstance(binding, HealthBinding) or not isinstance(key, bytes) or len(key) != 32:raise ValueError('HEALTH_KEY_INVALID')
        self.binding, self.key, self.seq = binding, key, 0

    def response(self, nonce, observation):
        if not _hex(nonce, 64) or not isinstance(observation, dict) or set(observation) != set(FLAGS) | {'phase', 'last_rx_age_ms'}:
            raise ValueError('HEALTH_INVALID')
        self.seq += 1
        obj = self.binding.fields() | observation | dict(seq=self.seq, nonce=nonce, mac='0'*64)
        validate_message(obj)
        obj['mac'] = hmac.new(self.key, canonical({k:v for k,v in obj.items() if k != 'mac'}), hashlib.sha256).hexdigest()
        content = canonical(obj)
        if len(content) > LIMIT:raise ValueError('HEALTH_INVALID')
        return content


class HealthVerifier:
    def __init__(self, binding, key, identity_current, *, ttl=15, clock=time.monotonic):
        if (not isinstance(binding, HealthBinding) or not isinstance(key, bytes) or len(key) != 32 or
            not callable(identity_current) or type(ttl) is not int or not 15 <= ttl <= 30):raise ValueError('HEALTH_BINDING_INVALID')
        self.binding, self.key, self.identity_current = binding, key, identity_current
        self.ttl, self.clock = ttl, clock
        self.nonce = None;self.challenge_at = None;self.seq = 0
        self.expires = 0.;self.trusted = False;self.observation = None

    def challenge(self):
        self.nonce = secrets.token_hex(32);self.challenge_at = self.clock()
        return self.nonce

    def invalidate(self):
        self.trusted = False;self.expires = 0.;self.observation = None

    def _identity_current(self):
        try:return self.identity_current(self.binding) is True
        except Exception:return False  # closed, never expose OS/registry exception text

    def accept(self, content):
        now = self.clock()
        try:
            obj = validate_message(strict_json(content))
            if self.nonce is None or obj['nonce'] != self.nonce or not 0 <= now-self.challenge_at <= 3:
                raise ValueError()
            if any(obj[k] != v for k,v in self.binding.fields().items()) or obj['seq'] <= self.seq:raise ValueError()
            body = canonical({k:v for k,v in obj.items() if k != 'mac'})
            if not hmac.compare_digest(obj['mac'], hmac.new(self.key, body, hashlib.sha256).hexdigest()) or not self._identity_current():raise ValueError()
            self.seq = obj['seq'];self.expires = self.challenge_at+self.ttl
            self.observation = {k:obj[k] for k in FLAGS+('phase', 'last_rx_age_ms')}
            self.trusted = True
            return True
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
            self.invalidate();return False
        finally:self.nonce = None;self.challenge_at = None

    def ready(self):
        remaining = self.expires-self.clock()
        if not self.trusted or not 0 < remaining <= self.ttl or not self._identity_current():
            self.invalidate();return False
        o = self.observation
        return o['phase'] == 'ready' and all(o[k] is True for k in FLAGS) and o['last_rx_age_ms'] <= 105000

    def safe_status(self):
        ready=self.ready()
        return dict(trusted=self.trusted, ready=ready, sequence=self.seq,
                    armed=bool(self.observation and self.observation['rx_watch_armed']))

    def mirror(self):
        ready = self.ready()
        return dict(ready=ready, expires_mono=self.expires if ready else 0., sequence=self.seq)
