"""Actual runner + actual AstrBot synthetic regression; never home SSH/QQ/real CLI."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from qqbot_gateway.backends import OLLAMA_DEFAULTS
from qqbot_gateway.ollama_ssh_runner import OllamaSSHRunner
from qqbot_gateway.token_budget import InputBudget
from qqbot_gateway.workbuddy_cli_runner import CLIRunner


FAKE_CLI = '''import json,sys
from pathlib import Path
sys.stdin.read()
print(json.dumps({'type':'system','subtype':'init','model':'deepseek-v4.1-flash','tools':[],'mcp_servers':[]}))
print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':Path(__file__).with_suffix('.txt').read_text(encoding='utf-8'),'usage':{'input_tokens':12,'output_tokens':3}}))
'''


class Harness:
    def __init__(self,root,backend):
        self.root=root;self.backend=backend;self._text=''
        if backend=='codebuddy_cli':
            self.script=root/'synthetic_cli.py';self.script.write_text(FAKE_CLI,encoding='utf-8')
            self.runner=CLIRunner(ROOT,'deepseek-v4.1-flash',budget=InputBudget())
            self.runner.root=root;self.runner.node=Path(sys.executable);self.runner.entry=self.script
        else:
            harness=self
            class Native:
                def __init__(self,*args):pass
                def close(self):pass
                def request(self,method,path,payload=None,*,deadline,before_send=None):
                    if path=='/api/version':return {'version':'synthetic'}
                    if path=='/api/tags':return {'models':[{'name':OLLAMA_DEFAULTS['model'],'digest':'a'*64}]}
                    if path=='/api/show':return {'capabilities':['completion','thinking'],'thinking':{'values':[False,True]},'model_info':{'qwen35.context_length':262144}}
                    if path=='/api/ps':return {'models':[]}
                    assert method=='POST' and path=='/api/chat'
                    assert payload['think'] is False and 'tools' not in payload
                    before_send()
                    return {'model':OLLAMA_DEFAULTS['model'],'done':True,'done_reason':'stop',
                        'message':{'role':'assistant','content':harness.text},'eval_count':3,'prompt_eval_count':12}
            self.runner=OllamaSSHRunner(root,OLLAMA_DEFAULTS|{'expected_digest':'a'*64},InputBudget(),transport_factory=Native)

    def __getattr__(self,name):return getattr(self.runner,name)
    @property
    def text(self):return self._text
    @text.setter
    def text(self,value):
        self._text=value
        if self.backend=='codebuddy_cli':self.script.with_suffix('.txt').write_text(value,encoding='utf-8')


async def verify_context_switch(root):
    import yaml
    from astrbot.core.db.po import Conversation
    from astrbot.api.platform import AstrBotMessage,MessageMember,MessageType,PlatformMetadata
    from astrbot.api.message_components import At,Plain
    from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    from astrbot.core.pipeline.waking_check.stage import build_unique_session_id
    from plugins.qq_router.main import QQRouter
    class Conversations:
        def __init__(self):self.current={};self.items={}
        async def get_curr_conversation_id(self,umo):return self.current.get(umo)
        async def get_conversation(self,umo,cid):return self.items[(umo,cid)]
        async def new_conversation(self,umo,persona_id):
            cid=str(len(self.items)+1);self.current[umo]=cid
            self.items[(umo,cid)]=Conversation('qqbot',umo,cid,history='[]',persona_id=persona_id)
            return cid
        async def update_conversation(self,umo,cid,history):self.items[(umo,cid)].history=json.dumps(history)
    directory=root/'context-test';(directory/'config').mkdir(parents=True)
    settings=yaml.safe_load((ROOT/'config/settings.example.yaml').read_text(encoding='utf-8'))
    settings['bot']['qq']='222';settings['access'].update(allowed_groups=['111'],admin_users=['333'])
    settings['chat']['user_cooldown_seconds']=0
    settings['llm']['profiles']['ollama_ssh']['expected_digest']='a'*64
    (directory/'config/persona.md').write_text('合成人设',encoding='utf-8')
    path=directory/'config/settings.local.yaml';manager=Conversations();previous=None
    with patch.dict(os.environ,{'QQBOT_ROOT':str(directory)}):
        for index,backend in enumerate(('codebuddy_cli','codebuddy_cli','ollama_ssh','ollama_ssh','codebuddy_cli')):
            settings['llm']['backend']=backend
            if index==1:settings['llm']['profiles']['ollama_ssh']['temperature']=.8 # inactive
            if index==3:settings['llm']['profiles']['ollama_ssh']['num_predict']=1025 # active
            path.write_text(yaml.safe_dump(settings),encoding='utf-8')
            router=QQRouter(SimpleNamespace(conversation_manager=manager))
            message=AstrBotMessage();message.self_id='222';message.type=MessageType.GROUP_MESSAGE
            message.group_id='111';message.sender=MessageMember('333','synthetic');message.message_id=str(index)
            message.message=[At(qq='222'),Plain(text='问题')];message.message_str='问题';message.session_id='111'
            event=AiocqhttpMessageEvent('问题',message,PlatformMetadata(name='aiocqhttp',description='offline',id='qqbot'),'111',None)
            event.session_id=build_unique_session_id(event)
            generator=router.on_group(event);request=await anext(generator);current=request.conversation.cid
            if index==1:assert current==previous
            elif previous is not None:assert current!=previous
            await generator.aclose();router.tasks.close()
            if index==0:
                first=(event.unified_msg_origin,current)
                manager.items[first].history=json.dumps([{'role':'user','content':'旧问题'},{'role':'assistant','content':'旧回答'}])
            if index>1:assert json.loads(manager.items[first].history)[-1]['content']=='旧回答'
            previous=current
    return dict(inactive_edit_preserves_current=True,backend_and_active_parameters_start_new=True,old_history_preserved=True,real_requests=0)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--backend',choices=['codebuddy_cli','ollama_ssh'],required=True)
    parser.add_argument('--mode',choices=['single','adaptive'],required=True)
    args=parser.parse_args()
    os.environ['ASTRBOT_DISABLE_METRICS']='1'
    from scripts import verify_lap11,verify_lap16
    previous=Path.cwd()
    with tempfile.TemporaryDirectory(prefix='qqbot-lap17-framework-',ignore_cleanup_errors=True) as directory:
        root=Path(directory);os.chdir(root)
        try:
            harness=Harness(root,args.backend)
            path=ROOT/f'reports/lap-17-{args.backend}-{args.mode}-offline.json'
            async def run():
                context=await verify_context_switch(root)
                await (verify_lap16 if args.mode=='adaptive' else verify_lap11).verify(harness,args.backend,path)
                return context
            context=asyncio.run(run())
            report=json.loads(path.read_text(encoding='utf-8'))
            report.update(backend=args.backend,mode=args.mode,actual_runner=True,transport='synthetic',real_ssh_authentications=0,context_switch=context)
            path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        finally:os.chdir(previous)


if __name__=='__main__':main()
