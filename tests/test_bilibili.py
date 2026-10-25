"""LAP-42 subtitle retirement tests, no real HTTP/auth/model calls."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from qqbot_gateway.bilibili_policy import validate
from qqbot_gateway.web_policy import DEFAULTS as WEB
from qqbot_gateway.web_retrieval import Retriever,CURRENT_TEXT
class RetiredTests(unittest.IsolatedAsyncioTestCase):
 async def test_video_no_http_or_subtitle_service(self):
  def forbidden(*args,**kwargs):raise AssertionError('Unexpected HTTP')
  r=Retriever(WEB|dict(enabled=True),http_factory=forbidden,bilibili={'enabled':True})
  self.assertFalse(hasattr(r,'bilibili'))
  for text in ('https://www.bilibili.com/video/BV1234567890','BV1234567890','https://b23.tv/test'):
   for mentioned in (True,False):
    token=CURRENT_TEXT.set((mentioned,'fixture'))
    try:
     result=await r.retrieve(text);self.assertFalse(result.sources)
     if mentioned:self.assertIn('retired',result.notice)
    finally:CURRENT_TEXT.reset(token)
 async def test_legacy_false_parses_true_rejected_service_absent(self):
  self.assertFalse(validate({'enabled':False},WEB)['enabled'])
  with self.assertRaisesRegex(ValueError,'BILIBILI_RETIRED'):validate({'enabled':True},WEB)
  from qqbot_gateway import bilibili_subtitles
  self.assertFalse(hasattr(bilibili_subtitles,'Subtitles'))
  self.assertFalse(hasattr(bilibili_subtitles,'credentials'))
if __name__=='__main__':unittest.main()
