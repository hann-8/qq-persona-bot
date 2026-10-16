import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('process_host',Path(__file__).resolve().parents[1]/'scripts/process_host.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class LogTests(unittest.TestCase):
    def test_only_metadata_survives(self):
        self.assertEqual(module.safe_line('gate','2026 INFO CHANNEL_CONNECTED_SELF_ID_VERIFIED'),'CHANNEL_CONNECTED_SELF_ID_VERIFIED')
        self.assertEqual(module.safe_line('model','2026 INFO CLI_START request_id=abcdef1234 attempt=1'),'CLI_START request_id=abcdef1234 attempt=1')
        for line in ('a private group message','token=secret','API failed Current Key: abcdef',
                     'Failed to send chain: [Plain(text="private")]','CLI_START request_id=abcdef1234 token=private'):
            self.assertIsNone(module.safe_line('model',line))
        self.assertIsNone(module.safe_line('astrbot','CLI_START request_id=abcdef1234 attempt=1'))
