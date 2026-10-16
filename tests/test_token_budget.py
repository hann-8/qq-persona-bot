import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.token_budget import InputBudget, dialog_text, validate_model_settings
from qqbot_gateway.contracts import normalize_request
from qqbot_gateway.errors import GatewayError


class BudgetTests(unittest.TestCase):
    def test_chinese_emoji_and_json_escapes_use_wire_bytes(self):
        text='中文🙂\\"\n\t'*10
        prompt=dialog_text([{'role':'user','content':text}])
        budget=InputBudget(overhead=32)
        self.assertGreater(budget.usage('人设',prompt),len(text.encode())+32)
        exact=budget.usage('人设',prompt)
        InputBudget(limit=exact,overhead=32).check('人设',prompt)
        with self.assertRaises(GatewayError):InputBudget(limit=exact-1,overhead=32).check('人设',prompt)

    def test_trims_oldest_complete_turns_and_tool_pollution(self):
        history=[{'role':'assistant','content':'orphan'},
                 {'role':'user','content':'old'*100},{'role':'assistant','content':'old answer'},
                 {'role':'user','content':'polluted'},{'role':'assistant','content':'<tool_call>Read</tool_call>'},
                 {'role':'user','content':'new'},{'role':'assistant','content':'new answer'}]
        selected=InputBudget(limit=400,overhead=32).select_history('SYS','current',history)
        self.assertEqual([m['content'] for m in selected],['new','new answer'])
        self.assertEqual(InputBudget(history_turns=1).select_history('SYS','current',history),[])

    def test_never_truncates_system_or_current_question(self):
        budget=InputBudget(limit=1024,overhead=128)
        for system,question in [('人设'*1000,'hi'),('SYS','🙂'*1000)]:
            with self.assertRaises(GatewayError) as error:budget.select_history(system,question,[])
            self.assertEqual(error.exception.code,'INPUT_TOO_LONG')

    def test_capacity_input_and_total_window_are_distinct(self):
        InputBudget(limit=1000,output=2000,max_input=1000).validate_capacity()
        with self.assertRaises(ValueError):InputBudget(limit=1001,max_input=1000).validate_capacity()
        with self.assertRaises(ValueError):InputBudget(limit=1000,output=100,window=1099).validate_capacity()

    def test_more_than_old_character_and_message_limits(self):
        budget=InputBudget(limit=100000,overhead=0,history_turns=64)
        messages=[{'role':'system','content':'SYS'}]
        for i in range(63):messages += [{'role':'user','content':str(i)},{'role':'assistant','content':'a'}]
        messages += [{'role':'user','content':'x'*25000}]
        self.assertEqual(len(messages),128)
        _,prompt=normalize_request({'model':'workbuddy-local','messages':messages},budget=budget)
        self.assertEqual(len(json.loads(prompt)),127)
        with self.assertRaises(GatewayError):normalize_request({'model':'workbuddy-local','messages':messages})
        self.assertEqual(InputBudget(limit=1048576).payload_limit,8*1024*1024)
        self.assertEqual(InputBudget(limit=1024).payload_limit,512*1024)

    def test_explicit_effort_unknown_native_and_capacity_refuse(self):
        settings={'llm':{'model':'x','reasoning_effort':'high'},'chat':{
            'history_turns':8,'context_input_limit_tokens':16384,
            'context_overhead_reserve_tokens':2048,'output_reserve_tokens':2048}}
        with self.assertRaises(ValueError):validate_model_settings(settings,{})
        metadata={'x':{'maxInputTokens':20000,'reasoning':{'supportedEfforts':['high']}}}
        validate_model_settings(settings,metadata)
        settings['llm']['context_window_tokens']=200000
        with self.assertRaises(ValueError):validate_model_settings(settings,metadata)


if __name__=='__main__':unittest.main()
