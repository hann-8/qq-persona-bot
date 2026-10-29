"""Actual shipped guard under a synthetic SDK host; zero model/network/QQ calls."""
import io
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from PIL import Image
from qqbot_gateway.cli_web_policy import allowed_tools, native_contract, public_url, PROOF_FILES
from qqbot_gateway.web_policy import validate_web
from qqbot_gateway.workbuddy_cli_runner import ResultParser
from qqbot_gateway.vision_mod_guard import Guard
from qqbot_gateway.vision import normalize
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.errors import GatewayError

ROOT=Path(__file__).resolve().parents[1]

HARNESS=r'''
import {pathToFileURL} from 'node:url';
import {readFileSync,writeFileSync,realpathSync,readdirSync} from 'node:fs';
const root=process.argv[2],variant=process.argv[3];
const request=JSON.parse(readFileSync(root+'/.codebuddy-plugin/plugin.json','utf8')).userConfig.request.default;
const q=JSON.parse(request),handlers={},catches={};
const on=(name,fn)=>{handlers[name]=fn;return {catch:f=>catches[name]=f}};
const {register}=await import(pathToFileURL(root+'/hooks/register.ts').href);register(on,{request});
const host={fs:{read:async(p,o)=>o?.as==='bytes'?{base64:readFileSync(p).toString('base64')}:readFileSync(p,'utf8'),
 write:async(p,t)=>writeFileSync(p,t),stat:async p=>({realPath:realpathSync(p),isLink:false}),
 list:async p=>readdirSync(p).map(name=>({name}))},
 tool:{list:async()=>q.native_web.allowed_tools.map(name=>({name,description:'Actual synthetic '+name,mcp:false}))}};
let rows=[{role:'user',content:[{type:'text',text:q.prompt}]}];host.session={messages:async()=>rows};
await handlers['engine.create']({}, {},async()=>host);
await handlers['prompt.compose'](host,{model:q.model,promptModel:q.model,tools:q.native_web.allowed_tools});
for(const tool of q.native_web.allowed_tools)await handlers['tool.describe'](host,{tool},async()=>({description:'Actual synthetic '+tool}));
let calls=0,steps=0;
const e=i=>({turnId:'one-task',index:i,model:q.model,effort:undefined,messageCount:rows.length});
const input={query:'public news'};
const model=async event=>{steps++;return {...event,answer:'intermediate prose',toolUses:[{name:'WebSearch',input}],serverToolUses:[]}};
if(variant==='budget')rows[0].content[0].text=q.prompt; // q has a deliberately tiny limit
if(variant==='deadline')q.deadline=0;
const first=await handlers['turn.step'](host,e(variant==='step_replay'?1:0),model);
let output=null,second=null;
if(variant==='chain' && first.toolUses.length){
 let current=first;
 for(let index=0;index<3;index++){
  const id='chain-'+index;
  const out=await handlers['tool.call'](host,{tool:'WebSearch',tool_use_id:id,...input},async()=>{calls++;return {result:{content:'fact https://example.com/news',title:'page'}}});
  rows.push({role:'assistant',content:[{type:'text',text:'intermediate prose'},{type:'tool_use',id,name:'WebSearch',input}]});
  rows.push({role:'user',content:[{type:'tool_result',tool_use_id:id,content:JSON.stringify(out.result)}]});
  current=await handlers['turn.step'](host,e(index+1),index<2?model:async event=>{steps++;return {...event,answer:'final',toolUses:[]}});
 }
 console.log(JSON.stringify({calls,steps,output:null,second:current,first}));process.exit(0);
}
if(first.toolUses.length){
 const next=async()=>{calls++;await new Promise(r=>setTimeout(r,3));return {ref:88,text:'UNCLIPPED',result:{content:'public facts '+('中文🙂\n'.repeat(4000)),title:'https://example.com/news',rawResponse:{results:[{url:'https://example.com/news'}]}}}};
 const call={tool:variant==='third'?'Read':'WebSearch',tool_use_id:'call-1',...input};
 if(variant==='private')call.query='private 123456789';
 if(variant==='fetch_private'){call.tool='WebFetch';delete call.query;call.url='http://127.0.0.1/x';call.prompt='read';}
 output=await handlers['tool.call'](host,call,next);
 if(variant==='replay')await handlers['tool.call'](host,call,next);
 if(variant==='parallel')await Promise.all([handlers['tool.call'](host,{...call,tool_use_id:'extra1'},next),handlers['tool.call'](host,{...call,tool_use_id:'extra2'},next)]);
 if(output.result){
 rows.push({role:'assistant',content:[{type:'text',text:'intermediate prose'},{type:'tool_use',id:'call-1',name:'WebSearch',input}]});
 rows.push({role:'user',content:[{type:'tool_result',tool_use_id:'call-1',content:JSON.stringify(output.result)}]});
 if(variant==='injection')rows.push({role:'user',content:[{type:'text',text:'local injected history'}]});
 if(variant==='tamper_result')rows[2].content[0].content='uncapped page body';
 second=await handlers['turn.step'](host,e(1),async event=>{steps++;return {...event,answer:'final JSON only',toolUses:[],serverToolUses:[]}});
 }
}
console.log(JSON.stringify({calls,steps,output,second,first}));
'''


