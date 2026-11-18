# Hosting and private access

## Choose the right mode

| Mode | Start | Access / credentials |
|---|---|---|
| Personal desktop | `python launch_hologram.py` | Loopback only. May use fresh, server-side provider keys set in your environment. Never reads legacy `.env`, sessions or account databases. |
| Shareable demonstration | `python launch_hologram.py --preview --no-open --port 8080` | Binds to `0.0.0.0`; **always ignores both private provider keys**. Public, read-only data skills. For a shared demo behind HTTPS, not a private device-control service. |
| Existing Streamlit deployment | `streamlit run app.py` | Anonymous mode only supports keyless public lookups. Setting `OWNER_EMAIL` locks backend commands; private providers require a verified owner session. |
| Downloaded HTML | Open `hologram/ui/index.html` | Rendering, orbit, local controls, timers and a small offline clock vocabulary. No server or API requests. Voice is browser-dependent. |

`--port 0` picks a free local port; `--browser-tab` opens the default browser instead of requesting a full-screen app window. The personal server does not expose a filesystem or serve repository files. Do not port-forward it. Use the authenticated Streamlit path for remote private access.

## Streamlit / Community Cloud

1. Apply the update at the real repository root (see README), review the diff, and commit the clean changes from your own account.
2. Use `app.py` as the main file. Use 64-bit **Python 3.12** for the hosted neural engine. With a compatible local environment: `python -m pip install -r requirements.txt` then `python -m streamlit run app.py`. `.streamlit/config.toml` is part of the update.
3. Public time, weather, Wikipedia, headlines and the on-host neural voice do not need API keys. Network/provider limits apply. The iframe asks for no microphone access until a gesture. Host browser chrome or the hosting platform's own consent screens are outside the app.
4. For owner-only access, register an OpenID Connect client with a provider that supplies **verified email claims**. Set its callback URL exactly to `https://YOUR-APP.streamlit.app/oauth2callback` (use the actual address). Configure values in Streamlit's **Secrets** settings, or in a local, ignored `.streamlit/secrets.toml`. See `.streamlit/secrets.example.toml` for the shape.
5. Set the top-level `OWNER_EMAIL` to your verified account. Use a fresh, randomly generated `cookie_secret` (e.g. generate one locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`). Restart after changing Secrets. On the sphere, tap/Space or O opens the provider sign-in when locked. O signs out an active session.

With `OWNER_EMAIL` set, missing auth config, an unverified email, or a different email **does not unlock commands**. The decorative hologram itself is not secret. A browser mic is not identity and there is no voiceprint enrollment. To prevent even unauthenticated viewing, also set the hosting platform's sharing/access policy to private. On a shared touch device, sign out via the keyboard shortcut before handing it over, or end the private browser session.

## Male voice and the speaking rig

`requirements.txt` includes `requirements-voice.txt` for supported Python 3.10–3.13 environments; on a desktop the latter can be installed alone. For Community Cloud, select Python 3.12 and allow the app to rebuild from the repository. Check **Manage app → logs** from an authorized owner session if a build fails. A Git push does not prove a private Cloud build succeeded.

With the runtime installed, a matching authorized Streamlit render (or standalone server startup) begins warming a CPU-only model in the background. The first download is 92,361,116 bytes for the quantized network plus two 522,240-byte voice embeddings. Pinned revisions and SHA-256 are checked before use. Only model assets and their local embedding bundle live in `~/.cache/jarvis-amber-voice/`. No TTS service account, API key, speaker enrollment or microphone sample is required. The host needs writable cache space and, on first use, access to the model host. Allow adequate memory for the runtime; short voices used hundreds of MB in local testing. Ephemeral hosts may download again after a restart.

Press **V** to test a real sentence without opening the mic, then **E** to hear English or **H** for Hindi. Only the returned speech audio drives the neural visualizer: the outer shell hinges into staggered sectors, the inner vanes deploy, and their light follows the 25 Hz loudness track at the *actual playback position*. The shell folds shut again after speech. Reduced-motion mode uses a shallow opening and no automatic spinning. The same geometry works in WebGL and its projected Canvas fallback.

If model loading, synthesis or a host limit prevents a clip, JARVIS can use device synthesis, prioritizing known masculine voices in the same language. Device voice gender, quality, offline support and word-boundary events vary. Some device voices may themselves use the browser vendor's service. Set environment/Streamlit secret `JARVIS_VOICE = "system"` and restart for system speech only; the default is `auto`. The device-only installer-free path still supports hands-free conversation. [Voice assets and notices](hologram/licenses/kokoro-VOICE-NOTICE.md).

## Optional external providers

Set `OPENROUTER_API_KEY` for conversational AI. Set `OPENROUTER_MODEL` to a model available in your account; the default is `openrouter/auto`. Set `BRAVE_SEARCH_API_KEY` for explicit full-web search commands. These are unrelated to GitHub access. The app never needs a GitHub token.

On the desktop, configure these variables using your OS's environment-variable settings and restart the launcher. On Streamlit, put them in Secrets **only alongside owner authentication** to use them. Do not place values in HTML, front-end JavaScript, the URL or a committed file. Do not paste them into chat. Provider usage can incur charges; configure quotas in the provider dashboard.

General chat sends at most two prior AI exchanges plus the current prompt to OpenRouter. That short context is in tab memory, not saved as chat history. Model output is plain speech, not an instruction to execute anything. Brave Search is a separate, explicitly invoked read-only provider; search snippets are not instructions either. The app has no access to a private email, drive, camera, payment account, shell or smart-home device.

## Privacy and data sources

- **Microphone:** off by default. One foreground gesture opts in. The recognizer stops on a completed question; it is not running during lookup, voice generation or speaker playback. After the complete answer it opens a new listening turn. A quiet timeout retries without asking for another tap. Saying “stop listening” / “माइक बंद करो”, tapping the core again, Esc, hiding or leaving the tab disarms the session. Mic denial or a persistent recognizer failure stops retries. The on/off choice is never persisted. This is not background wake-word detection, barge-in, speaker verification or an audio recorder. Browser speech recognition may send the utterance to the browser vendor. Use a secure context (HTTPS or localhost) with mic permission.
- **Synthesis:** the browser sends short reply clauses to its own enabled host; text is not sent to Hugging Face or to an external TTS API by this neural engine. The host returns 24 kHz mono WAV plus a bounded signal envelope. Work is rate-limited, one inference at a time. Audio is transient, not saved to a speech database. Failed playback cannot silently re-enable a blocked microphone.
- **Text:** the web frontend sends a recognized or deliberately typed command to its own backend. The app does not write transcripts to files or a database. The latest request/result can exist in session memory; providers and your hosting platform have their own policies.
- **Location:** no GPS permission, IP geolocation or automated location scraping. The local clock uses the browser's IANA timezone. Weather/remote clocks use the city you ask about. City matching can be ambiguous: read/listen to the returned place and qualify the name with a country when needed.
- **Weather and geocoding:** [Open-Meteo](https://open-meteo.com/), including its GeoNames-based geocoding data. Weather is cached for about four minutes and responses older than four hours are explicitly identified as old. Observe the provider's attribution and plan terms when deploying commercially.
- **Headlines:** [BBC World RSS](https://feeds.bbci.co.uk/news/world/rss.xml) for English and [BBC Hindi RSS](https://feeds.bbci.co.uk/hindi/rss.xml) for Hindi. The two most recent dated items in the retrieved feed are read without storing articles. Bulletins older than two days are labelled, not passed off as current.
- **Knowledge:** [Wikipedia](https://www.wikipedia.org/) via MediaWiki's public search/extracts API. A short extract is attributed in the spoken response; article title and source are also returned by the backend. Wikipedia text is by its contributors under its applicable licenses.
- **Time zones:** system IANA data first; stock Windows can fall back to the included `hologram/zones.zip` (TZif files from `tzdata` 2026.6, IANA 2026f). Notices in `hologram/licenses/`.

## Implementation and checks

`hologram/ui/index.html` is self-contained, editable source, not a screenshot or movie. No CDN, fonts, textures, npm runtime or third-party JS. It generates irregular 3D fragments, bundled conductors and a hollow optical lens, renders four independent rotations, and composites two bloom scales. A reduced 2D renderer projects the same 3D data if WebGL is unavailable. The renderer yields when hidden and respects reduced-motion preferences.

The same document works as a Streamlit bidirectional component or as a standalone frontend with same-origin `/api/command` and `/api/voice` endpoints. Provider addresses are fixed; no arbitrary URL fetching. The launcher opens only its own loopback URL. Bounded requests, timeouts, rate limits and request IDs avoid unbounded work or replaying a stale spoken answer after cancellation. Native speech-service availability, provider uptime and permissions are not guaranteed.

```sh
python -m unittest discover -s tests -v
python launch_hologram.py --ask "weather in Delhi" --lang en
python launch_hologram.py --ask "world headlines" --lang en
```

The Python regression suite is offline (the NumPy-specific unit case skips if the optional dependency is absent). To recheck turn-taking on a local server with Playwright and its Chromium installed, run `node tests/browser_conversation.cjs` (set `AMBER_TEST_URL` if not using the default `http://127.0.0.1:8765`). It simulates microphone and device-voice events, exercises two real local clock answers including a contextual follow-up, and checks no mid-reply capture, spoken stop, silence, denial, hidden tabs and stale replies. Real Linux CPU-generated Hindi and English WAVs were also decoded and played in a fresh local Streamlit bridge check. This does not test a physical microphone or the availability of a browser vendor's recognition service.

 Browser checks during packaging covered desktop/mobile layout, WebGL and CPU fallback, orbit/fullscreen, typed queries, the Streamlit request/reply round trip, plus the speech state machine with simulated microphone/synthesis events. Real public weather, geocoding, encyclopedia and headline requests were also exercised. No real personal provider keys or owner identity were used; a physical microphone, paid provider and OAuth sign-in must be checked on your device/deployment.
