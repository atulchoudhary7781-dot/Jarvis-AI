"""Preview HTTP integration with a mocked provider; not a real Groq or microphone test."""
import base64
import http.client
import json
import os
import threading
import unittest
from unittest.mock import patch
from hologram.server import make_server

class GroqPreviewTests(unittest.TestCase):
    def test_preview_transcription_and_guards(self):
        with patch.dict(os.environ, {'JARVIS_GROQ_EXPERIMENT':'1','GROQ_API_KEY':'test-key-123'}), \
             patch('hologram.groq_speech.transcribe', return_value={'ok':True,'text':'abre youtube','language':'spanish'}) as transcribe, \
             patch('hologram.groq_speech.translate', return_value={'ok':True,'text':'open youtube'}):
            server=make_server(0,preview=True);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            host=f'127.0.0.1:{server.server_port}'
            def req(path, body, headers):
                c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=4)
                c.request('POST',path,json.dumps(body),{'Content-Type':'application/json',**headers})
                r=c.getresponse();out=(r.status,json.loads(r.read()));c.close();return out
            try:
                c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=4);c.request('GET','/');r=c.getresponse();html=r.read().decode();c.close()
                self.assertIn('name="jarvis-cloud" content="preview"',html)
                self.assertNotIn('test-key-123',html)
                body={'audio':base64.b64encode(b'x'*100).decode(),'mime':'audio/webm'}
                self.assertEqual(req('/api/transcribe',body,{})[0],403)
                self.assertEqual(req('/api/transcribe',body,{'Origin':'https://evil.invalid'})[0],403)
                status,out=req('/api/transcribe',body,{'Origin':'http://'+host})
                self.assertEqual(status,200);self.assertEqual(out['command'],'open youtube')
                self.assertEqual(transcribe.call_count,1)
            finally:server.shutdown();server.server_close();thread.join()
    def test_default_public_does_not_expose_provider(self):
        with patch.dict(os.environ, {'GROQ_API_KEY':'test-key-123','VERCEL_ENV':'production'}, clear=False):
            server=make_server(0,preview=True);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=4);c.request('POST','/api/transcribe','{}',{'Content-Type':'application/json'});self.assertEqual(c.getresponse().status,404);c.close()
            finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__': unittest.main()