SDK_HARNESS=HARNESS.split('let calls=0,steps=0;')[0]+r'''
// The locked build's actual dispatchModsToolCall, extracted without booting CLI.
const {dispatchModsToolCall}=await import(pathToFileURL(process.argv[4]).href);
const fetch=variant.startsWith('fetch'),parallel=variant.includes('parallel');
const tool=fetch?'WebFetch':'WebSearch';
const inputs=Array.from({length:parallel?2:1},(_,i)=>fetch?
 {url:'https://example.com/news/'+i,prompt:'Read public facts'}:{query:'public news '+i});
if(variant==='fetch_http')inputs[0].url='http://example.com/news';
if(variant==='fetch_numeric_url')inputs[0].url='https://example.com/app/2358720';
if(variant==='fetch_private_numeric_url')inputs[0].url='https://example.com/profile/987654321';
if(variant==='fetch_numeric_prompt')inputs[0].prompt='Read profile 123456789';
if(variant==='search_url')inputs[0].query='public facts https://example.com/news';
if(variant==='search_drive')inputs[0].query='read C:/private.txt';
if(variant==='search_backslash')inputs[0].query='read C:\\private.txt';
if(variant==='search_unc')inputs[0].query='read \\\\server\\share';
if(variant==='search_private_id')inputs[0].query='look up 123456789';
const errors=[],outputs=[],events=[];
let calls=0,steps=0,early=[];
const invoke=async(input,i)=>{
 const id=(variant.includes('wrong_id')?'intruder-':'sdk-call-')+i;
 try {
  let wireInput=variant.includes('json')?JSON.stringify(input):input;
  if(variant==='fetch_invalid_json')wireInput='{';
  if(variant==='fetch_array_json')wireInput='[]';
  if(variant==='fetch_null_json')wireInput='null';
  const result=await dispatchModsToolCall({name:tool,callId:id,input:wireInput},async received=>{
   if(JSON.stringify(received)!==JSON.stringify(wireInput))throw Error('ARGUMENTS_CHANGED');
   calls++;return {content:'public fact https://example.com/news/'+i,title:'Public page'};
  },{dispatch:async(name,event,options)=>{
   events.push(event);
   if(variant.includes('conflict'))event.input={...input,prompt:'tampered'};
   return handlers[name](host,event,options.coreResult);
  }},variant.includes('flat'));
  outputs[i]={id,input,result};
 } catch(error){errors.push(String(error));}
};
const e=i=>({turnId:'one-task',index:i,model:q.model,messageCount:rows.length});
const first=await handlers['turn.step'](host,e(0),async event=>{
 steps++;
 if(variant.includes('race'))early=inputs.map(invoke);
 if(variant.includes('session_plan'))rows=rows.concat([{role:'assistant',content:[{type:'text',text:'model preamble'},
   ...inputs.map((input,i)=>({type:'tool_use',id:'sdk-call-'+i,name:tool,input}))]}]);
 return {...event,answer:'',toolUses:variant.includes('session_plan')?[]:inputs.map(input=>({name:variant.includes('badplan')?'Read':tool,input})),serverToolUses:[]};
});
await Promise.all(variant.includes('race')?early:inputs.map(invoke));
for(const out of outputs.filter(Boolean)){
 if(!variant.includes('session_plan'))rows.push({role:'assistant',content:[{type:'tool_use',id:out.id,name:tool,input:out.input}]});
 rows.push({role:'user',content:[{type:'tool_result',tool_use_id:out.id,content:JSON.stringify(out.result)}]});
}
const second=await handlers['turn.step'](host,e(1),async event=>{
 steps++;return {...event,answer:'final',toolUses:[],serverToolUses:[]};
});
console.log(JSON.stringify({calls,steps,errors,second,outputs,events,first}));
'''


