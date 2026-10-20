"""Independent LAP-34 verifier. Synthetic temp roots only; no old main() calls."""
import asyncio
import copy
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / 'tests')]
os.environ['ASTRBOT_DISABLE_METRICS'] = '1'


async def framework_case(root, backend, mode, participation, family='memory'):
    from scripts.verify_lap30_framework import verify
    from scripts.verify_lap20 import verify as plain
    from scripts.verify_lap21 import verify as media
    from qqbot_gateway.config_files import read_project, create_snapshot, snapshot_environment, load_consumer
    from qqbot_gateway.config_layout_ops import initialize
    import plugins.qq_router.main as router_module
    from qqbot_gateway import onebot_gate, model_gateway
    from scripts import configure_astrbot
    from astrbot.core.config.default import DEFAULT_CONFIG
    from astrbot.core import sp, db_helper
    environments = []
    observations = []
    # Hook the actual router constructor's loader after the existing fixture has
    # created only synthetic settings. Neither old verifier main() is executed.
    def bound_loader(project_root):
        initialize(project_root, migrate=True)
        config = read_project(project_root)
        path, metadata = create_snapshot(config, 'a' * 32)
        env = snapshot_environment(project_root, path, metadata)
        environments.append(env)
        original = load_consumer(project_root, environ=env)
        # Deliberately change disk after capturing the instance; all subsequent
        # real consumers must still load the original selected settings.
        source = project_root / 'config/local/chat.yaml'
        source.write_bytes(source.read_bytes().replace(b'history_turns: 8', b'history_turns: 9'))
        observations.append(dict(consumer='router', semantic=metadata['semantic_digest']))
        return original
    with patch.object(router_module, 'load_consumer', side_effect=bound_loader):
        if family == 'memory':result = await verify(root, backend, mode, participation)
        elif family == 'media':result = await media(root, backend, mode, participation, full_lifecycle=True, lap24=True, lap25=True)
        else:result = await plain(root, backend, mode, full_lifecycle=True, lap24=True, lap25=True)
    env = environments[0]
    data = load_consumer(root, environ=env)
    assert data['chat']['history_turns'] == 8 and read_project(root).settings['chat']['history_turns'] == 9
    # Configure the actual framework preparation routine against a temporary
    # AstrBot tree, with only its DB preference transport replaced.
    target = root / 'runtime/astrbot/data';(target / 'plugins').mkdir(parents=True)
    (target / 'cmd_config.json').write_text(json.dumps(copy.deepcopy(DEFAULT_CONFIG)), encoding='utf-8')
    shutil.copytree(ROOT / 'plugins/qq_router', root / 'plugins/qq_router')
    (root / 'secrets').mkdir(exist_ok=True)
    tokens = dict(model_gateway='t'*40, onebot_inbound='a'*40, onebot_upstream='b'*40)
    (root / 'secrets/local-tokens.json').write_text(json.dumps(tokens), encoding='utf-8')
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, env))
        stack.enter_context(patch.object(configure_astrbot, 'ROOT', root))
        stack.enter_context(patch.object(db_helper, 'engine', SimpleNamespace(dispose=AsyncMock())))
        for obj, method, value in ((db_helper,'initialize',None),
                                   (sp,'global_get',[]),(sp,'global_put',None),(sp,'close',None)):
            stack.enter_context(patch.object(obj, method, AsyncMock(return_value=value)))
        await configure_astrbot.configure()
        prepared = json.loads((target / 'cmd_config.json').read_text(encoding='utf-8-sig'))
        assert prepared['agent_runner']['config']['compression']['max_turns'] == 8
        observations.append(dict(consumer='prepare', history_turns=8))
        # Real gate CLI loader/config builder; network listener replaced only.
        gates = []
        cls = onebot_gate.OneBotGate
        def gate_builder(config, project_root):
            assert project_root == root and config.participation_mode == participation
            assert config.bot_qq == data['bot']['qq'] and config.blocked_users == frozenset(data['access']['blocked_users'])
            gate = cls(config, project_root);gates.append(gate)
            return gate
        with patch.object(sys,'argv',['gate','--root',str(root),'--config',env['QQBOT_CONFIG_SNAPSHOT']]), \
                patch.object(onebot_gate,'OneBotGate',side_effect=gate_builder),patch.object(onebot_gate.web,'run_app'):
            onebot_gate.main()
        for gate in gates:gate.store.close()
        observations.append(dict(consumer='gate', root_explicit=True))
        runners = []
        def runner_builder(project_root, settings, budget):
            assert project_root == root and settings == data
            runners.append(settings)
            return SimpleNamespace()
        with patch.object(sys,'argv',['model','--root',str(root),'--config',env['QQBOT_CONFIG_SNAPSHOT']]), \
                patch.object(model_gateway,'create_runner',side_effect=runner_builder), \
                patch.object(model_gateway,'application',return_value=object()),patch.object(model_gateway.web,'run_app'):
            model_gateway.main()
        assert len(runners) == 1
        observations.append(dict(consumer='model', root_explicit=True, history_turns=8))
    result.update(lap34=True, family=family, snapshot_consumers=observations, source_edited_during_instance=True)
    return result


def main():
    if sys.argv[1:] != ['--frameworks-only']:
        # A tracked user-owned persona is deliberately not part of LAP-34.
        # The old LAP-24 fixed-size regression uses its committed test baseline;
        # no workspace persona is read, changed, staged, or printed by this run.
        baseline = subprocess.run(['git','show','HEAD:config/persona.md'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8')
        read_text = Path.read_text
        def fixture_read(path, *args, **kwargs):
            if path.resolve() == (ROOT/'config/persona.md').resolve():return baseline
            return read_text(path, *args, **kwargs)
        with patch.object(Path,'read_text',fixture_read):
            result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(str(ROOT/'tests')))
        if not result.wasSuccessful():return 1
        subprocess.run([str(ROOT/'runtime/astrbot-tool/astrbot/Scripts/python.exe'),'-X','utf8',str(Path(__file__).resolve()),'--frameworks-only'],cwd=ROOT/'runtime/astrbot',check=True)
        rows=json.loads((ROOT/'reports/lap-34-framework-offline.json').read_text(encoding='utf-8'))
        summary=dict(passed=True,unit_tests=result.testsRun,persona_fixture='committed HEAD baseline; workspace untouched',
                     framework_combinations=len(rows),framework_cases=sum(len(row['cases']) for row in rows),
                     real_model_calls=0,real_qq_calls=0,real_bot_operations=0,local_migrated=False,
                     real_acceptance=False,complete_acceptance=False)
        (ROOT/'reports/lap-34-offline.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('PASS LAP-34 offline; real migration/loading pending')
        return 0
    rows=[];previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap34-framework-',ignore_cleanup_errors=True) as directory:
        os.chdir(directory)
        try:
            for backend in ('codebuddy_cli','ollama_ssh'):
                for mode in ('single','adaptive'):
                    for family in ('memory','media','plain'):
                        for participation in (('free',) if family == 'plain' else ('mentions','free')):
                            root=Path(directory)/(backend+mode+participation+family);root.mkdir()
                            rows.append(asyncio.run(framework_case(root,backend,mode,participation,family)))
                            print('PASS',backend,mode,participation,family,len(rows[-1]['cases']))
        finally:os.chdir(previous)
    (ROOT/'reports/lap-34-framework-offline.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0


if __name__ == '__main__':raise SystemExit(main())
