# J.A.R.V.I.S. · Amber Companion

> **Windows app control is an experimental local feature.** The approval and launch flow has been tested with simulated dialogs and launches, but has not yet been verified on a real Windows PC. Browser speech accuracy also depends on the recognition service and microphone.

## New local features and safety

- Open this folder on your own Windows PC and double-click **Start Private JARVIS.cmd** (never Run as administrator). It needs Python 3.9+. In Chrome/Edge, allow the mic. Say **“नोटपैड खोलो”**, **“open calculator”**, or **“पेंट खोलो”**. A Windows confirmation names the app and defaults to No. Only these three Windows system apps are allowed; the server is loopback-only and cannot run commands, arguments, arbitrary programs, or files. Stop the session by closing the command window. A fresh session expires after two hours.
- For the optional local neural voice, first run **Start Enhanced JARVIS.cmd** and accept its installation. Close that session, then run **Start Private JARVIS.cmd**. It reuses the installed voice engine. Without it, your browser uses a device voice.
- Say **“यूट्यूब खोल दो”**, **“open Google Maps”**, or **“search YouTube for music”**. JARVIS shows the destination; tap its button to open. Only reviewed destinations are supported. Never approves a website by speaking alone. Esc cancels.
- JARVIS waits briefly for the rest of a phrase. Say **“listen patiently”** / **“आराम से सुनो”** for longer pauses, **“normal pauses”** to restore the default, and **“what did you hear”** for the preceding phrase. Say **“listen in Hindi”** or **“listen in English”** to choose the recognition language for the current tab. Speech recognition is provided by your browser and may still mishear Hindi/Hinglish; it is not guaranteed.
- The website cannot control your Windows apps. This local feature is opt-in, not a user authentication system. Use a locked, trusted Windows account and approve only requests you made; malicious software running as your user can bypass these protections. Nothing can be guaranteed completely misuse-proof.


