# J.A.R.V.I.S. — Golden hologram

Kaali screen par sirf ek sunehra 3D hologram. **Ek baar on karo, phir baat karte raho.** Jawaab bolte waqt baahari paratein alag hokar khulti hain, beech ka iris nazar aata hai aur awaaz ke utaar-chadhaav ke saath roshni badalti hai. Baat khatam hone par gola dobara judta hai. Koi button, transcript, menu ya dashboard nahi.

## Sabse pehle aise try karo

1. **Windows, enhanced male voice:** ZIP extract karo aur **`Start Enhanced JARVIS.cmd`** double-click karo. 64-bit Python **3.12** recommended (3.10–3.13 supported). Pehli baar yeh permission lekar ek alag Python environment mein speech engine install karega. Pehle enhanced start par host lagbhag **94 MB** ke verified voice/model files download karta hai. Uske baad unhe baar-baar download nahi karna padta. Agli baar isi launcher ya `Start Hologram.bat` se khol sakte ho.
2. **Core par ek baar tap karo** ya **Space** dabao aur browser ko mic ki permission do. Bolo: **“Jarvis, Tokyo mein kitne baje hain?”** Jab jawab khatam ho, seedha bolo: **“Aur London mein?”** Wake word ya doosra tap zaroori nahi. JARVIS apna jawab dete waqt mic nahi chalata.
3. **“Jarvis, mic band karo”**, **Esc**, ya core par dobara tap conversation band karta hai. Tab chhodne par bhi mic band hota hai; wapas aane par bina aapki marzi ke shuru nahi hota. Yeh foreground conversation hai, background mein chhupa hua listener nahi.

**Mic ke bina awaaz aur animation check karne ke liye `V` dabao.** Hindi default hai; **E** English, **H** Hindi. Enhanced mode mein asli neural synthesis hoti hai: Hindi ke liye `hm_omega`, English ke liye `bm_george`. Yeh stock masculine voices hain, kisi actor ki recording ya clone nahi. Model warm ho raha ho, download fail ho, ya host busy ho to app matching device voice use karta hai; us fallback mein male voice ki availability aapke browser par depend karti hai.

**Preview mein mic block ho?** Live app ko apne **alag HTTPS tab** mein Chrome ya Edge se kholo (local launcher `localhost` bhi theek hai). Browser/OS mic permission aur output volume check karo. File viewer mein khula hua HTML live app nahi hai. Browser ka permission dialog aur mic indicator normal hain; JARVIS unhe hide nahi karta.

### macOS / Linux

64-bit Python 3.12 aur supported wheels waale host par extracted folder mein:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-voice.txt
.venv/bin/python launch_hologram.py
```

**Halka, bina install ka mode:** Windows par `Start Hologram.bat`, ya `python3 launch_hologram.py` (stock Python 3.9+). Neural runtime na ho to system voice milegi; baat karne ka loop aur opening animation wahi rahenge. Terminal ko khula rakho; **Ctrl+C** launcher band karta hai.

## Kya pooch sakte ho?

| Pehla sawaal / order | Phir kya hoga |
|---|---|
| “Tokyo mein kitne baje hain?” → “Aur London mein?” | Dono shehron ke local clocks, DST ke saath. City time/date/weather ka chhota follow-up do minute tak samajhta hai. |
| “Aaj ka mausam batao” → “Delhi” | Agar shehar nahi bataya to JARVIS khud poochta hai; agla jawaab seedha bolo. Open-Meteo reading purani ho to saaf batata hai. |
| “Duniya ki khabrein sunao” / “World headlines” | BBC Hindi ya BBC World ki do dated headlines. |
| “Chandrayaan ke baare mein batao” / “Search Wikipedia for the Moon” | Source ke naam ke saath chhota encyclopedia jawab. |
| “Ek minute ka timer lagao” / “Cancel timer” | Is tab mein ek timer. Naya timer purane ko replace karta hai; device sleep ya background mein der ho sakti hai. |
| “Zoom in”, “rotate slower”, “reset view” | Seedha 3D hologram badalta hai. |

### Screen khaali rakhne waale shortcuts

- **Tap / Space / Enter:** hands-free session on/off. Jawab ke beech mein bhi tap ya Esc turant rokta hai; mic dobara nahi khulta. Server ko pehle hi mil chuki request wapas nahi li ja sakti.
- **V:** bina mic ke voice/iris preview. **E / H:** English / Hindi.
- **Drag / arrows:** orbit. **P:** auto-rotation pause/resume. **F** ya core par **long-press karke chhodo:** full screen.
- **T → order type karo → Enter:** mic ke bina wahi command; typed input screen par nahi dikhta. Password mat likhna. Touch devices par OS keyboard alag se dikh sakta hai.
- **O:** configured private Streamlit deployment mein owner sign-in/sign-out. Browser aur hosting platform ke apne dialogs app ke bahar hain.

## Repo aur hosting

`app.py` ke saath `hologram/`, `requirements.txt` aur `requirements-voice.txt` **repo root** mein rakho. Existing Streamlit app ka target **`main` → `app.py`** hai. Optional private AI (`OPENROUTER_API_KEY`), explicit public-web search (`BRAVE_SEARCH_API_KEY`), verified owner login, privacy, model attribution aur tests: **[DEPLOYMENT.md](DEPLOYMENT.md)**.

Standalone local mode sirf loopback par hai; yeh speaker verification nahi hai. Public preview keys nahi padhta. Private accounts, payments, OS shell ya device-control ka access nahi joda gaya hai. Original full checkout par `python Jarvis_Project/run_jarvis.py --classic` purana Tk mode kholta hai. Is runnable update mein legacy account DB, sessions, credentials, personal photos ya bundled Python nahi hain.

**Security:** Agar GitHub token chat ya repository mein expose hua tha to use revoke karo. Naye secrets chat mein mat bhejo. Asli public checkout ki historic credential/session files ko sirf `.gitignore` se private nahi banaya ja sakta; real secrets rotate aur zaroorat par history clean karo.
