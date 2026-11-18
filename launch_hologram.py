#!/usr/bin/env python3
"""Start the standalone hologram with stock Python 3.9+; no pip install needed."""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from hologram.server import make_server
from hologram.skills import answer


def open_window(url, *, tab=False):
    """Open only the local app URL supplied by main, never an utterance or a link.

    An installed Chromium-family browser can open a clean, full-screen app
    window. Fall back to the user's normal default browser if unavailable.
    """
    if not tab:
        candidates = []
        if sys.platform == "win32":
            for base in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
                if os.environ.get(base):
                    candidates.extend(
                        Path(os.environ[base]) / rel
                        for rel in [
                            "Microsoft/Edge/Application/msedge.exe",
                            "Google/Chrome/Application/chrome.exe",
                        ]
                    )
        elif sys.platform == "darwin":
            candidates = [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            ]
        else:
            candidates = [
                Path(p)
                for name in ["google-chrome", "microsoft-edge", "chromium", "chromium-browser"]
                if (p := shutil.which(name))
            ]
        for exe in candidates:
            if exe.is_file():
                try:
                    subprocess.Popen(
                        [str(exe), "--new-window", "--start-fullscreen", "--app=" + url],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except OSError:
                    continue
    webbrowser.open_new_tab(url)


def main(argv=None):
    ap = argparse.ArgumentParser(description="JARVIS · amber hologram")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true", help="do not open a browser")
    ap.add_argument(
        "--browser-tab",
        action="store_true",
        help="use a regular browser tab rather than a full-screen app window",
    )
    ap.add_argument(
        "--preview",
        action="store_true",
        help="shared read-only preview on 0.0.0.0; private AI is always disabled",
    )
    ap.add_argument(
        "--ask", help="test a spoken information query as text, without launching a window"
    )
    ap.add_argument("--lang", choices=["hi", "en"], default="hi")
    ap.add_argument("--zone", default="UTC", help="IANA timezone for a local-time CLI question")
    args = ap.parse_args(argv)
    if args.ask is not None:
        out = answer(
            args.ask,
            args.lang,
            args.zone,
            key="" if args.preview else os.environ.get("OPENROUTER_API_KEY", ""),
            search_key="" if args.preview else os.environ.get("BRAVE_SEARCH_API_KEY", ""),
            model=os.environ.get("OPENROUTER_MODEL", "openrouter/auto"),
        )
        try:
            print(out["text"])
        except UnicodeEncodeError:
            sys.stdout.buffer.write((out["text"] + "\n").encode("utf-8"))
        return 0
    if not 0 <= args.port <= 65535:
        ap.error("port must be 0–65535")
    try:
        server = make_server(args.port, preview=args.preview)
    except OSError as exc:
        ap.exit(1, f"Cannot open port {args.port}: {exc}. Try --port 0.\n")
    url = f"http://127.0.0.1:{server.server_port}/"
    mode = "Shared public-data preview" if args.preview else "Local device only"
    print(
        f"JARVIS hologram | {mode}\n{url}\nTap the core or press Space to speak. F: full screen. Ctrl+C here to stop.",
        flush=True,
    )
    if not args.no_open and not args.preview:
        opener = threading.Timer(0.25, open_window, args=(url,), kwargs={"tab": args.browser_tab})
        opener.daemon = True
        opener.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
