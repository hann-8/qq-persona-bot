import asyncio
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import socket
import ssl
import sys
import tempfile
import unittest
from unittest.mock import patch,AsyncMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import psutil
from qqbot_gateway.public_http import PublicHTTP,PublicResolver,WebFailure,Audit,safe_url,public_ip
from qqbot_gateway.public_network import validate_network,tls_context,page_url,doh_answers,BootstrapResolver,CA_FILE
from qqbot_gateway.web_extractor import WebExtractor
from qqbot_gateway.evidence_selection import select,sources_for_budget,manifest,validate_manifest,encoded
from qqbot_gateway.web_retrieval import Retriever,Retrieval,WebRunner,evidence_prompt,source_plan
from qqbot_gateway.web_policy import DEFAULTS,SEARCH_QUALITY_PASSED
from qqbot_gateway.token_budget import InputBudget,dialog_text
from qqbot_gateway.reply_plan import DEFAULTS as OUTPUT


FACTS=[
    ('中文新闻','河口观测站于2026年10月21日启动。首批安装了十二台传感器。所有监测数据每小时公开一次。'),
    ('中文长文章','试验第一阶段使用太阳能供电。第二阶段增加蓄电池储能。第三阶段把多余电能交给公共电网。'),
    ('技术文档','连接必须先验证证书。超时后终止当前请求。失败后不会自动切换到其他提供方。'),
    ('English documentation','The endpoint accepts exactly one document. Requests expire after two seconds. Results retain original paragraph order.'),
]


def fixture(title,body):
    return '<!doctype html><html><head><title>'+title+'</title><meta property="article:published_time" content="2026-10-21"></head><body><nav>NAV_NOISE</nav><article><h1>'+title+'</h1>'+''.join('<p>'+('第%d段。'%n if title=='中文长文章' else '')+body+'</p>' for n in range(80 if title=='中文长文章' else 6))+'</article><div hidden>HIDDEN_NOISE</div><iframe>FRAME_NOISE</iframe><script>SCRIPT_NOISE</script><footer>FOOTER_NOISE</footer></body></html>'


