"""Short, on-host conversational inference. No tools, prompt logging or training."""

from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path

SOURCE = "Companion"
TERMS = "gemma-2026-04-01"
_BASE = (
    "You are Jarvis, an AI voice companion. Talk like a thoughtful, easygoing friend. "
    "Start with the detail they shared, not a canned greeting. If they are venting, listen before offering advice. Be concrete instead of giving a list. "
    "Use one or two short spoken sentences, and at most one natural follow-up. "
    "Never pretend to be human or to remember a person outside this conversation. "
    "Do not claim to save things, use the internet, take actions, or know live facts. "
    "For live information suggest asking for a city clock, weather or a Wikipedia lookup. "
    "If you do not know, say so. No markdown, role labels, stage directions or reasoning. "
    "Never encourage harm or give dangerous instructions. "
)


def plain(text, limit):
    # Encode messages ourselves. Do not let text include chat-template delimiters.
    return " ".join(str(text).replace("<", "‹").replace(">", "›").split())[:limit]


def prompt(query, lang, history):
    hi = lang.startswith("hi")
    guide = (
        "तुम जार्विस हो, एक एआई साथी। तुम कहकर बोलो, जैसे दोस्त से चाय पर बात कर रहे हो। पहले उसकी कही असली बात पकड़ो। उदास हो तो फ़ौरन नसीहत मत दो। हर जवाब को सवाल मत बनाओ। हिंदी या हिंग्लिश समझो, जवाब बोलचाल की हिंदी में दो। सिर्फ़ एक या दो छोटे वाक्य। न इमोजी, न सूची, न अभिनय। जब पता न हो तो साफ़ बोलो। कुछ करने, इंटरनेट चलाने या बातें सहेजने का दावा मत करो। खतरनाक या पेशेवर सलाह मत दो।"
        if hi
        else _BASE
        + " Answer directly in English. If asked for an idea, give one specific idea now, not just encouragement. No emoji."
    )
    turns = []
    # Accept only complete recent user/assistant pairs from this request, never
    # trust a client-supplied system role. There is no global conversation log.
    recent = history[-4:] if isinstance(history, list) else []
    for a, b in zip(recent[::2], recent[1::2]):
        if (
            isinstance(a, dict)
            and isinstance(b, dict)
            and a.get("role") == "user"
            and b.get("role") == "assistant"
            and isinstance(a.get("content"), str)
            and isinstance(b.get("content"), str)
        ):
            turns.extend(
                [("user", plain(a["content"], 180)), ("assistant", plain(b["content"], 230))]
            )
    turns.append(("user", plain(query, 360)))
    # Gemma uses user/model turns. Place the instructions in the first user
    # turn rather than inventing a system role or relying on auto-detection.
    return (
        "".join(
            f"<start_of_turn>{'user' if role == 'user' else 'model'}\n{(guide + chr(10) + chr(10) if i == 0 else '') + msg}<end_of_turn>\n"
            for i, (role, msg) in enumerate(turns)
        )
        + "<start_of_turn>model\n"
    )


def spoken(s, lang):
    s = re.sub(r"<think>.*?(?:</think>|$)", "", str(s), flags=re.I | re.S)
    s = s.split("<|")[0].split("<start_of_turn>")[0].split("<end_of_turn>")[0].split("```")[0]
    s = re.sub(r"[\U0001F000-\U0001FAFF\u200d\ufe0f]", "", s)
    s = re.sub(r"^(?:assistant|jarvis|जार्विस)\s*:\s*", "", s.strip(), flags=re.I)
    s = " ".join(s.replace("*", "").replace("`", "").split())
    if (
        not s
        or re.search(r"[\u4e00-\u9fff]", s)
        or (lang.startswith("hi") and not re.search(r"[\u0900-\u097f]", s))
    ):
        return ""
    # Prefer a complete thought to a half-spoken sentence at the token limit.
    ends = list(re.finditer(r"[.!?।]+(?=\s|$)", s[:320]))
    if ends:
        s = s[: ends[min(1, len(ends) - 1)].end()]
    elif len(s) > 245:
        s = s[:242].rsplit(" ", 1)[0] + "…"
    return s.strip()


class CompanionModel:
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.retry_at = 0.0

    def respond(self, query, lang, history=()):
        path = os.environ.get("JARVIS_CHAT_MODEL", "")
        if not path or not Path(path).is_file() or time.monotonic() < self.retry_at:
            return None
        if not self.lock.acquire(blocking=False):
            return None
        try:
            if self.model is None:
                from llama_cpp import Llama

                self.model = Llama(
                    model_path=path,
                    n_ctx=1024,
                    n_batch=96,
                    n_ubatch=48,
                    n_threads=2,
                    n_threads_batch=2,
                    n_gpu_layers=0,
                    verbose=False,
                    use_mmap=True,
                )
            lm = self.model
            p = prompt(query, lang, history)
            if len(lm.tokenize(p.encode(), special=True)) > 865:
                p = prompt(query, lang, [])
            # The native context is locked, cleared before/after every request,
            # and never backed by a session file or reusable prompt cache.
            lm.reset()
            lm._ctx.kv_cache_clear()
            tokens = 88 if lang.startswith("hi") else 66
            result = lm.create_completion(
                prompt=p,
                max_tokens=tokens,
                temperature=0.45 if lang.startswith("hi") else 0.68,
                top_p=0.88,
                top_k=25,
                repeat_penalty=1.12,
                stop=["<end_of_turn>", "<start_of_turn>", "<think>", "\nUser:", "\nHuman:"],
                echo=False,
            )
            text = spoken(result["choices"][0]["text"], lang)
            return {"source": SOURCE, "text": text, "lang": lang} if text else None
        except (
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
            AttributeError,
            IndexError,
            KeyError,
        ):
            self.retry_at = time.monotonic() + 12
            return None
        finally:
            try:
                if self.model is not None:
                    self.model.reset()
                    self.model._ctx.kv_cache_clear()
            except (AttributeError, RuntimeError, OSError):
                self.model = None
            finally:
                self.lock.release()


engine = CompanionModel()
