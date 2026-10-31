"""One-use current WeFlow media and explicit shared-context mapping."""
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from PIL import Image
from qqbot_gateway.wechat_materials import WeChatMaterials

class CurrentImage(unittest.IsolatedAsyncioTestCase):
    async def test_gateway_current_native_image_same_turn_and_failed_cap_zero_model(self):
        from types import SimpleNamespace
        from aiohttp.test_utils import TestClient,TestServer
        from qqbot_gateway.model_gateway import application,ModelQueue
        from qqbot_gateway.backends import BackendResult
        from qqbot_gateway.vision import member_source,attach_image,CURRENT
        from qqbot_gateway.turn_v2 import sha
        from qqbot_gateway.attention import canonical
        from qqbot_gateway import wechat_materials as module
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'config/local/akasha.json';media=root/'state/akasha-wechat/media';caps=media.parent/'media-caps'
            media.mkdir(parents=True);caps.mkdir()
            config.parent.mkdir(parents=True);config.write_text(json.dumps(dict(bridge=dict(bot_wxid='synthetic',sessions=[],private_sessions=[]),pairings=[])))
            out=io.BytesIO();Image.new('RGB',(20,12),'red').save(out,format='PNG');image=media/'current.image';image.write_bytes(out.getvalue())
            cap='a'*64;ref='i_'+'b'*32
            (caps/(cap+'.json')).write_text(json.dumps(dict(path=str(image),image_ref=ref,expires=time.time()+60)))
            source=member_source('合成当前图问题',['鱼鱼']);attach_image(source,dict(image_ref=ref,cap=cap))
            header=dict(version=2,kind='group_turn',request_key='a'*64,epoch='b'*64,config_version='c'*64,source_digest=sha(source),mode='free',addressing='mention',must_reply=True,target_seq=1,resource_caps=[cap])
            class Runner:
                count=0
                async def run(self,system,prompt,trace):
                    self.count+=1;self.image=CURRENT.get();self_test.assertIsNotNone(self.image)
                    return BackendResult(json.dumps(dict(qqbot_turn_reply=2,decision='speak',kind='answer',bubbles=['合成红色图片'],meme_id=None,response_to_seq=1,mention=None,memory_updates={},memory_receipt=False)))
            self_test=self;runner=Runner()
            from qqbot_gateway.token_budget import InputBudget
            app=application(ModelQueue(runner),'t'*32,budget=InputBudget(limit=524288),v2=dict(mode='free',config_version='c'*64,aliases=['鱼鱼']),materials=SimpleNamespace(reserve=4096))
            with patch.object(module,'CONFIG',config):
                async with TestClient(TestServer(app)) as client:
                    for n in (1,2):
                        response=await client.post('/v1/chat/completions',json=dict(model='workbuddy-local',messages=[dict(role='user',content=canonical(source))],qqbot_request=header),headers={'Authorization':'Bearer '+'t'*32,'X-QQBot-Trace':'d'*32,'X-QQBot-Transport':'wechat_akasha'})
                        self.assertEqual(response.status,200,await response.text());value=await response.json()
                        if n==1:self.assertIn('红色',value['choices'][0]['message']['content'])
                        else:self.assertIn('暂时无法读取',value['choices'][0]['message']['content'])
                    self.assertEqual(runner.count,1)

    async def test_exact_local_image_normalizer_and_no_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'config/local/akasha.json';media=root/'state/akasha-wechat/media';caps=media.parent/'media-caps'
            media.mkdir(parents=True);caps.mkdir()
            out=io.BytesIO();Image.new('RGB',(20,12),'red').save(out,format='PNG');image=media/'current.image';image.write_bytes(out.getvalue())
            cap='a'*64;ref='i_'+'b'*32
            (caps/(cap+'.json')).write_text(json.dumps(dict(path=str(image),image_ref=ref,expires=time.time()+60)))
            from qqbot_gateway import wechat_materials as module
            with patch.object(module,'CONFIG',config):
                native,descriptor=await WeChatMaterials(4096).resolve(dict(resource_caps=[cap]),dict(images=[dict(image_ref=ref)]),time.monotonic()+15)
                self.assertEqual((native.blob.width,native.blob.height),(20,12));self.assertEqual(descriptor['image_ref'],ref)
                with self.assertRaises(OSError):await WeChatMaterials(4096).resolve(dict(resource_caps=[cap]),dict(images=[dict(image_ref=ref)]),time.monotonic()+15)
                # A wrong source ref fails even when a valid newer file exists.
                (caps/(cap+'.json')).write_text(json.dumps(dict(path=str(image),image_ref=ref,expires=time.time()+60)))
                with self.assertRaises(ValueError):await WeChatMaterials(4096).resolve(dict(resource_caps=[cap]),dict(images=[dict(image_ref='i_'+'c'*32)]),time.monotonic()+15)

    async def test_explicit_shared_context_and_unpaired_isolation(self):
        from qqbot_gateway.attention import Attention
        from qqbot_gateway.participation import validate_participation
        import sys,site
        root=Path(__file__).resolve().parents[1]
        site.addsitedir(str(root/'runtime/astrbot-tool/astrbot/Lib/site-packages'))
        from plugins.qq_router.wechat import AliasedAttention,RoutedAttention
        cfg=validate_participation(dict(mode='free',attention=dict(enabled=True)))
        qq=Attention(cfg,'q');qq.bot='qqbot';local=Attention(cfg,'w');local.bot='wxbot'
        shared=AliasedAttention(qq,{'wxroom':'qqroom'},{('wxroom','wxactor'):'qqactor'},'wxbot')
        wx=RoutedAttention(local,shared,{'wxroom'})
        wx.observe('wxroom','wxactor','mid','合成成员','合成称呼')
        self.assertEqual(qq.window('qqroom').rows[-1]['sender'],'qqactor')
        self.assertIs(wx.window('wxroom'),qq.window('qqroom'))
        wx.observe('other','wxactor','mid','同名','独立消息')
        self.assertEqual(len(qq.window('qqroom').rows),1)
        wx.reset('wxroom');self.assertFalse(qq.window('qqroom').rows)

if __name__=='__main__':unittest.main()
