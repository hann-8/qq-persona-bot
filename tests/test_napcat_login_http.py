"""Real stdlib HTTP transport against an ephemeral synthetic loopback server."""
from contextlib import contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from qqbot_gateway.napcat_login_client import WebUI, LoginFailure


@contextmanager
def fake_server(*, status=200, body=None, raw=None):
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            requests.append((self.path,dict(self.headers),self.rfile.read(int(self.headers.get('Content-Length','0')))))
            self.send_response(status);self.send_header('Connection','close');self.end_headers()
            self.wfile.write(raw if raw is not None else json.dumps(body).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    original=http.client.HTTPConnection
    def connect(host,port,**kwargs):
        assert (host,port)==('127.0.0.1',6099)
        return original('127.0.0.1',server.server_port,**kwargs)
    try:
        with patch('qqbot_gateway.napcat_login_client.http.client.HTTPConnection',side_effect=connect):yield requests
    finally:server.shutdown();server.server_close();thread.join()


class HTTPContract(unittest.TestCase):
    def test_fixed_route_bearer_and_no_proxy(self):
        with fake_server(body={'code':0,'data':{'Credential':'synthetic-bearer'},'message':'ignored'}) as requests:
            web=WebUI(lambda:True)
            auth=web.request('auth',{'hash':'synthetic-hash'});web.credential=auth['Credential']
            web.request('status')
        self.assertEqual(requests[0][0],'/api/auth/login')
        self.assertEqual(requests[1][0],'/api/QQLogin/CheckLoginStatus')
        self.assertEqual(requests[1][1]['Authorization'],'Bearer synthetic-bearer')
    def test_bad_envelopes_and_rejection(self):
        for body in ({'code':-1,'data':None},{'code':True,'data':{}},{'code':0},{'code':0,'data':[]},[],{'code':'0','data':{}}):
            with self.subTest(body=body),fake_server(body=body):
                with self.assertRaises(LoginFailure):WebUI(lambda:True).request('auth')
        with fake_server(raw=b'{"code":0,"code":0,"data":{}}'):
            with self.assertRaises(LoginFailure):WebUI(lambda:True).request('auth')
    def test_redirect_oversize_invalid_json(self):
        for status,raw in ((302,b''),(200,b'x'*65537),(200,b'invalid')):
            with fake_server(status=status,raw=raw) as requests:
                with self.assertRaises(LoginFailure):WebUI(lambda:True).request('auth')
                self.assertEqual(len(requests),1)
    def test_deadline_request_budget_and_no_arbitrary_routes(self):
        now=[0];web=WebUI(lambda:True,clock=lambda:now[0]);now[0]=21
        with self.assertRaises(LoginFailure):web.request('auth')
        with fake_server(body={'code':0,'data':{}}) as requests:
            web=WebUI(lambda:True)
            for _ in range(4):web.request('status')
            with self.assertRaises(LoginFailure):web.request('status')
            web.request('auth')
            with self.assertRaises(LoginFailure):web.request('auth')
            with self.assertRaises(LoginFailure):web.request('ResetDeviceID')
            self.assertEqual(len(requests),5)
    def test_invalid_listener_prevents_any_connection(self):
        with patch('http.client.HTTPConnection',side_effect=AssertionError('opened')):
            with self.assertRaises(LoginFailure):WebUI(lambda:False).request('auth')


if __name__=='__main__':unittest.main()
