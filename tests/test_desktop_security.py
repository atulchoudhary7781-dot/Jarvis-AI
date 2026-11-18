"""Local broker security unit tests. OS and dialog are mocked; not a Windows smoke test."""
import http.client
import json
import threading
import unittest
from hologram.desktop import DesktopSession
from hologram.server import make_server

class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.now=0
        self.launched=[]
        self.yes=True
        self.s=DesktopSession(ask=lambda _:self.yes, launch=self.launched.append, clock=lambda:self.now)
    def test_allowed_single_use_and_cross_app(self):
        self.assertFalse(self.s.approve('cmd')['ok'])
        permit=self.s.approve('notepad')['permit']
        self.assertFalse(self.s.commit('paint',permit)['ok'])
        self.assertFalse(self.s.commit('notepad',permit)['ok'])
        permit=self.s.approve('notepad')['permit']
        self.assertTrue(self.s.commit('notepad',permit)['ok'])
        self.assertFalse(self.s.commit('notepad',permit)['ok'])
        self.assertEqual(self.launched,['notepad'])
    def test_expiry_rejection_rate_limit(self):
        self.yes=False
        self.assertFalse(self.s.approve('paint')['ok'])
        self.yes=True
        permit=self.s.approve('paint')['permit'];self.now=5
        self.assertFalse(self.s.commit('paint',permit)['ok'])
        self.s.approve('paint');self.s.approve('paint')
        self.assertFalse(self.s.approve('paint')['ok'])
        self.now=7201
        self.assertFalse(self.s.admits(self.s.key))
    def test_local_http_guards(self):
        server=make_server(0,desktop=self.s)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        host=f'127.0.0.1:{server.server_port}'
        def request(path, headers, data):
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            c.request('POST',path,body=json.dumps(data),headers={'Content-Type':'application/json',**headers})
            r=c.getresponse(); result=(r.status,json.loads(r.read()));c.close();return result
        try:
            good={'Origin':'http://'+host,'X-Jarvis-Session':self.s.key}
            for hdr in [{},{'Origin':'http://evil.invalid','X-Jarvis-Session':self.s.key},{'Origin':'http://'+host,'X-Jarvis-Session':'wrong'},{**good,'Sec-Fetch-Site':'cross-site'}]:
                self.assertEqual(request('/api/desktop/approve',hdr,{'app':'notepad'})[0],403)
            self.assertFalse(request('/api/desktop/approve',good,{'app':'powershell'})[1]['ok'])
            p=request('/api/desktop/approve',good,{'app':'calculator'})[1]['permit']
            self.assertTrue(request('/api/desktop/commit',good,{'app':'calculator','permit':p})[1]['ok'])
            self.assertFalse(request('/api/desktop/commit',good,{'app':'calculator','permit':p})[1]['ok'])
            self.assertEqual(self.launched,['calculator'])
        finally:server.shutdown();server.server_close();thread.join()
    def test_public_has_no_desktop_routes(self):
        server=make_server(0,preview=True);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            c.request('POST','/api/desktop/approve',body='{}',headers={'Content-Type':'application/json'})
            self.assertEqual(c.getresponse().status,404);c.close()
        finally:server.shutdown();server.server_close();t.join()
if __name__=='__main__':unittest.main()
