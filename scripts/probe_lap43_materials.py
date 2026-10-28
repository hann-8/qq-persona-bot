"""R2 only: inspect by default; exclusive frozen batch, RAM-only public bodies.

The production Retriever entry point is unchanged. This standalone operator probe
calls its private fetch stage with search still disabled in the configuration.
No model, CLI, account, runtime manager or production configuration is loaded.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from qqbot_gateway import web_retrieval as wr
from qqbot_gateway.web_policy import DEFAULTS, intent
from qqbot_gateway.public_network import DEFAULTS as NETWORK, failure_status
from qqbot_gateway.public_http import PublicHTTP
from qqbot_gateway.evidence_selection import sources_for_budget, question_terms
from qqbot_gateway.web_freshness import facts, usable

LIMITS = dict(search_entries=3, page_entries=8, pages_per_search=2,
              direct_entries=2, seconds_per_item=15, redirects_per_entry=2, retries=0)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(root):
    paths = sorted((root / 'src/qqbot_gateway').glob('*.py'))
    paths += [root / 'scripts/probe_lap43_materials.py']
    return sha(json.dumps({p.relative_to(root).as_posix(): sha(p.read_bytes())
                           for p in paths}, sort_keys=True).encode())


def load_spec(path, expected, root):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError('FROZEN_MANIFEST_CHANGED')
    spec = json.loads(raw)
    if set(spec) != {'schema', 'frozen_at', 'source_head', 'source_sha256', 'network', 'limits', 'items'}:
        raise ValueError('MANIFEST_SCHEMA')
    if spec['schema'] != 'lap43_materials_r2_v1' or spec['network'] != NETWORK or spec['limits'] != LIMITS:
        raise ValueError('FIXED_NETWORK_AND_LIMITS')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if spec['source_head'] != head or spec['source_sha256'] != fingerprint(root):
        raise ValueError('SOURCE_DRIFT')
    rows = spec['items']
    if not isinstance(rows, list) or len(rows) != 5:
        raise ValueError('FIVE_FROZEN_ITEMS')
    ids = set()
    for index, row in enumerate(rows):
        if set(row) != {'id', 'kind', 'query', 'expected_object', 'time_policy', 'expectation', 'comparison_basis'}:
            raise ValueError('ITEM_SCHEMA')
        if any(not isinstance(v, str) or not 1 <= len(v) <= 1200 for v in row.values()):
            raise ValueError('EXPECTATIONS_REQUIRED')
        if row['id'] in ids:
            raise ValueError('DUPLICATE_ITEM')
        ids.add(row['id'])
        decision = intent(row['query'], dict(DEFAULTS, enabled=True))
        if row['kind'] != ('search' if index < 3 else 'read') or decision.kind != row['kind']:
            raise ValueError('THREE_SEARCH_TWO_DIRECT')
        if decision.time_policy != row['time_policy'] or (index >= 3 and len(decision.urls) != 1):
            raise ValueError('TIME_OR_DIRECT_CONTRACT')
    return spec


def reserve(root, expected):
    directory = root / 'state/lap43-materials-r2' / expected
    directory.mkdir(parents=True, exist_ok=True)
    # A partial/crashed batch consumes its authorization too; never replay it.
    with (directory / 'attempt.json').open('x', encoding='utf-8') as stream:
        json.dump(dict(manifest_sha256=expected, reserved_at=now(), state='reserved'), stream)
    return directory


def brief(source, question, requested_at):
    text = source['text']
    # Never persist a whole source, including a short one. At most three small
    # fragments per source; total character allowance is <= half the source.
    limit = min(600, len(text) // 2)
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    terms = question_terms(question)
    ranked = sorted(paragraphs, key=lambda p: -sum(t in p.lower() for t in terms))
    fragments = []
    for p in (paragraphs[:1] + ranked):
        fragment = p[:min(200, limit)]
        if fragment and fragment not in fragments:
            fragments.append(fragment)
            limit -= len(fragment)
        if limit <= 0 or len(fragments) == 3:
            break
    strict = {}
    for label, q in [('today', '今天'), ('rolling_24h', '过去24小时')]:
        f = facts(source.get('_date_candidates', []), requested_at, source['fetched_at'], q)
        strict[label] = dict(freshness=f, usable=usable(f, 'strict_window'))
    return dict(url=source['url'], material=source['material'],
                body_method=source.get('body_method', 'none'),
                selected_bytes=len(text.encode()), selected_sha256=sha(text.encode()),
                freshness=source['freshness'], time_policy=source['time_policy'],
                strict_checks=strict, public_fragments=fragments,
                topic_match=wr.topic_match(text, terms),
                substantive=wr.substantive(source, question))


async def run(root, manifest, expected):
    spec = load_spec(manifest, expected, root)
    directory = reserve(root, expected)
    events = []
    counters = dict(search_entries=0, page_entries=0)
    cfg = dict(DEFAULTS, enabled=True, search_enabled=False)

    class ObservedHTTP(PublicHTTP):
        def __init__(self, settings, audit):
            super().__init__(settings, audit)
            resolve = self.resolver.resolve

            async def observed_resolve(*args, **kwargs):
                event = dict(kind='system_resolution', status='started')
                events.append(event)
                try:
                    result = await resolve(*args, **kwargs)
                    event['status'] = 'ok'
                    return result
                except BaseException as error:
                    event.update(failure_status(error))
                    raise
            self.resolver.resolve = observed_resolve

        async def get(self, url, **kwargs):
            key = 'search_entries' if kwargs.get('rss') else 'page_entries'
            counters[key] += 1
            if counters[key] > LIMITS[key]:
                raise ValueError('BATCH_ENTRY_LIMIT')
            before = (self.audit.http_calls, self.audit.redirect_hops, self.audit.dns_calls)
            event = dict(kind='search' if kwargs.get('rss') else 'page', url=url)
            events.append(event)
            started = time.monotonic()
            try:
                result = await super().get(url, **kwargs)
                event.update(status='ok', final_url=result[1], mime=result[2],
                             decoded_bytes=len(result[0].encode()),
                             decoded_sha256=sha(result[0].encode()))
                return result
            except BaseException as error:
                event.update(failure_status(error))
                raise
            finally:
                event.update(elapsed_seconds=round(time.monotonic() - started, 3),
                             http_attempts=self.audit.http_calls-before[0],
                             redirect_hops=self.audit.redirect_hops-before[1],
                             doh_attempts=self.audit.dns_calls-before[2])

    class ObservedRetriever(wr.Retriever):
        async def extract(self, text, url, mime):
            event = dict(kind='extract', url=url)
            events.append(event)
            try:
                source = await super().extract(text, url, mime)
                event.update(status='ok', body_method=source['body_method'],
                             body_bytes=len(source['text'].encode()), body_sha256=sha(source['text'].encode()))
                return source
            except BaseException as error:
                event.update(failure_status(error))
                raise
            finally:
                if self.extractor:
                    event['metrics'] = dict(self.extractor.last_metrics)

    report = dict(schema='lap43_materials_r2_result_v1', manifest_sha256=expected,
                  source_head=spec['source_head'], source_sha256=spec['source_sha256'],
                  started_at=now(), items=[], real_model_calls=0, qq_calls=0,
                  human_review='pending', quality_passed=False)
    parse = wr.parse_rss
    for row in spec['items']:
        events.clear()
        candidates = []

        def observed_parse(*args, **kwargs):
            parsed = parse(*args, **kwargs)
            candidates.extend(dict(url=r['url'], text_sha256=sha(r['text'].encode()),
                                   text_bytes=len(r['text'].encode()),
                                   topic_match=wr.topic_match(r['title']+' '+r['text'], question_terms(args[1])),
                                   substantive=wr.substantive(r, args[1]),
                                   reported_date=r.get('reported_date')) for r in parsed)
            return parsed

        requested = now()
        token = wr.REQUEST_TIME.set(requested)
        retriever = ObservedRetriever(cfg, network=NETWORK, root=directory, http_factory=ObservedHTTP)
        item = dict(id=row['id'], requested_at=requested, time_policy=row['time_policy'])
        try:
            # Only this standalone probe enters the pre-gate fetch stage.
            # All transport, parsing, ranking and selection remain production code.
            with patch.object(wr, 'parse_rss', observed_parse):
                result = await retriever._fetch(intent(row['query'], cfg), row['query'])
            item.update(expired=result.expired, notice=result.notice, partial=result.partial)
            sources = sources_for_budget(result.sources, 6000, 4000, cfg['long_text_policy'], row['query'], 'gist') if result.sources else []
            # Restore only date candidates from RAM for strict counterchecks.
            for selected, original in zip(sources, result.sources):
                selected['_date_candidates'] = original.get('_date_candidates', [])
            item['sources'] = [brief(s, row['query'], requested) for s in sources]
            item['status'] = 'selected' if sources else 'no_material'
        except Exception as error:
            item.update(status='failed', failure=failure_status(error), sources=[])
        finally:
            wr.REQUEST_TIME.reset(token)
        item.update(audit=retriever.last_audit, events=list(events), candidates=candidates)
        report['items'].append(item)
        report['counters'] = dict(counters,
            http_attempts=sum(r['audit'].get('http_calls', 0) for r in report['items']),
            redirect_hops=sum(r['audit'].get('redirect_hops', 0) for r in report['items']),
            doh_attempts=sum(r['audit'].get('dns_calls', 0) for r in report['items']),
            system_resolutions=sum(e['kind']=='system_resolution' for r in report['items'] for e in r['events']))
        (directory / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    report['completed_at'] = now()
    (directory / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (directory / 'completed.json').write_text(json.dumps(dict(items=len(report['items']), completed_at=now())), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    if not args.run:
        print('inspect only: no network; requires frozen manifest, matching SHA and explicit --run')
        return
    if not args.manifest or not args.expected_sha256:
        parser.error('frozen manifest and SHA required')
    report = asyncio.run(run(ROOT, args.manifest, args.expected_sha256))
    print(json.dumps(dict(manifest_sha256=report['manifest_sha256'], counters=report['counters'],
                          items=len(report['items']), human_review='pending')))


if __name__ == '__main__':
    main()
