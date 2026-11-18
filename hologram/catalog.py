"""A read-only, reviewed recipe feed. No write endpoint, user identifiers or code."""

from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener

FILE = Path(__file__).resolve().parents[1] / "community" / "skills.json"
URL = "https://raw.githubusercontent.com/atulchoudhary7781-dot/Jarvis-AI/main/community/skills.json"
MAX_BYTES = 32_768


def phrase_ok(s, length=44):
    return (
        isinstance(s, str)
        and s == s.strip()
        and 2 <= len(s) <= length
        and 1 <= len(s.split()) <= 7
        and any(c.isalpha() for c in s)
        and all(c.isalpha() or unicodedata.category(c).startswith("M") or c in " '-’" for c in s)
    )


def card_ok(s, limit):
    return (
        isinstance(s, str)
        and 1 <= len(s) <= limit
        and s == s.strip()
        and any(c.isalnum() for c in s)
        and all(
            c.isalnum() or unicodedata.category(c).startswith("M") or c in " ,?!.'’():;।-"
            for c in s
        )
        and not re.search(r"https?:|www\.|\d{5,}|password|passcode|token|api key|पासवर्ड", s, re.I)
    )


def validate(doc):
    if (
        not isinstance(doc, dict)
        or set(doc) != {"version", "skills"}
        or type(doc["version"]) is not int
        or doc["version"] != 1
        or not isinstance(doc["skills"], list)
        or len(doc["skills"]) > 64
    ):
        raise ValueError("Invalid catalog")
    seen = set()
    for r in doc["skills"]:
        if (
            not isinstance(r, dict)
            or set(r) != {"phrase", "steps"}
            or not phrase_ok(r["phrase"])
            or not isinstance(r["steps"], list)
            or not 1 <= len(r["steps"]) <= 2
        ):
            raise ValueError("Invalid recipe")
        key = unicodedata.normalize("NFKC", " ".join(r["phrase"].casefold().split()))
        if re.match(
            r"^(?:yes|no|okay|haan|हाँ|हां|नहीं|help|hello|hi|hey|नमस्ते|start|stop|cancel|jarvis|जार्विस|turn off|mic|microphone|माइक|forget|remember|teach|learn|share|community skills|my skills|when i say|जब मैं|सिख|नया शॉर्टकट)(?:\s|$)",
            key,
            re.I,
        ) or re.search(r"password|passcode|secret|api key|phone number|पासवर्ड|गुप्त", key, re.I):
            raise ValueError("Reserved phrase")
        if key in seen:
            raise ValueError("Duplicate phrase")
        seen.add(key)
        for step in r["steps"]:
            if not isinstance(step, dict):
                raise ValueError("Invalid step")
            kind = step.get("kind")
            if (
                kind in ("time", "date", "weather")
                and set(step) == {"kind", "city"}
                and phrase_ok(step["city"], 48)
            ):
                continue
            if (
                kind == "quiz"
                and set(step) == {"kind", "question", "answer"}
                and len(r["steps"]) == 1
                and card_ok(step["question"], 125)
                and card_ok(step["answer"], 48)
            ):
                continue
            if kind == "headlines" and set(step) == {"kind"}:
                continue
            if (
                kind == "timer"
                and set(step) == {"kind", "minutes"}
                and type(step["minutes"]) is int
                and 1 <= step["minutes"] <= 120
                and len(r["steps"]) == 1
            ):
                continue
            raise ValueError("Unsupported step")
    return doc


class FixedOrigin(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch():
    req = Request(
        URL, headers={"User-Agent": "Jarvis-Reviewed-Recipes/1", "Accept": "application/json"}
    )
    with build_opener(FixedOrigin).open(req, timeout=3) as r:
        raw = r.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Catalog too large")
    return validate(json.loads(raw))


class Catalog:
    def __init__(self):
        self.lock = threading.Lock()
        self.next = 0.0
        self.origin = "bundled"
        self.data = (
            validate(json.loads(FILE.read_text(encoding="utf-8")))
            if FILE.is_file()
            else {"version": 1, "skills": []}
        )

    def read(self, sync=False):
        now = time.monotonic()
        if sync and now >= self.next and self.lock.acquire(blocking=False):
            try:
                if now >= self.next:
                    self.next = now + 600
                    try:
                        self.data = fetch()
                        self.origin = "reviewed-main"
                    except (OSError, ValueError, TypeError, KeyError):
                        self.next = now + 60  # Bundled/last validated catalog stays usable offline.
            finally:
                self.lock.release()
        return {**self.data, "origin": self.origin}
