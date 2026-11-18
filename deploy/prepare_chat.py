"""Download one public, revision- and SHA-256-pinned model. No prompts leave the host."""

import hashlib
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

REPO = "ggml-org/gemma-3-1b-it-GGUF"
REVISION = "f9c28bcd85737ffc5aef028638d3341d49869c27"
FILE = "gemma-3-1b-it-Q4_K_M.gguf"
SIZE = 806058240
DIGEST = "8ccc5cd1f1b3602548715ae25a66ed73fd5dc68a210412eea643eb20eb75a135"


def prepare(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / FILE
    if target.is_file() and target.stat().st_size == SIZE:
        h = hashlib.sha256()
        with target.open("rb") as f:
            for b in iter(lambda: f.read(1024 * 1024), b""):
                h.update(b)
        if h.hexdigest() == DIGEST:
            return target
    fd, temp = tempfile.mkstemp(dir=folder, prefix=".fetch-")
    try:
        req = Request(
            f"https://huggingface.co/{REPO}/resolve/{REVISION}/{FILE}",
            headers={"User-Agent": "Jarvis-Pinned-Model/1"},
        )
        h = hashlib.sha256()
        size = 0
        with os.fdopen(fd, "wb") as f, urlopen(req, timeout=35) as r:
            if not r.geturl().startswith("https://"):
                raise ValueError("Expected HTTPS model asset")
            for b in iter(lambda: r.read(1024 * 1024), b""):
                size += len(b)
                if size > SIZE:
                    raise ValueError("Unexpected model size")
                h.update(b)
                f.write(b)
        if size != SIZE or h.hexdigest() != DIGEST:
            raise ValueError("Model integrity check failed")
        os.chmod(temp, 0o444)
        os.replace(temp, target)
        return target
    finally:
        Path(temp).unlink(missing_ok=True)


if __name__ == "__main__":
    print(
        prepare(sys.argv[1] if len(sys.argv) == 2 else Path.home() / ".cache" / "jarvis-amber-chat")
    )
