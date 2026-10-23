// Original fixed request handler; deliberately creates no listener or process.
import { createHmac, timingSafeEqual } from 'node:crypto';
import { createHealthProducer } from './project_policy.mjs';
const DOMAIN = 'qqbot-snowluma-control-v1', ACK = 'qqbot-snowluma-control-ack-v1';
const canonical = x => x && typeof x === 'object' && !Array.isArray(x)
  ? Object.fromEntries(Object.keys(x).sort().map(k => [k, canonical(x[k])])) : x;
const encode = x => JSON.stringify(canonical(x));
const hex = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
const mac = (key, x) => createHmac('sha256', key).update(encode(x)).digest('hex');
const equalMac = (a, b) => hex(a) && hex(b) && timingSafeEqual(Buffer.from(a, 'hex'), Buffer.from(b, 'hex'));

export function createControlHandler({ binding, key, observe, identityCurrent, stopRequested,
  onBind, onDrain, onStop, now = Date.now }) {
  const producer = createHealthProducer(binding, key);binding = structuredClone(binding);key = Buffer.from(key);
  if ([observe, identityCurrent, stopRequested, onBind, onDrain, onStop].some(x => typeof x !== 'function')) throw Error('CONTROL_CONFIG_INVALID');
  let bound = false, bindingStarted = false, draining = false, stopped = false, sequence = 0, generation = 0;
  const nonces = new Map();
  const deny = () => ({ status: 403, body: '{"code":"CONTROL_DENIED"}' });
  const owned = () => { try { return identityCurrent() === true; } catch { return false; } };
  const stop = () => { try { return stopped || stopRequested() !== false; } catch { return true; } };
  return Object.freeze({
    async handle({ method, url, body = '' }) {
      try {
        if (typeof body !== 'string' || Buffer.byteLength(body) > 8192 || !owned()) return deny();
        if (method === 'GET' && typeof url === 'string' && /^\/health\?nonce=[a-f0-9]{64}$/.test(url)) {
          if (body) return deny();
          const observation = observe();
          const phase = stop() ? 'stopped' : draining ? 'draining' : !bound ? 'starting' : observation.phase;
          return { status: 200, body: producer.response(url.slice('/health?nonce='.length), { ...observation, phase }) };
        }
        if (method !== 'POST' || !['/bind', '/drain', '/stop'].includes(url)) return deny();
        const obj = JSON.parse(body);
        // Canonical-only input also rejects duplicate keys, whitespace ambiguity and NaN.
        if (!obj || typeof obj !== 'object' || Array.isArray(obj) || encode(obj) !== body) return deny();
        const { mac: signature, ...unsigned } = obj;
        const required = { ...binding, domain: DOMAIN, action: url.slice(1), seq: obj.seq, nonce: obj.nonce, issued_ms: obj.issued_ms, expires_ms: obj.expires_ms };
        if (encode(unsigned) !== encode(required) || !equalMac(signature, mac(key, unsigned)) ||
            !Number.isSafeInteger(obj.seq) || obj.seq <= sequence || !hex(obj.nonce) ||
            !Number.isSafeInteger(obj.issued_ms) || !Number.isSafeInteger(obj.expires_ms) ||
            obj.expires_ms - obj.issued_ms !== 3000 || now() < obj.issued_ms || now() > obj.expires_ms) return deny();
        for (const [nonce, expiry] of nonces) if (expiry < now()) nonces.delete(nonce);
        if (nonces.has(obj.nonce) || nonces.size >= 128 || obj.action !== 'stop' && stop()) return deny();
        sequence = obj.seq;nonces.set(obj.nonce, obj.expires_ms);
        if (obj.action === 'bind') {
          if (draining || stopped || bindingStarted && !bound) return deny();
          if (!bound) {
          bindingStarted = true;const epoch = generation;
          const current = () => epoch === generation && owned() && !stop() && !draining;
          await onBind(current);if (!current()) return deny();bound = true;
          }
        }
        if (obj.action === 'drain') { generation++;draining = true;await onDrain(); }
        if (obj.action === 'stop' && !stopped) { generation++;stopped = true;bound = false;await onStop(); }
        const response = { ...binding, domain: ACK, action: obj.action, seq: obj.seq, nonce: obj.nonce,
          status: { bind: 'bound', drain: 'draining', stop: 'stopped' }[obj.action] };
        return { status: 200, body: encode({ ...response, mac: mac(key, response) }) };
      } catch { return deny(); } // no arbitrary exception or upstream stack output
    },
    status() { return { bound, draining, stopped: stop(), sequence, nonces: nonces.size }; },
  });
}
