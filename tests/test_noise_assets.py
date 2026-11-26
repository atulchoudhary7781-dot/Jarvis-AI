"""Noise asset routing and CSP; no real audio devices or external providers."""
import http.client
import threading
import unittest
from hologram.server import make_server

class NoiseAssetsTests(unittest.TestCase):
    def setUp(self):
        self.server = make_server(0, preview=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
    def get(self, path):
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=4)
        c.request('GET', path); r = c.getresponse()
        out = r.status, dict(r.getheaders()), r.read(); c.close(); return out
    def test_pinned_assets_served_same_origin_with_correct_mime(self):
        status, headers, payload = self.get('/api/audio/rnnoise.wasm')
        self.assertEqual(status, 200); self.assertEqual(headers['Content-Type'], 'application/wasm')
        self.assertEqual(payload[:4], b'\x00asm'); self.assertGreater(len(payload), 1000)
        status, headers, js = self.get('/api/audio/rnnoise-worklet.js')
        self.assertEqual(status, 200); self.assertIn('text/javascript', headers['Content-Type'])
        self.assertIn(b'@sapphi-red/web-noise-suppressor/rnnoise', js)
        status, headers, _ = self.get('/')
        self.assertEqual(status, 200); self.assertIn("'wasm-unsafe-eval'", headers['Content-Security-Policy'])
        self.assertIn("'sha256-", headers['Content-Security-Policy'])
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
    def test_no_arbitrary_file_serving(self):
        for path in ['/api/audio/not-an-asset', '/api/audio/../../server.py', '/api/audio/rnnoise.wasm/other']:
            self.assertEqual(self.get(path)[0], 404)

if __name__ == '__main__': unittest.main()
