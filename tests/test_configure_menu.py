from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import psutil
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from scripts.configure_bot import ConfigMenu, main, menu
from scripts.console_ui import Console
from qqbot_gateway.config import load_settings, configuration_lock


class RecordedConsole(Console):
    def __init__(self, answers):
        self.answers = iter(answers)
        self.events = []
        super().__init__(self.answer, self.output, interactive=True)
    def clear(self):self.events.append(('clear', None))
    def answer(self, prompt):
        self.events.append(('input', prompt))
        result = next(self.answers)
        if isinstance(result, BaseException):raise result
        if callable(result):result = result()
        return result
    def output(self, text, **kwargs):self.events.append(('text', str(text)))
    @property
    def text(self):return '\n'.join(value for kind,value in self.events if kind != 'clear')


class MenuTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='qqbot menu ')
        self.root = Path(self.temp.name)
        (self.root/'config').mkdir()
        self.path = self.root/'config/settings.local.yaml'
        settings = yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
        settings['bot']['qq'] = '222'
        settings['access'].update(allowed_groups=['111'], admin_users=['333'])
        settings['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'] = 200000
        settings['extension'] = {'preserve':'existing'}
        self.path.write_text(yaml.safe_dump(settings), encoding='utf-8')
        self.original = self.path.read_bytes()
    def tearDown(self):self.temp.cleanup()

    def test_page_timing_keeps_list_visible_until_enter_and_main_hides_ids(self):
        ui = RecordedConsole(['1','1','','0','0'])
        menu(self.path, ui)
        listed = next(i for i,e in enumerate(ui.events) if e == ('text','  1.  111'))
        pause = next(i for i,e in enumerate(ui.events[listed+1:],listed+1) if e[0] == 'input')
        self.assertIn('按回车返回',ui.events[pause][1])
        self.assertFalse(any(kind == 'clear' for kind,_ in ui.events[listed+1:pause+1]))
        self.assertEqual(ui.events[pause+1][0],'clear')
        before_list='\n'.join(value for kind,value in ui.events[:listed] if kind=='text')
        self.assertNotIn('111',before_list)
        self.assertNotIn('原生窗口',before_list)
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_non_tty_never_clears_or_writes_ansi(self):
        output=[]
        answers=iter(['invalid','0'])
        ui=Console(lambda _:next(answers),lambda text,**kw:output.append(text),interactive=False)
        with patch('scripts.console_ui.subprocess.run') as shell:
            menu(self.path,ui)
        shell.assert_not_called()
        text='\n'.join(output)
        self.assertNotIn('\033',text)
        self.assertEqual(text.count('机器人配置'),1)
        if os.name == 'nt':
            fallback=Console(write=lambda text,**kw:output.append(text),interactive=True)
            with patch('scripts.console_ui.subprocess.run',side_effect=OSError('no terminal')) as shell:
                fallback.page('仍可阅读');fallback.page('下一页')
            self.assertEqual(shell.call_count,1)
            self.assertIn('仍可阅读\n',output)

    def test_each_field_has_its_own_prompt_and_cancel_never_writes(self):
        for section,action,name,detail in [('groups','add','群号','123456789'),
                ('groups','remove','完整群号','至少保留一个'),('blacklist','add','QQ号','所有授权群'),
                ('model','set','模型ID','字符串'),('context','set','输入预算','UTF-8'),
                ('effort','set','编号或英文值','auto'),('history','set','记忆轮数','1—64')]:
            with self.subTest(section=section,action=action):
                ui=RecordedConsole(['',''])
                ConfigMenu(self.path,ui).edit(section,action)
                self.assertIn(name,ui.text);self.assertIn(detail,ui.text)
                self.assertNotIn('输入ID/预算/强度/轮数',ui.text)
                self.assertEqual(self.path.read_bytes(),self.original)

    def test_bad_number_then_valid_budget_is_one_page_and_preserves_unknown_fields(self):
        ui=RecordedConsole(['1e5','3','32768',''])
        ConfigMenu(self.path,ui).edit('context','set')
        result=load_settings(self.path)
        self.assertEqual(result['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'],32768)
        self.assertEqual(result['extension'],{'preserve':'existing'})
        self.assertEqual(sum(kind=='clear' for kind,_ in ui.events),1)
        self.assertIn('1024—1048576',ui.text)

    def test_effort_numbers_and_case_map_to_supported_strings(self):
        for value,expected in [('1','auto'),('2','low'),('HIGH','high'),('max','max')]:
            with self.subTest(value=value):
                ui=RecordedConsole(['99',value,''])
                ConfigMenu(self.path,ui).edit('effort','set')
                result=load_settings(self.path)
                self.assertEqual(result['llm']['profiles']['codebuddy_cli']['reasoning_effort'],expected)
                self.assertEqual(result['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'],200000)

    def test_unknown_model_effort_only_auto_and_no_fallback(self):
        settings=load_settings(self.path);settings['llm']['profiles']['codebuddy_cli']['model']='unknown-model'
        self.path.write_text(yaml.safe_dump(settings),encoding='utf-8')
        ui=RecordedConsole(['high','2','auto',''])
        ConfigMenu(self.path,ui).edit('effort','set')
        self.assertIn('仅允许auto',ui.text)
        self.assertEqual(load_settings(self.path)['llm']['profiles']['codebuddy_cli']['reasoning_effort'],'auto')

    def test_live_lock_conflict_and_failed_replace_are_actionable_and_preserve_file(self):
        ui=RecordedConsole(['32768',''])
        with configuration_lock(self.root):ConfigMenu(self.path,ui).edit('context','set')
        self.assertIn('操作正在进行',ui.text)
        self.assertEqual(self.path.read_bytes(),self.original)
        state=self.root/'state/managed-processes.json'
        state.write_text(json.dumps([{'pid':os.getpid(),'created':psutil.Process().create_time()}]),encoding='utf-8')
        ui=RecordedConsole(['32768','']);ConfigMenu(self.path,ui).edit('context','set')
        self.assertIn('先关闭机器人',ui.text)
        state.unlink()
        ui=RecordedConsole(['32768',''])
        with patch('qqbot_gateway.config.os.replace',side_effect=OSError('SECRET RAW PAYLOAD')):
            ConfigMenu(self.path,ui).edit('context','set')
        self.assertNotIn('SECRET',ui.text);self.assertIn('未保存',ui.text)
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_digest_conflict_reentry_reads_latest_value_without_overwriting(self):
        def concurrent_edit():
            raw=yaml.safe_load(self.path.read_text(encoding='utf-8'));raw['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens']=65536
            self.path.write_text(yaml.safe_dump(raw),encoding='utf-8')
            return '32768'
        ui=RecordedConsole([concurrent_edit,''])
        editor=ConfigMenu(self.path,ui);editor.edit('context','set')
        self.assertIn('配置已在别处更新',ui.text)
        self.assertEqual(load_settings(self.path)['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'],65536)
        ui=RecordedConsole(['','']);ConfigMenu(self.path,ui).edit('context','set')
        self.assertIn('当前输入预算：65536',ui.text)

    def test_remove_last_group_fails_and_blocked_add_uses_qq_number(self):
        ui=RecordedConsole(['111','']);ConfigMenu(self.path,ui).edit('groups','remove')
        self.assertIn('至少保留一个授权群',ui.text)
        self.assertEqual(self.path.read_bytes(),self.original)
        ui=RecordedConsole(['555','']);ConfigMenu(self.path,ui).edit('blacklist','add')
        self.assertEqual(load_settings(self.path)['access']['blocked_users'],['555'])
        self.assertEqual(load_settings(self.path)['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'],200000)
        ui=RecordedConsole(['555','']);ConfigMenu(self.path,ui).edit('blacklist','remove')
        self.assertIn('要移除的完整QQ号',ui.text)
        self.assertEqual(load_settings(self.path)['access']['blocked_users'],[])

    def test_details_are_opt_in_and_eof_or_interrupt_exit_cleanly(self):
        ui=RecordedConsole(['3','','0']);menu(self.path,ui)
        self.assertIn('原生窗口',ui.text);self.assertIn('强制压缩',ui.text)
        for exception in (EOFError(),KeyboardInterrupt()):
            ui=RecordedConsole([exception]);output=StringIO()
            with patch('scripts.configure_bot.ROOT',self.root),patch('scripts.configure_bot.Console',return_value=ui), \
                 patch.object(sys,'argv',['configure_bot.py']),redirect_stdout(output):
                self.assertEqual(main(),0)
            self.assertIn('已退出',output.getvalue())
        self.assertEqual(self.path.read_bytes(),self.original)

    def test_reply_mode_menu_save_cancel_and_limits(self):
        ui=RecordedConsole(['4','1','adaptive','','0','0'])
        menu(self.path,ui)
        settings=load_settings(self.path)
        self.assertEqual(settings['output']['delivery_mode'],'adaptive')
        self.assertEqual(settings['llm']['profiles']['codebuddy_cli']['input_budget']['context_input_limit_tokens'],200000)
        self.assertEqual(settings['extension'],{'preserve':'existing'})
        self.assertTrue(list((self.root/'state/config-backups').glob('*.yaml')))
        self.assertIn('下次启动生效',ui.text)
        original=self.path.read_bytes()
        ui=RecordedConsole(['2','4','','1','','','0'])
        ConfigMenu(self.path,ui).output_group()
        self.assertEqual(self.path.read_bytes(),original)
        self.assertIn('本次未保存',ui.text);self.assertIn('已取消',ui.text)
        ui=RecordedConsole(['1','single','','0'])
        ConfigMenu(self.path,ui).output_group()
        self.assertEqual(load_settings(self.path)['output']['delivery_mode'],'single')