**[Open the live hologram →](https://jarvis-ai-bay-one.vercel.app/)** · [Teach a skill](#teach-jarvis-something) · [Community contributions](CONTRIBUTING.md) · [Run it yourself](#run-it-yourself)

JARVIS is a voice companion for Hindi and English. There is no chat window: a golden mechanical core opens while JARVIS speaks, closes when it finishes, and listens for your next turn. Tell it about your day, ask it to invent something, or teach it a shortcut you want to use tomorrow.

[![The golden hologram unfolding during speech, captured from the app](docs/amber-core.webp)](https://jarvis-ai-bay-one.vercel.app/)

## Your first minute

1. Open **[the live site](https://jarvis-ai-bay-one.vercel.app/)** in its own tab. JARVIS tries to listen as soon as the page opens. If the browser asks for microphone access, choose **Allow** to talk. If permission is already granted and your browser permits hands-free startup, no initial tap is needed. If your browser requires a gesture for recognition or audio, tap the core once or press **Space**. Start with **“नमस्ते”**. Hindi is the default; say **“speak in English”** to switch.
2. Talk normally. Try **“आज पहली बार मैंने गिटार बजाया”** or **“Invent a tiny animal that lives in a pencil case.”** Ask a follow-up after the reply. On the first open-ended question, JARVIS asks whether you accept the [open-chat terms](https://jarvis-ai-bay-one.vercel.app/terms) for this tab. Say yes to continue with your original question. Basic conversation, public lookups and notebook skills do not require model chat.
3. Say **“surprise me”** for a creative prompt, or **“पहेली सुनाओ”** and then **“इशारा दो”** for a riddle and a hint. If you repeat a supported city lookup, JARVIS can suggest turning it into a shortcut. Say **“suggestions off”** to stop these offers.
4. Say **“माइक बंद करो”**, tap the core, or press **Esc** to stop. The mic is released while JARVIS is thinking or speaking. Leaving the tab disarms it; coming back does not silently reactivate it. To keep future visits manual too, say **“auto mic off”** or press **A**. Say **“auto mic on”** during a manual conversation to restore automatic startup.

Chrome or Edge in a standalone HTTPS tab is a good starting point. Recognition, permissions and autoplay vary by browser and OS; a website cannot override a denial. Embedded previews and downloaded HTML stay tap-to-start. If autoplay blocks a reply after automatic startup, the mic pauses. Tap the core to hear that reply without repeating the question. Press **V** to hear the voice without the mic, or **T** to type a turn and **Enter** to send it. Typed input is intentionally invisible to preserve the hologram-only display.

## Teach JARVIS something

| What you want | What to say | What happens |
| --- | --- | --- |
| A personal routine | **“When I say match day, then time in London.”** | JARVIS reads the action back. Say **“yes”** to save it; later, just say **“match day.”** |
| A Hindi shortcut | **“जब मैं सुबह की घंटी बोलूँ तो दिल्ली का समय।”** | Confirm with **“हाँ”**, then run it by name. For guided teaching, start with **“नया शॉर्टकट”**. |
| A practice question | **“Teach a quiz.”** | Give the quiz a name, a question and a short answer. Confirm to save it. Say its name later and JARVIS checks your answer. |
| A nickname | **“Call me Sky.”** | Only an explicit confirmation saves the name. **“Forget my name”** removes it. |
| Reviewed skills from other people | **“Community skills”**, then **“city duet”** or **“planet pop quiz.”** | Runs an entry from the shared catalog. New proposals do not go live until a maintainer reviews and merges them. |
| Memory controls | **“My shortcuts”**, **“forget shortcut match day”**, or **“forget everything.”** | List saved routines, delete one, or clear the entire local notebook after confirmation. |

Up to **24 personal recipes** are stored in this browser, not in a cloud profile. A recipe can combine two city/headline lookups, start one timer, or teach a single quiz card. It cannot install software or run code. If site storage is blocked, JARVIS tells you that a new recipe lasts only for the open page.

**Share only what you choose.** Say **“share skill match day.”** After your confirmation the mic switches off. Tap the core or press **S** to review the public GitHub draft. Nothing is posted by the app. The chat model is not continuously retrained on conversations; personal learning and community publishing are separate. [How review works →](CONTRIBUTING.md)

## Public information and controls

- **World clocks and dates:** “Time in Tokyo” → “What about London?” Uses IANA time zones and daylight-saving rules. The short city follow-up lasts about two minutes.
- **Weather:** “Weather in Delhi.” Without a city, JARVIS asks for one. Readings come from Open-Meteo; stale readings are identified.
- **Headlines and reference:** “World headlines” and “Search Wikipedia for the Moon” use BBC feeds and Wikipedia, not a language model guessing today's news.
- **Timers and movement:** “Set a timer for five minutes,” “cancel timer,” “zoom in” or “reset view.” Timers run in the tab, not after the browser is closed.
- **Keyboard:** **H / E** select Hindi / English, **V** previews speech, **P** pauses rotation, **F** toggles fullscreen, arrow keys orbit, **L** opens the chat terms. Drag to orbit. The renderer respects reduced-motion preferences.

## How it works

| Layer | Implementation |
| --- | --- |
| Hologram and turn-taking | Self-contained HTML, procedural 3D geometry and a playback-driven iris. The controller waits for playback to finish before listening again. |
| Open conversation | A quantized **Gemma 3 1B IT** runs on the application host using `llama-cpp-python`. It receives the current question and at most two recent conversational exchanges. It generates words, not actions. Like any small model, it can misunderstand or be wrong. |
| Voice | Stock Kokoro voice blends: `hm_psi` / `hm_omega` for Hindi and `bm_george` / `bm_fable` for English. They are synthesized, not human recordings. The host synthesizes speech without a paid TTS API. If the host is warming or busy, the app tries a device voice; its gender and quality depend on the browser. |
| Personal notebook | Consent-based browser storage for a name, recipes and the shortcut-suggestion preference. No transcript database or background learning service. |
| Shared catalog | [`community/skills.json`](community/skills.json), validated in Python and the browser. The public host can fetch reviewed changes from this repository's `main`; it keeps a validated bundled copy for outages. |

**Privacy in practice:** the browser or its speech-recognition provider may process microphone audio. Recognized commands and recent chat context go to the JARVIS host when a server answer is needed. Text to be spoken—including a name or recipe read-back—can go to the host for synthesis. Public lookups send lookup data to their providers. The app does not save chat transcripts or speech audio, but browser/provider and hosting policies still apply. Do not use the public demo for secrets. A person using the same browser profile can access saved shortcuts.

## Run it yourself

For the lightweight desktop app, use Python **3.9+**:

```sh
python launch_hologram.py
```

It binds to loopback, opens the hologram and uses device speech if neural voice is not installed. On Windows, `Start Hologram.bat` starts the lightweight version; `Start Enhanced JARVIS.cmd` installs the optional neural voice with your permission. A 64-bit Python **3.12** installation is recommended for local voice and chat. The desktop voice setup does not silently install the chat model.

For **full on-host chat and both neural voices**, use the supplied container:

```sh
docker build -f Dockerfile.vercel -t jarvis-amber .
docker run --rm -p 127.0.0.1:8080:8080 -e PORT=8080 jarvis-amber
```

Open `http://localhost:8080`. The image build downloads and verifies the chat model and voice assets (about **900 MB** before runtime dependencies). The first model reply can take longer; concurrent or unavailable inference falls back to built-in activities rather than inventing a live answer. No private provider key is needed on the public host. See [deployment and native setup](DEPLOYMENT.md) for the optional source build, memory requirements, resource limits and troubleshooting.

## Tests and third-party notices

```sh
python -m unittest discover -s tests -v
node tests/notebook.cjs
```

The core tests require no model download, microphone or network credentials. [Deployment notes](DEPLOYMENT.md#verification) cover browser and real-model checks. Gemma is subject to its [terms and use restrictions](hologram/licenses/gemma-TERMS.txt); voice and time-zone notices are in [`hologram/licenses`](hologram/licenses/). The hologram is an original rendering. This project is not affiliated with Marvel, Google or the creators of the named voices.
