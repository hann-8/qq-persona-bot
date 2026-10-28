"""Offline authorization boundaries for the one-shot R2 probe."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from scripts import probe_lap43_materials as probe
from qqbot_gateway.web_retrieval import Retriever
from qqbot_gateway.web_policy import DEFAULTS
from qqbot_gateway.web_freshness import facts, usable
from qqbot_gateway.evidence_selection import material


class FrozenBatch(unittest.TestCase):
    def spec(self):
        items = []
        for i, q in enumerate(['搜索 Python 最新稳定版本', '搜索 Mozilla Firefox 近期发布公告',
                               '搜索 中国空间站 最近动态',
                               '这页讲什么 https://www.python.org/doc/essays/blurb/',
                               '这页讲什么 https://docs.python.org/3/tutorial/controlflow.html']):
            decision = probe.intent(q, dict(DEFAULTS, enabled=True))
            items.append(dict(id=str(i), kind=decision.kind, query=q,
                              expected_object='public object', time_policy=decision.time_policy,
                              expectation='substantive statements', comparison_basis='official public documents'))
        return dict(schema='lap43_materials_r2_v1', frozen_at='2026-10-28T20:00:00+08:00',
                    source_head='frozen-head', source_sha256='source-hash', network=probe.NETWORK,
                    limits=probe.LIMITS, items=items)

    def check(self, spec):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'manifest.json'
            p.write_text(json.dumps(spec), encoding='utf-8')
            with patch.object(probe, 'fingerprint', return_value='source-hash'), \
                 patch.object(probe.subprocess, 'check_output', return_value='frozen-head'):
                return probe.load_spec(p, probe.sha(p.read_bytes()), Path(tmp))

    def test_frozen_queries_and_limits(self):
        self.assertEqual(len(self.check(self.spec())['items']), 5)
        for mutation in ('network', 'limits', 'items', 'source_head', 'source_sha256'):
            spec = copy.deepcopy(self.spec())
            if mutation == 'network': spec['network']['resolver'] = 'cloudflare_doh'
            elif mutation == 'limits': spec['limits']['page_entries'] = 9
            elif mutation == 'items': spec['items'] = spec['items'][:4]
            else: spec[mutation] = 'changed'
            with self.assertRaises(ValueError): self.check(spec)

    def test_sha_mismatch_before_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'manifest.json'
            p.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'FROZEN_MANIFEST_CHANGED'):
                probe.load_spec(p, 'bad', Path(tmp))
            self.assertFalse((Path(tmp) / 'state').exists())

    def test_attempt_exclusive_even_without_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe.reserve(root, 'a' * 64)
            with self.assertRaises(FileExistsError): probe.reserve(root, 'a' * 64)
            self.assertEqual(len(list((root / 'state').rglob('attempt.json'))), 1)

    def test_bounded_fragments_unknown_is_not_fresh(self):
        now = '2026-10-28T12:00:00+00:00'
        text = 'Python supports public programming documentation. ' * 80
        source = dict(text=text, url='https://example.org/public', material=material(),
                      body_method='semantic_main', freshness=facts([], now, now),
                      fetched_at=now, time_policy='current_status')
        row = probe.brief(source, 'Python 最新稳定版本', now)
        self.assertLessEqual(sum(map(len, row['public_fragments'])), 600)
        self.assertNotIn('text', row)
        self.assertNotIn(text, json.dumps(row))
        self.assertEqual(row['freshness']['freshness_status'], 'unknown')
        self.assertTrue(all(not r['usable'] for r in row['strict_checks'].values()))

    def test_strict_time_missing_stale_conflict_future_and_rss(self):
        now = '2026-10-28T12:00:00+00:00'
        def date(value): return dict(kind='published', source='time', value=value)
        cases = [[], [date('2025-10-01')], [date('2026-10-27'), date('2026-10-28')],
                 [date('2026-10-29')], [date('2026-10-28')]]
        for rows in cases:
            f = facts(rows, now, now, '过去24小时')
            self.assertFalse(usable(f, 'strict_window', reported_at=now))


class ProductionBoundary(unittest.IsolatedAsyncioTestCase):
    async def test_production_entry_never_accepts_probe_bypass(self):
        retriever = Retriever(dict(DEFAULTS, enabled=True, search_enabled=True))
        with patch.object(retriever, '_fetch', side_effect=AssertionError('NETWORK_DENIED')):
            result = await retriever.retrieve('搜索 Python 最新稳定版本')
        self.assertEqual(result.kind, 'search')
        self.assertEqual(result.sources, [])
        self.assertIn('尚未通过', result.notice)
        with self.assertRaises(TypeError):
            await retriever.retrieve('搜索 Python 最新稳定版本', bypass_quality=True)


if __name__ == '__main__':
    unittest.main()