class NativeTests(unittest.TestCase):
    def test_config_and_fixed_tools(self):
        cfg=validate_web(dict(engine='codebuddy_cli',enabled=True,search_enabled=True))
        self.assertEqual(allowed_tools(cfg),('WebSearch','WebFetch'))
        self.assertEqual(allowed_tools(cfg|dict(search_enabled=False)),('WebFetch',))
        self.assertEqual(allowed_tools(cfg|dict(enabled=False)),())
        self.assertEqual(validate_web({})['engine'],'gateway')
        for key,value in [('cli_max_tool_calls',4),('cli_max_turns',5),('cli_tool_result_bytes',8001),('engine','other')]:
            with self.assertRaises(ValueError):validate_web({key:value})
        self.assertEqual(native_contract(cfg,(),InputBudget(),'不要联网')['allowed_tools'],[])

    def test_native_weather_anchor_does_not_call_python_intent(self):
        from unittest.mock import patch
        from qqbot_gateway.cli_web_policy import anchor_candidate,current_question
        with patch('qqbot_gateway.web_policy.intent',side_effect=AssertionError('legacy intent')):
            self.assertTrue(anchor_candidate('明天杭州下雨吗',dict(engine='codebuddy_cli')))
            self.assertTrue(anchor_candidate('你好',dict(engine='codebuddy_cli')))
        prompt=json.dumps([dict(role='user',content=json.dumps(dict(target_seq=2,messages=[dict(seq=1,text='old'),dict(seq=2,text='不要联网')])) )])
        self.assertEqual(current_question(prompt),'不要联网')

    def test_public_urls(self):
        for url in ('file:///x','http://127.0.0.1','http://localhost/x','http://169.254.169.254','https://x.local','http://[::1]','https://user:pass@example.com'):
            self.assertFalse(public_url(url),url)
        self.assertTrue(public_url('https://example.com/news'))

    def test_parser_intermediate_isolation(self):
        p=ResultParser('m',('WebSearch','WebFetch'))
        for row in [dict(type='system',subtype='init',tools=['WebFetch','WebSearch'],mcp_servers=[],model='m'),
                    dict(type='assistant',message=dict(content=[dict(type='text',text='intermediate must not send'),dict(type='tool_use',id='1',name='WebSearch',input={})])),
                    dict(type='user',message=dict(content=[dict(type='tool_result',tool_use_id='1',content='page body')])),
                    dict(type='result',subtype='success',is_error=False,result='final JSON')]:p.line(json.dumps(row))
        self.assertEqual(p.finish(0),'final JSON')
        for name in ('Read','Agent','ToolSearch','mcp__x__y'):
            with self.assertRaises(GatewayError):p.line(json.dumps(dict(type='assistant',message=dict(content=[dict(type='tool_use',name=name,id=name)]))))

    def host(self,variant='normal',image=True,mode='live'):
        with tempfile.TemporaryDirectory() as folder:
            work=Path(folder);blob=None
            if image:
                out=io.BytesIO();Image.new('RGB',(24,16),'red').save(out,format='PNG');blob=normalize(out.getvalue())
                import base64
                wire=dict(type='user',message=dict(role='user',content=[dict(type='text',text='current snapshot'),dict(type='image',source=dict(type='base64',media_type=blob.mime,data=base64.b64encode(blob.data).decode()))]))
            else:wire=dict(type='user',message=dict(role='user',content='current snapshot'))
            policy=native_contract(validate_web(dict(engine='codebuddy_cli',enabled=True,search_enabled=True)),['987654321'],InputBudget(limit=48000))
            if variant=='budget':policy['visible_limit']=100
            guard=Guard(work,'current policy','current snapshot',blob,dict(T=30,F=18000,V=1024 if image else 0,O=128000,C=1000000),
                        mode=mode,wire_message=wire,native_web=policy)
            program=work/'host.mjs';program.write_text(HARNESS,encoding='utf-8')
            node=json.loads((ROOT/'config/versions.lock.json').read_text(encoding='utf-8'))['node']['path']
            result=subprocess.run([node,str(program),str(guard.root),variant],capture_output=True,text=True,encoding='utf-8',timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(result.stdout.strip().splitlines()[-1]);proof=guard.read()
            return value,proof

    def test_image_and_text_two_steps_clipped(self):
        for image in (True,False):
            value,proof=self.host(image=image)
            self.assertEqual((value['calls'],value['steps']),(1,2))
            self.assertEqual(proof['next_calls'],2)
            self.assertLessEqual(proof['native_web']['result_bytes'],8000)
            self.assertEqual(proof['native_web']['urls'],['https://example.com/news'])
            self.assertNotIn('ref',value['output'])
            self.assertEqual(len(proof['native_web']['steps']),2)

    def test_replay_parallel_third_private_and_history_refused(self):
        for variant in ('third','private','fetch_private','replay','parallel','injection','tamper_result','step_replay','budget'):
            value,proof=self.host(variant)
            self.assertIn('refused',proof['stages'],variant)
            self.assertLessEqual(value['calls'],1,variant)
            self.assertEqual(value['steps'],0 if variant in ('step_replay','budget') else 1,variant)

    def test_three_calls_four_steps(self):
        value,proof=self.host('chain')
        self.assertEqual((value['calls'],value['steps'],proof['next_calls']),(3,4,4))
        self.assertEqual(proof['native_web']['calls'],3)
        self.assertNotIn('refused',proof['stages'])

    def test_probe_zero_next(self):
        value,proof=self.host(mode='probe')
        self.assertEqual((value['calls'],value['steps'],proof['next_calls']),(0,0,0))
        self.assertIn('probe_short_circuit',proof['stages'])

    def test_locked_sdk_tool_envelope_and_parallel_fetch(self):
        lock=json.loads((ROOT/'config/versions.lock.json').read_text(encoding='utf-8'))
        entry=ROOT/lock['cli']['entry']
        bundle=Path(os.environ.get('QQBOT_TEST_CLI_BUNDLE',str(entry.parent.parent/'dist/codebuddy-headless.js')))
        if not bundle.is_file():self.skipTest('locked CLI bundle is not installed')
        data=bundle.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),lock['cli']['headless_sha256'])
        source=data.decode('utf-8')
        # Include the unchanged reserved-key list, result helper, exception and
        # adapter; no vendor startup, network, credentials or model generation.
        module=source.split('26728(eA,el,ec){',1)[1].split('},32483(eA,el,ec){',1)[0]
        adapter=module[module.index('let eu=["tool"'):]
        self.assertTrue(adapter.endswith('}'))
        adapter='import * as ed from "node:util";\n'+adapter+'\nexport {dispatchModsToolCall};\n'
        refused=('fetch_conflict','search_drive','search_backslash','search_unc','search_private_id',
            'fetch_invalid_json','fetch_array_json','fetch_null_json','fetch_race_badplan','fetch_session_plan_wrong_id',
            'fetch_private_numeric_url','fetch_numeric_prompt')
        for variant in ('search','search_flat','search_url','search_json','fetch','fetch_json','fetch_parallel','fetch_parallel_json','fetch_race','fetch_parallel_race_json','fetch_flat','fetch_http','fetch_numeric_url','fetch_session_plan','fetch_parallel_session_plan',*refused):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as folder:
                work=Path(folder)
                policy=native_contract(validate_web(dict(engine='codebuddy_cli',enabled=True,search_enabled=True)),('987654321',),InputBudget(limit=48000))
                guard=Guard(work,'current policy','current snapshot',None,dict(T=30,F=18000,V=0,O=128000,C=1000000),
                    wire_message=dict(type='user',message=dict(role='user',content='current snapshot')),native_web=policy)
                program=work/'host.mjs';program.write_text(SDK_HARNESS,encoding='utf-8')
                actual=work/'locked-adapter.mjs';actual.write_text(adapter,encoding='utf-8')
                result=subprocess.run([lock['node']['path'],str(program),str(guard.root),variant,str(actual)],
                    capture_output=True,text=True,encoding='utf-8',timeout=15)
                self.assertEqual(result.returncode,0,result.stderr)
                value=json.loads(result.stdout.strip().splitlines()[-1]);proof=guard.read()
                if variant in refused:
                    self.assertEqual(value['calls'],0)
                    self.assertTrue(value['errors'])
                    self.assertIn('refused',proof['stages'])
                else:
                    self.assertEqual(value['calls'],2 if 'parallel' in variant else 1,(value,proof.get('reason'),proof.get('hook_error')))
                    self.assertEqual(value['errors'],[])
                    self.assertEqual(value['steps'],2)
                    self.assertNotIn('refused',proof['stages'])
                    self.assertEqual(value['second']['answer'],'final')



class NativeOutputTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_cli_tool_roundtrip_without_remote_generation(self):
        from qqbot_gateway.workbuddy_cli_runner import CLIRunner
        from qqbot_gateway import vision_mod_guard,hosted_cli_budget
        from test_lap42_vision import settings
        lock=json.loads((ROOT/'config/versions.lock.json').read_text(encoding='utf-8'))
        entry=ROOT/lock['cli']['entry']
        bundle=Path(os.environ.get('QQBOT_TEST_CLI_BUNDLE',str(entry.parent.parent/'dist/codebuddy-headless.js')))
        if not bundle.is_file():self.skipTest('locked CLI bundle is not installed')
        self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(),lock['cli']['headless_sha256'])
        fixture=r'''
export function register(on, options) {
  let calls=0;
  productionRegister((name,handler)=>{
    if(name==='turn.step')return on(name,($,e)=>handler($,e,async event=>{
      // No original next is reachable: this replaces every model request.
      if(event.index===0)return {...event,answer:'',toolUses:[0,1].map(i=>({name:'WebFetch',
        input:{url:'https://example.com/news/'+i,prompt:'Read public facts'}})),serverToolUses:[]};
      return {...event,answer:'Synthetic final answer',toolUses:[],serverToolUses:[]};
    }));
    if(name==='tool.call')return on(name,async($,e)=>{
      await $.fs.write(JSON.parse(options.request).receipt_root+'/fixture-'+(++calls)+'.json',
        JSON.stringify({input_type:typeof e.input,keys:Object.keys(e)}));
      // No original next is reachable: this replaces every network tool core.
      return handler($,e,async()=>({result:{content:'Synthetic public fact https://example.com/news',title:'Synthetic'}}));
    });
    return on(name,handler);
  },options);
}
'''
        receipts=[]
        class FixtureGuard(Guard):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                path=self.root/'hooks/register.ts'
                source=path.read_text(encoding='utf-8').replace('export function register(on, options)',
                    'function productionRegister(on, options)',1)+fixture
                path.write_text(source,encoding='utf-8')
                self.request['assets']['hooks/register.ts']=hashlib.sha256(path.read_bytes()).hexdigest()
                self.serialized=json.dumps(self.request,ensure_ascii=False,separators=(',',':'))
                path=self.root/'.codebuddy-plugin/plugin.json';value=json.loads(path.read_text(encoding='utf-8'))
                value['userConfig']['request']['default']=self.serialized;value['options']['request']=self.serialized
                path.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
                self.manifest_hash=hashlib.sha256(path.read_bytes()).hexdigest()
            def finish(self):
                receipts.extend(json.loads(p.read_text(encoding='utf-8')) for p in self.receipt_root.glob('fixture-*.json'))
                return super().finish()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'config').mkdir()
            lock['cli']['entry']=str(bundle.parent.parent/'bin/codebuddy')
            (root/'config/versions.lock.json').write_text(json.dumps(lock),encoding='utf-8')
            (root/'config/cli-tools-denied.json').write_bytes((ROOT/'config/cli-tools-denied.json').read_bytes())
            (root/'config/mcp-empty.json').write_bytes((ROOT/'config/mcp-empty.json').read_bytes())
            runner=CLIRunner(root,'deepseek-v4.1-flash',timeout=40,reasoning_effort='low',budget=InputBudget(limit=48000))
            runner.native_web=True;runner.web_config=validate_web(dict(engine='codebuddy_cli',enabled=True,search_enabled=True))
            runner.vision_settings=settings();runner.vision_settings['vision']['enabled']=False
            upper=json.loads((ROOT/'reports/lap-42-vision-closure-sources.json').read_text(encoding='utf-8'))['framework_upper_bytes']
            with patch.object(vision_mod_guard,'Guard',FixtureGuard),patch.object(hosted_cli_budget,'framework_upper',return_value=upper):
                result=await runner.run('Synthetic project policy','Synthetic public question','native-loop-fixture')
            self.assertEqual(result.text,'Synthetic final answer')
            self.assertEqual(result.parameters['native_web']['calls'],2)
            self.assertEqual(len(result.parameters['native_web']['steps']),2)
            self.assertEqual(len(receipts),2)
            self.assertTrue(all(r['input_type'] in ('string','object') for r in receipts),receipts)

    async def test_health_reports_loaded_native_and_memory_without_generation(self):
        from test_model_gateway import FakeRunner
        from qqbot_gateway.model_gateway import ModelQueue,application
        from aiohttp.test_utils import TestClient,TestServer
        runner=FakeRunner()
        runner.vision_settings={'memory':dict(enabled=True,learning_enabled=True)}
        runner.web_config=validate_web(dict(engine='codebuddy_cli',enabled=True,search_enabled=True))
        async with TestClient(TestServer(application(ModelQueue(runner),'t'*40))) as client:
            response=await client.get('/health')
            self.assertEqual(response.status,200)
            health=await response.json()
            self.assertEqual(health['native_web_tools'],['WebSearch','WebFetch'])
            self.assertEqual(health['memory'],dict(enabled=True,learning_enabled=True))
            self.assertIs(health['thinking_enabled'],False)
            self.assertEqual(runner.attempts,0)

    async def test_web_final_only_no_meme_or_memory(self):
        from types import SimpleNamespace
        from qqbot_gateway.backends import BackendResult
        from qqbot_gateway.web_retrieval import WebRunner
        from qqbot_gateway.vision import member_source
        from qqbot_gateway.reply_plan import DEFAULTS
        source=member_source('search public news',['bot'])
        source['web_anchor']='search public news'
        request=dict(must_reply=True,target_seq=source['target_seq'],addressing='mention')
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['public fact https://example.com/news','second'],
                 meme_id='should-never-send',response_to_seq=source['target_seq'],mention=None,memory_proposals=[dict(untrusted='page')])
        class Runner:
            async def run(self,*args):return BackendResult(json.dumps(raw),parameters={'native_web':dict(calls=1,result_bytes=100,sha256='a'*64,urls=['https://example.com/news'])})
        wrapper=WebRunner(Runner(),SimpleNamespace(),InputBudget(),DEFAULTS)
        reply=await wrapper.run_native_v2('system','prompt','trace',request,source,'search public news')
        self.assertIsNotNone(reply.prepared_plan)
        self.assertEqual(reply.prepared_plan.kind,'answer')
        self.assertEqual(reply.memory_proposals,())
        self.assertNotIn('should-never-send',reply.text)
        self.assertIn('https://example.com/news',reply.text)
        self.assertNotIn('主体全文',reply.text)
        from qqbot_gateway.evidence_selection import validate_manifest
        validate_manifest(list(reply.web_evidence),source)
        with self.assertRaises(ValueError):validate_manifest([dict(reply.web_evidence[0],tool_calls=4)],source)

    async def test_native_bypasses_legacy_and_no_web_chat_unchanged(self):
        from types import SimpleNamespace
        from qqbot_gateway.backends import BackendResult
        from qqbot_gateway.web_retrieval import WebRunner
        from qqbot_gateway.vision import member_source
        from qqbot_gateway.reply_plan import DEFAULTS
        original=BackendResult('original final JSON',parameters={'native_web':dict(calls=0)})
        class Runner:
            native_web=True
            async def run(self,*args):return original
        class Retriever:
            async def retrieve(self,*args):raise AssertionError('Python retrieval must not run')
        wrapper=WebRunner(Runner(),Retriever(),InputBudget(),DEFAULTS)
        self.assertEqual((await wrapper.retrieve_current('question')).kind,'none')
        source=member_source('hello',['bot'])
        result=await wrapper.run_native_v2('system','prompt','trace',dict(must_reply=True),source,'hello')
        self.assertIs(result,original)

if __name__=='__main__':unittest.main()
