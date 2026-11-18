"""Build-time model seeding and public HTTP entrypoint for Dockerfile.vercel."""

import os
import sys
import tempfile
from pathlib import Path

from deploy.prepare_chat import prepare
from hologram.voice import ASSETS, REVISION, checked_asset

MODEL_DIR = Path("/opt/amber-voice") / REVISION[:12]


def seed_assets(dest):
    dest.mkdir(parents=True, exist_ok=True)
    for entry in ASSETS:
        asset = checked_asset(dest, entry)
        # checked_asset creates owner-only files. The final container user is
        # unprivileged; these are public model data, not credentials or speech.
        asset.chmod(0o444)
    print("Verified and packaged the Hindi and English neural voice assets.")


def configure_cache(home, assets):
    # The original audio engine reads ~/.cache and builds a small NPZ there.
    # Link immutable assets into per-instance /tmp, not the other way around.
    cache = home / ".cache" / "jarvis-amber-voice" / REVISION[:12]
    cache.mkdir(parents=True, mode=0o700)
    for filename, size, _ in ASSETS:
        name = Path(filename).name
        source = assets / name
        if not source.is_file() or source.stat().st_size != size:
            raise RuntimeError("Packaged voice asset is missing; rebuild the container")
        (cache / name).symlink_to(source)
    os.environ["HOME"] = str(home)


def serve(assets=MODEL_DIR):
    port = int(os.environ.get("PORT", "8080"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    from launch_hologram import main

    with tempfile.TemporaryDirectory(prefix="amber-vercel-", dir="/tmp") as home:
        configure_cache(Path(home), assets)
        # Public host intentionally ignores paid provider keys. Do not turn the
        # personal desktop/loopback mode into a public unauthenticated gateway.
        return main(["--preview", "--no-open", "--port", str(port)])


if __name__ == "__main__":
    if sys.argv[1:] == ["--seed-assets"]:
        seed_assets(MODEL_DIR)
        print("Verified chat model:", prepare(Path("/opt/amber-chat")))
    elif sys.argv[1:]:
        raise SystemExit("Usage: python vercel_host.py [--seed-assets]")
    else:
        raise SystemExit(serve())
