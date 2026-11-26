# J.A.R.V.I.S. — Amber Companion

A Hindi and English voice companion with an animated hologram, spoken replies, public-information lookups, personal shortcuts, and carefully restricted launch actions.

**[Open the live JARVIS website](https://jarvis-ai-bay-one.vercel.app/)** · [Contributing](CONTRIBUTING.md) · [Deployment guide](DEPLOYMENT.md)

![JARVIS hologram](docs/amber-core.webp)

> Cross-device and native app features are experimental. The public deployment may not yet contain the latest repository changes; real-device testing is still needed.

## Getting started

1. Open JARVIS in its own browser tab. Speech recognition and microphone permission vary by browser and device.
2. Allow microphone access if prompted. JARVIS attempts to listen automatically when the page opens. Browser permissions, device settings, and autoplay rules can require a tap on the core or a press of **Space**.
3. Say **“Hello”**, **“Time in Tokyo”**, or **“Open YouTube.”** Hindi is the default reply language; say **“Speak in English”** for English replies.
4. Say **“Stop listening”**, press **Esc**, or tap the core to turn the microphone off. Leaving the tab also disarms it.

During an active conversation the microphone may remain active or reopen while JARVIS speaks so you can interrupt; echo cancellation varies by browser. Stop listening, press Esc, or leave the tab to disarm it. If automatic playback is blocked, tap the core to play the pending reply without repeating the command. Say **“Auto mic off”** or press **A** to keep future visits manual; say **“Auto mic on”** to restore automatic startup.

## Features

| Feature | Example or description |
| --- | --- |
| Conversation | Talk about your day, ask for an idea, or request a riddle. Open-ended model chat requires accepting the displayed terms for the current tab. |
| Speech and listening | Synthesized Hindi and English voices, pause-aware turn-taking, and recognition alternatives. Say **“Listen patiently”** for longer pauses or **“Normal pauses”** to return to the default. |
| Recognition language | Say **“Listen in Hindi”** or **“Listen in English.”** The reply language is controlled separately. Say **“What did you hear”** to hear the previous recognized phrase. |
| Website opening | Say **“Open YouTube”**, **“Open Google Maps”**, or **“Search YouTube for music.”** Review the displayed destination and tap its button to open it. |
| Local computer apps | An optional private session can request Calculator, Notepad and Paint on Windows, or Calculator and TextEdit on macOS, after native approval. See [Local app control](#local-app-control-experimental). |
| Public information | Ask for a city clock or date, weather, world headlines, or a Wikipedia search. Availability depends on the upstream services. |
| Basic arithmetic | Ask “What is 17 multiplied by 23?” or “१७ गुणा २३ कितना है?” Simple +, −, × and ÷ expressions are calculated locally; unsupported expressions are not guessed. |
| Timers and view controls | Say **“Set a timer for five minutes,”** **“Cancel timer,”** **“Zoom in,”** or **“Reset view.”** Timers last only while the tab remains open. |
| Personal shortcuts | Teach a reviewed routine or quiz, confirm it, and run it later by name. Shortcuts are stored in the current browser profile. |
| Community skills | Say **“Community skills”** to discover reviewed examples such as **“City duet”** and **“Planet pop quiz.”** |

For an unmatched spoken request, JARVIS asks you to try again rather than assuming you wanted open chat. To use open-ended Gemma chat, say **“Open chat”**, read its terms and explicitly agree for the tab. A typed open-chat request, where a typing interface is enabled, can also show the terms.

To reduce long waits, slow neural speech may fall back to a device voice; its sound and availability depend on the browser. The response itself and recognition may still be delayed by the network or provider.

The browser's speech-recognition service and microphone determine recognition accuracy. Hindi and Hinglish may still be misheard; recognition is not guaranteed. For a missed command, repeat it or use the visible **Type** button, then **Send**. Spoken replies and status messages are also displayed on screen; anyone looking at the screen can see them.

### Keyboard controls

| Key | Action |
| --- | --- |
| **Space** | Start or stop listening; confirm a displayed website action when appropriate |
| **Esc** | Cancel and stop listening |
| **T** | Type a command |
| **A** | Toggle automatic microphone startup for future visits |
| **N** | Toggle the optional cloud noise filter for this tab; browser voice is unchanged |
| **H / E** | Select Hindi / English replies |
| **V** | Preview the voice |
| **P / F** | Pause rotation / toggle full screen |
| **Arrow keys** | Orbit the hologram |
| **L** | Open the model terms |

## Teach a shortcut

Say **“When I say match day, then time in London.”** JARVIS reads the proposed action back. Say **“Yes”** to save it, then say **“Match day”** to run it. You can also say **“Teach a quiz,”** **“My shortcuts,”** **“Forget shortcut match day,”** or **“Forget everything.”**

The notebook supports up to 24 personal recipes in the browser. Recipes can combine supported public lookups, start a timer, or store a quiz card; they cannot install software or run code. If browser storage is blocked, saved items may last only for the current page.

## Local app control (experimental)

The public website **cannot control apps on your computer**. To try local app control on your own Windows computer:

1. Install Python 3.9 or later. A 64-bit Python 3.12 installation is recommended if you also want the optional neural voice.
2. Optionally run `Start Enhanced JARVIS.cmd` and approve the voice setup. Close that session when it opens.
3. Run `Start Private JARVIS.cmd` normally, **not as administrator**, and keep its command window open.
4. Allow the microphone if needed. Say **“Open Calculator,”** **“Open Notepad,”** or **“Open Paint.”** Approve only a request that you made in the Windows dialog. The dialog defaults to **No**.
5. Close the command window to stop the local session. Restart it after the two-hour session expires.

On macOS, install Python 3.9 or newer, open Terminal in the extracted JARVIS folder, and run:

```sh
python3 launch_hologram.py --desktop --browser-tab --port 0
```

Keep Terminal open. Ask for **Calculator** or **TextEdit**, then approve the macOS dialog only if you made the request. Start as a normal user, never root. Close Terminal or press Ctrl+C to stop. This uses fixed system app locations; if they are absent on your macOS version, launching will fail.

The broker is loopback-only, accepts no shell commands or arbitrary paths, and uses short-lived, single-use approvals. Windows and macOS dialogs and launches were tested with mocks, **not yet on real computers**. Use a trusted, locked account: malicious software already running as your user can bypass these protections.

### Phones and tablets

On Android or iOS, supported links such as YouTube and Google Maps are shown for approval. Depending on the app, operating system, browser, and link settings, tapping may open the app or its website; this is not a general installed-app launcher. Websites cannot enumerate or launch arbitrary installed mobile apps. Voice recognition and automatic playback also vary; use **Type** if voice is unavailable. Real mobile devices have not yet been tested.

## Voice, privacy, and safety

- The natural-sounding voices are **synthetic stock-voice blends**, not recordings of a human or an actor. If neural speech is unavailable, the browser may use a device voice.
- The public site is not owner-authenticated. Do not share passwords, private keys, or other secrets with it.
- Your browser or its recognition provider may process microphone audio. Commands and recent chat context are sent to the JARVIS host when a server answer is needed. Speech text may be sent to the host for synthesis. Public lookups are sent to their respective providers.
- In the opt-in Groq cloud voice path, an optional 48 kHz AudioWorklet can apply RNNoise locally before transcription when the browser supports it. The filter is off by default because it can make some speech harder to recognize; enable it only if it helps in your environment. Otherwise the existing browser suppression/high-pass fallback is used; browser-native speech recognition is not passed through RNNoise. Say “noise filter off”/“noise filter on”, or press **N**, to change the advanced filter for the tab. Say “noise status” to hear whether browser or cloud voice is configured. The browser's own audio processing can remain active when the filter is off.
- Noise reduction is not voice identification, does not reliably remove other speakers, and can affect quiet speech. Acoustic results and mobile support require real-device testing. Cloud voice requires its explicit consent and configured service and quotas.
- The application does not maintain a chat-transcript or audio database, but browser, recognition-provider, and hosting policies still apply. Anyone using the same browser profile may access saved shortcuts.
- Open-ended model output can be slow, unavailable, or incorrect; it cannot independently execute device actions. No security system can guarantee that misuse is impossible.

## Run locally

For a lightweight loopback-only session with the device voice:

```sh
python launch_hologram.py
```

On Windows, `Start Hologram.bat` starts the lightweight version and `Start Enhanced JARVIS.cmd` offers optional local neural-voice setup. The Windows app launcher is a separate opt-in session.

For the container build:

```sh
docker build -f Dockerfile.vercel -t jarvis-amber .
docker run --rm -p 127.0.0.1:8080:8080 -e PORT=8080 jarvis-amber
```

Then open `http://localhost:8080`. The image build downloads and verifies model assets. See [DEPLOYMENT.md](DEPLOYMENT.md) for requirements and troubleshooting.

Deployment settings vary by Vercel project. Verify that a new deployment is ready and that the production domain serves it; a Git push alone does not prove that the website was updated.

## Tests

```sh
python -m unittest discover -s tests -v
node tests/notebook.cjs
```

Optional Playwright browser suites cover microphone lifecycle and command review with simulated recognition. The tests do not prove physical-microphone accuracy, native app associations, or actual Windows or macOS execution.

## Third-party notices

Open conversation uses Gemma and is subject to its [terms](hologram/licenses/gemma-TERMS.txt). Voice and time-zone notices are in [`hologram/licenses`](hologram/licenses/). This project is not affiliated with Marvel, Google, or the creators of the named voices.
