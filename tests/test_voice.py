"""Optional voice contract, without downloading a model or sending user text."""

import base64
import hashlib
import importlib.util
import io
import json
import tempfile
import threading
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from hologram import voice
from hologram.server import make_server


class ModelAssets(unittest.TestCase):
    def test_system_switch_does_not_import_a_runtime(self):
        with patch.object(voice.importlib.util, "find_spec", side_effect=AssertionError()):
            for mode in ["  off", "system", False, 0]:
                self.assertFalse(voice.available(mode))

    def test_cache_verified_before_use(self):
        data = b"checked fixture"
        spec = ("voices/test.bin", len(data), hashlib.sha256(data).hexdigest())
        with tempfile.TemporaryDirectory() as d, patch.object(voice, "build_opener") as net:
            root = Path(d)
            (root / "test.bin").write_bytes(b"x" * len(data))
            net.return_value.open.return_value = io.BytesIO(data)
            self.assertEqual(voice.checked_asset(root, spec).read_bytes(), data)
            self.assertEqual(voice.checked_asset(root, spec).read_bytes(), data)
            net.return_value.open.assert_called_once()
            self.assertEqual(sorted(x.name for x in root.iterdir()), ["test.bin"])

    def test_invalid_download_never_installed(self):
        with tempfile.TemporaryDirectory() as d, patch.object(voice, "build_opener") as net:
            net.return_value.open.return_value = io.BytesIO(b"wrong")
            with self.assertRaises(ValueError):
                voice.checked_asset(Path(d), ("sample.bin", 5, "not-the-digest"))
            self.assertEqual(list(Path(d).iterdir()), [])


class Engine(unittest.TestCase):
    def test_input_limits_and_busy(self):
        engine = voice.VoiceEngine()
        with patch.object(engine, "prepare", side_effect=AssertionError("no model needed")):
            for text, lang in [
                ("", "hi-IN"),
                ("   ", "en-IN"),
                ("x" * 129, "hi-IN"),
                ("a", []),
                (None, "en-IN"),
            ]:
                self.assertFalse(engine.speak(text, lang)["ok"])
            self.assertFalse(engine.speak("hello", "en-IN", enabled=False)["ok"])
            engine.slot.acquire()
            self.assertEqual(engine.speak("hello", "en-IN")["reason"], "busy")
            engine.slot.release()

    def test_prepare_runs_once(self):
        model = object()
        engine = voice.VoiceEngine()
        with patch.object(voice, "load_engine", return_value=model) as load:
            engine.prepare()
            engine.prepare()
            self.assertTrue(engine.ready.wait(1))
            engine.prepare()
            self.assertIs(engine.model, model)
            self.assertEqual(load.call_count, 1)

    def test_startup_failure_degrades_without_repeated_downloads(self):
        engine = voice.VoiceEngine()
        with patch.object(voice, "load_engine", side_effect=OSError("offline")) as load:
            self.assertEqual(engine.speak("test", "en-IN"), {"ok": False, "reason": "system"})
            self.assertEqual(engine.speak("test", "en-IN")["reason"], "system")
            self.assertEqual(load.call_count, 1)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "optional neural runtime not installed")
    def test_audio_format_male_voice_and_envelope(self):
        import numpy as np

        engine = voice.VoiceEngine()
        engine.model = Mock()
        engine.model.tokenizer.phonemize.return_value = "hello"
        signal = np.r_[np.zeros(960), np.sin(np.arange(4800) * 0.08) * 0.3, np.zeros(960)]
        engine.model.create.return_value = (signal, 24000)
        for lang, name, backend_lang in [
            ("hi-IN", "amber_dost_hi", "hi"),
            ("en-IN", "amber_dost_en", "en-gb"),
        ]:
            out = engine.speak("J.A.R.V.I.S.", lang)
            self.assertTrue(out["ok"])
            self.assertEqual(out["speaker"], name)
            self.assertEqual(engine.model.create.call_args.kwargs["lang"], backend_lang)
            self.assertEqual(out["mime"], "audio/wav")
            self.assertEqual(out["hz"], 25)
            with wave.open(io.BytesIO(base64.b64decode(out["audio"]))) as wav:
                self.assertEqual(
                    (wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes()),
                    (24000, 1, 2, len(signal)),
                )
            levels = base64.b64decode(out["levels"])
            self.assertEqual(len(levels), 7)
            self.assertEqual(levels[0], 0)
            self.assertGreater(max(levels), 150)
        engine.model.tokenizer.phonemize.return_value = "x" * 187
        self.assertFalse(engine.speak("test", "en-IN")["ok"])
        engine.model.tokenizer.phonemize.return_value = "test"
        engine.model.create.return_value = (np.zeros(300), 24000)
        self.assertFalse(engine.speak("test", "en-IN")["ok"])


class VoiceHttp(unittest.TestCase):
    def setUp(self):
        with patch.object(voice, "available", return_value=True):
            self.server = make_server(0)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.03}, daemon=True
        )
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/api/voice"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(1)

    def post(self, obj, **headers):
        req = Request(
            self.url,
            data=json.dumps(obj).encode(),
            headers={"Content-Type": "application/json", **headers},
        )
        with urlopen(req, timeout=3) as r:
            return json.load(r)

    def test_voice_media_contract(self):
        with patch.object(
            voice.engine, "speak", return_value={"ok": True, "speaker": "hm_omega"}
        ) as engine:
            r = self.post({"text": "नमस्ते।", "lang": "hi-IN"})
            self.assertEqual(r["speaker"], "hm_omega")
            engine.assert_called_once_with("नमस्ते।", "hi-IN", enabled=True)

    def test_bad_payload_or_origin_not_synthesized(self):
        with patch.object(voice.engine, "speak", side_effect=AssertionError()) as engine:
            for obj in [
                {},
                {"text": "x" * 129, "lang": "hi-IN"},
                {"text": "hi", "lang": "fr"},
                [1],
            ]:
                with self.assertRaises(HTTPError) as error:
                    self.post(obj)
                self.assertEqual(error.exception.code, 400)
            with self.assertRaises(HTTPError) as error:
                self.post({"text": "hi", "lang": "en-IN"}, Origin="https://other.invalid")
            self.assertEqual(error.exception.code, 403)
            engine.assert_not_called()
