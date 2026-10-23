// Original private-adapter interface. No upstream code, file stores or logger sinks.
import { createHmac } from 'node:crypto';

const id = x => (typeof x === 'string' || Number.isSafeInteger(x)) && /^[1-9][0-9]{0,19}$/.test(String(x)) ? String(x) : null;
const mid = x => {
  if (!(typeof x === 'string' || Number.isSafeInteger(x)) || !/^-?[0-9]+$/.test(String(x)) || String(x).length > 32) return null;
  const value = BigInt(x);return value === 0n ? null : value.toString();
};
const hex = (x, n) => typeof x === 'string' && new RegExp(`^[a-f0-9]{${n}}$`).test(x);
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x) && Object.getPrototypeOf(x) === Object.prototype;
const size = x => Buffer.byteLength(JSON.stringify(x));
const KINDS = new Set(['message', 'media', 'reaction', 'temp', 'rkey']);

class MetadataIndex {
  #rows = new Map(); #bytes = 0;
  constructor(limit, bytes, ttl, clock) { this.limit = limit; this.bytes = bytes; this.ttl = ttl; this.clock = clock; }
  prune() {
    const now = this.clock();
    for (const [key, row] of this.#rows) if (now < row.at || now - row.at >= this.ttl) this.remove(key);
  }
  remove(key) { const old = this.#rows.get(key); if (old) { this.#bytes -= old.bytes; this.#rows.delete(key); } }
  put(kind, group, sender, message) {
    this.prune();
    const value = { kind, group, sender, message };
    const key = `${kind}:${group}:${sender}:${message}`;
    const bytes = size(value) + Buffer.byteLength(key) + 32;
    if (bytes > this.bytes) return false;
    this.remove(key);
    while (this.#rows.size >= this.limit || this.#bytes + bytes > this.bytes) this.remove(this.#rows.keys().next().value);
    this.#rows.set(key, { at: this.clock(), bytes, value }); this.#bytes += bytes;
    return true;
  }
  clear() { this.#rows.clear(); this.#bytes = 0; }
  status() { this.prune(); return { entries: this.#rows.size, bytes: this.#bytes }; }
}

export function createProjectPolicy({ instanceId, transportEpoch, bot, allowedGroups, blockedUsers, identityCurrent, clock = () => performance.now() }) {
  if (!hex(instanceId, 32) || !hex(transportEpoch, 64) || !id(bot) ||
      !Array.isArray(allowedGroups) || !allowedGroups.length || allowedGroups.some(x => !id(x)) ||
      !Array.isArray(blockedUsers) || blockedUsers.some(x => !id(x)) || typeof identityCurrent !== 'function') throw Error('POLICY_CONFIG_INVALID');
  bot = id(bot);
  const groups = new Set(allowedGroups.map(id)), blocked = new Set(blockedUsers.map(id));
  // All message/media/reaction/temp/RKey metadata share this actual aggregate bound.
  const current = new MetadataIndex(512, 2 * 1024 * 1024, 300000, clock);
  const sends = new MetadataIndex(128, 128 * 512, 600000, clock);
  let accepted = 0, rejected = 0;
  const currentIdentity = () => { try { return identityCurrent() === true; } catch { return false; } };
  function admitEnvelope(e) {
    if (!plain(e) || !currentIdentity() || e.instance_id !== instanceId || e.transport_epoch !== transportEpoch ||
        e.post_type !== 'message' || e.message_type !== 'group' || id(e.self_id) !== bot ||
        !groups.has(id(e.group_id)) || !id(e.user_id) || id(e.user_id) === bot || blocked.has(id(e.user_id)) || !mid(e.message_id)) return false;
    return true;
  }
  function admitted(e) {
    if (!admitEnvelope(e) || !Number.isSafeInteger(e.time) || e.time <= 0) return false;
    if (!Array.isArray(e.message) || !e.message.length || e.message.length > 128) return false;
    // Check bounded text before serialization; never format rejected event exceptions.
    let bytes = 0;
    for (const part of e.message) {
      if (!plain(part) || typeof part.type !== 'string' || !plain(part.data)) return false;
      if (part.type === 'text') {
        if (typeof part.data.text !== 'string' || part.data.text.length > 8192) return false;
        bytes += Buffer.byteLength(part.data.text);
      }
    }
    return bytes <= 16384;
  }
  function sanitize(e) {
    const safe = [];
    for (const p of e.message) {
      if (p.type === 'text') safe.push({ type: 'text', data: { text: p.data.text } });
      else if (p.type === 'at' && (id(p.data.qq) || p.data.qq === 'all')) safe.push({ type: 'at', data: { qq: id(p.data.qq) || 'all' } });
      else if (p.type === 'reply') safe.push({ type: 'reply', data: { id: mid(p.data.id) || '0' } });
      else if (p.type === 'image') {
        // Current event metadata only: existing gate validates image source/pixels.
        const data = {};
        for (const k of ['file', 'url']) if (typeof p.data[k] === 'string' && p.data[k].length <= 2048) data[k] = p.data[k];
        safe.push({ type: 'image', data });
      }
      else if (p.type === 'at') continue;
      else safe.push({ type: 'text', data: { text: '[非文本未解析]' } });
    }
    // No embedded quote/forward body, media URL, sender profile or raw logger input.
    return { post_type: 'message', message_type: 'group', self_id: bot, group_id: id(e.group_id),
      user_id: id(e.user_id), sender: { user_id: id(e.user_id) }, message_id: mid(e.message_id), time: e.time,
      raw_message: '', message: safe };
  }
  return Object.freeze({
    admitEnvelope, // no message conversion, storage, formatting, logs or callbacks
    processEnvelope(e, convert, forward) {
      if (!admitEnvelope(e)) { rejected = Math.min(2147483647, rejected + 1); return false; }
      if (typeof convert !== 'function') throw Error('POLICY_CONVERT_INVALID');
      // Conversion happens only after the native identity envelope has passed.
      const converted = convert();
      if (!plain(converted)) return false;
      return this.process({ ...e, time: converted.time, message: converted.message }, forward);
    },
    process(e, forward) {
      if (!admitted(e)) { rejected = Math.min(2147483647, rejected + 1); return false; }
      if (typeof forward !== 'function') throw Error('POLICY_FORWARD_INVALID');
      const safe = sanitize(e);
      current.put('message', safe.group_id, safe.user_id, safe.message_id);
      accepted = Math.min(2147483647, accepted + 1);
      forward(safe); // first external callback; only current authorized sanitized event
      return true;
    },
    remember(e, kind) {
      // No separate cache bypass: metadata also requires current admitted envelope.
      if (!KINDS.has(kind) || !admitted(e)) return false;
      return current.put(kind, id(e.group_id), id(e.user_id), mid(e.message_id));
    },
    correlateSend(group, message) {
      if (!currentIdentity() || !groups.has(id(group)) || !mid(message)) return false;
      return sends.put('send', id(group), bot, mid(message));
    },
    allowsRpc(action) {
      // Internal backfill/history calls must use this same closed boundary.
      return currentIdentity() && ['get_status', 'get_login_info', 'get_version_info', 'get_group_list',
        'get_stranger_info', 'get_group_info', 'get_group_member_info', 'get_group_member_list',
        'send_group_msg', 'fetch_custom_face', 'fetch_custom_face_detail'].includes(action);
    },
    clear() { current.clear(); sends.clear(); },
    status() { return { accepted, rejected, current: current.status(), sends: sends.status() }; },
  });
}

const flags = ['account_match', 'pipe_connected', 'logged_in', 'rx_watch_armed', 'receive_healthy', 'outbound_healthy'];
const canonical = obj => {
  if (Array.isArray(obj)) return obj.map(canonical);
  if (plain(obj)) return Object.fromEntries(Object.keys(obj).sort().map(k => [k, canonical(obj[k])]));
  return obj;
};
export function createHealthProducer(binding, key) {
  const fields = ['schema', 'instance_id', 'transport_epoch', 'config_digest', 'policy_digest', 'build_hash', 'node', 'qq', 'listener_port'];
  if (!plain(binding) || Object.keys(binding).sort().join() !== [...fields].sort().join() ||
      binding.schema !== 1 || !hex(binding.instance_id, 32) ||
      ['transport_epoch', 'config_digest', 'policy_digest', 'build_hash'].some(k => !hex(binding[k], 64)) ||
      !Buffer.isBuffer(key) || key.length !== 32 || !Number.isInteger(binding.listener_port) || binding.listener_port < 1 || binding.listener_port > 65535) throw Error('HEALTH_BINDING_INVALID');
  for (const who of ['node', 'qq']) {
    const i = binding[who];
    if (!plain(i) || Object.keys(i).sort().join() !== 'created,pid' || !Number.isInteger(i.pid) || i.pid <= 0 || i.pid > 2147483647 ||
        !Number.isSafeInteger(i.created) || i.created <= 0) throw Error('HEALTH_BINDING_INVALID');
  }
  binding = structuredClone(binding); key = Buffer.from(key);
  let sequence = 0;
  return Object.freeze({ response(nonce, observation) {
    if (!hex(nonce, 64) || !plain(observation) || Object.keys(observation).sort().join() !== [...flags, 'phase', 'last_rx_age_ms'].sort().join() ||
        flags.some(k => typeof observation[k] !== 'boolean') || !['starting', 'ready', 'draining', 'stopped', 'failed'].includes(observation.phase) ||
        !Number.isInteger(observation.last_rx_age_ms) || observation.last_rx_age_ms < 0 || observation.last_rx_age_ms > 2147483647 || sequence >= Number.MAX_SAFE_INTEGER) throw Error('HEALTH_INVALID');
    const body = canonical({ ...binding, ...observation, seq: ++sequence, nonce });
    const mac = createHmac('sha256', key).update(JSON.stringify(body)).digest('hex');
    const content = JSON.stringify(canonical({ ...body, mac }));
    if (Buffer.byteLength(content) > 8192) throw Error('HEALTH_INVALID');
    return content;
  } });
}
