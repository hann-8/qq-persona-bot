import sys
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from qqbot_gateway.config_comments import annotate_yaml
from qqbot_gateway.config_layout_ops import render


class InlineCommentTests(unittest.TestCase):
    def test_move_notes_keep_values_spelling_and_user_comments(self):
        source = ('# 文件用途\n# bot.qq：机器人个人QQ，必填正整数字符串，占位不能启动；新装默认 "REQUIRED"\n'
                  'bot:\n  qq: "222"  # 用户自己的备注\naccess:\n  allowed_groups:\n  - "111"\n')
        output = annotate_yaml(source)
        self.assertEqual(yaml.safe_load(output), yaml.safe_load(source))
        self.assertIn('  qq: "222"  # 用户自己的备注；机器人个人QQ', output)
        self.assertIn('新装默认 "REQUIRED"', output)
        self.assertNotIn('# bot.qq：', output)
        self.assertIn('  allowed_groups:  # ', output)
        self.assertEqual(annotate_yaml(output), output)

    def test_bom_crlf_and_missing_final_newline(self):
        source = '\ufeff# 自己的头注释\r\nbot:\r\n  qq: "222"'
        output = annotate_yaml(source)
        self.assertTrue(output.startswith('\ufeff# 自己的头注释\r\n'))
        self.assertNotIn('\n', output.replace('\r\n', ''))
        self.assertFalse(output.endswith('\n'))
        self.assertEqual(yaml.safe_load(source), yaml.safe_load(output))

    def test_quotes_hash_multiline_and_block_values(self):
        source = ('extension:\n  quoted: "literal # is data"\n  folded: >- # 保留块头备注\n'
                  '    第一行 # 仍是正文\n    第二行\n  literal: |\n    key: value\n'
                  '    # 块内正文不改\n  multiline: "一行\n    二行 # 也是正文"\n')
        output = annotate_yaml(source)
        self.assertEqual(yaml.safe_load(source), yaml.safe_load(output))
        self.assertIn('    # 块内正文不改\n', output)
        self.assertIn('folded: >- # 保留块头备注；', output)
        self.assertEqual(annotate_yaml(output), output)

    def test_flow_mapping_context_and_empty_values(self):
        source = 'bot: {qq: "222"}\nweb: {enabled: false}\nparticipation:\n  silence:\n    enabled: true\naccess:\n  admin_users:\n  -\n'
        output = annotate_yaml(source)
        self.assertEqual(yaml.safe_load(source), yaml.safe_load(output))
        self.assertIn('web.enabled：共用网页读取开关', output)
        self.assertIn('enabled: true  # 临时停言开关', output)
        self.assertIn('admin_users:  # bot管理员QQ', output)
        self.assertEqual(annotate_yaml(output), output)

    def test_render_is_inline_and_safe_for_untrusted_strings(self):
        data = {'bot': {'qq': '222'}, 'access': {'admin_users': ['333']},
                'extension': {'value': '换行\naccess: injected\n# literal'}}
        output = render('bot.yaml', data)
        self.assertEqual(yaml.safe_load(output), data)
        self.assertIn('qq:', output)
        self.assertNotIn('# bot.qq：', output)
        self.assertIn('admin_users:  # bot管理员QQ', output)

    def test_bad_yaml_diagnostics_never_echo_payload(self):
        for source in ('bot: [PRIVATE_VALUE', 'bot: &a {qq: 222}\naccess: *a'):
            with self.assertRaises(ValueError) as caught:annotate_yaml(source)
            self.assertNotIn('PRIVATE_VALUE', str(caught.exception))


if __name__ == '__main__':unittest.main()
