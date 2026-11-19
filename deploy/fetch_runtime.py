"""Materialize a small public release from a pinned Git commit, never a full checkout."""

import hashlib
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = "https://raw.githubusercontent.com/atulchoudhary7781-dot/Jarvis-AI/"
FILES = """community/skills.json deploy/prepare_chat.py hologram/__init__.py hologram/catalog.py hologram/chat.py hologram/groq_speech.py hologram/quota.py hologram/licenses/Notice.txt hologram/licenses/gemma-TERMS.txt hologram/licenses/kokoro-VOICE-NOTICE.md hologram/licenses/tzdata-LICENSE.txt hologram/licenses/tzdata-LICENSE_APACHE.txt hologram/server.py hologram/skills.py hologram/ui/index.html hologram/voice.py hologram/zones.zip launch_hologram.py requirements-chat.txt requirements-voice.txt vercel_host.py""".split()


def materialize(commit, manifest_digest, root):
    if not re.fullmatch("[0-9a-f]{40}", commit) or not re.fullmatch(
        "[0-9a-f]{64}", manifest_digest
    ):
        raise ValueError("Expected immutable commit and manifest digest")

    def get(name, digest, cap):
        url = ROOT + commit + "/" + name
        with urlopen(
            Request(url, headers={"User-Agent": "Jarvis-Release-Build/3"}), timeout=25
        ) as r:
            if r.geturl() != url:
                raise ValueError("Unexpected redirect")
            buf = r.read(cap + 1)
        if len(buf) > cap or hashlib.sha256(buf).hexdigest() != digest:
            raise ValueError("Source verification failed: " + name)
        return buf

    manifest = get("deploy/runtime.sha256", manifest_digest, 5000).decode("ascii")
    rows = [line.split("  ", 1) for line in manifest.splitlines()]
    if len(rows) != len(FILES) or {r[1] for r in rows} != set(FILES):
        raise ValueError("Unexpected release paths")
    for digest, name in rows:
        content = get(name, digest, 600000)
        p = Path(root) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    print(f"Verified {len(rows)} release files at {commit}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: fetch_runtime.py COMMIT MANIFEST_SHA256 OUTPUT_DIR")
    materialize(*sys.argv[1:])
