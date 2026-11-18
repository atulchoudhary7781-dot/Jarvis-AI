"""Opt-in Windows broker. Never imported by the public host. No shell, file or URL input."""
from __future__ import annotations

import ctypes
import secrets
import subprocess
import sys
import threading
import time
from pathlib import Path

# Identifiers, native labels and filenames are build-time constants, not model output.
APPS = {"calculator": ("Calculator", "calc.exe"), "notepad": ("Notepad", "notepad.exe"), "paint": ("Paint", "mspaint.exe")}


def _directory():
    buf = ctypes.create_unicode_buffer(32768)
    n = ctypes.windll.kernel32.GetSystemDirectoryW(buf, len(buf))
    if not 0 < n < len(buf) or not Path(buf.value).is_absolute():
        raise OSError("Windows system directory unavailable")
    return Path(buf.value)


def _ask(app):
    # System modal is intentionally NOT used. Default is No. A late Yes expires.
    return ctypes.windll.user32.MessageBoxW(None, f"Open {APPS[app][0]} on this PC?\n\nOnly approve if this was your request. This approval expires in 30 seconds.", "JARVIS · Local approval", 0x4 | 0x20 | 0x100 | 0x10000) == 6


def _launch(app):
    directory = _directory()
    exe = directory / APPS[app][1]
    if not exe.is_file():
        raise OSError("App not installed")
    subprocess.Popen([str(exe)], shell=False, cwd=str(directory), close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class DesktopSession:
    def __init__(self, *, ask=_ask, launch=_launch, clock=time.monotonic):
        self.key = secrets.token_urlsafe(32)
        self.clock, self.ask, self.launch = clock, ask, launch
        self.expires = clock() + 7200
        self.lock = threading.Lock()
        self.dialog = threading.Lock()
        self.recent = []
        self.permit = None

    def admits(self, key):
        return (isinstance(key, str) and key.isascii() and len(key) == len(self.key)
                and self.clock() < self.expires and secrets.compare_digest(key, self.key))

    def approve(self, app):
        if not isinstance(app, str) or app not in APPS or self.clock() >= self.expires:
            return {"ok": False, "reason": "unavailable"}
        if not self.dialog.acquire(blocking=False):
            return {"ok": False, "reason": "busy"}
        try:
            start = self.clock()
            with self.lock:
                self.permit = None
                self.recent = [t for t in self.recent if start - t < 60]
                if len(self.recent) >= 4:
                    return {"ok": False, "reason": "busy"}
                self.recent.append(start)
            if not self.ask(app) or self.clock() - start >= 30 or self.clock() >= self.expires:
                return {"ok": False, "reason": "cancelled"}
            p = secrets.token_urlsafe(24)
            with self.lock:
                self.permit = (app, p, self.clock() + 4)
            return {"ok": True, "permit": p}
        except (OSError, AttributeError):
            return {"ok": False, "reason": "unavailable"}
        finally:
            self.dialog.release()

    def commit(self, app, proof):
        with self.lock:
            permit, self.permit = self.permit, None
            if (not permit or app != permit[0] or not isinstance(proof, str) or not proof.isascii()
                    or self.clock() >= min(permit[2], self.expires) or not secrets.compare_digest(proof, permit[1])):
                return {"ok": False, "reason": "cancelled"}
        try:
            self.launch(app)
            return {"ok": True}
        except (OSError, AttributeError):
            return {"ok": False, "reason": "unavailable"}


def new_session():
    if sys.platform != "win32":
        raise ValueError("Desktop actions require Windows.")
    if ctypes.windll.shell32.IsUserAnAdmin():
        raise ValueError("Start JARVIS normally, not as administrator.")
    return DesktopSession()
