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

from . import voice
from .skills import MAX_QUERY, RateLimit, answer, reply

UI = Path(__file__).parent / "ui" / "index.html"


def make_server(port=8765, *, preview=False):
    neural = voice.available(os.environ.get("JARVIS_VOICE", "auto"))
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
        .encode()
    )
    script = body.split(b"<script>", 1)[1].split(b"</script>", 1)[0]
    digest = base64.b64encode(hashlib.sha256(script).digest()).decode()
    csp = f"default-src 'none'; script-src 'sha256-{digest}'; style-src 'unsafe-inline'; img-src data:; connect-src 'self'; media-src blob: data:; base-uri 'none'; form-action 'none'"
    if not preview:
        csp += "; frame-ancestors 'self'"
    limit = RateLimit(35 if preview else 24)
    slots = threading.BoundedSemaphore(6)
    voice_limit = RateLimit(55, 60)
    # The shared host deliberately never reads the provider key. This is not a
    # LAN or public gateway to a user's desktop, accounts or paid AI service.
    ai_key = "" if preview else os.environ.get("OPENROUTER_API_KEY", "")
    search_key = "" if preview else os.environ.get("BRAVE_SEARCH_API_KEY", "")
    model = "openrouter/auto" if preview else os.environ.get("OPENROUTER_MODEL", "openrouter/auto")

    class Handler(BaseHTTPRequestHandler):
        server_version = "Amber/2"
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
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", csp)
            self.send_header("Permissions-Policy", "camera=(), geolocation=(), microphone=(self)")
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
            if path == "/health":
                return self.out(200, {"ok": True, "mode": "public-preview" if preview else "local"})
            if path == "/favicon.ico":
                return self.write_reply(204, b"", "image/x-icon")
            return self.out(404, {"error": "Not found"})

        def do_POST(self):
            if not self.host_ok():
                return self.out(403, {"error": "Local host only"})
            route = urlsplit(self.path).path
            if route not in {"/api/command", "/api/voice"}:
                return self.out(404, {"error": "Not found"})
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
                if not same and not (preview and site == "same-origin"):
                    return self.out(403, {"error": "Same origin required"})
            if site == "cross-site":
                return self.out(403, {"error": "Same origin required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self.out(400, {"error": "Invalid length"})
            if not 0 < size <= 8500:
                return self.out(413, {"error": "Use one short command"})
            try:
                req = json.loads(self.rfile.read(size))
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
                    or not isinstance(history, list)
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

    host = Host(("0.0.0.0" if preview else "127.0.0.1", port), Handler)
    host.neural_voice = neural
    return host
