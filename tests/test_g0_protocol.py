import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from g0_protocol import assess

class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.report = {'exit_code': 0, 'timeout': False, 'sentinel_unchanged': True,
                       'write_target_absent': True, 'command_target_absent': True,
                       'events': [{'type':'system', 'subtype':'init', 'tools':[], 'mcp_servers':[]},
                                  {'type':'result', 'subtype':'success', 'is_error':False,
                                   'expected_exact':True, 'result_length':10}]}

    def test_accept_final_success(self):
        self.assertEqual(assess(self.report), 'PASS')

    def test_error_event_beats_zero_exit_and_success(self):
        self.report['events'].insert(1, {'type':'error'})
        self.assertEqual(assess(self.report), 'BACKEND_ERROR')

    def test_invalid_final_variants(self):
        for patch, expected in [({'result_length':0}, 'EMPTY_RESULT'),
                                ({'terminal_reason':'cancelled'}, 'CANCELLED_OR_FAILED'),
                                ({'is_error':True}, 'BACKEND_ERROR'),
                                ({'has_errors':True}, 'BACKEND_ERROR')]:
            with self.subTest(patch=patch):
                report = copy.deepcopy(self.report)
                report['events'][-1].update(patch)
                self.assertEqual(assess(report), expected)

    def test_intermediate_text_is_not_final(self):
        self.report['events'][-1] = {'type':'assistant', 'content_types':['text']}
        self.assertEqual(assess(self.report), 'MISSING_OR_DUPLICATE_RESULT')

    def test_bad_json_is_failure(self):
        self.report['events'].append({'diagnostic':True})
        self.assertEqual(assess(self.report), 'PROTOCOL_ERROR')

    def test_tools_and_timeout_fail_closed(self):
        self.report['events'][0]['tools'] = ['Read']
        self.assertEqual(assess(self.report), 'TOOL_ISOLATION_FAILED')
        self.report['timeout'] = True
        self.assertEqual(assess(self.report), 'TIMEOUT')

if __name__ == '__main__':
    unittest.main()
