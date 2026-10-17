import json
from pathlib import Path
import sys
import unittest
from copy import deepcopy

import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
from qqbot_gateway.reply_plan import DEFAULTS, make_reply_plan, trusted_plan
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.config import normalize_settings
from qqbot_gateway.persona import compose_persona, persona_version


class ReplyTests(unittest.TestCase):
    cfg=DEFAULTS | {'delivery_mode':'adaptive'}

    def raw(self,parts,kind='chat',**extra):
        return json.dumps(dict(qqbot_reply=1,kind=kind,bubbles=parts,**extra),ensure_ascii=False)

    def test_chat_counts_and_answer_merge(self):
        for count in (1,2,3):
            parts=['鱼'+str(i) for i in range(count)]
            self.assertEqual(make_reply_plan(self.raw(parts),self.cfg).bubbles,tuple(parts))
            self.assertEqual(make_reply_plan(self.raw(parts,'answer'),self.cfg).bubbles,('\n'.join(parts),))

    def test_overflow_retains_all_tail(self):
        for parts in (['一','二','三','尾'],['鱼'*41,'尾'],['鱼'*30]*3):
            p=make_reply_plan(self.raw(parts),self.cfg)
            self.assertEqual(p.bubbles,('\n'.join(parts),));self.assertEqual(p.fallback_reason,'chat_limit')
        p=make_reply_plan(self.raw(['鱼'*300,'尾']),self.cfg | {'max_reply_chars':200})
        self.assertTrue(p.limited);self.assertLessEqual(len(p.canonical_text),200)
        self.assertIn('内容未展示完',p.canonical_text)

    def test_literal_content_and_one_conversion(self):
        text='```\n**literal**\n    a && b || c\n    2.5 https://a.b/c_d 🙂\n```'
        p=make_reply_plan(self.raw([text,'尾'],'answer'),self.cfg)
        self.assertIn('**literal**',p.canonical_text)
        self.assertIn('    a && b || c',p.canonical_text)
        meta=p.metadata('chatcmpl-test')
        self.assertEqual(trusted_plan(meta,p.canonical_text,'chatcmpl-test',self.cfg),p)
        self.assertEqual(make_reply_plan('{"a":1}',self.cfg).bubbles,('{"a":1}',))
        self.assertEqual(make_reply_plan('qqbot_reply只是字段名',self.cfg).bubbles,('qqbot_reply只是字段名',))
        self.assertEqual(make_reply_plan(self.raw(['🙂','2.5 https://a.b']),self.cfg).bubbles,('🙂','2.5 https://a.b'))

    def test_explicit_serious_and_code_are_single(self):
        for question in ('请详细解释','给出步骤','给代码'):
            p=make_reply_plan(self.raw(['一','二']),self.cfg,question)
            self.assertEqual(p.bubbles,('一\n二',));self.assertEqual(p.kind,'answer')
        self.assertEqual(len(make_reply_plan(self.raw(['```\na*b\n```','尾']),self.cfg).bubbles),1)
        self.assertEqual(make_reply_plan(self.raw(['{"a":1}','说明']),self.cfg).bubbles,('{"a":1}\n说明',))

    def test_bad_protocol_never_leaks(self):
        cases=['{"qqbot_reply":','qqbot_reply',self.raw(['']),self.raw(['ok'],action='send'),
               '{"qqbot_reply":true,"kind":"chat","bubbles":["a"]}',
               '{"qqbot_reply":2,"kind":"chat","bubbles":["a"]}',
               '{"qqbot_reply":1,"kind":"chat","bubbles":["a"],"kind":"answer"}',
               self.raw([1]),self.raw(['a'],'tool'), 'prefix '+self.raw(['a'])]
        for raw in cases:
            with self.subTest(raw=raw),self.assertRaises(GatewayError) as error:make_reply_plan(raw,self.cfg)
            self.assertEqual(error.exception.code,'PROTOCOL_ERROR')
        p=make_reply_plan('```json\n'+self.raw(['a'])+'\n```',self.cfg)
        self.assertEqual(p.bubbles,('a',))

    def test_tools_decoded_and_nested_escapes_rejected(self):
        for text in ('<tool_call>Read</tool_call>','<｜DSML｜invoke name="Read">',
                     '&lt;tool_call&gt;x','\\u003ctool_call\\u003eRead',
                     '\\u005cu003ctool_call\\u005cu003e'):
            with self.subTest(text=text),self.assertRaises(GatewayError) as error:
                make_reply_plan(self.raw([text]),self.cfg)
            self.assertEqual(error.exception.code,'TOOL_ISOLATION_FAILED')

    def test_metadata_missing_inconsistent_and_boolean_version_fallback(self):
        p=make_reply_plan(self.raw(['一','二']),self.cfg);meta=p.metadata('chatcmpl-a')
        for value in (None,{},meta | {'version':True}, meta | {'response_id':'other'},
                      meta | {'content_sha256':'bad'}, meta | {'bubbles':['一']},meta | {'kind':'answer'}):
            self.assertEqual(trusted_plan(value,p.canonical_text,'chatcmpl-a',self.cfg).bubbles,('一\n二',))

    def test_config_compatibility_strict_ranges_and_version(self):
        raw=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        raw['bot']['qq']='222';raw['access'].update(allowed_groups=['111'],admin_users=['333'])
        for version in (1,2):
            old=deepcopy(raw);old['schema_version']=version;old['output']={'mode':'plain_chat','max_reply_chars':1200}
            self.assertEqual(normalize_settings(old)['output']['delivery_mode'],'single')
            self.assertNotIn('delivery_mode',old['output'])
        for key in ('max_bubbles','casual_max_chars','bubble_max_chars','bubble_delay_min_ms','bubble_delay_max_ms'):
            for value in (True,1.5,'3',-1,9000):
                bad=deepcopy(raw);bad['output'][key]=value
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):normalize_settings(bad)
        for fields in ({'bubble_max_chars':60,'casual_max_chars':20},{'bubble_delay_min_ms':1000,'bubble_delay_max_ms':500}):
            bad=deepcopy(raw);bad['output'].update(fields)
            with self.assertRaises(ValueError):normalize_settings(bad)
        single=compose_persona('character')
        adaptive=compose_persona('character',self.cfg)
        self.assertNotEqual(persona_version(single),persona_version(adaptive))
        self.assertEqual(adaptive,compose_persona('character',self.cfg | {'bubble_delay_min_ms':0}))
        self.assertNotEqual(adaptive,compose_persona('character',self.cfg | {'max_bubbles':2}))


if __name__=='__main__':unittest.main()
