import { readFileSync, writeFileSync, renameSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { resolve, dirname } from 'node:path';

// No tools, processes, HTTP or model nouns. Only the host's typed prompt events.
export function register(on, options) {
  const hash = x => createHash('sha256').update(x).digest('hex');
  const q = JSON.parse(options.request);
  const need = (ok) => { if (!ok) throw Error('VISION_GUARD_CONTRACT'); };
  need(q.schema === 2 && /^[a-f0-9]{64}$/.test(q.nonce));
  need(q.model === 'deepseek-v4.1-flash' && q.effort === 'low');
  need(q.mode === 'probe' || q.mode === 'live');
  need(typeof q.system === 'string' && typeof q.prompt === 'string');
  need(hash(q.system) === q.system_sha256 && Buffer.byteLength(q.system) === q.system_bytes);
  need(hash(q.prompt) === q.prompt_sha256 && q.T === q.system_bytes + Buffer.byteLength(q.prompt));
  need(q.T + q.F + q.V + q.O <= q.C && q.V === 1024 && q.O >= 2048);
  need(resolve(q.receipt) === resolve(q.root, 'receipt.json'));
  need(dirname(resolve(q.root)) === process.cwd());
  for (const [file, sha] of Object.entries(q.assets)) {
    need(!file.includes('..') && hash(readFileSync(resolve(q.root, file))) === sha);
  }
  let composed = false, context = false, admitted = false, failed = false;
  const state = {schema: 2, nonce: q.nonce, system_sha256: q.system_sha256,
    system_bytes: q.system_bytes, assets_sha256: q.assets_sha256,
    request_sha256: hash(options.request), model: q.model, effort: q.effort,
    mode: q.mode, stages: [], next_calls: 0};
  function receipt(stage, extra = {}) {
    Object.assign(state, extra); state.stages.push(stage);
    const tmp = q.receipt + '.tmp';
    writeFileSync(tmp, JSON.stringify(state), {mode: 0o600});
    renameSync(tmp, q.receipt);
  }
  function empty(e) {
    return {turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: null, usage: null};
  }
  function reject(e, reason) {
    failed = true;
    try { receipt('refused', {reason}); } catch {}
    return empty(e);
  }
  on('engine.create', async ($, e, next) => {
    const engine = await next(e);
    receipt('ready');
    return engine;
  }); // engine.create has no Registration.catch; failure fails the load.
  const project = () => ({sections: [{id: 'qqbot-vision-guard:system', scope: 'session', text: q.system}]});
  on('prompt.compose', ($, e) => {
    need(e.model === q.model && e.promptModel === q.model && e.tools.length === 0);
    receipt('composed'); composed = true;
    return project();
  }).catch(() => { failed = true; return project(); });
  const clear = () => ({blocks: [], instructionFiles: []});
  on('prompt.context', () => {
    receipt('context_cleared'); context = true;
    return clear();
  }).catch(() => { failed = true; return clear(); });
  on('turn.step', async ($, e, next) => {
    if (failed || !composed || !context || admitted || e.agentId || e.index !== 0 ||
        e.model !== q.model || e.effort !== q.effort || e.messageCount !== 1 || Date.now() > q.deadline) {
      return reject(e, 'identity_projection_or_step');
    }
    // Public normalized transcript, not an assertion that TurnStepInput exposes
    // the SDK system. Reject unexpected reminder/tool/history/content expansion.
    const rows = await $.session.messages({as: 'api'});
    need(Array.isArray(rows) && rows.length === 1 && rows[0].role === 'user');
    const blocks = rows[0].content;
    need(Array.isArray(blocks) && blocks.length === 2);
    const texts = blocks.filter(b => b.type === 'text');
    const images = blocks.filter(b => b.type === 'image');
    need(texts.length === 1 && images.length === 1);
    need(texts[0].text === q.prompt || texts[0].text === '<user_query>' + q.prompt + '</user_query>');
    need(images[0].source?.type === 'base64' && images[0].source.media_type === 'image/png');
    need(hash(Buffer.from(images[0].source.data, 'base64')) === q.image_sha256);
    receipt(q.mode === 'probe' ? 'probe_short_circuit' : 'admitted', {transcript_verified: true});
    admitted = true;
    if (q.mode === 'probe') return empty(e);
    // Set before calling next; catch may replay that same call, never generate twice.
    state.next_calls = 1;
    receipt('next');
    const result = await next(e);
    receipt('completed');
    return result;
  }).catch(($, e, next) => next.called ? next(e) : reject(e, 'hook_failure'));
}
