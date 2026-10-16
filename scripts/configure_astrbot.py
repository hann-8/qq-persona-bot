"""Configure only the isolated project instance, using upstream APIs for preferences."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from qqbot_gateway.config import load_settings


async def configure():
    settings=load_settings(ROOT/'config/settings.local.yaml')
    path=ROOT/'runtime/astrbot/data/cmd_config.json'
    config=json.loads(path.read_text(encoding='utf-8-sig'))
    tokens=json.loads((ROOT/'secrets/local-tokens.json').read_text(encoding='utf-8'))
    config['provider_sources']=[]
    config['provider']=[{'id':'workbuddy-local','type':'openai_chat_completion','provider':'openai',
        'provider_type':'chat_completion','enable':True,'key':[tokens['model_gateway']],
        'api_base':'http://127.0.0.1:8765/v1','model':'workbuddy-local','modalities':['text'],
        'custom_extra_body':{},'timeout':180,'proxy':''}]
    config['provider_settings'].update({'enable':True,'streaming_response':False,'web_search':False,
        'web_search_link':False,'display_reasoning_text':False,'show_tool_use_status':False,
        'computer_use_runtime':'none'})
    config['provider_settings']['proactive_capability']['add_cron_tools']=False
    config['provider_settings']['file_extract']['enable']=False
    persona=(ROOT/'config/persona.md').read_text(encoding='utf-8')
    persona_id='fatfish-test-'+hashlib.sha256(persona.encode()).hexdigest()[:8]
    from astrbot.core.config.agent_runner import get_agent_runner_config_default
    runner=get_agent_runner_config_default('local')
    runner['model'].update(provider_id='workbuddy-local',request_max_retries=1,fallback_provider_ids=[])
    runner['persona']['persona_id']=persona_id
    runner['compression'].update(max_turns=settings['chat']['history_turns'],trim_turns=1,
        fallback_max_tokens=settings['chat']['context_input_limit_tokens']+settings['chat']['output_reserve_tokens'],
        overflow_strategy='truncate_by_turns')
    runner['misc'].update(max_steps=1)
    config['agent_runner']={'runner_type':'local','config':runner}
    config['provider_ltm_settings']['group_icl_enable']=False
    config['provider_ltm_settings']['group_message_history_enable']=False
    config['provider_ltm_settings']['active_reply']['enable']=False
    config['kb_ids']=[]
    config['t2i']=False
    config['disable_metrics']=True
    config['trace_enable']=False;config['trace_log_enable']=False;config['log_file_enable']=False
    config['log_level']='ERROR'
    config['platform_settings']['segmented_reply']['enable']=False
    config['platform_settings']['reply_with_quote']=True
    config['platform_settings']['reply_with_mention']=False
    config['platform_settings']['forward_threshold']=100000
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8-sig')
    target=ROOT/'runtime/astrbot/data/plugins'
    unknown=[p.name for p in target.iterdir() if p.is_dir() and p.name not in ('qq_router','__pycache__')]
    if unknown:raise RuntimeError('Unexpected project-instance plugins; preserve and inspect first')
    shutil.copytree(ROOT/'plugins/qq_router',target/'qq_router',dirs_exist_ok=True)
    from astrbot.core import sp, db_helper
    await db_helper.initialize()
    disabled=await sp.global_get('inactivated_plugins',[])
    for name in ('astrbot.builtin_stars.astrbot.main','astrbot.builtin_stars.builtin_commands.main'):
        if name not in disabled:disabled.append(name)
    await sp.global_put('inactivated_plugins',disabled)
    await sp.close();await db_helper.engine.dispose()
    ready=ROOT/'state/router-ready.json'
    if ready.exists():ready.unlink()
    print('Isolated AstrBot text profile configured; builtin command plugins disabled.')


if __name__=='__main__':asyncio.run(configure())
