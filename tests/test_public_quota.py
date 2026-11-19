"""Shared quota contract; provider and Redis REST transport are mocked."""
import base64
import concurrent.futures
import http.client
import json
import os
import threading
import unittest
from unittest.mock import patch
from hologram import quota
from hologram.server import make_server

try:
    import fakeredis
except ImportError:
    fakeredis = None

URL = 'https://test-region.upstash.io'
TOKEN = 'local-test-token-123456'

class Response:
    status = 200
    def __init__(self, url, data): self.url, self.data = url, data
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def geturl(self): return self.url
    def read(self, n): return self.data[:n]

class FakeRedisTransport:
    def __init__(self): self.server = fakeredis.FakeServer(); self.commands=[]; self.lock=threading.Lock()
    def open(self, req, timeout):
        cmd=json.loads(req.data); self.commands.append(cmd)
        with self.lock:
            value=fakeredis.FakeRedis(server=self.server).execute_command(*cmd)
        return Response(req.full_url,json.dumps({'result':value}).encode())

class ConfigTests(unittest.TestCase):
    def test_validation(self):
        self.assertTrue(quota.valid_config(URL,TOKEN))
        for bad in ('http://test-region.upstash.io','https://evil.test','https://test-region.upstash.io.evil.test',
                    'https://evil.test@upstash.io','https://test-region.upstash.io/path'):
            self.assertFalse(quota.valid_config(bad,TOKEN))
        self.assertFalse(quota.valid_config(URL,'short'))
    def test_fail_closed(self):
        class Down:
            def open(self,*a,**k): raise OSError('down')
        self.assertFalse(quota.reserve(URL,TOKEN,'1.2.3.4',1,opener=Down()))
        self.assertFalse(quota.reserve(URL,TOKEN,'bad-ip',1,opener=Down()))
        class Bad:
            def open(self,req,timeout): return Response(req.full_url,b'{"result": true}')
        self.assertFalse(quota.reserve(URL,TOKEN,'1.2.3.4',1,opener=Bad()))

@unittest.skipUnless(fakeredis, 'Install fakeredis[lua] for atomic script tests')
class AtomicTests(unittest.TestCase):
    def test_weighted_and_privacy(self):
        t=FakeRedisTransport()
        for _ in range(4): self.assertTrue(quota.reserve(URL,TOKEN,'1.2.3.4',2,opener=t))
        self.assertFalse(quota.reserve(URL,TOKEN,'1.2.3.4',1,opener=t))
        self.assertTrue(quota.reserve(URL,TOKEN,'1.2.3.5',1,opener=t))
        self.assertNotIn('1.2.3.4', json.dumps(t.commands))
        r=fakeredis.FakeRedis(server=t.server)
        self.assertGreater(r.ttl('jarvis:voice:daily'),0)
        self.assertGreater(r.ttl('jarvis:voice:minute'),0)
    def test_daily_bound_across_many_instances(self):
        t=FakeRedisTransport()
        # Advance fixed minute windows without changing the shared daily budget.
        for window in range(5):
            for ip in range(10):
                self.assertTrue(quota.reserve(URL,TOKEN,f'10.{window}.0.{ip+1}',2,opener=t))
            r=fakeredis.FakeRedis(server=t.server);r.delete('jarvis:voice:minute')
        self.assertFalse(quota.reserve(URL,TOKEN,'10.8.0.1',1,opener=t))
        self.assertEqual(int(r.get('jarvis:voice:daily')),quota.DAILY_UNITS)
    def test_concurrent_never_exceeds_minute(self):
        t=FakeRedisTransport()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results=list(pool.map(lambda i:quota.reserve(URL,TOKEN,f'10.1.1.{i+1}',2,opener=t), range(30)))
        self.assertEqual(sum(results),quota.MINUTE_UNITS//2)

class ProductionIntegration(unittest.TestCase):
    def request(self, server, body):
        c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
        c.request('POST','/api/transcribe',json.dumps(body),{'Content-Type':'application/json','Origin':f'http://127.0.0.1:{server.server_port}','x-vercel-forwarded-for':'1.2.3.4'})
        r=c.getresponse();value=r.status,json.loads(r.read());c.close();return value
    def run_server(self, env, quota_allowed):
        with patch.dict(os.environ,env,clear=True),patch('hologram.quota.reserve',return_value=quota_allowed) as limit,patch('hologram.groq_speech.transcribe',return_value={'ok':True,'text':'hello','language':'english'}) as provider:
            server=make_server(0,preview=True);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
            try:
                body={'audio':base64.b64encode(b'x'*100).decode(),'mime':'audio/webm'}
                status,result=self.request(server,body)
                return status,result,limit.call_count,provider.call_count
            finally: server.shutdown();server.server_close();t.join()
    def test_guard(self):
        base={'VERCEL_ENV':'production','JARVIS_GROQ_PUBLIC':'1','GROQ_API_KEY':'local-test-key-123'}
        self.assertEqual(self.run_server(base,True)[0],404)
        base.update({'UPSTASH_REDIS_REST_URL':URL,'UPSTASH_REDIS_REST_TOKEN':TOKEN})
        status,result,limit,provider=self.run_server(base,False)
        self.assertEqual((status,limit,provider),(429,1,0))
        status,result,limit,provider=self.run_server(base,True)
        self.assertEqual((status,limit,provider),(200,1,1))
    def test_preview_quota_mode_never_bypasses_missing_storage(self):
        env={'VERCEL_ENV':'preview','JARVIS_GROQ_QUOTA_TEST':'1','GROQ_API_KEY':'local-test-key-123'}
        self.assertEqual(self.run_server(env,True)[0],404)
        env.update({'KV_REST_API_URL':URL,'KV_REST_API_TOKEN':TOKEN})
        self.assertEqual(self.run_server(env,False)[0],429)
        self.assertEqual(self.run_server(env,True)[0],200)
    def test_experiment_flag_cannot_enable_production(self):
        env={'VERCEL_ENV':'production','JARVIS_GROQ_EXPERIMENT':'1','GROQ_API_KEY':'local-test-key-123'}
        self.assertEqual(self.run_server(env,True)[0],404)
if __name__ == '__main__': unittest.main()
