// Uses the documented Mod host API and pure JavaScript; no Node imports.
export function register(on, options) {
  const bytes = text => {
    const out=[];
    for (const ch of text) {
      const n=ch.codePointAt(0);
      if(n<128)out.push(n);
      else if(n<2048)out.push(192|(n>>>6),128|(n&63));
      else if(n<65536)out.push(224|(n>>>12),128|((n>>>6)&63),128|(n&63));
      else out.push(240|(n>>>18),128|((n>>>12)&63),128|((n>>>6)&63),128|(n&63));
    }
    return out;
  };
  // SHA-256 over bytes, no unavailable sandbox imports/Web Crypto dependency.
  const hash = value => {
    const data=typeof value==='string'?bytes(value):Array.from(value);
    const bitLength=data.length*8; data.push(128);
    while(data.length%64!==56)data.push(0);
    const high=Math.floor(bitLength/4294967296),low=bitLength>>>0;
    for(let i=3;i>=0;i--)data.push((high>>>(i*8))&255);
    for(let i=3;i>=0;i--)data.push((low>>>(i*8))&255);
    const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    const H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const rotr=(x,n)=>(x>>>n)|(x<<(32-n));
    for(let pos=0;pos<data.length;pos+=64){
      const W=[];
      for(let i=0;i<16;i++)W[i]=(data[pos+i*4]<<24)|(data[pos+i*4+1]<<16)|(data[pos+i*4+2]<<8)|data[pos+i*4+3];
      for(let i=16;i<64;i++){
        const x=W[i-15],y=W[i-2];
        W[i]=(W[i-16]+(rotr(x,7)^rotr(x,18)^(x>>>3))+W[i-7]+(rotr(y,17)^rotr(y,19)^(y>>>10)))|0;
      }
      let [a,b,c,d,e,f,g,h]=H;
      for(let i=0;i<64;i++){
        const t1=(h+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^(~e&g))+K[i]+W[i])|0;
        const t2=((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))|0;
        h=g;g=f;f=e;e=(d+t1)|0;d=c;c=b;b=a;a=(t1+t2)|0;
      }
      const working=[a,b,c,d,e,f,g,h];
      for(let i=0;i<8;i++)H[i]=(H[i]+working[i])|0;
    }
    return H.map(x=>(x>>>0).toString(16).padStart(8,'0')).join('');
  };
  const decode = text => {
    const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    const out=[];let buffer=0,bits=0;
    for(const ch of text){if(ch==='=')break;const n=alphabet.indexOf(ch);if(n<0)throw Error('VISION_GUARD_BASE64');
      buffer=(buffer<<6)|n;bits+=6;if(bits>=8){bits-=8;out.push((buffer>>>bits)&255);}}
    return out;
  };
  const path = x => x.replace(/\\/g,'/').replace(/\/$/,'').toLowerCase();
  const q = JSON.parse(options.request);
  const canonical = x => Array.isArray(x) ? '[' + x.map(canonical).join(',') + ']' :
    x && typeof x === 'object' ? '{' + Object.keys(x).sort().map(k => JSON.stringify(k)+':'+canonical(x[k])).join(',') + '}' : JSON.stringify(x);
  const need = (ok, reason='contract') => { if (!ok) throw Error('VISION_GUARD_' + reason); };
  need(q.schema === 2 && /^[a-f0-9]{64}$/.test(q.nonce));
  need(q.model === 'deepseek-v4.1-flash' && q.effort === 'low');
  need(q.mode === 'probe' || q.mode === 'live');
  need(typeof q.system === 'string' && typeof q.prompt === 'string');
  need(q.T + q.F + q.V + q.O <= q.C && (q.V === 1024 || q.native_web && q.V === 0) && q.O >= 2048);
  need(path(q.receipt_root) === path(q.root).replace(/\/vision-plugin$/,'/vision-receipts'));
  need(path(q.receipt) === path(q.receipt_root + '/receipt.json'));
  const state = {schema: 2, nonce: q.nonce, system_sha256: q.system_sha256,
    system_bytes: q.system_bytes, assets_sha256: q.assets_sha256,
    model: q.model, effort: q.effort, mode: q.mode, stages: [], next_calls: 0};
  const phaseNames=['context_cleared','composed','refused','admitted','probe_short_circuit','next','completed'];
  async function readState($) {
    const current=JSON.parse(await $.fs.read(q.receipt));
    need(current.nonce===q.nonce,'receipt_identity');
    const stages=['ready'];let calls=0,lastProof=-1;
    const entries=(await $.fs.list(q.receipt_root)).filter(x=>x.name.startsWith('phase-') && x.name.endsWith('.json'));
    need(entries.length<=128,'receipt_count');
    for(const entry of entries){
      let row;
      try {row=JSON.parse(await $.fs.read(q.receipt_root+'/'+entry.name));} catch {continue;}
      need(row.nonce===q.nonce && phaseNames.includes(row.stage),'phase_identity');
      stages.push(row.stage);
      for(const key of ['reason','guard_reason','hook_error','diagnostic','registered_tools','catalog_tools','transcript_verified'])
        if(row[key]!==undefined)current[key]=row[key];
      if(row.native_web && row.seq>lastProof){current.native_web=row.native_web;lastProof=row.seq;}
      if(row.stage==='next')calls++;
    }
    current.stages=stages;current.next_calls=calls;
    return current;
  }
  let phaseSeq=0;
  async function receipt($, stage, extra = {}) {
    if(stage==='ready'){
      await $.fs.write(q.receipt,JSON.stringify({...state,...extra,stages:['ready']}));
      return;
    }
    need(phaseNames.includes(stage),'phase_name');
    // Independent immutable phase files prevent concurrent context/composition
    // dispatches from erasing admission/refusal/short-circuit evidence.
    const name='phase-'+stage+'-'+Date.now()+'-'+Math.floor(Math.random()*4294967296).toString(16)+'.json';
    await $.fs.write(q.receipt_root+'/'+name,JSON.stringify({nonce:q.nonce,stage,seq:++phaseSeq,...extra}));
  }
  function empty(e) {
    return {turnId: e.turnId, index: e.index, answer: '', toolUses: [], stopReason: null, usage: null};
  }
  async function reject($, e, reason, details = {}) {
    try { await receipt($, 'refused', {reason,...details}); } catch {}
    return empty(e);
  }
  on('engine.create', async ($, e, next) => {
    const engine = await next(e);
    const rootStat=await engine.fs.stat(q.root,{resolve:true});
    need(rootStat.realPath && path(rootStat.realPath) === path(q.root) && !rootStat.isLink, 'root');
    need(await hash(q.system) === q.system_sha256 && bytes(q.system).length === q.system_bytes, 'system');
    need(await hash(q.prompt) === q.prompt_sha256 && q.T === q.system_bytes + bytes(q.prompt).length, 'prompt');
    for (const [file, sha] of Object.entries(q.assets)) {
      need(!file.includes('..') && !file.startsWith('/'), 'asset_path');
      const data = await engine.fs.read(q.root + '/' + file, {as:'bytes'});
      need(await hash(decode(data.base64)) === sha, 'asset');
    }
    const wireText=await engine.fs.read(q.wire_path);
    need(hash(wireText)===q.wire_sha256,'wire_hash');
    const wire=JSON.parse(wireText);
    need(wire.type==='user' && wire.message.role==='user','wire_shape');
    if(!q.image_sha256){need(wire.message.content===q.prompt,'wire_text');}
    else {
    need(wire.message.content[0].type==='text' && wire.message.content[0].text===q.prompt,'wire_text');
    const image=wire.message.content[1];
    need(image.type==='image' && image.source.type==='base64' && image.source.media_type==='image/png','wire_image');
    need(hash(decode(image.source.data))===q.image_sha256,'wire_pixels');
    }
    await receipt(engine, 'ready', {request_sha256: await hash(canonical(q)),wire_verified:true});
    return engine;
  }); // engine.create has no Registration.catch; failure fails the load.
  const project = () => ({sections: [{id: 'qqbot-vision-guard:system', scope: 'session', text: q.system}]});
  on('prompt.compose', async ($, e) => {
    need(e.model === q.model && e.promptModel === q.model && e.tools.every(t => q.denied_tools.includes(t) || (q.native_web?.allowed_tools??[]).includes(t)), 'compose_shape');
    const catalog=await $.tool.list();
    need(Array.isArray(catalog) && catalog.every(t => t.mcp===false), 'tool_catalog');
    // This build's public catalog ignores an empty --tools string. Locked
    // createIsEnabledChecker + SDK getAllTools remove every function before
    // the actual model request; the parent also requires init tools/MCP=[] .
    await receipt($, 'composed', {registered_tools:e.tools.length,catalog_tools:catalog.length});
    return project();
  }).catch(() => project());
  const clear = () => ({blocks: [], instructionFiles: []});
  // Context preparation also runs around host API calls. This handler must be
  // pure: doing fs I/O here recursively prepares context again in this build.
  on('prompt.context', () => clear()).catch(() => clear());

  const web=q.native_web;
  if(web)need(Array.isArray(web.allowed_tools) && web.allowed_tools.every(t=>['WebSearch','WebFetch'].includes(t)) &&
    web.allowed_tools.length===new Set(web.allowed_tools).size && web.max_calls>=1 && web.max_calls<=3 &&
    web.max_turns>=1 && web.max_turns<=4 && web.result_bytes<=8000 && web.total_result_bytes===12000 &&
    Number.isSafeInteger(web.visible_limit) && web.visible_limit>0 && web.visible_limit+q.F+q.V+q.O<=q.C && web.schema_bytes_per_tool===4096,'native_policy');
  const native={step:0,turn:null,calls:0,resultBytes:0,requests:new Map(),results:new Map(),planned:[],
    descriptions:new Map(),answers:[],prefix:null,urls:[],steps:[],failed:false};
  const publicURL=value=>{
    if(typeof value!=='string' || /[\\\s\x00-\x1f]/.test(value))return false;
    const m=/^https?:\/\/([^/?#]+)(?:[/?#]|$)/i.exec(value);
    if(!m || /[@%\[\]]/.test(m[1]))return false;
    const parts=m[1].toLowerCase().split(':');
    if(parts.length>2 || parts[1] && !['80','443'].includes(parts[1]))return false;
    const h=parts[0].replace(/\.$/,'');
    return h.includes('.') && !h.split('.').every(x=>/^(?:0x[0-9a-f]+|\d+)$/i.test(x)) && !/^(?:0x[0-9a-f]+)$/i.test(h) &&
      !/(?:^|\.)(?:localhost|local|internal|lan)$/.test(h) && h!=='metadata.google.internal';
  };
  const urls=text=>Array.from(new Set((text.match(/https?:\/\/[^\s<>"\u3000]+/g)??[])
    .map(x=>x.replace(/[。，；！？、)\]}]+$/g,'')).filter(publicURL)));
  const cut=(text,cap)=>{let out='';for(const ch of text){if(bytes(out+ch).length>cap)break;out+=ch;}return out;};
  const sensitive=text=> /(?:\d{5,}|QQ号|群号|密码|口令|token|secret|api.?key|\b[A-Za-z]:[\\/]|\\\\|[\w.+-]+@[\w.-]+)/i.test(
    text.replace(/\b\d{4}-\d{2}-\d{2}\b/g,'DATE')) || web.private_ids.some(x=>text.includes(x));
  const proof=()=>({calls:native.calls,result_bytes:native.resultBytes,urls:native.urls.slice(0,2),steps:native.steps,
    allowed_tools:web.allowed_tools,thinking_enabled:false,sha256:hash(canonical(Array.from(native.results.values()).map(x=>x.visible??'')))});
  const argsOf=e=>{
    const flat=Object.fromEntries(Object.entries(e).filter(([k])=>!['tool','tool_use_id','agentId','consent','input'].includes(k)));
    if(!Object.prototype.hasOwnProperty.call(e,'input'))return flat;
    // The locked SDK's non-flat adapter carries both spread arguments and an
    // input copy. Require agreement before removing that transport envelope.
    let input=e.input;
    if(typeof input==='string'){
      need(bytes(input).length<=8192,'tool_envelope');
      input=JSON.parse(input);
    }
    need(input && typeof input==='object' && !Array.isArray(input),'tool_envelope');
    need(Object.keys(flat).length===0 || canonical(flat)===canonical(input),'tool_envelope');
    return input;
  };
  const denyText='Native web call refused or unavailable; this request has not verified the claim.';
  async function webDeny($,e,reason,guard_reason='none'){
    native.failed=true;
    try{await receipt($,'refused',{reason,guard_reason,native_web:proof()});}catch{}
    return {deny:denyText};
  }
  if(web){
    on('tool.describe',async($,e,next)=>{
      if(!web.allowed_tools.includes(e.tool))return {description:'Unavailable',isDeferred:false};
      const value=await next(e);
      need(typeof value.description==='string' && bytes(value.description).length<=8000,'tool_description');
      native.descriptions.set(e.tool,value.description);
      return {...value,isDeferred:false};
    }).catch(()=>({description:'Unavailable',isDeferred:false}));
    on('tool.call',async($,e,next)=>{
      try{
        // Streaming CLI can dispatch a tool before turn.step's next() reply
        // has crossed the Mod bridge. Wait for that exact plan, never guess it.
        if(native.pendingStep)await native.pendingStep;
        const id=e.tool_use_id,args=argsOf(e),known=native.planned.find(x=>x.tool===e.tool && canonical(x.input)===canonical(args));
        // Synchronous reservation, before any await, closes parallel and replay gaps.
        if(native.failed || e.agentId || !web.allowed_tools.includes(e.tool) || typeof id!=='string' ||
          !known || known.tool!==e.tool || canonical(known.input)!==canonical(args) ||
          native.results.has(id) || native.calls>=web.max_calls || Date.now()>q.deadline)
          return await webDeny($,e,'tool_identity_replay_or_limit');
        native.calls++;native.planned.splice(native.planned.indexOf(known),1);native.requests.set(id,known);native.results.set(id,{pending:true});
        need(!sensitive(JSON.stringify(args)),'tool_private');
        if(e.tool==='WebFetch'){
          need(Object.keys(args).every(k=>['url','prompt'].includes(k)) && publicURL(args.url) &&
            typeof args.prompt==='string' && args.prompt.length<=1000,'fetch_input');
        }else{
          need(Object.keys(args).every(k=>['query','allowed_domains','blocked_domains','freshness'].includes(k)) &&
            typeof args.query==='string' && args.query.length>=2 && args.query.length<=240,'search_input');
          for(const k of ['allowed_domains','blocked_domains'])if(args[k]!==undefined)
            need(Array.isArray(args[k]) && args[k].length<=5 && args[k].every(x=>typeof x==='string' && publicURL('https://'+x)),'search_domains');
          for(const u of (args.query.match(/https?:\/\/[^\s<>"]+/g)??[]))need(publicURL(u),'search_url');
        }
        const result=await next(e);
        const cap=Math.min(web.result_bytes,web.total_result_bytes-native.resultBytes);
        need(cap>=256,'tool_total_bytes');
        let text='',found=[];
        if(!result.deny && !result.isError && result.result && typeof result.result.content==='string'){
          const body=result.result;
          need(!body.content.includes('Do NOT retry WebFetch') && !body.content.includes('cb-fetch-XXXXXX'),'non_text_resource');
          need(!web.private_ids.some(x=>JSON.stringify(body).includes(x)) && !/(?:api.?key|access.?token|密码)\s*[:=]/i.test(body.content),'result_private');
          found=urls(JSON.stringify(body));
          text=cut(found.slice(0,2).join('\n')+'\n'+String(body.title??'').replace(/\x1b\[[0-9;]*m/g,'')+'\n'+body.content,cap-64);
        }else text=cut(denyText,cap-64);
        // Return a fresh generic tool result. Keeping core's ref would bypass clipping.
        const clean={content:text,title:'Native web material',renderer:{type:'text'}};
        while(bytes(JSON.stringify(clean)).length>cap && clean.content.length)clean.content=cut(clean.content,bytes(clean.content).length-64);
        text=clean.content;
        need(bytes(JSON.stringify(clean)).length<=cap,'tool_result_bytes');
        const visible=JSON.stringify(clean);
        native.resultBytes+=bytes(visible).length;
        const actual=urls(text);native.urls=Array.from(new Set([...native.urls,...actual])).slice(0,2);
        native.results.set(id,{text,result:clean,visible});
        await receipt($,'admitted',{native_web:proof()});
        return {result:clean};
      }catch(error){
        const tag=/^Error: VISION_GUARD_([a-z_]{1,80})$/.exec(String(error));
        return await webDeny($,e,'tool_validation_or_io',tag?tag[1]:'tool_io_or_invalid_json');
      }
    }).catch(async($,e)=>webDeny($,e,'tool_hook_failure'));
  }
  async function nativeStep($,e,next){
    let entered=false;
    let releasePlan;
    try{
      const prior=await readState($);
      need(!native.failed && !prior.stages.includes('refused') && prior.stages.includes('composed'),'native_ready');
      need(!e.agentId && e.index===native.step && e.index<web.max_turns && Date.now()<=q.deadline &&
        e.model===q.model && (e.effort===undefined || e.effort===q.effort),'native_step_identity');
      if(native.turn===null)native.turn=e.turnId;
      need(e.turnId===native.turn,'native_turn');
      const rows=await $.session.messages({as:'api'});
      need(Array.isArray(rows) && rows.length>=1 && rows[0].role==='user','native_rows');
      need(rows[0].content.length===1 && rows[0].content[0].type==='text' &&
        [q.prompt,'<user_query>'+q.prompt+'</user_query>'].includes(rows[0].content[0].text),'native_first');
      const seenCalls=new Set(),seenResults=new Set();
      for(let i=1;i<rows.length;i++){
        const row=rows[i];need(Array.isArray(row.content),'native_blocks');
        for(const b of row.content){
          if(row.role==='assistant' && b.type==='text')need(native.answers.includes(b.text),'native_answer_history');
          else if(row.role==='assistant' && b.type==='tool_use'){
            const call=native.requests.get(b.id);
            need(call && call.tool===b.name && canonical(call.input)===canonical(b.input) && !seenCalls.has(b.id),'native_call_history');
            seenCalls.add(b.id);
          }else if(row.role==='user' && b.type==='tool_result'){
            const out=native.results.get(b.tool_use_id);
            need(out && !out.pending && seenCalls.has(b.tool_use_id) && !seenResults.has(b.tool_use_id) &&
              [out.text,out.visible].includes(b.content),'native_result_history');
            seenResults.add(b.tool_use_id);
          }else need(false,'native_history_type');
        }
      }
      need(native.planned.length===0 && seenCalls.size===native.requests.size && seenResults.size===native.results.size &&
        seenCalls.size===seenResults.size,'native_history_complete');
      if(native.prefix)need(canonical(rows.slice(0,native.prefix.length))===canonical(native.prefix),'native_prefix');
      const tools=await $.tool.list();need(tools.every(t=>!t.mcp),'native_mcp');
      // Definitions are the current dynamic descriptions plus the locked parameter-schema upper bound.
      const definitions=web.allowed_tools.map(name=>({name,description:native.descriptions.get(name)??tools.find(t=>t.name===name)?.description}));
      need(definitions.every(t=>typeof t.description==='string'),'native_tool_definitions');
      const D=bytes(JSON.stringify(definitions)).length+definitions.length*web.schema_bytes_per_tool;
      const T=q.system_bytes+bytes(JSON.stringify(rows)).length;
      need(T+D+web.overhead<=web.visible_limit && T+D+q.F+q.V+q.O<=q.C,'native_step_budget');
      native.steps.push({index:e.index,text_bytes:T,tool_definition_bytes:D,visible_bytes:T+D+web.overhead});
      await receipt($,'context_cleared',{transcript_verified:true,native_web:proof()});
      if(q.mode==='probe'){await receipt($,'probe_short_circuit',{transcript_verified:true,native_web:proof()});return empty(e);}
      await receipt($,'next',{native_web:proof()});native.step++;entered=true;
      native.pendingStep=new Promise(resolve=>{releasePlan=resolve;});
      const result=await next(e);
      need(!result.serverToolUses?.length,'server_tool');
      need((result.toolUses??[]).length+native.calls<=web.max_calls,'native_planned_limit');
      for(const call of result.toolUses??[]){
        need(web.allowed_tools.includes(call.name),'native_returned_tool');
        native.planned.push({tool:call.name,input:call.input});
      }
      if(result.answer)native.answers.push(result.answer);
      native.prefix=JSON.parse(JSON.stringify(rows));
      await receipt($,'completed',{native_web:proof()});
      return result;
    }catch(error){native.failed=true;return reject($,e,entered?'native_result_validation':'native_step_validation',{hook_error:String(error).slice(0,160),native_web:proof()});}
    finally{if(releasePlan){native.pendingStep=null;releasePlan();}}
  }

  on('turn.step', async ($, e, next) => {
    if(q.native_web)return nativeStep($,e,next);
    let nextEntered=false;
    let diagnostic={};
    try {
    const prior = await readState($);
    const stages = prior.stages ?? [];
    if (prior.nonce !== q.nonce || !stages.includes('composed') ||
        stages.some(x => ['refused','admitted','probe_short_circuit','next','completed'].includes(x)) ||
        e.agentId || e.index !== 0 ||
        e.model !== q.model || (e.effort !== undefined && e.effort !== q.effort) || e.messageCount !== 1 || Date.now() > q.deadline) {
      return reject($, e, 'identity_projection_or_step');
    }
    const rows = await $.session.messages({as: 'api'});
    diagnostic={rows:Array.isArray(rows)?rows.length:-1,roles:Array.isArray(rows)?rows.map(r=>r.role):[],
      blocks:Array.isArray(rows)?rows.map(r=>Array.isArray(r.content)?r.content.map(b=>({type:b.type,keys:Object.keys(b),
        text_bytes:typeof b.text==='string'?bytes(b.text).length:null,source_keys:b.source?Object.keys(b.source):[]})):[]):[]};
    need((await $.tool.list()).every(t => t.mcp===false), 'step_tools');
    need(Array.isArray(rows) && rows.length === 1 && rows[0].role === 'user', 'messages');
    const blocks = rows[0].content;
    // Locked toApiMessages() intentionally emits text/tool blocks only. Pixel
    // identity is bound to the exact parent stdin frame verified at engine.create.
    need(Array.isArray(blocks) && blocks.length === 1, 'blocks');
    const texts = blocks.filter(b => b.type === 'text');
    need(texts.length === 1, 'content');
    need(texts[0].text === q.prompt || texts[0].text === '<user_query>' + q.prompt + '</user_query>', 'text');
    await receipt($, 'context_cleared', {transcript_verified: true});
    await receipt($, q.mode === 'probe' ? 'probe_short_circuit' : 'admitted', {transcript_verified: true});
    if (q.mode === 'probe') return empty(e);
    await receipt($, 'next', {next_calls: 1});
    nextEntered=true;
    const result = await next(e);
    await receipt($, 'completed');
    return result;
    } catch (error) {
      if(nextEntered)return next(e); // host replay of that same admission
      // Keep ordinary validation/host-I/O failures inside the handler. A thrown
      // guard is skipped by the host, so it is never our refusal mechanism.
      return reject($, e, 'step_validation_or_io', {hook_error:String(error).slice(0,160),diagnostic});
    }
  }).catch(async ($, e, next) => {
    if(q.native_web)return empty(e);
    // next.called alone is insufficient: replay only after our own persisted
    // admission. Any inability to prove that state returns an empty refusal.
    try {
      const prior=await readState($);
      if(prior.nonce===q.nonce && prior.next_calls===1 && prior.stages.includes('next') && next.called)
        return await next(e);
    } catch {}
    return empty(e);
  });
}
