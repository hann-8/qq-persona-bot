import test from 'node:test';
import assert from 'node:assert/strict';
import { createProjectPolicy, createHealthProducer } from './project_policy.mjs';

const envelope = (patch = {}) => ({ instance_id: 'a'.repeat(32), transport_epoch: 'b'.repeat(64),
  self_id: '222', group_id: '111', user_id: '333', message_id: '-12', time: 1700000000, post_type: 'message', message_type: 'group',
  message: [{ type: 'text', data: { text: '#sl hello' } }], ...patch });
const setup = () => {
  let now = 0, owned = true;
  const policy = createProjectPolicy({ instanceId: 'a'.repeat(32), transportEpoch: 'b'.repeat(64), bot: '222',
    allowedGroups: ['111'], blockedUsers: ['999'], identityCurrent: () => owned, clock: () => now });
  return { policy, advance: x => { now += x; }, revoke: () => { owned = false; } };
};

test('reject before all external callbacks and metadata; identity and account strict', () => {
  const { policy, revoke } = setup(); let calls = 0;
  const forward = () => { ++calls; };
  for (const patch of [{ message_type: 'private' }, { group_id: '444' }, { user_id: '999' }, { user_id: '222' },
    { self_id: '444' }, { user_id: true }, { message_id: 0 }, { transport_epoch: 'c'.repeat(64) },
    { instance_id: 'd'.repeat(32) }, { message: [{ type: 'text', data: { text: 'x'.repeat(8193) } }] }]) {
    assert.equal(policy.process(envelope(patch), forward), false);
    assert.equal(policy.remember(envelope(patch), 'media'), false);
  }
  revoke(); assert.equal(policy.process(envelope(), forward), false);
  assert.equal(calls, 0); assert.equal(policy.status().current.entries, 0);
});

test('quotes/forwards/media never expand, no built-in #sl reply or raw logger', () => {
  const { policy } = setup(); const rows = [];
  const e = envelope({ raw_message: 'PRIVATE_RAW', sender: { nickname: 'PRIVATE_NAME' }, message: [
    { type: 'text', data: { text: '#sl' } },
    { type: 'reply', data: { id: '17', content: 'PRIVATE_QUOTE' } },
    { type: 'forward', data: { content: 'PRIVATE_FORWARD' } },
    { type: 'image', data: { url: 'https://private.invalid/image' } },
  ] });
  assert.equal(policy.process(e, row => rows.push(row)), true);
  assert.equal(rows.length, 1); // one current-event forward, zero automatic response API
  assert.equal(rows[0].message[0].data.text, '#sl');
  assert.equal(rows[0].message[1].data.id, '17');
  assert.doesNotMatch(JSON.stringify(rows), /PRIVATE/);
  assert.equal(rows[0].time, 1700000000);
  assert.deepEqual(rows[0].message[3], { type: 'image', data: { url: 'https://private.invalid/image' } });
  assert.doesNotMatch(JSON.stringify(policy.status()), /222|111|333|#sl|PRIVATE/);
  for (const action of ['get_msg', 'get_group_msg_history', 'get_friend_msg_history', 'get_forward_msg', '#sl', 'login']) {
    assert.equal(policy.allowsRpc(action), false);
  }
});

test('native envelope rejects before convert/store/log/backfill and invalid at never becomes all', () => {
  const { policy } = setup();let calls = 0;
  const native = envelope();delete native.message;
  assert.equal(policy.admitEnvelope(native), true);
  assert.equal(policy.processEnvelope({ ...native, user_id: '999' }, () => { ++calls; }, () => { ++calls; }), false);
  assert.equal(calls, 0);assert.equal(policy.status().current.entries, 0);
  const rows = [];
  assert.equal(policy.processEnvelope(native, () => ({ time: native.time, message: [
    { type: 'at', data: { qq: false } }, { type: 'at', data: { qq: 'all' } },
    { type: 'at', data: { qq: '222' } }, { type: 'text', data: { text: 'hello' } },
  ] }), row => rows.push(row)), true);
  assert.deepEqual(rows[0].message.filter(p => p.type === 'at').map(p => p.data.qq), ['all', '222']);
  assert.equal(policy.process(envelope({ message_id: '-00012' }), row => assert.equal(row.message_id, '-12')), true);
});

test('actual aggregate RAM bound and TTL for all metadata kinds; no disk fallback', () => {
  const { policy, advance } = setup();
  for (let i = 1; i <= 900; i++) {
    const e = envelope({ message_id: String(i) });
    for (const kind of ['message', 'media', 'reaction', 'temp', 'rkey']) assert.equal(policy.remember(e, kind), true);
    policy.correlateSend('111', String(i));
  }
  const s = policy.status();
  assert.equal(s.current.entries, 512); assert.ok(s.current.bytes <= 2 * 1024 * 1024);
  assert.equal(s.sends.entries, 128); assert.ok(s.sends.bytes <= 128 * 512);
  advance(300000); assert.equal(policy.status().current.entries, 0);
  assert.equal(policy.status().sends.entries, 128);
  advance(300000); assert.deepEqual(policy.status().sends, { entries: 0, bytes: 0 });
});

test('clock rollback clears prior metadata and revocation denies new sends', () => {
  const { policy, advance, revoke } = setup();
  policy.process(envelope(), () => {});advance(-1);
  assert.equal(policy.status().current.entries, 0);
  revoke();assert.equal(policy.correlateSend('111', '12'), false);
  policy.clear();assert.equal(policy.status().sends.entries, 0);
});

test('producer emits fixed bound canonical proof; unknown observation rejected', () => {
  const binding = { schema: 1, instance_id: 'a'.repeat(32), transport_epoch: 'b'.repeat(64), config_digest: 'c'.repeat(64),
    policy_digest: 'd'.repeat(64), build_hash: 'e'.repeat(64), node: { pid: 12, created: 1700000000000 },
    qq: { pid: 13, created: 1700000000001 }, listener_port: 5098 };
  const p = createHealthProducer(binding, Buffer.alloc(32, 107));
  const o = { account_match: true, phase: 'ready', pipe_connected: true, logged_in: true,
    rx_watch_armed: true, receive_healthy: true, outbound_healthy: true, last_rx_age_ms: 1 };
  const first = JSON.parse(p.response('f'.repeat(64), o));
  assert.equal(first.seq, 1);assert.equal(first.node.created, 1700000000000);
  assert.equal(first.mac.length, 64);assert.ok(Buffer.byteLength(JSON.stringify(first)) < 8192);
  assert.equal(JSON.parse(p.response('0'.repeat(64), o)).seq, 2);
  assert.throws(() => p.response('f'.repeat(64), { ...o, valid: true }));
  assert.throws(() => p.response('f'.repeat(64), { ...o, last_rx_age_ms: NaN }));
});
