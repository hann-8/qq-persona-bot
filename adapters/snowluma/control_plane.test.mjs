import test from 'node:test';
import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { createControlHandler } from './control_plane.mjs';
const binding = { schema: 1, instance_id: 'a'.repeat(32), transport_epoch: 'b'.repeat(64), config_digest: 'c'.repeat(64),
  policy_digest: 'd'.repeat(64), build_hash: 'e'.repeat(64), node: { pid: 12, created: 1700000000000 }, qq: { pid: 13, created: 1700000000001 }, listener_port: 5098 };
const key = Buffer.alloc(32, 107);
const canonical = x => x && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map(k => [k, canonical(x[k])])) : x;
const encode = x => JSON.stringify(canonical(x));
const sign = (action, seq, extra = {}) => {
  const obj = { ...binding, domain: 'qqbot-snowluma-control-v1', action, seq, nonce: String(seq).padStart(64, '0'), issued_ms: 1000, expires_ms: 4000, ...extra };
  return encode({ ...obj, mac: createHmac('sha256', key).update(encode(obj)).digest('hex') });
};
function setup(overrides = {}) {
  let stopped = false, owned = true;const calls = [];
  const handler = createControlHandler({ binding, key, now: () => 1000,
    observe: () => ({ account_match: true, phase: 'ready', pipe_connected: true, logged_in: true, rx_watch_armed: true,
      receive_healthy: true, outbound_healthy: true, last_rx_age_ms: 1 }),
    identityCurrent: () => owned, stopRequested: () => stopped,
    onBind: () => calls.push('bind'), onDrain: () => calls.push('drain'), onStop: () => calls.push('stop'), ...overrides });
  return { handler, calls, stop: () => { stopped = true; }, revoke: () => { owned = false; } };
}
test('fixed bind/health/drain/stop are domain separated and replay resistant', async () => {
  const { handler, calls } = setup();
  const health = () => handler.handle({ method: 'GET', url: '/health?nonce=' + 'f'.repeat(64) });
  assert.equal(JSON.parse((await health()).body).phase, 'starting');
  for (const [action, seq] of [['bind', 1], ['drain', 2], ['stop', 3]]) {
    const request = { method: 'POST', url: '/' + action, body: sign(action, seq) };
    assert.equal((await handler.handle(request)).status, 200);
    assert.equal((await handler.handle(request)).status, 403);
  }
  assert.deepEqual(calls, ['bind', 'drain', 'stop']);assert.equal(JSON.parse((await health()).body).phase, 'stopped');
});
test('bind side effect is once per lease, including concurrent retry and stop race', async () => {
  let release, calls = 0, lease;
  const wait = new Promise(resolve => { release = resolve; });
  const { handler } = setup({ onBind: async current => { calls++;lease = current;await wait; } });
  const first = handler.handle({ method: 'POST', url: '/bind', body: sign('bind', 1) });
  assert.equal((await handler.handle({ method: 'POST', url: '/bind', body: sign('bind', 2) })).status, 403);
  assert.equal((await handler.handle({ method: 'POST', url: '/stop', body: sign('stop', 3) })).status, 200);
  assert.equal(lease(), false);release();assert.equal((await first).status, 403);assert.equal(calls, 1);
  const ready = setup();
  for (const seq of [1, 2]) assert.equal((await ready.handler.handle({ method: 'POST', url: '/bind', body: sign('bind', seq) })).status, 200);
  assert.deepEqual(ready.calls, ['bind']);
});
test('stop marker wins, wrong identity/path/key/domain/unknown/duplicate/oversize rejected', async () => {
  const { handler, stop, revoke, calls } = setup();
  for (const [path, body] of [['/shell', sign('bind', 1)], ['/bind', sign('bind', 1, { domain: 'health' })],
    ['/bind', sign('bind', 1, { node: { pid: 99, created: 1700000000000 } })], ['/bind', sign('bind', 1, { arbitrary: true })],
    ['/bind', '{}'], ['/bind', 'x'.repeat(8193)], ['/bind', '{"seq":1,"seq":1}']]) {
    assert.equal((await handler.handle({ method: 'POST', url: path, body })).status, 403);
  }
  stop();assert.equal((await handler.handle({ method: 'POST', url: '/bind', body: sign('bind', 1) })).status, 403);
  assert.equal((await handler.handle({ method: 'POST', url: '/stop', body: sign('stop', 2) })).status, 200);
  revoke();assert.equal((await handler.handle({ method: 'GET', url: '/health?nonce=' + 'f'.repeat(64) })).status, 403);
  assert.deepEqual(calls, ['stop']);assert.doesNotMatch(JSON.stringify(handler.status()), /pid|key|QQ|token/);
});
