"""Groq adapter tests use fake HTTP responses, not real provider audio or credentials."""
import json
import unittest
import urllib.error
from hologram import groq_speech as g

class Response:
    def __init__(self, data, url=g.URL):
        self.data, self.url, self.status = data, url, 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def geturl(self): return self.url
    def read(self, n): return self.data[:n]

class Client:
    def __init__(self, result): self.result, self.calls = result, []
    def open(self, req, timeout):
        self.calls.append((req, timeout))
        if isinstance(self.result, Exception): raise self.result
        return self.result

class GroqSpeechTest(unittest.TestCase):
    def test_multilingual_response_and_fixed_endpoint(self):
        c=Client(Response(json.dumps({'text':'  Hola, mundo  ','language':'spanish'}).encode()))
        result=g.transcribe(b'x'*100,'audio/webm;codecs=opus','test-key-123',opener=c)
        self.assertEqual(result,{'ok':True,'text':'Hola, mundo','language':'spanish'})
        req,timeout=c.calls[0]
        self.assertEqual(req.full_url,g.URL)
        self.assertEqual(timeout,22)
        self.assertIn(b'whisper-large-v3-turbo',req.data)
        self.assertNotIn(b'test-key-123',req.data)
        self.assertNotIn(b'name="language"',req.data)
    def test_translation_safely_bounded(self):
        c=Client(Response(json.dumps({'choices':[{'message':{'content':'Open YouTube'}}]}).encode(), url=g.CHAT_URL))
        result=g.translate('Abre YouTube', 'English', 'test-key-123', opener=c)
        self.assertEqual(result,{'ok':True,'text':'Open YouTube'})
        req,_=c.calls[0];self.assertEqual(req.full_url,g.CHAT_URL)
        msg=json.loads(req.data);self.assertIn('Preserve negatives',msg['messages'][0]['content'])
        self.assertEqual(msg['messages'][1]['content'],'Abre YouTube')
        self.assertFalse(g.translate('secret', 'English"} inject', 'test-key-123', opener=c)['ok'])
    def test_invalid_inputs_do_not_send(self):
        c=Client(Response(b'{}'))
        for data,mime,key in [(b'x'*99,'audio/wav','test-key-123'),(b'x'*100,'text/html','test-key-123'),(b'x'*100,'audio/wav','bad\r\nkey')]:
            self.assertFalse(g.transcribe(data,mime,key,opener=c)['ok'])
        self.assertEqual(c.calls,[])
    def test_limits_redirect_and_generic_errors(self):
        c=Client(Response(b'{}',url='https://attacker.invalid'))
        self.assertEqual(g.transcribe(b'x'*100,'audio/wav','test-key-123',opener=c)['reason'],'unavailable')
        c=Client(Response(json.dumps({'text':'x'*361,'language':'en'}).encode()))
        self.assertEqual(g.transcribe(b'x'*100,'audio/wav','test-key-123',opener=c)['reason'],'too_long')
        c=Client(urllib.error.HTTPError(g.URL,429,'provider details',{},None))
        self.assertEqual(g.transcribe(b'x'*100,'audio/wav','test-key-123',opener=c)['reason'],'rate_limited')

if __name__=='__main__': unittest.main()
