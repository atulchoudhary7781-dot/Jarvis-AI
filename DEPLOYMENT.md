# Running and deploying Amber Companion

Production: **https://jarvis-ai-bay-one.vercel.app/**. The public site runs the standalone Python HTTP host, not Streamlit or a static export. Do not expose a private desktop assistant, legacy databases, repository files or personal API keys as part of this site.

## Vercel

Use the existing **`jarvis-ai`** project with the **Container** preset, a project-level `PORT=8080`, and the repository root as the build root. Keep the existing domain and plan. Do not create a second project to ship an update. This project's original production deployment was a file-based deployment: a push to this GitHub repository alone does not update the application code on Vercel. Deploy a pinned release explicitly unless the owner deliberately enables a Git integration in future. Catalog-only edits are the exception described below.

`Dockerfile.vercel` selects a small runtime allowlist. A separate build stage compiles the pinned `llama-cpp-python` source against Debian's libc. Another stage downloads the Gemma GGUF and two Kokoro voice embeddings plus the voice graph, verifying sizes and SHA-256 before use. Neither compilers nor the historical desktop environment belong in the final runtime. `vercel_host.py` runs as an unprivileged user and links the immutable audio assets into a writable temporary home. No conversation, API secret or microphone data is needed at build time.

The runtime serves these paths from **one origin**:

| Path | Contract |
| --- | --- |
| `GET /` | Hologram UI; no externally hosted scripts, fonts or graphics. |
| `GET /health` | JSON with `ok: true` and `mode: public-preview` on the public host. Liveness alone is not a speech or model test. |
| `GET /terms` | Open-chat terms, Gemma license and incorporated use restrictions. |
| `GET /api/community-skills` | Validated, read-only recipes. No submission endpoint. |
| `POST /api/command` | Short JSON `query`, optional `lang`, `zone` and recent conversation turns. Open-ended inference requires informed acceptance of the current `chatTerms` version. There are no model tools. |
| `POST /api/voice` | Bounded text (up to 128 characters per chunk) and `hi-IN`/`en-IN`; returns WAV and a playback envelope or an explicit device-fallback result. |

`JARVIS_CHAT_MODEL` in the image points to the baked-in GGUF. `JARVIS_COMMUNITY_SYNC=1` checks the fixed `main/community/skills.json` URL on demand, no more than about once every ten minutes per instance. A failed refresh retries after a minute and does not replace validated data. New functions require a code deployment; a merged recipe can become available without one. `--preview` deliberately ignores private provider keys even if someone sets them by mistake.

The Docker context excludes unrelated files; never replace the source stage with `COPY . .`. For a file-based release, resolve an immutable Git commit and materialize only the runtime files with integrity checks. For a local container smoke test, use the two Docker commands in the README. Do not expose the local-only server by port forwarding.

## Native desktop setup

The lightweight launcher runs on stock Python 3.9+ without neural dependencies. For voice and local model inference together, use a supported **64-bit Python 3.10–3.13** (3.12 is a good default), a C/C++ toolchain and CMake. The GGUF download is 806,058,240 bytes; voice assets add about 94 MB. Allow room for dependencies and the native build. Reserve at least 2 GB for the running app, plus memory for the OS and browser; several GB of free RAM is preferable on a desktop. No GPU or paid model key is required.

Example for macOS/Linux, from the repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-voice.txt
CMAKE_BUILD_PARALLEL_LEVEL=2 python -m pip install -r requirements-chat.txt
export JARVIS_CHAT_MODEL="$(python deploy/prepare_chat.py)"
python launch_hologram.py
```

The last two lines select the checksum-verified GGUF and launch the app. For Windows, `Start Enhanced JARVIS.cmd` installs **voice** only. To add local chat, use a compatible environment and Visual Studio C++ Build Tools with CMake, install `requirements-chat.txt`, run `python deploy/prepare_chat.py`, and set `JARVIS_CHAT_MODEL` to the printed path before starting the launcher. Gemma's terms apply to the model download and use. To run without generated chat, omit the variable; built-in conversation, personal recipes and public lookups still work. `JARVIS_VOICE=system` selects device speech.

The default server binds to loopback. Optional private providers are a separate, opt-in local feature; the Vercel host does not need them. The historical `app.py` is not the Vercel entry point. Nothing in this release requires a Streamlit deployment or changes a cloud account login.

## Verification

1. Run `python -m unittest discover -s tests -v` and `node tests/notebook.cjs`. They test routing, safe fallbacks, bounded history, consent, recipe validation, deletion and the draft boundary without downloading a model.
2. With a configured native host, after reading the terms, run `python launch_hologram.py --ask "Invent a tiny animal for a pencil case" --lang en --accept-chat-terms`. For a host check, test `/api/voice` in both languages and confirm a nonempty 24 kHz mono WAV from each expected speaker.
3. For browser regressions install Playwright/Chromium in a test environment, start the HTTP host and set `AMBER_TEST_URL` to its URL. Run `node tests/browser_conversation.cjs` and `node tests/browser_companion.cjs`. Set `AMBER_TEST_MODEL=1` to exercise two actual model turns as well. These scripts simulate recognized speech and device playback; they do not prove a physical microphone or OS permission works.
4. Test a production update on the public domain, not just a protected team deployment URL. Try a recent chat follow-up, teach/confirm/run a shortcut, open a community quiz, and ask for the time in two cities with **one** activation. Confirm **Esc** stops listening and **V** animates the iris during playback.

## Troubleshooting and limits

- **No microphone:** open in a separate Chrome/Edge tab on HTTPS (or `localhost`), allow the site microphone and check OS permissions. `T` provides an invisible typing alternative. Background/lock-screen listening is intentionally unsupported.
- **Different voice or delayed reply:** a cold start or a busy CPU may use built-in chat or a device voice. Wait and retry. A liveness response does not guarantee a model was installed. A typed API reply and a real audible clip test different layers.
- **Missing personal skill:** use the same browser profile and origin. Private browsing and blocked/cleared site data can erase it. A public contribution is not a backup. Use **“forget everything”** or clear this site's browser data to wipe your notebook.
- **New shared recipe missing:** ensure the recipe was merged into `main`, passes both validators and is not just an open issue. Check `origin` on the catalog endpoint and allow for client/server caching.
- **Capacity:** inference is bounded and rate-limited per instance. Hosting quotas, CPU, memory, build time and registry limits still apply; the live demo is not an unlimited worldwide inference service. Do not disable integrity checks or expose a private API key to compensate for a temporary outage.

See [Vercel Container Runtime](https://vercel.com/docs/functions/runtimes/container), [function limits](https://vercel.com/docs/functions/limitations) and [registry limits](https://vercel.com/docs/container-registry/limits-and-pricing).
