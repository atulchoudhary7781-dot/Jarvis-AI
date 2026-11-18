"""Bounded, on-host speech synthesis. Text/audio never go to a TTS provider.

Two stock, non-cloned masculine Kokoro voices. The optional runtime is loaded
lazily. Only pinned model assets are cached on disk; speech is not cached.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import io
import os
import re
import tempfile
import threading
import time
import wave
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

REVISION = "1939ad2a8e416c0acfeecc08a694d14ef25f2231"
BASE = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/" + REVISION + "/"
ASSETS = (
    (
        "onnx/model_quantized.onnx",
        92361116,
        "fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478",
    ),
    (
        "voices/hm_omega.bin",
        522240,
        "b02d9222d9ed00ce26b302173a862c2c93f96cc40b5c422b8d14910b9ff34137",
    ),
    (
        "voices/bm_george.bin",
        522240,
        "c4b235a4c1f2cd3b939fed08b899ce9385638b763f7b73a59616c4fc9bd6c9bc",
    ),
    ("voices/hm_psi.bin", 522240, "644daf88ba8aeb7bd08950bbdcd4453bb280864e49dc4df93fabc6be32e03f37"),
    ("voices/bm_fable.bin", 522240, "f889083196807b4adb15e9204252165f503b8d33d3982e681c52443c49d798f1"),
)
SPEAKERS = {"hi-IN": ("amber_dost_hi", "hi"), "en-IN": ("amber_dost_en", "en-gb")}

MAX_SEGMENT = 128


def available(setting="auto"):
    return (
        str(setting).strip().lower() not in {"off", "system", "0", "false"}
        and importlib.util.find_spec("kokoro_onnx") is not None
    )


class ModelRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        dest = urlsplit(newurl)
        host = (dest.hostname or "").lower()
        if dest.scheme != "https" or not (
            host in {"huggingface.co", "hf.co"} or host.endswith((".huggingface.co", ".hf.co"))
        ):
            raise ValueError("Unexpected model asset location")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def checked_asset(root, entry):
    rel, size, digest = entry
    path = root / Path(rel).name
    if path.is_file() and path.stat().st_size == size:
        sha = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(512 * 1024), b""):
                sha.update(block)
        if sha.hexdigest() == digest:
            return path
    fd, tmp = tempfile.mkstemp(prefix=".voice-", dir=root)
    deadline = time.monotonic() + 65
    try:
        with os.fdopen(fd, "wb") as f:
            request = Request(BASE + rel, headers={"User-Agent": "Jarvis-Amber-Speech/2.0"})
            with build_opener(ModelRedirect).open(request, timeout=10) as resp:
                total = 0
                sha = hashlib.sha256()
                while block := resp.read(256 * 1024):
                    total += len(block)
                    if total > size or time.monotonic() > deadline:
                        raise ValueError("Model download limit")
                    sha.update(block)
                    f.write(block)
        if total != size or sha.hexdigest() != digest:
            raise ValueError("Model integrity check failed")
        os.replace(tmp, path)
        return path
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def load_engine():
    # Keep the normal (stock-Python) launcher working without the optional wheel.
    import numpy as np
    import onnxruntime as rt
    from kokoro_onnx import Kokoro

    root = Path.home() / ".cache" / "jarvis-amber-voice" / REVISION[:12]
    root.mkdir(parents=True, exist_ok=True)
    model, *voices = [checked_asset(root, e) for e in ASSETS]
    # Float arrays only; no executable code, pickled weights, or user-supplied URLs.
    arrays = {p.stem: np.fromfile(p, dtype="<f4").reshape(510, 1, 256) for p in voices}
    # Convex blends of licensed stock embeddings, not an imitation or voiceprint.
    arrays["amber_dost_hi"] = 0.58 * arrays["hm_psi"] + 0.42 * arrays["hm_omega"]
    arrays["amber_dost_en"] = 0.60 * arrays["bm_george"] + 0.40 * arrays["bm_fable"]
    fd, tmp = tempfile.mkstemp(prefix=".pair-", dir=root)
    try:
        with os.fdopen(fd, "wb") as f:
            np.savez(f, **arrays)
        pair = root / "amber-pair.npz"
        os.replace(tmp, pair)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
    opt = rt.SessionOptions()
    opt.inter_op_num_threads = 1
    opt.intra_op_num_threads = min(2, os.cpu_count() or 1)
    opt.enable_cpu_mem_arena = False
    opt.enable_mem_pattern = False
    opt.log_severity_level = 3
    opt.add_session_config_entry("session.intra_op.allow_spinning", "0")
    session = rt.InferenceSession(str(model), sess_options=opt, providers=["CPUExecutionProvider"])
    return Kokoro.from_session(session, str(pair))


class VoiceEngine:
    def __init__(self):
        self.model = None
        self.guard = threading.Lock()
        self.slot = threading.BoundedSemaphore(1)
        self.ready = threading.Event()
        self.loading = False
        self.retry_at = 0.0

    def _load(self):
        try:
            model = load_engine()
        except Exception:
            model = None  # An unavailable runtime/model never breaks the screen.
        with self.guard:
            self.model = model
            self.loading = False
            self.retry_at = time.monotonic() + (180 if model is None else 0)
            self.ready.set()

    def prepare(self):
        """Prime once in the background. No text, microphone or synthesis involved."""
        with self.guard:
            if self.model is None and not self.loading and time.monotonic() >= self.retry_at:
                self.loading = True
                self.ready.clear()
                threading.Thread(target=self._load, daemon=True, name="Amber speech model").start()

    def speak(self, text, lang, *, enabled=True):
        if (
            not enabled
            or not isinstance(text, str)
            or not 0 < len(text) <= MAX_SEGMENT
            or not text.strip()
            or not isinstance(lang, str)
            or lang not in SPEAKERS
        ):
            return {"ok": False, "reason": "system"}
        if not self.slot.acquire(blocking=False):
            return {"ok": False, "reason": "busy"}
        try:
            self.prepare()
            if self.model is None and (not self.ready.wait(3.0) or self.model is None):
                return {"ok": False, "reason": "warming" if self.loading else "system"}
            import numpy as np

            name, language = SPEAKERS[lang]
            # eSpeak understands Hindi; turn a danda into a prosodic sentence break.
            clean = " ".join(text.replace("।", ". ").split())
            clean = re.sub(
                r"J\.?A\.?R\.?V\.?I\.?S\.?",
                "जार्विस" if language == "hi" else "Jarvis",
                clean,
                flags=re.IGNORECASE,
            )
            if language == "hi":
                names = {"youtube": "यूट्यूब", "google maps": "गूगल मैप्स", "gmail": "जीमेल", "notepad": "नोटपैड", "spotify": "स्पॉटिफ़ाई", "calculator": "कैलकुलेटर", "windows": "विंडोज़", "github": "गिटहब", "space": "स्पेस"}
                clean = re.sub(r"\b(?:" + "|".join(names) + r")\b", lambda m: names[m[0].lower()], clean, flags=re.I)
            phones = self.model.tokenizer.phonemize(clean, language)
            if not phones or len(phones) > 186:
                return {"ok": False, "reason": "system"}
            # Short, bounded intonation groups limit CPU, peak RAM and first-audio delay.
            sound, sr = self.model.create(
                phones,
                voice=name,
                lang=language,
                is_phonemes=True,
                speed=0.97 if clean.endswith("?") else (0.99 if language == "hi" else 1.0),
                sentence_pause=0.27,
                clause_pause=0.13,
            )
            sound = np.asarray(sound, dtype=np.float32).reshape(-1)
            if sr != 24000 or not 0 < len(sound) <= sr * 26 or not np.isfinite(sound).all():
                return {"ok": False, "reason": "system"}
            peak = float(np.max(np.abs(sound)))
            if peak < 0.0001:
                return {"ok": False, "reason": "system"}
            # Preserve natural dynamics; no pitch shifting. Only safe peak gain and
            # a short fade at each edge to prevent clicks between streaming clauses.
            sound = sound * min(1.45, 0.92 / peak)
            n = min(100, len(sound) // 2)
            if n:
                sound[:n] *= np.linspace(0, 1, n)
                sound[-n:] *= np.linspace(1, 0, n)
            pcm = (np.clip(sound, -1, 1) * 32767).astype("<i2")
            b = io.BytesIO()
            with wave.open(b, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sr)
                w.writeframes(pcm.tobytes())
            # 25-Hz loudness contour. The eye samples it against the actual speaker
            # playback clock, never the microphone, even when the device uses a headset.
            hop = sr // 25
            pad = (-len(sound)) % hop
            frames = np.pad(sound, (0, pad)).reshape(-1, hop)
            rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-10)
            levels = np.clip((20 * np.log10(rms) + 50) / 38, 0, 1)
            return {
                "ok": True,
                "mime": "audio/wav",
                "speaker": name,
                "hz": 25,
                "levels": base64.b64encode((levels * 255).astype("uint8").tobytes()).decode(
                    "ascii"
                ),
                "audio": base64.b64encode(b.getvalue()).decode("ascii"),
            }
        except Exception:
            return {"ok": False, "reason": "system"}
        finally:
            self.slot.release()


engine = VoiceEngine()