class NetworkTests(unittest.IsolatedAsyncioTestCase):
    def test_network_enums(self):
        self.assertEqual(validate_network({}),dict(resolver='system',ca_bundle_file=None))
        for cfg in ({'resolver':'auto'},{'ca_bundle_file':'C:/ca.pem'},{'ca_bundle_file':False},{'resolver':'google_doh'},{'verify':False}):
            with self.subTest(cfg=cfg),self.assertRaises(ValueError):validate_network(cfg)
        self.assertFalse(SEARCH_QUALITY_PASSED)

    def test_url_credentials_and_normal_queries(self):
        for url in ('https://example.com/a?token=x','https://example.com/?%61pi_key=x','https://example.local/a','https://example.internal/a','https://example.com/?password=x'):
            with self.subTest(url=url),self.assertRaises(WebFailure):page_url(url)
        self.assertEqual(page_url('https://example.com/article?id=7&lang=zh'),'https://example.com/article?id=7&lang=zh')
        for ip in ('127.0.0.1','10.1.2.3','169.254.169.254','100.64.0.1','198.18.0.1','::ffff:8.8.8.8','ff02::1','::1'):
            with self.subTest(ip=ip),self.assertRaises(WebFailure):public_ip(ip)

    async def test_bootstrap_does_not_use_system_dns(self):
        with patch('socket.getaddrinfo',side_effect=AssertionError('system DNS called')):
            result=await BootstrapResolver().resolve('cloudflare-dns.com',443)
            self.assertEqual([x['host'] for x in result],['1.1.1.1'])
            with self.assertRaises(WebFailure):await BootstrapResolver().resolve('elsewhere.example',443)

    def answer(self):
        return dict(Status=0,Question=[dict(name='example.com.',type=1)],Answer=[dict(name='example.com.',type=5,TTL=90,data='cdn.example.com.'),dict(name='cdn.example.com.',type=1,TTL=120,data='8.8.8.8')])

    def test_doh_cname_and_limits(self):
        good=self.answer();self.assertEqual(doh_answers(good,'example.com'),(['8.8.8.8'],60))
        variants=[]
        for field,value in [('Status',2),('TC',True),('Question',[dict(name='other.com',type=1)]),('Answer',[])]:
            row=deepcopy(good);row[field]=value;variants.append(row)
        for ip in ('127.0.0.1','198.18.0.1','::ffff:8.8.8.8'):
            row=deepcopy(good);row['Answer'][1]['data']=ip;variants.append(row)
        row=deepcopy(good);row['Answer'].append(dict(name='unused.example.com',type=1,TTL=1,data='8.8.8.8'));variants.append(row)
        row=deepcopy(good);row['Answer'][1]=dict(name='cdn.example.com.',type=5,TTL=1,data='example.com.');variants.append(row)
        row=deepcopy(good);row['Answer']+=deepcopy(row['Answer'][1:])*8;variants.append(row)
        for row in variants:
            with self.subTest(row=row),self.assertRaises(WebFailure):doh_answers(row,'example.com')

    async def test_doh_transport_tls_failure_no_fallback(self):
        resolver=PublicResolver(dict(resolver='cloudflare_doh'))
        # Unknown CA remains a TLS error, no system DNS or alternate provider.
        with patch('aiohttp.ClientSession.get',side_effect=ssl.SSLCertVerificationError('synthetic')),patch('socket.getaddrinfo',side_effect=AssertionError()):
            with self.assertRaises(ssl.SSLCertVerificationError):await resolver.resolve('example.com',443)
        self.assertEqual(resolver.audit.dns_calls,1)
        resolver.audit.dns_calls=8
        with self.assertRaisesRegex(WebFailure,'dns_limit'):await resolver.resolve('example.com',443)

    async def test_doh_ram_cache_ttl(self):
        resolver=PublicResolver(dict(resolver='cloudflare_doh'))
        import time
        resolver.cache['example.com']=(time.monotonic()+30,['8.8.8.8'])
        with patch('aiohttp.ClientSession',side_effect=AssertionError()):
            self.assertEqual((await resolver.resolve('example.com',443))[0]['host'],'8.8.8.8')
        self.assertEqual(resolver.audit.dns_calls,0)

    async def test_doh_fixed_transport_schema_size_and_cache(self):
        outer=self;response_body=json.dumps(self.answer()).encode()
        class Response:
            status=200;headers={'Content-Type':'application/dns-json'}
            async def __aenter__(self):return self
            async def __aexit__(self,*a):pass
            @property
            def content(self):return self
            async def iter_chunked(self,size):yield response_body
        class Session:
            def __init__(self,**kwargs):
                self.connector=kwargs['connector'];outer.assertFalse(kwargs['trust_env']);outer.assertFalse(kwargs['auto_decompress'])
                outer.assertEqual(kwargs['timeout'].total,3)
                outer.assertIsInstance(self.connector._resolver,BootstrapResolver)
                outer.assertTrue(self.connector._ssl.check_hostname)
            async def __aenter__(self):return self
            async def __aexit__(self,*a):await self.connector.close()
            def get(self,url,**kwargs):
                outer.assertFalse(self._retry_connection)
                outer.assertEqual(url,'https://cloudflare-dns.com/dns-query')
                outer.assertEqual(kwargs,dict(params={'name':'example.com','type':'A'},allow_redirects=False))
                return Response()
        with patch('aiohttp.ClientSession',Session),patch('socket.getaddrinfo',side_effect=AssertionError('system DNS')):
            resolver=PublicResolver({'resolver':'cloudflare_doh'})
            self.assertEqual((await resolver.resolve('example.com',443))[0]['host'],'8.8.8.8')
            self.assertEqual((await resolver.resolve('example.com',443))[0]['host'],'8.8.8.8');self.assertEqual(resolver.audit.dns_calls,1)
            response_body=b'x'*32769
            with self.assertRaisesRegex(WebFailure,'doh_limit'):await PublicResolver({'resolver':'cloudflare_doh'}).resolve('example.com',443)

    def cert(self,ca):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes,serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'synthetic local test')])
        cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(1)
              .not_valid_before(datetime.now(timezone.utc)-timedelta(days=1)).not_valid_after(datetime.now(timezone.utc)+timedelta(days=1))
              .add_extension(x509.BasicConstraints(ca=ca,path_length=None),critical=True).sign(key,hashes.SHA256()))
        return cert.public_bytes(serialization.Encoding.PEM)

    def test_ca_fixed_path_private_key_leaf_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/CA_FILE;path.parent.mkdir()
            for data in (b'-----BEGIN PRIVATE KEY-----\nx\n-----END PRIVATE KEY-----',b'x'*1048577,self.cert(False)):
                path.write_bytes(data)
                with self.assertRaises(WebFailure):tls_context(dict(ca_bundle_file=CA_FILE),root)
            path.write_bytes(self.cert(True))
            ctx=tls_context(dict(ca_bundle_file=CA_FILE),root)
            self.assertTrue(ctx.check_hostname);self.assertEqual(ctx.verify_mode,ssl.CERT_REQUIRED)
            path.unlink()
            try:path.symlink_to(root/'outside.pem')
            except OSError:pass
            else:
                with self.assertRaises(WebFailure):tls_context(dict(ca_bundle_file=CA_FILE),root)

    def test_env_ca_cannot_override(self):
        with patch.dict(os.environ,{'SSL_CERT_FILE':'does-not-exist','SSL_CERT_DIR':'does-not-exist','HTTPS_PROXY':'http://127.0.0.1:1'}):
            ctx=tls_context();self.assertTrue(ctx.check_hostname);self.assertEqual(ctx.verify_mode,ssl.CERT_REQUIRED)

    async def test_real_tls_unknown_ca_wrong_hostname_and_explicit_trust(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes,serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'secrets').mkdir()
            key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'synthetic.example')])
            cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(2)
                  .not_valid_before(datetime.now(timezone.utc)-timedelta(days=1)).not_valid_after(datetime.now(timezone.utc)+timedelta(days=1))
                  .add_extension(x509.BasicConstraints(ca=True,path_length=None),critical=True)
                  .add_extension(x509.SubjectAlternativeName([x509.DNSName('synthetic.example')]),critical=False).sign(key,hashes.SHA256()))
            (root/CA_FILE).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            private=root/'key.pem';private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            server_context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server_context.load_cert_chain(root/CA_FILE,private)
            async def handler(reader,writer):writer.close();await writer.wait_closed()
            server=await asyncio.start_server(handler,'127.0.0.1',0,ssl=server_context)
            try:
                port=server.sockets[0].getsockname()[1]
                for ctx,hostname in ((tls_context(),'synthetic.example'),(tls_context({'ca_bundle_file':CA_FILE},root),'wrong.example')):
                    with self.assertRaises(ssl.SSLCertVerificationError):await asyncio.open_connection('127.0.0.1',port,ssl=ctx,server_hostname=hostname)
                _,writer=await asyncio.open_connection('127.0.0.1',port,ssl=tls_context({'ca_bundle_file':CA_FILE},root),server_hostname='synthetic.example')
                writer.close();await writer.wait_closed()
            finally:server.close();await server.wait_closed()


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory=tempfile.TemporaryDirectory();self.extractor=WebExtractor(Path(self.directory.name))
    async def asyncTearDown(self):self.directory.cleanup()

    async def test_chinese_news_long_technical_english_quality(self):
        for title,body in FACTS:
            result=await self.extractor.extract(fixture(title,body))
            self.assertEqual(result['title'],title);self.assertEqual(result['published_at'],'2026-10-21')
            self.assertIn(body,result['text'])
            self.assertFalse(any(x in result['text'] for x in ('NAV_NOISE','HIDDEN_NOISE','SCRIPT_NOISE','FOOTER_NOISE','FRAME_NOISE')))
            self.assertTrue(self.extractor.last_metrics['exited']);self.assertTrue(self.extractor.last_metrics['cleanup'])
            self.assertLess(self.extractor.last_metrics['peak_rss'],256*1024*1024)
            self.assertLess(self.extractor.last_metrics['elapsed_seconds'],2)
        self.assertIsNone(self.extractor.active_pid)

    async def test_shell_entities_restricted_and_empty(self):
        for html in ('<title>only title</title><nav>links</nav>', '<title>application</title><script>renderEverything()</script>',
                     '<!DOCTYPE foo [<!ENTITY x SYSTEM "http://127.0.0.1/">]><p>&x;</p>',fixture('restricted','登录后阅读。'*40)):
            with self.subTest(html=html[:20]),self.assertRaises(WebFailure):await self.extractor.extract(html)
            self.assertTrue(self.extractor.last_metrics['cleanup'])

    async def test_malformed_and_input_cap(self):
        result=await self.extractor.extract('<title>broken</title><article><p>'+('中文事实。'*80))
        self.assertIn('中文事实',result['text'])
        with self.assertRaisesRegex(WebFailure,'extract_input_limit'):await self.extractor.extract('x'*1048577)
        legacy=await self.extractor.extract(fixture(*FACTS[0]),'legacy')
        self.assertIn(FACTS[0][1],legacy['text']);self.assertTrue(self.extractor.last_metrics['exited'])

    async def test_cancel_reaps_owned_worker(self):
        task=asyncio.create_task(self.extractor.extract(fixture(*FACTS[0])))
        for _ in range(200):
            if self.extractor.active_pid:break
            await asyncio.sleep(.001)
        pid=self.extractor.active_pid;self.assertIsNotNone(pid)
        task.cancel();await asyncio.gather(task,return_exceptions=True)
        self.assertFalse(psutil.pid_exists(pid));self.assertTrue(self.extractor.last_metrics['cleanup'])
        # A second invocation proves cancellation did not leave the owner locked.
        self.assertIn('text',await self.extractor.extract(fixture(*FACTS[1])))

    async def test_timeout_reaps_and_no_orphan_pipe(self):
        # Fixed script substitute at the spawn boundary only, never a product option.
        real=asyncio.create_subprocess_exec
        async def slow(*args,**kwargs):
            return await real(args[0],'-I','-c','import time;time.sleep(20)',**kwargs)
        with patch('asyncio.create_subprocess_exec',slow):
            with self.assertRaisesRegex(WebFailure,'extract_timeout'):await self.extractor.extract(fixture(*FACTS[0]))
        self.assertTrue(self.extractor.last_metrics['exited']);self.assertTrue(self.extractor.last_metrics['cleanup'])

    async def test_memory_cap_and_children_denied(self):
        # Same fixed leaf executable under the product's Job limits. Synthetic
        # malicious parser replacement cannot allocate >256MiB or spawn Python.
        real=asyncio.create_subprocess_exec
        for code in ('x=bytearray(300*1024*1024)',
                     'import subprocess,sys;subprocess.run([sys.executable,"-c","pass"],check=True)'):
            async def replacement(*args,**kwargs):return await real(args[0],'-I','-c',code,**kwargs)
            with patch('asyncio.create_subprocess_exec',replacement):
                with self.assertRaises(WebFailure):await self.extractor.extract(fixture(*FACTS[0]))
            self.assertTrue(self.extractor.last_metrics['exited']);self.assertTrue(self.extractor.last_metrics['cleanup'])


