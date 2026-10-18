"""M01--12: generated identities/text and temporary stores only."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

from qqbot_gateway.group_memory import MemoryStore,DEFAULTS,validate_config,proposals,wire_proposals,size
from qqbot_gateway.vision import member_source
from qqbot_gateway.turn_v2 import fit,manifest,sha,validate_source,plan,metadata,verify
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT
from qqbot_gateway.token_budget import InputBudget

class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.now=1000000.;self.count=0
        self.cfg=DEFAULTS|dict(enabled=True,learning_enabled=True)
        self.store=self.new();self.ref=None
    def new(self,**kwargs):return MemoryStore(self.root,kwargs.pop('bot','222'),kwargs.pop('groups',['111','444']),kwargs.pop('blocked',[]),['333'],kwargs.pop('cfg',self.cfg),clock=lambda:self.now,**kwargs)
    def doc(self,g='111'):return json.loads(self.store.path(g).read_text(encoding='utf-8'))
    def turn(self,text='我喜欢茶',sender='555',group='111',mid=None,kind='preference',slot='likes',fact='茶',subject=None,phase='inbound',targets=None):
        self.count+=1;self.now+=.1;s=member_source(text,['botname']);ref=s['messages'][0]['member_ref'];self.ref=ref
        context=self.store.prepare(group,f'{self.count:064x}',s,{ref:sender},{1:(sender,mid or str(self.count),self.now)})
        p=dict(op='add',subject_ref=subject or ref,kind=kind,slot=slot,fact=fact,source_seqs=[1],target_ids=targets or [],phase=phase,ack_parts=[] if phase=='inbound' else [0],privacy='general')
        return context,s,p
    def stage(self,c,s,p,parts=None):self.store.stage(c,[dict(index=0,proposal=p,parts=parts or [])],s)
    def add(self,**kw):
        c,s,p=self.turn(**kw);self.stage(c,s,p);self.store.close(c);return c,s,p
    def test_M01_schema_key_restart_and_namespace_isolation(self):
        self.add();d=self.doc();self.assertEqual(len(d['records']),1)
        other=self.new(bot='223');self.assertNotEqual(other.path('111'),self.store.path('111'))
        other=self.new(bot='223',blocked=['555']);self.assertEqual(len(self.doc()['records']),1)
        self.assertNotEqual(self.store.actor('111','555'),self.store.actor('444','555'))
        self.assertEqual(self.new().path('111'),self.store.path('111'))
        self.assertNotIn('"555"',json.dumps(d));self.assertEqual(self.new().manage('111','inspect')['records'],1)
        (self.root/'secrets/group-memory-key.local.json').unlink();lost=self.new();self.assertIn('111',lost.disabled);self.assertIsNone(lost.key)
    def test_M02_peer_candidate_independent_self_promotion_admin(self):
        self.add(text='自造乙喜欢茶',sender='666',subject='group',kind='background',slot='shared_topic',fact='茶')
        self.assertEqual(self.doc()['records'][0]['status'],'candidate')
        # Same stable member subject with independently mapped source actor.
        c,s,p=self.turn();ref='p_'+'b'*16;s['messages'][0]['member_ref']=ref
        c['subjects'][ref]=self.store.actor('111','666');p['subject_ref']=ref
        self.stage(c,s,p);self.store.close(c)
        self.assertEqual(self.doc()['records'][-1]['status'],'candidate')
        rid=self.doc()['records'][-1]['id']
        self.add(sender='666');r=next(r for r in self.doc()['records'] if r['id']==rid)
        self.assertEqual(r['status'],'active');self.assertEqual(r['confidence'],2)
        self.add(sender='333',text='本群主题是种茶',subject='group',kind='background',slot='shared_topic',fact='种茶')
        self.assertEqual(self.doc()['records'][-1]['confidence'],3)
    def test_M03_mentions_no_history_and_large_group_sender(self):
        c,s,p=self.turn();p['source_seqs']=[999];self.stage(c,s,p);self.store.close(c)
        self.assertFalse(self.doc()['records'])
        self.add();c,s,p=self.turn();self.assertEqual(len(s['memory']['records']),1)
        c2,s2,p2=self.turn(sender='666');self.assertEqual(s2['memory']['records'],[])
        self.store.close(c);self.store.close(c2)
    def test_M04_inbound_and_acked_commitment_partial_unknown(self):
        c,s,p=self.turn();self.stage(c,s,p);self.assertEqual(len(self.doc()['records']),1);self.store.close(c)
        for ack,expected in (([],1),([(0,'unknown','')],1),([(1,'sent','m')],1),([(0,'sent','m')],2)):
            c,s,p=self.turn(text='请明天提醒',subject='group',kind='bot_commitment',slot='commitment',fact='明天提醒',phase='acked_bot')
            self.stage(c,s,p,[0]);self.assertTrue(self.doc()['pending']);self.store.close(c,ack)
            self.assertEqual(len(self.doc()['records']),expected)
        self.assertFalse(self.doc()['pending'])
    def test_M05_base_revision_CAS_and_closed_marker(self):
        self.add();a,s,p=self.turn();b,t,q=self.turn(text='我喜欢咖啡',fact='咖啡')
        p.update(op='replace',target_ids=[s['memory']['records'][0]['fact_ref']])
        q.update(op='replace',target_ids=[t['memory']['records'][0]['fact_ref']])
        self.stage(b,t,q);self.store.close(b);self.stage(a,s,p);self.store.close(a)
        self.assertEqual(self.doc()['records'][0]['fact'],'咖啡')
        before=self.doc();self.stage(a,s,p);self.store.close(a,[(0,'sent','x')]);self.assertEqual(self.doc(),before)
    def test_M06_purge_generation_late_ACK_restart_pending(self):
        c,s,p=self.turn(text='请明天提醒',subject='group',kind='bot_commitment',slot='commitment',fact='明天提醒',phase='acked_bot')
        self.stage(c,s,p,[0]);generation=self.doc()['generation'];restart=self.new();self.assertFalse(restart._load('111')['pending'])
        info=self.store.manage('111','inspect');self.store.manage('111','clear',expected=info['digest'])
        self.assertNotEqual(self.doc()['generation'],generation);self.store.close(c,[(0,'sent','id')]);self.assertFalse(self.doc()['records'])
    def test_M07_same_source_no_TTL_and_single_multi(self):
        self.add(mid='same');before=deepcopy(self.doc()['records'][0]);self.now+=100
        self.add(mid='same');self.assertEqual(self.doc()['records'][0],before)
        self.add(fact='咖啡',text='我喜欢咖啡');self.assertEqual(len(self.doc()['records']),2)
        self.add(kind='name',slot='preferred_name',text='我叫甲',fact='甲');self.now+=100
        self.add(kind='name',slot='preferred_name',text='我叫乙',fact='乙');names=[r for r in self.doc()['records'] if r['kind']=='name']
        self.assertEqual(len(names),1);self.assertEqual(names[0]['fact'],'乙');self.assertEqual(names[0]['conflict_old'],'甲')
    def test_M08_effective_refs_and_combined_budget(self):
        self.add();c,s,p=self.turn();s['member_candidates']=[]
        request=dict(version=2,kind='member_turn',mode='mentions',request_key='a'*64,epoch='b'*64,config_version='c'*64,source_digest=sha(s),addressing='mention',must_reply=True,target_seq=1,resource_caps=[])
        validate_source(json.dumps(s),request)
        fitted=json.loads(fit(s,request,'policy',InputBudget(limit=900,overhead=0,output=0)))
        self.assertTrue(fitted['memory'] is None or size(fitted['memory'])<=180)
        p['target_ids']=['f_'+'f'*32];p['op']='replace';self.assertFalse(proposals([p],fitted))
        self.store.close(c)
    def test_M09_bad_aux_core_truncation_disk_error(self):
        c,s,p=self.turn();request={'must_reply':True,'target_seq':1}
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['你好'],meme_id=None,response_to_seq=1,mention=None,memory_proposals=[p|{'extra':1}])
        aux=[];decision,result,_=plan(json.dumps(raw),OUTPUT,'',request,s,memory_out=aux)
        self.assertEqual(result.canonical_text,'你好');self.assertFalse(aux)
        aux=[];plan(json.dumps(raw)[:-5],OUTPUT,'',request,s,memory_out=aux);self.assertFalse(aux)
        with patch.object(self.store,'_write',side_effect=OSError('synthetic')):self.stage(c,s,p)
        self.assertIn('111',self.store.disabled);self.assertIsNone(self.store.prepare('111','d'*64,s,{},{ }))
    def test_M10_blacklist_pinned_all_copies_and_persistent_failure(self):
        self.add();info=self.store.manage('111','inspect');rid=self.doc()['records'][0]['id']
        self.store.manage('111','pin',record_id=rid,expected=info['digest'])
        path=self.store.path('111');(path.parent/'memory.md').write_text('self fixture');(path.parent/'memory.bak').write_text('self fixture')
        blocked=self.new(blocked=['555']);self.assertFalse(blocked._load('111')['records']);self.assertFalse((path.parent/'memory.md').exists())
        self.add();(path.parent/'memory.md').write_text('fixture')
        info=self.store.manage('111','inspect');original=Path.unlink
        def fail(p,*a,**kw):
            if p.name=='memory.md':raise OSError('synthetic sharing violation')
            return original(p,*a,**kw)
        with patch.object(Path,'unlink',fail):
            with self.assertRaises(OSError):self.store.manage('111','clear',expected=info['digest'])
            self.assertIsNotNone(self.doc()['purge']);self.assertIn('111',self.new().disabled)
        recovered=self.new();self.assertIsNone(recovered._load('111')['purge']);self.assertFalse(recovered._load('111')['records'])
    def test_M11_group_total_pending_marker_caps(self):
        groups=[str(100+i) for i in range(17)];self.store=self.new(groups=groups)
        for g in groups[:16]:self.add(group=g)
        c,s,p=self.turn(group=groups[-1]);self.assertIsNone(c);self.assertFalse(self.store.path(groups[-1]).exists())
        self.store=self.new();contexts=[]
        for i in range(8):contexts.append(self.turn()[0])
        self.assertIsNone(self.turn()[0])
        for c in contexts:self.store.close(c)
        doc=self.doc();doc['applied_txns']=['f'*64]*129
        with self.assertRaises(ValueError):self.store._write('111',doc)
        tiny=self.new(cfg=self.cfg|dict(max_total_bytes=1));self.assertIsNone(tiny.prepare('111','e'*64,member_source('我喜欢茶',['bot']),{},{}))
    def test_M12_disabled_and_invalid_config_no_files(self):
        with tempfile.TemporaryDirectory() as directory:
            off=MemoryStore(directory,'222',['111']);self.assertIsNone(off.key);self.assertFalse((Path(directory)/'secrets').exists())
        for cfg in ({'learning_enabled':True},{'extra':1},{'enabled':1},{'max_groups':17}):
            with self.assertRaises(ValueError):validate_config(cfg)
    def test_merge_actor_dependencies_expiry_stable_eviction(self):
        self.add();self.add(text='我喜欢咖啡',fact='咖啡');c,s,p=self.turn(text='我喜欢茶和咖啡',fact='茶和咖啡')
        p.update(op='merge',target_ids=[v['fact_ref'] for v in s['memory']['records']]);self.stage(c,s,p);self.store.close(c)
        self.assertEqual(len(self.doc()['records']),1);self.assertEqual(len(self.doc()['records'][0]['source_refs']),3)
        self.now+=91*86400;c,s,p=self.turn();self.assertFalse(s['memory']['records']);self.store.close(c)
        self.store=self.new(cfg=self.cfg|dict(max_records=1));self.add();self.now+=1;self.add(text='我喜欢咖啡',fact='咖啡')
        self.assertEqual(self.doc()['records'][0]['fact'],'咖啡')
    def test_ack_mapping_single_and_adaptive(self):
        c,s,p=self.turn(text='请明天提醒',subject='group',kind='bot_commitment',slot='commitment',fact='明天提醒',phase='acked_bot')
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['明天提醒','记下了'],meme_id=None,response_to_seq=1,mention=None,memory_proposals=[p])
        for mode,expected in [('single',[0]),('adaptive',[0])]:
            aux=[];decision,r,_=plan(json.dumps(raw),OUTPUT|dict(delivery_mode=mode),'',dict(must_reply=True,target_seq=1),s,memory_out=aux)
            self.assertEqual(aux[0]['parts'],expected)
        p['ack_parts']=[9];self.assertFalse(wire_proposals([p],s,raw['bubbles'],r))
    def test_manual_lock_digest_export_sensitive_and_quota(self):
        self.add();info=self.store.manage('111','inspect');rid=self.doc()['records'][0]['id']
        exported=self.store.manage('111','export',expected=info['digest']);self.assertEqual(Path(exported['path']).name,'memory.md')
        with self.assertRaises(ValueError):self.store.manage('111','pin',record_id=rid,expected='f'*64)
        with self.assertRaises(ValueError):self.store.manage('111','correct',record_id=rid,expected=info['digest'],fact='我的密码abc')
        from qqbot_gateway.group_memory import locked
        with locked(self.root):
            with self.assertRaises((OSError,ValueError)):
                with locked(self.root):pass

    def test_retired_group_blacklist_and_derived_actor_delete(self):
        self.add(group='444');path=self.store.path('444');(path.parent/'memory.bad').write_text('synthetic copy')
        retired=self.new(groups=['111'],blocked=['555'])
        self.assertFalse(json.loads(path.read_text())['records']);self.assertFalse((path.parent/'memory.bad').exists())
        self.assertFalse(retired._load('retired:'+path.parent.name)['records'])
    def test_many_blacklist_subjects_never_expand_to_group_clear(self):
        self.add(sender='555');self.add(sender='666')
        blocked=self.new(blocked=['555']+[str(1000+i) for i in range(40)])
        rows=blocked._load('111')['records'];self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['subject_key'],blocked.actor('111','666'))
        self.assertIsNone(blocked._load('111')['purge'])
    def test_affirmative_self_only_not_report_question_or_guess(self):
        for text in ('我不知道别人喜欢茶','我猜小明喜欢茶','我喜欢茶吗','听说我喜欢茶','如果我喜欢茶'):
            self.add(text=text,fact='茶')
        self.assertEqual(self.doc()['records'][0]['status'],'candidate')
        self.add(text='我喜欢茶');self.assertEqual(self.doc()['records'][0]['status'],'active')
    def test_txn_id_fixed_input_revision_and_phase(self):
        a,s,p=self.turn();fixed=a['base_revision'];self.add(text='我喜欢咖啡',fact='咖啡')
        self.stage(a,s,p)
        marker=self.store.hmac('txn',a['request_key'],0,fixed,'inbound',a['generation'])
        self.assertIn(marker,self.doc()['applied_txns']);self.store.close(a)
        self.assertEqual(len(self.doc()['records']),2)
    def test_batch_first_conflicting_operation_only_and_five_sources(self):
        c,s,p=self.turn(text='我叫甲 我叫乙',fact='甲',kind='name',slot='preferred_name')
        second=p|dict(fact='乙')
        self.store.stage(c,[dict(index=0,proposal=p,parts=[]),dict(index=1,proposal=second,parts=[])],s);self.store.close(c)
        self.assertEqual(self.doc()['records'][0]['fact'],'甲')
        for _ in range(6):self.add()
        r=next(r for r in self.doc()['records'] if r['kind']=='preference')
        self.assertLessEqual(len(r['source_refs']),4)
        before=deepcopy(r);self.now-=100
        self.add(mid='earlier-source');self.assertEqual(next(r for r in self.doc()['records'] if r['kind']=='preference'),before)
    def test_purge_first_write_failure_does_not_claim_persistence(self):
        self.add();before=self.doc();info=self.store.manage('111','inspect')
        with patch.object(self.store,'_write',side_effect=OSError('synthetic disk full')):
            with self.assertRaisesRegex(ValueError,'not persisted'):self.store.manage('111','clear',expected=info['digest'])
        self.assertEqual(self.doc(),before);self.assertIn('111',self.store.disabled)
    def test_pinned_correction_delete_and_schema_corruption_fail_closed(self):
        for fact in ('茶','咖啡','牛奶','果汁','汽水'):self.add(text='我喜欢'+fact,fact=fact)
        for record in self.doc()['records'][:4]:
            info=self.store.manage('111','inspect');self.store.manage('111','pin',record_id=record['id'],expected=info['digest'])
        info=self.store.manage('111','inspect')
        with self.assertRaises(ValueError):self.store.manage('111','pin',record_id=self.doc()['records'][-1]['id'],expected=info['digest'])
        self.assertEqual(sum(r['pinned'] for r in self.doc()['records']),4)
        rid=self.doc()['records'][0]['id'];self.store.manage('111','delete',record_id=rid,expected=info['digest'])
        self.assertNotIn(rid,[r['id'] for r in self.doc()['records']])
        path=self.store.path('111');original=path.read_text();path.write_text(original[:-1]+',"unknown":1}')
        bad=self.new();self.assertIn('111',bad.disabled);self.assertIn('unknown',path.read_text())
    def test_expired_live_request_late_ack_and_pending_temporary_caps(self):
        contexts=[self.turn()[0] for _ in range(8)];self.now+=601
        c,s,p=self.turn();self.assertIsNotNone(c)
        before=self.doc();self.stage(contexts[0],s,p);self.assertEqual(before,self.doc())
        self.store.close(c)
        doc=self.doc();doc['pending']=[dict(request_key=f'{i:064x}',generation=doc['generation'],base_revision=doc['revision'],expires_at=self.now+600,items=[{}]*3) for i in range(9)]
        with self.assertRaises(ValueError):self.store._write('111',doc)
    def test_merge_does_not_drop_actor_dependencies_to_fit(self):
        self.add();self.add(text='我喜欢咖啡',fact='咖啡');doc=self.doc()
        doc['records'][0]['actor_dependencies']=[f'{i:064x}' for i in range(1,9)]
        self.store._write('111',doc)
        c,s,p=self.turn(text='我喜欢茶和咖啡',fact='茶和咖啡');p.update(op='merge',target_ids=[r['fact_ref'] for r in s['memory']['records']])
        self.stage(c,s,p);self.store.close(c)
        self.assertEqual(len(self.doc()['records']),2);self.assertEqual(len(self.doc()['records'][0]['actor_dependencies']),8)
    def test_metadata_effective_fact_revision_and_silent_phase(self):
        self.add();c,s,p=self.turn();request=dict(version=2,kind='member_turn',mode='mentions',request_key='a'*64,epoch='b'*64,config_version='c'*64,source_digest=sha(s),addressing='mention',must_reply=True,target_seq=1,resource_caps=[])
        aux=[];raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['你好'],meme_id=None,mention=None,memory_proposals=[p])
        decision,r,response=plan(json.dumps(raw),OUTPUT,'',request,s,memory_out=aux)
        value=metadata(request,'chatcmpl-x',decision,r,s,response,memory_proposals=aux)
        self.assertEqual(verify(value,request,'chatcmpl-x',r.canonical_text,OUTPUT,s),r)
        value['manifest']['memory']['records'][0]['record_revision']+=1;value['plan_hash']=sha({k:v for k,v in value.items() if k!='plan_hash'})
        with self.assertRaises(ValueError):verify(value,request,'chatcmpl-x',r.canonical_text,OUTPUT,s)
    def test_combined_member_memory_budget_and_bad_proposal_independence(self):
        for i in range(8):self.add(text='我喜欢茶'+str(i),fact='茶'+str(i))
        c,s,p=self.turn();s['member_candidates']=[dict(member_ref='p_'+f'{i:016x}',name='合成名字'*5,aliases=[]) for i in range(8)]
        request=dict(must_reply=True,target_seq=1,addressing='mention')
        body=json.loads(fit(s,request,'policy',InputBudget(limit=4000,overhead=0,output=0)))
        extra=(size(body['memory']) if body['memory'] else 0)+(size(body['member_candidates']) if body['member_candidates'] else 0)
        self.assertLessEqual(extra,800);self.assertLessEqual(size(body['member_candidates']),768)
        values=[p|{'privacy':'sensitive'},p,p|{'source_seqs':[1,1]}]
        self.assertEqual([i['index'] for i in proposals(values,s)],[1])
    def test_missing_primary_does_not_silently_create_blank(self):
        self.add();path=self.store.path('111');(path.parent/'memory.bak').write_bytes(path.read_bytes());path.unlink()
        broken=self.new();self.assertIn('111',broken.disabled)
        self.assertIsNone(broken.prepare('111','f'*64,member_source('我喜欢茶',['bot']),{},{}));self.assertFalse(path.exists())
    def test_valid_inbound_independent_of_body_length_normalization(self):
        c,s,p=self.turn();aux=[]
        raw=dict(qqbot_turn_reply=2,decision='speak',kind='chat',bubbles=['长'*100],meme_id=None,mention=None,memory_proposals=[p])
        decision,result,_=plan(json.dumps(raw),OUTPUT,'',dict(must_reply=True,target_seq=1),s,memory_out=aux)
        self.assertEqual(decision,'speak');self.assertTrue(aux);self.assertEqual(result.fallback_reason,'chat_limit')
    def test_real_child_process_cannot_bypass_OS_memory_lock(self):
        import subprocess
        from qqbot_gateway.group_memory import locked
        source=str(Path(__file__).resolve().parents[1]/'src')
        code="import sys\nsys.path.insert(0,sys.argv[1])\nfrom qqbot_gateway.group_memory import locked\ntry:\n with locked(sys.argv[2]): pass\nexcept (OSError,ValueError): sys.exit(0)\nsys.exit(1)\n"
        with locked(self.root):
            result=subprocess.run([sys.executable,'-X','utf8','-c',code,source,str(self.root)],capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr.decode())
    def test_record_subject_and_actual_atomic_temporary_space_limits(self):
        for i in range(65):self.add(text='我喜欢茶'+str(i),fact='茶'+str(i))
        doc=self.doc();self.assertEqual(len(doc['records']),64);self.assertNotIn('茶0',[r['fact'] for r in doc['records']])
        self.assertLessEqual(size(doc)+2048,65536)
        for i in range(33):self.add(sender=str(1000+i),text='我喜欢茶',fact='茶')
        doc=self.doc();self.assertLessEqual(len({r['subject_key'] for r in doc['records']}),32)
        before=self.store.path('111').read_bytes();self.store.cfg['max_total_bytes']=self.store._total()+size(doc)-1
        with self.assertRaisesRegex(ValueError,'temporary quota'):self.store._write('111',doc)
        self.assertEqual(self.store.path('111').read_bytes(),before)
    def test_actual_local_management_menu_digest_and_legacy_export(self):
        import yaml
        from scripts.configure_bot import memory_action,ConfigMenu
        from qqbot_gateway.config import read_settings,export_legacy_config
        settings=yaml.safe_load((Path(__file__).resolve().parents[1]/'config/settings.example.yaml').read_text(encoding='utf-8'))
        settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333'],blocked_users=['999'])
        settings['memory']=self.cfg
        path=self.root/'config/settings.local.yaml';path.parent.mkdir();path.write_text(yaml.safe_dump(settings),encoding='utf-8')
        settings,config_digest=read_settings(path)
        info=memory_action(path,'111','inspect',config_digest=config_digest)
        memory_action(path,'111','add',user='555',kind='preference',slot='likes',fact='茶',expected=info['digest'],config_digest=config_digest)
        with self.assertRaises(ValueError):memory_action(path,'111','inspect',config_digest='f'*64)
        class UI:
            def __init__(self):self.values=iter(['3','111','1','已核对']);self.rows=[]
            def page(self,*a):pass
            def write(self,text):self.rows.append(text)
            def pause(self):pass
            def read(self,*a):return next(self.values)
            def choose(self,allowed):
                value=next(self.values);assert value in allowed;return value
        ui=UI();ConfigMenu(path,ui).memory_group();self.assertTrue((self.store.path('111').parent/'memory.md').exists())
        result=export_legacy_config(path);old=yaml.safe_load(Path(result['review']).read_text(encoding='utf-8'))
        self.assertNotIn('memory',old);self.assertTrue(read_settings(path)[0]['memory']['enabled'])

if __name__=='__main__':unittest.main()
