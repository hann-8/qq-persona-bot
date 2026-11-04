"""The existing Akasha-preserving startup must refresh the actual provider source."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from scripts import manage


class DeploymentTests(unittest.TestCase):
    def test_existing_provider_source_timeout_changes_without_rebuilding_platforms(self):
        settings={'llm':{'backend':'codebuddy_cli','queue_wait_seconds':30,'profiles':{'codebuddy_cli':{'run_timeout_seconds':180}}}}
        original={'provider':[{'id':'workbuddy-local','provider_source_id':'source'}],
            'provider_sources':[{'id':'source','timeout':180,'key':['private-fixture']}],
            'platform':[{'id':'akasha-wechat','unchanged':True}],
            'platform_settings':{},'provider_settings':{'proactive_capability':{}}}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'runtime/astrbot/data/cmd_config.json';path.parent.mkdir(parents=True)
            path.write_text(json.dumps(original),encoding='utf-8')
            gate=SimpleNamespace(upstream_token='fixture',allowed_groups=['1'],admin_users=['2'])
            with patch.object(manage,'ROOT',root),patch.object(manage,'load_consumer',return_value=settings),patch('scripts.configure_akasha.configure'),patch('scripts.configure_akasha.augment'):
                manage._configure_snow_framework(gate,True,{})
            current=json.loads(path.read_text(encoding='utf-8-sig'))
            expected=deepcopy(original['provider_sources']);expected[0]['timeout']=235
            self.assertEqual(current['provider_sources'],expected)
            self.assertEqual(current['provider'],original['provider'])
            self.assertIn(original['platform'][0],current['platform'])

if __name__=='__main__':unittest.main()