class EvidenceTests(unittest.TestCase):
    def body(self):return '\n'.join(('第%02d段：'%n)+('材料事实不会变。'*12) for n in range(36))
    def source(self,text):return dict(title='真实标题',url='https://example.com/a',text=text,status='body',published_at=None)

    def test_six_zones_full_and_excerpt(self):
        body=self.body();value=select(body,4000)
        self.assertEqual(value['coverage'],'excerpt');self.assertGreaterEqual(len(value['ranges']),4)
        self.assertIn('第00段',value['text']);self.assertIn('第35段',value['text'])
        self.assertEqual(value['text'],'\n'.join(body[a:b] for a,b in value['ranges']))
        self.assertEqual(select(body,20000)['coverage'],'full')
        for policy,complete in [('reject',False),('excerpt',True)]:
            with self.assertRaises(WebFailure):select(body,4000,policy,complete)

    def test_insufficient_complete_paragraphs(self):
        for text,cap in [('中文'*5000,3000),(self.body(),500)]:
            with self.assertRaises(WebFailure):select(text,cap)

    def test_metadata_counts_and_two_page_shared_cap(self):
        rows=sources_for_budget([self.source(self.body()),self.source(self.body())|{'url':'https://example.com/b'}],6000,4000,'excerpt','概括')
        self.assertLessEqual(len(encoded(dict(partial=False,sources=rows))),6000)
        for row in rows:self.assertEqual(row['coverage'],'excerpt');self.assertGreaterEqual(row['selected_bytes'],1200)
        with self.assertRaises(WebFailure):sources_for_budget([self.source(self.body())],6000,4000,'excerpt','完整总结')

    def test_final_budget_recomputes_without_policy_or_question_loss(self):
        retrieval=Retrieval('read',[self.source(self.body())])
        prompt=dialog_text([dict(role='user',content='old'),dict(role='assistant',content='old answer'),dict(role='user',content='总结 https://example.com/a')])
        budget=InputBudget(limit=6500,overhead=100)
        result,rows=evidence_prompt('FIXED_POLICY',prompt,retrieval,budget,DEFAULTS)
        self.assertIsNotNone(result);self.assertLessEqual(budget.usage('FIXED_POLICY',result),budget.limit)
        self.assertIn('总结 https://example.com/a',result);self.assertEqual(rows[0]['coverage'],'excerpt')
        notice=source_plan('回答',rows,OUTPUT,'问题');self.assertIn('节选',notice.canonical_text)
        self.assertEqual(evidence_prompt('policy',prompt,retrieval,InputBudget(limit=800),DEFAULTS),(None,[]))

    def test_manifest_range_digest_and_forgery(self):
        source={'web_anchor':'https://example.com/a'}
        rows=sources_for_budget([self.source(self.body())],6000,4000,'excerpt','概括')
        m=manifest(rows);validate_manifest(m,source)
        for key,value in [('url','http://127.0.0.1/'),('sha256','bad'),('ranges',[[9,1]]),('coverage','full')]:
            changed=deepcopy(m);changed[0][key]=value
            with self.assertRaises(ValueError):validate_manifest(changed,source)


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    def setup_pipeline(self,question,body,budget=16384):
        from qqbot_gateway.vision import member_source
        from qqbot_gateway.attention import canonical
        source=member_source(question,['鱼片']);source['web_anchor']=question
        reader=Retriever(DEFAULTS|{'enabled':True})
        async def retrieve(q):return Retrieval('read',[dict(title='Title',url='https://example.com',text=body,status='body')])
        reader.retrieve=retrieve
        runner=type('Runner',(),{'run':AsyncMock(return_value='{"qqbot_turn_reply":2,"decision":"speak","kind":"answer","bubbles":["正文回答"],"meme_id":null,"response_to_seq":1,"mention":null,"memory_proposals":[]}')})()
        wrapper=WebRunner(runner,reader,InputBudget(limit=budget),OUTPUT)
        prompt=dialog_text([dict(role='user',content=canonical(source))])
        return wrapper,runner,prompt,source

    async def test_full_request_and_final_budget_direct_notice_ambient_silent(self):
        body='\n'.join('第%d段：'%i+'正文事实。'*30 for i in range(36))
        for question,budget in [('完整总结 https://example.com',16384),('总结 https://example.com',1500)]:
            wrapper,runner,prompt,_=self.setup_pipeline(question,body,budget)
            for direct in (True,False):
                result=await wrapper.run_v2('FIXED_POLICY',prompt,'a'*10,dict(must_reply=direct,target_seq=1))
                self.assertFalse(result.generation_performed)
                self.assertEqual(result.prepared_plan is not None,direct)
                if direct:self.assertEqual(result.prepared_plan.fallback_reason,'local_web_notice')
            runner.run.assert_not_called()

    async def test_once_final_material_manifest_and_no_memory_promotion(self):
        wrapper,runner,prompt,source=self.setup_pipeline('总结 https://example.com','合格正文事实。'*60)
        result=await wrapper.run_v2('FIXED_POLICY',prompt,'a'*10,dict(must_reply=True,target_seq=1))
        runner.run.assert_awaited_once();self.assertIn('来源：',result.text)
        self.assertEqual(result.memory_proposals,());self.assertEqual(result.web_evidence[0]['coverage'],'full')
        validate_manifest(list(result.web_evidence),source)


if __name__=='__main__':unittest.main()
