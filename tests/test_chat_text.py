from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from qqbot_gateway.chat_text import plain_chat, prepare_reply
from qqbot_gateway.errors import GatewayError
from qqbot_gateway.persona import POLICY, compose_persona, persona_version


class ChatTextTests(unittest.TestCase):
    def test_nested_formatting_and_blocks(self):
        source = '# 标题\n\n> **重点与*强调***\n\n- 第一项\n  - ~~第二项~~\n\n---'
        self.assertEqual(plain_chat(source), '标题\n重点与强调\n第一项\n第二项')

    def test_table_values_and_empty_table_headers(self):
        self.assertEqual(plain_chat('| 姓名 | 数值 |\n|---|---|\n| **鱼** | 2 * 3 |'), '姓名：鱼；数值：2 * 3')
        self.assertEqual(plain_chat('| a | b |\n|---|---|'), 'a；b')

    def test_literal_symbols_unicode_and_code_whitespace(self):
        source = '2 * 3，a*b，*.py，https://example.com/a_b 中文🙂\n\n`a * b`\n\n```python\nif x:\n    print("**literal**")\n```'
        expected = '2 * 3，a*b，*.py，https://example.com/a_b 中文🙂\na * b\nif x:\n    print("**literal**")'
        self.assertEqual(plain_chat(source), expected)
        self.assertEqual(plain_chat('    a * b\n        c\n'), 'a * b\n    c')

    def test_links_images_and_html_are_text_without_fetching(self):
        self.assertEqual(plain_chat('[**文档**](https://example.com/a) <https://example.com>'),
                         '文档（https://example.com/a） https://example.com')
        self.assertEqual(plain_chat('![图片](https://example.com/a.png)'), '图片（https://example.com/a.png）')
        self.assertEqual(plain_chat('<b>内容</b>'), '<b>内容</b>')

    def test_tool_markup_rejected_before_conversion_even_inside_code(self):
        for source in ('```\n<tool_call>x</tool_call>\n```', '**<｜DSML｜invoke name="Read">**',
                       '&lt;tool_call&gt;x&lt;/tool_call&gt;'):
            with self.subTest(source=source), self.assertRaises(GatewayError) as error:
                plain_chat(source)
            self.assertEqual(error.exception.code, 'TOOL_ISOLATION_FAILED')

    def test_empty_format_only_is_failure(self):
        for source in ('', '   ', '---', '```\n```', '# '):
            with self.subTest(source=source), self.assertRaises(GatewayError) as error:
                plain_chat(source)
            self.assertEqual(error.exception.code, 'EMPTY_REPLY')

    def test_limit_after_conversion_and_visible_truncation(self):
        self.assertEqual(prepare_reply('**' + '鱼' * 200 + '**', 200), ('鱼' * 200, False))
        result, limited = prepare_reply('鱼' * 110 + '。' + '鲸' * 200, 200)
        self.assertTrue(limited)
        self.assertEqual(result, '鱼' * 110 + '。……（内容未展示完）')
        result, limited = prepare_reply('🙂' * 300, 200)
        self.assertEqual(len(result), 200)

    def test_policy_is_before_editable_character_and_versioned(self):
        prompt = compose_persona('角色材料')
        self.assertTrue(prompt.startswith(POLICY))
        self.assertNotEqual(persona_version(prompt), persona_version(compose_persona('新角色')))
        self.assertNotEqual(persona_version(prompt), persona_version(prompt + '新政策'))

    def test_conversion_is_deliberately_not_idempotent(self):
        # This literal must reach the framework unchanged, never parse it a second time.
        result = plain_chat('`**字面量**`')
        self.assertEqual(result, '**字面量**')
        self.assertNotEqual(plain_chat(result), result)
