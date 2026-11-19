"""Tiny first-party host. Loopback is the default; shared preview is public-data-only."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import voice, groq_speech, quota
from .catalog import Catalog
from .skills import MAX_QUERY, RateLimit, answer, reply

UI = Path(__file__).parent / "ui" / "index.html"


def make_server(port=8765, *, preview=False, desktop=None):
    if preview and desktop is not None:
        raise ValueError("Desktop actions are loopback only")
    public_origin = os.environ.get("JARVIS_PUBLIC_ORIGIN", "").rstrip("/") if preview else ""
    neural = voice.available(os.environ.get("JARVIS_VOICE", "auto"))
    # Paid/free quota is available only in an explicitly restricted test session.
    # Never enable unauthenticated production merely because a key is present.
    groq_key = os.environ.get("GROQ_API_KEY", "")
    redis_url = os.environ.get("KV_REST_API_URL", "")
    redis_token = os.environ.get("KV_REST_API_TOKEN", "")
    if not (redis_url and redis_token):
        redis_url = os.environ.get("UPSTASH_REDIS_REST_URL", "")
        redis_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
    vercel_env = os.environ.get("VERCEL_ENV", "")
    quota_test = vercel_env == "preview" and os.environ.get("JARVIS_GROQ_QUOTA_TEST") == "1"
    guarded = (vercel_env == "production" and os.environ.get("JARVIS_GROQ_PUBLIC") == "1") or quota_test
    groq_public = bool(preview and groq_key and guarded and quota.valid_config(redis_url, redis_token))
    groq_preview = bool(preview and groq_key and not quota_test and (vercel_env == "preview" or (vercel_env != "production" and os.environ.get("JARVIS_GROQ_EXPERIMENT") == "1")))
    groq_enabled = groq_preview or groq_public
    body = (
        UI.read_text(encoding="utf-8")
        .replace(
            '<meta name="jarvis-host" content="portable">',
            '<meta name="jarvis-host" content="http">',
        )
        .replace(
            '<meta name="jarvis-voice" content="system">',
            '<meta name="jarvis-voice" content="neural">'
            if neural
            else '<meta name="jarvis-voice" content="system">',
        )
        .replace('<meta name="jarvis-cloud" content="off">',
                 '<meta name="jarvis-cloud" content="preview">' if groq_enabled else '<meta name="jarvis-cloud" content="off">')
        .encode()
    )
    script = body.split(b"<script>", 1)[1].split(b"</script>", 1)[0]
    digest = base64.b64encode(hashlib.sha256(script).digest()).decode()
    csp = f"default-src 'none'; script-src 'sha256-{digest}'; style-src 'unsafe-inline'; img-src data:; connect-src 'self'; media-src blob: data:; base-uri 'none'; form-action 'none'"
    csp += "; object-src 'none'"
    if not preview:
        csp += "; frame-ancestors 'none'"
    terms_path = Path(__file__).parent / "licenses" / "gemma-TERMS.txt"
    catalog = Catalog()
    sync_catalog = os.environ.get("JARVIS_COMMUNITY_SYNC", "").strip() == "1"
    limit = RateLimit(35 if preview else 24)
    slots = threading.BoundedSemaphore(6)
    voice_limit = RateLimit(55, 60)
    groq_limit = RateLimit(6, 60)
    groq_global = RateLimit(30, 60)
    # The shared host deliberately never reads the provider key. This is not a
    # LAN or public gateway to a user's desktop, accounts or paid AI service.
    ai_key = "" if preview else os.environ.get("OPENROUTER_API_KEY", "")
    search_key = "" if preview else os.environ.get("BRAVE_SEARCH_API_KEY", "")
    model = "openrouter/auto" if preview else os.environ.get("OPENROUTER_MODEL", "openrouter/auto")

    class Handler(BaseHTTPRequestHandler):
        server_version = "Amber/3"
        sys_version = ""

        def log_message(self, fmt, *args):
            pass  # No addresses or transcripts in logs.

        def setup(self):
            super().setup()
            self.connection.settimeout(12)

        def host_ok(self):
            if preview:
                return True
            try:
                return urlsplit("//" + self.headers.get("Host", "")).hostname in (
                    "localhost",
                    "127.0.0.1",
                    "::1",
                )
            except ValueError:
                return False

        def write_reply(self, code, data, kind):
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Link", '</terms>; rel="terms-of-service"')
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", csp)
            self.send_header("Permissions-Policy", "camera=(), geolocation=(), microphone=(self), payment=(), usb=(), serial=()")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.end_headers()
            if self.command != "HEAD":
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def out(self, code, doc):
            return self.write_reply(
                code,
                json.dumps(doc, ensure_ascii=False).encode(),
                "application/json; charset=utf-8",
            )

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            if not self.host_ok():
                return self.out(403, {"error": "Local host only"})
            path = urlsplit(self.path).path
            if path in ("/", "/index.html"):
                return self.write_reply(200, body, "text/html; charset=utf-8")
            if path == "/api/community-skills":
                return self.out(200, catalog.read(sync_catalog))
            if path == "/terms" and terms_path.is_file():
                return self.write_reply(200, terms_path.read_bytes(), "text/plain; charset=utf-8")
            if path == "/health":
                return self.out(200, {"ok": True, "mode": "public-preview" if preview else "local"})
            if path == "/favicon.ico":
                return self.write_reply(204, b"", "image/x-icon")
            return self.out(404, {"error": "Not found"})

        def do_POST(self):
            if not self.host_ok():
                return self.out(403, {"error": "Local host only"})
            route = urlsplit(self.path).path
            native = route in {"/api/desktop/approve", "/api/desktop/commit"}
            if native:
                if preview or desktop is None:
                    return self.out(404, {"error": "Not found"})
                host = f"127.0.0.1:{self.server.server_port}"
                if (self.client_address[0] != "127.0.0.1" or self.headers.get("Host") != host
                        or self.headers.get("Origin") != "http://" + host
                        or not desktop.admits(self.headers.get("X-Jarvis-Session"))):
                    return self.out(403, {"error": "Local approval required"})
            elif route not in {"/api/command", "/api/voice", "/api/transcribe", "/api/translate"}:
                return self.out(404, {"error": "Not found"})
            is_groq = route in {"/api/transcribe", "/api/translate"}
            if is_groq and not groq_enabled:
                return self.out(404, {"error": "Not found"})
            if is_groq and not self.headers.get("Origin"):
                return self.out(403, {"error": "Same origin required"})
            if self.headers.get_content_type() != "application/json":
                return self.out(415, {"error": "Use JSON"})
            origin = self.headers.get("Origin")
            site = self.headers.get("Sec-Fetch-Site", "")
            if origin:
                try:
                    same = urlsplit(origin).netloc.casefold() == self.headers.get(
                        "Host", ""
                    ).casefold() and urlsplit(origin).scheme in ("http", "https")
                except ValueError:
                    same = False
                if not same and not (public_origin and origin == public_origin):
                    return self.out(403, {"error": "Same origin required"})
            if site in {"cross-site", "same-site"}:
                return self.out(403, {"error": "Same origin required"})
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
                return self.out(400, {"error": "One content length required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self.out(400, {"error": "Invalid length"})
            if not 0 < size <= (2_010_000 if route == "/api/transcribe" else (384 if native else 8500)):
                return self.out(413, {"error": "Use one short command"})
            try:
                req = json.loads(self.rfile.read(size))
                if not isinstance(req, dict):
                    raise ValueError()
                if native:
                    if route.endswith("/approve") and set(req) == {"app"}:
                        return self.out(200, desktop.approve(req["app"]))
                    if route.endswith("/commit") and set(req) == {"app", "permit"}:
                        return self.out(200, desktop.commit(req["app"], req["permit"]))
                    raise ValueError()
                if is_groq:
                    if not groq_public and (not groq_limit.allow(self.client_address[0]) or not groq_global.allow("global")):
                        return self.out(429, {"ok": False, "reason": "rate_limited"})
                    if not slots.acquire(blocking=False):
                        return self.out(429, {"ok": False, "reason": "busy"})
                    try:
                        if route == "/api/transcribe":
                            if set(req) != {"audio", "mime"} or not isinstance(req.get("audio"), str) or len(req["audio"]) > 2_000_000:
                                raise ValueError("Invalid audio")
                            audio = base64.b64decode(req["audio"], validate=True)
                            if groq_public and not quota.reserve(redis_url, redis_token, self.headers.get("x-vercel-forwarded-for", ""), 2):
                                return self.out(429, {"ok": False, "reason": "rate_limited"})
                            result = groq_speech.transcribe(audio, req["mime"], groq_key)
                            # A failed translation cannot be interpreted as an action.
                            if result.get("ok") and result.get("text") and result.get("language", "").lower() not in {"", "english", "en", "hindi", "hi"}:
                                tr = groq_speech.translate(result["text"], "English", groq_key)
                                if not tr.get("ok"):
                                    return self.out(200, {"ok": False, "reason": "unavailable"})
                                result["command"] = tr["text"]
                            return self.out(200, result)
                        if set(req) != {"text", "target"}:
                            raise ValueError("Invalid translation")
                        if groq_public and not quota.reserve(redis_url, redis_token, self.headers.get("x-vercel-forwarded-for", ""), 1):
                            return self.out(429, {"ok": False, "reason": "rate_limited"})
                        return self.out(200, groq_speech.translate(req["text"], req["target"], groq_key))
                    finally:
                        slots.release()
                if route == "/api/voice":
                    if (
                        not isinstance(req, dict)
                        or not isinstance(req.get("text"), str)
                        or not 0 < len(req["text"]) <= voice.MAX_SEGMENT
                        or req.get("lang") not in ("hi-IN", "en-IN")
                    ):
                        return self.out(400, {"ok": False, "reason": "invalid"})
                    if not neural or not voice_limit.allow(self.client_address[0]):
                        return self.out(200, {"ok": False, "reason": "system"})
                    return self.out(
                        200, voice.engine.speak(req["text"], req["lang"], enabled=neural)
                    )
                q = req["query"]
                lang = req.get("lang", "hi-IN")
                history = req.get("history", [])
                if (
                    not isinstance(q, str)
                    or not 0 < len(q.strip()) <= MAX_QUERY
                    or not isinstance(lang, str)
                    or lang not in {"hi", "en", "hi-IN", "en-IN", "en-US", "en-GB"}
                    or not isinstance(history, list) or len(history) > 4
                    or not all(isinstance(m, dict) and m.get("role") in ("user", "assistant")
                               and isinstance(m.get("content"), str) and len(m["content"]) <= 440 for m in history)
                    or not isinstance(req.get("zone", "UTC"), str) or len(req.get("zone", "UTC")) > 85
                    or req.get("pending", "") not in ("", "weather")
                ):
                    raise ValueError()
            except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
                return self.out(400, {"error": "Invalid command"})
            if not limit.allow(self.client_address[0]) or not slots.acquire(blocking=False):
                return self.out(
                    429,
                    reply("A little too fast. Please wait a moment.", "थोड़ा रुककर फिर पूछिए।", lang),
                )
            try:
                result = answer(
                    q,
                    lang,
                    req.get("zone", "UTC"),
                    pending=req.get("pending", ""),
                    history=history,
                    chat_terms=req.get("chatTerms"),
                    key=ai_key,
                    search_key=search_key,
                    model=model,
                )
                rid = req.get("id", "")
                result["id"] = (
                    rid if isinstance(rid, str) and re.fullmatch(r"[\w-]{1,80}", rid) else ""
                )
                return self.out(200, result)
            finally:
                slots.release()

    class Host(ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = True
        # Bound accepted worker threads as well as expensive model work. No queue
        # of private prompts is retained when the instance is at capacity.
        workers = threading.BoundedSemaphore(20)

        def process_request(self, request, address):
            if not self.workers.acquire(blocking=False):
                self.shutdown_request(request)
                return
            try:
                super().process_request(request, address)
            except BaseException:
                self.workers.release()
                raise

        def process_request_thread(self, request, address):
            try:
                super().process_request_thread(request, address)
            finally:
                self.workers.release()

    host = Host(("0.0.0.0" if preview else "127.0.0.1", port), Handler)
    host.neural_voice = neural
    return host
