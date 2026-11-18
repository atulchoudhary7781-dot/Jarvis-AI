# J.A.R.V.I.S. — Golden hologram

Ek khaali, kaali screen. Beech mein ek zinda sunehra core. Sirf wahi.

Yeh film ki still image ya GIF nahi hai. Patli metallic paratein, tute hue rings, particles aur beech ka khula lens 3D mein bane hain. Drag karne par inki depth dikhti hai. Sunte, jawab dhoondhte aur bolte waqt roshni badalti hai. Screen par koi naam, menu, button, chat ya transcript nahi aata.

## Pehle chala kar dekho

1. ZIP **extract** karo. Windows par **`Start Hologram.bat`** double-click karo. Python 3.9+ chahiye; local launcher ke liye `pip install` nahi karna hai. macOS / Linux par us folder mein `python3 launch_hologram.py` chalao.
2. Launcher installed Edge/Chrome mein ek clean full-screen app window kholne ki koshish karta hai. Agar normal browser tab khule, **F** dabao. Terminal khula rehne do; band karne ke liye terminal mein **Ctrl+C**.
3. **Core par ek baar tap/click karo** (ya **Space** dabao). Pehli baar browser mic ki permission maangega. Bolo: **“Jarvis, Tokyo mein abhi kitne baje hain?”** Jawab awaaz mein aayega, screen par nahi. Agle sawaal ke liye phir tap karo.

Hindi default hai. **E** se English, **H** se Hindi. Browser/OS mein us bhasha ki speech voice aur recognition support honi chahiye. Koi khaas actor ki awaaz use nahi hoti.

### Kuch orders aazmao

| Bolo | Kya hoga |
|---|---|
| “Tokyo mein kitne baje hain?” / “Time in Buenos Aires” | Us shehar ka current local time, daylight saving ke saath |
| “Delhi ka mausam batao” / “Weather in Paris” | Open-Meteo se mausam. Purani reading mile to JARVIS use purani hi batayega |
| “Duniya ki khabrein sunao” / “World headlines” | BBC Hindi / BBC World ki do dated headlines |
| “Chandrayaan ke baare mein batao” / “Search Wikipedia for the Moon” | Wikipedia se chhota jawab, source ke naam ke saath |
| “Ek minute ka timer lagao” / “Set a timer for five minutes” | Isi tab mein timer; “cancel timer” se rok sakte ho |
| “Zoom in”, “rotate slower”, “pause rotation”, “reset view” | Seedha hologram badalta hai |

Timer ke liye tab khula rakho; sleeping device ya browser background mein alarm delay kar sakta hai. Ek time par ek timer hai; naya timer purane ko replace karta hai. Geocoding mein milte-julte shehar hon to naam ke baad comma aur country do. General AI aur poore public web par search optional hain, neeche dekho.

### Bina screen par controls laaye

- **Drag / arrow keys:** hologram ko ghumao. **P:** auto-rotation pause/resume.
- **F** ya core ko **long-press karke chhodo:** full screen. Browser ka **F11** bhi use kar sakte ho.
- **Esc** ya active core par dobara tap: current listening, lookup ka intezaar, ya speech cancel. Pehle se provider tak pahunch chuki request wapas nahi li ja sakti.
- **T → order type karo → Enter:** mic ke bina wahi command chalao. Koi textbox/typed text **dikhega nahi**. Esc se cancel. Isme password mat likhna.
- **O:** sirf configured private Streamlit mode mein owner sign-in/sign-out. Browser ka login/permission dialog app ki screen se alag hai.

Mic iframe mein block ho to preview ko apne tab mein kholo, ya local launcher use karo. `localhost`/HTTPS, browser mic permission aur system audio check karo. Agar voice output installed nahi hai, accessible status screen reader ko milta hai. Info service ko terminal se bhi check kar sakte ho:

```sh
python launch_hologram.py --ask "time in Tokyo" --lang en
```

**Sirf design dekhna hai?** `hologram/ui/index.html` seedha kholo. Koi CDN, server ya image download nahi chahiye. File-only mode mein 3D, gestures, timers aur kuch clocks hain; internet waale jawaabon ke liye launcher ya Streamlit app chalao.

## Apne `Jarvis-AI` repo mein lagana

Yeh ready-to-run **update** hai, poore purane repository ki copy nahi. Public `main` revision `ebe7d939cb25` ke file paths ke hisaab se banaya gaya hai. Apne uncommitted changes ka backup lo. Nayi branch par ZIP ke **andar ke files** repo root mein copy karo: naya `app.py` purane `app.py` ki jagah aana chahiye, uske bagal mein `hologram/` hona chahiye. Extra nested folder mat banana.

- `app.py` ab Streamlit ke purane sidebar/chat ki jagah isi hologram ko chalata hai. Hosted app ka entrypoint ab bhi **`app.py`** hai. Dependencies ke liye updated `requirements.txt` bhi copy karo.
- `Jarvis_Project/run_jarvis.py` aur purana `.../Jarvis/Jarvis_Launcher.bat` ab hologram se khulte hain. Purana Tk interface delete nahi kiya gaya. Original checkout mein `python Jarvis_Project/run_jarvis.py --classic` se use chala sakte ho (uski apni dependencies chahiye).
- Database, account/session, personal photo, bundled Python, API-key file aur background services is update mein nahi hain. Naya mode unhe import nahi karta. Koi GitHub push/deployment apne aap nahi hota.

## Private AI, owner access aur poore public web ki search

Local mode sirf `127.0.0.1` par khulta hai. **Iska matlab speaker verification nahi hai:** unlocked device par mic activate karne wala koi bhi bol sakta hai. Hosted app ko sirf apne liye rakhne ke liye verified owner login configure karo. Is mode mein server har information request par owner ko check karta hai, sirf frontend par nahi.

- Bina keys: city clocks, current weather, public knowledge aur headlines.
- Private `OPENROUTER_API_KEY`: natural conversation, isi tab ke pichhle do AI exchanges ke context ke saath.
- Private `BRAVE_SEARCH_API_KEY`: “Search the web for lunar research” par public web ke do results aur unke source domains. JARVIS result pages par khud navigate ya code execute nahi karta.

Setup aur hosting: **[DEPLOYMENT.md](DEPLOYMENT.md)**. Yeh global information assistant hai, duniya ke private accounts/devices ka remote controller nahi. Payments, shell commands ya unrestricted system access isme nahi hai.

**Security:** Agar chat mein GitHub token share hua hai to use revoke karo. Naya token chat, code ya ZIP mein mat rakho. Original public checkout mein `api_key.env`, session aur account DB jaise filenames tracked hain. Agar unmein real credentials/personal data hain to unhe rotate/invalidate aur repo history se remove karo. Sirf `.gitignore` add karne se purani history nahi hatti.
