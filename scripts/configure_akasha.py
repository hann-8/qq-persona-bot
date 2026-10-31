"""Incrementally register Akasha; never rebuild the QQ platform/provider config."""
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))

def augment(config):
    from plugins.qq_router.wechat import CONFIG,stable_id
    if not CONFIG.exists():return
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    platform=dict(id='akasha-wechat',type='aiocqhttp',enable=True,ws_reverse_host='127.0.0.1',ws_reverse_port=11229,ws_reverse_token='')
    # Preserve all other platform entries verbatim, including QQ's token.
    platforms=config.setdefault('platform',[])
    current=next((p for p in platforms if p.get('id')=='akasha-wechat'),None)
    if current is None:platforms.append(platform)
    elif current.get('ws_reverse_port')!=11229:raise ValueError('Akasha platform ID already used on another port')
    b=cfg['bridge'];ids=[stable_id(b['bot_wxid'],'group',s['id']) for s in b['sessions']]
    if b['private_enabled']:ids += ['akasha-wechat:FriendMessage:'+stable_id(b['bot_wxid'],'user',s['id']) for s in b['private_sessions']]
    settings=config['platform_settings']
    settings['id_whitelist']=list(dict.fromkeys(settings.get('id_whitelist',[])+ids))

def configure():
    path=ROOT/'runtime/astrbot/data/cmd_config.json'
    backup=ROOT/'state/akasha-deployment/cmd_config.before.json'
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists():shutil.copy2(path,backup)
    config=json.loads(path.read_text(encoding='utf-8-sig'));augment(config)
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8-sig')
    shutil.copytree(ROOT/'plugins/qq_router',ROOT/'runtime/astrbot/data/plugins/qq_router',dirs_exist_ok=True)
    print('Akasha platform/plugin configured; QQ platform/provider entries preserved.')

if __name__=='__main__':configure()
