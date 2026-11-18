"""Read-only voice skills shared by the desktop, preview and Streamlit hosts.

No files, sessions, credentials or code from the legacy desktop installation are
loaded. Provider destinations are constants, never command parameters.
"""

from __future__ import annotations

import json
import math
import re
import threading
import time
import zipfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from html import unescape
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_QUERY = 360
AGENT = (
    "JarvisAmber/1.0 (https://github.com/atulchoudhary7781-dot/Jarvis-AI; read-only voice lookup)"
)
DESTINATIONS = {
    "https://geocoding-api.open-meteo.com/v1/search",
    "https://api.open-meteo.com/v1/forecast",
    "https://en.wikipedia.org/w/api.php",
    "https://hi.wikipedia.org/w/api.php",
    "https://openrouter.ai/api/v1/chat/completions",
    "https://api.search.brave.com/res/v1/web/search",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Especially important for the optional provider credential.


def fetch_json(endpoint, params=None, *, body=None, key=None, search_token=None):
    if endpoint not in DESTINATIONS or (key and urlsplit(endpoint).hostname != "openrouter.ai"):
        raise ValueError("Unknown provider")
    url = endpoint + ("?" + urlencode(params) if params else "")
    headers = {"User-Agent": AGENT, "Accept": "application/json"}
    if search_token:
        if endpoint != "https://api.search.brave.com/res/v1/web/search":
            raise ValueError("Invalid search provider")
        headers["X-Subscription-Token"] = search_token
    if key:
        headers["Authorization"] = "Bearer " + key
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(
        url, headers=headers, data=json.dumps(body).encode() if body is not None else None
    )
    with build_opener(NoRedirect).open(req, timeout=18 if body else 6) as response:
        data = response.read(700_001)
    if len(data) > 700_000:
        raise ValueError("Oversized provider response")
    return json.loads(data)


# Common places work without a geocoding request. All other city names are
# geocoded worldwide. Coordinates here are city centres, NOT user positions.
_CITIES = [
    ("New Delhi", "India", "Asia/Kolkata", 28.614, 77.209, "delhi|नई दिल्ली|दिल्ली|न्यू दिल्ली"),
    ("Mumbai", "India", "Asia/Kolkata", 19.076, 72.878, "bombay|मुंबई|मुम्बई"),
    ("Bengaluru", "India", "Asia/Kolkata", 12.972, 77.594, "bangalore|बेंगलुरु|बैंगलोर"),
    ("Kolkata", "India", "Asia/Kolkata", 22.573, 88.364, "calcutta|कोलकाता"),
    ("Chennai", "India", "Asia/Kolkata", 13.083, 80.271, "madras|चेन्नई"),
    ("Tokyo", "Japan", "Asia/Tokyo", 35.690, 139.692, "टोक्यो|टोकियो"),
    ("London", "United Kingdom", "Europe/London", 51.509, -0.126, "लंदन|लन्दन"),
    ("Paris", "France", "Europe/Paris", 48.853, 2.349, "पेरिस|पैरिस"),
    (
        "New York",
        "United States",
        "America/New_York",
        40.713,
        -74.006,
        "nyc|new york city|न्यूयॉर्क|न्यू यॉर्क|न्यूयार्क",
    ),
    (
        "Los Angeles",
        "United States",
        "America/Los_Angeles",
        34.052,
        -118.244,
        "लॉस एंजेलिस|लॉस एंजिल्स",
    ),
    ("San Francisco", "United States", "America/Los_Angeles", 37.775, -122.419, "सैन फ्रांसिस्को"),
    ("Dubai", "United Arab Emirates", "Asia/Dubai", 25.205, 55.271, "दुबई"),
    ("Singapore", "Singapore", "Asia/Singapore", 1.29, 103.851, "सिंगापुर"),
    ("Sydney", "Australia", "Australia/Sydney", -33.868, 151.209, "सिडनी"),
    ("Berlin", "Germany", "Europe/Berlin", 52.52, 13.405, "बर्लिन"),
    ("Seoul", "South Korea", "Asia/Seoul", 37.566, 126.978, "सियोल"),
    ("Nairobi", "Kenya", "Africa/Nairobi", -1.286, 36.817, "नैरोबी"),
    ("São Paulo", "Brazil", "America/Sao_Paulo", -23.551, -46.633, "sao paulo|साओ पाउलो"),
    ("Kathmandu", "Nepal", "Asia/Kathmandu", 27.717, 85.324, "काठमांडू|काठमाण्डू"),
]
ALIASES = {
    k.casefold(): (n, country, z, lat, lon)
    for n, country, z, lat, lon, aliases in _CITIES
    for k in [n, *aliases.split("|")]
}


HI_CITY = {
    n: next((a for a in aliases.split("|") if re.search(r"[\u0900-\u097f]", a)), n)
    for n, _, _, _, _, aliases in _CITIES
}
HI_COUNTRY = {
    "India": "भारत",
    "Japan": "जापान",
    "United Kingdom": "ब्रिटेन",
    "France": "फ़्रांस",
    "United States": "अमेरिका",
    "United Arab Emirates": "संयुक्त अरब अमीरात",
    "Singapore": "सिंगापुर",
    "Australia": "ऑस्ट्रेलिया",
    "Germany": "जर्मनी",
    "South Korea": "दक्षिण कोरिया",
    "Kenya": "केन्या",
    "Brazil": "ब्राज़ील",
    "Nepal": "नेपाल",
}


def norm(s):
    return " ".join(s.casefold().replace("’", "'").strip(" \t!?।.").split())


def strip_wake(s):
    return re.sub(
        r"^(?:(?:hey|ok(?:ay)?|हेलो|हे|ओके)\s+)?(?:jarvis|जार्विस|जारविस|जार्विश|जर्विस)[\s,:।.!-]*",
        "",
        s,
        flags=re.I,
    ).strip()


def reply(en, hi, language, *, source="local", **rest):
    hindi = language.startswith("hi")
    return dict(text=hi if hindi else en, lang="hi-IN" if hindi else "en-IN", source=source, **rest)


WEATHER = re.compile(
    r"(?<!\w)(?:weather|mausam|mosam|temperature|temp|tapman|तापमान|मौसम|वेदर)(?!\w)", re.I
)
TIME = re.compile(r"(?<!\w)(?:time|clock|samay|waqt|vakt|baje|टाइम|समय|वक़्त|वक्त|बजे)(?!\w)", re.I)
DATE = re.compile(r"(?<!\w)(?:date|tareekh|tarikh|तारीख़|तारीख|दिनांक|तिथि|डेट)(?!\w)", re.I)
FILL = set(
    """
    what what's whats is the it like now current currently tell me a an about at in for of please how
    right can you there today city local here my your get outside degrees today's todays do does are
    could would much and ka kaa ke ki ko mein mai abhi aaj aj kya hai hain h batao bataiye bata batana
    kitna kitni kitne raha rahi rahe chal jaan na mujhe mera mere yahan yaha wahan dikhao hua hoga
    kaisa kesa kaisi temperature weather time
    का की के को में मैं अभी है हैं क्या आज कितना कितने कितनी मुझे बताओ बताइए बताना बताइये बता दो
    रहा रही रहे चल यहाँ यहां वहां वहाँ मेरे अपना कर करके कृपया प्लीज़ प्लीज बजे देखो सुनाओ बताएं कि
    बताइएगा हुआ होगी होगा प्लीस कैसा कैसी मौसम समय टाइम
""".split()
)


def location_hint(q, pat):
    # Remove conversational scaffolding from the ends rather than forcing an
    # English-only city regex. Keep commas and inner words in e.g. Port of Spain.
    before, after = q[: pat.start()], q[pat.end() :]

    def trim(s):
        words = s.strip(" ,:.?!।").split()
        while words and words[0].strip(" ,:.?!।") in FILL:
            words.pop(0)
        while words and words[-1].strip(" ,:.?!।") in FILL:
            words.pop()
        return " ".join(words).strip(" ,:.?!।")

    return (trim(after) or trim(before))[:110]


@lru_cache(maxsize=256)
def place(name, language="en"):
    city, _, country = name.partition(",")
    city, country = city.strip(), country.strip().casefold()
    known = ALIASES.get(city.casefold())
    if known and (not country or country == known[1].casefold()):
        return known
    if not city or len(city) > 85:
        return None
    result = fetch_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": city, "count": 10, "language": language, "format": "json"},
    )
    rows = result.get("results") or []
    if country:
        rows = [
            r
            for r in rows
            if country
            in {str(r.get(x, "")).casefold() for x in ("country", "country_code", "admin1")}
        ]
    if not rows:
        return None
    r = rows[0]
    lat, lon = float(r["latitude"]), float(r["longitude"])
    if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Invalid coordinates")
    return (
        str(r["name"])[:80],
        str(r.get("country", ""))[:70],
        str(r.get("timezone", ""))[:80],
        lat,
        lon,
    )


def weather_words(code):
    if code == 0:
        return "clear skies", "आसमान साफ़ है"
    if code in (1, 2):
        return "partly cloudy skies", "हल्के बादल हैं"
    if code == 3:
        return "overcast skies", "घने बादल हैं"
    if code in (45, 48):
        return "fog", "कोहरा है"
    if code in (51, 53, 55, 56, 57):
        return "drizzle", "बूंदाबांदी है"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "rain", "बारिश है"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow", "बर्फ़बारी है"
    if code in (95, 96, 99):
        return "thunderstorms", "गरज के साथ तूफ़ान है"
    return "", ""


@lru_cache(maxsize=160)
def _observation(lat, lon, bucket):
    return fetch_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "timezone": "auto",
        },
    )


@lru_cache(maxsize=128)
def zone_info(name):
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+){0,3}", name)
        or ".." in name
    ):
        raise ValueError("Invalid time zone")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        # A stock Windows Python may have no IANA database. The small TZif
        # archive contains data only and is never extracted to the filesystem.
        with zipfile.ZipFile(Path(__file__).with_name("zones.zip")) as archive:
            try:
                data = archive.read(name)
            except KeyError:
                raise ZoneInfoNotFoundError(name) from None
        return ZoneInfo.from_file(BytesIO(data), key=name)


@lru_cache(maxsize=1)
def zone_names():
    from zoneinfo import available_timezones

    with zipfile.ZipFile(Path(__file__).with_name("zones.zip")) as archive:
        return {n.casefold(): n for n in set(archive.namelist()) | available_timezones()}


def clock(zone, name, lang, date=False, now=None):
    z = zone_info(zone)
    hi_name = HI_CITY.get(name, name)
    dt = (now or datetime.now(timezone.utc)).astimezone(z)
    if date:
        val = dt.strftime("%A, %d %B %Y")
        hi = f"{dt.day} {'जनवरी फरवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर'.split()[dt.month - 1]} {dt.year}"
        return reply(f"The date in {name} is {val}.", f"{hi_name} में आज {hi} है।", lang, zone=zone)
    hhmm = dt.strftime("%I:%M %p").lstrip("0")
    hi_hour = dt.hour % 12 or 12
    part = (
        "सुबह"
        if 5 <= dt.hour < 12
        else "दोपहर"
        if 12 <= dt.hour < 17
        else "शाम"
        if 17 <= dt.hour < 21
        else "रात"
    )
    hi_min = f" बजकर {dt.minute} मिनट" if dt.minute else " बजे"
    return reply(
        f"It is {hhmm} in {name}.", f"{hi_name} में अभी {part} {hi_hour}{hi_min} हैं।", lang, zone=zone
    )


def conditions(loc, lang, now=None):
    name, country, _, lat, lon = loc
    payload = _observation(lat, lon, int(time.monotonic() // 240))
    obs = payload["current"]
    val = round(float(obs["temperature_2m"]))
    en, hi = weather_words(int(obs["weather_code"]))
    stamp = datetime.fromisoformat(obs["time"])
    timestamp = obs["time"].replace("T", " ")
    age = abs(
        (now or datetime.now(timezone.utc)).timestamp()
        - (
            stamp.replace(tzinfo=timezone.utc).timestamp()
            - int(payload.get("utc_offset_seconds", 0))
        )
    )
    label = name if not country or name == country else f"{name}, {country}"
    hi_label = HI_CITY.get(name, name)
    if country and name != country:
        hi_label += ", " + HI_COUNTRY.get(country, country)
    if age > 4 * 3600:
        return reply(
            f"I do not have a fresh reading for {label}. Open-Meteo’s last available report was {val} degrees Celsius at {timestamp}, local time.",
            f"{hi_label} का ताज़ा मौसम नहीं मिला। ओपन मीटियो की पिछली रिपोर्ट {timestamp}, स्थानीय समय की है: {val} डिग्री सेल्सियस।",
            lang,
            source="Open-Meteo",
            observed=obs["time"],
        )
    return reply(
        f"Open-Meteo reports {val} degrees Celsius in {label}"
        + (f", with {en}" if en else "")
        + ".",
        f"ओपन मीटियो के अनुसार {hi_label} में तापमान {val} डिग्री सेल्सियस है"
        + (f" और {hi}" if hi else "")
        + "।",
        lang,
        source="Open-Meteo",
        observed=obs["time"],
    )


NEWS_FEEDS = {
    "en": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "hi": "https://feeds.bbci.co.uk/hindi/rss.xml",
}


@lru_cache(maxsize=4)
def _bulletin(language, bucket):
    url = NEWS_FEEDS[language]
    req = Request(
        url, headers={"User-Agent": AGENT, "Accept": "application/rss+xml, application/xml"}
    )
    with build_opener(NoRedirect).open(req, timeout=6) as response:
        raw = response.read(350_001)
    if len(raw) > 350_000 or b"<!ENTITY" in raw.upper():
        raise ValueError("Invalid feed")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise ValueError("Unusable feed") from e
    items = []
    for entry in root.findall("./channel/item")[:40]:
        title = " ".join((entry.findtext("title") or "").split())[:210]
        pub = entry.findtext("pubDate")
        if title and pub:
            try:
                stamp = parsedate_to_datetime(pub)
            except (ValueError, TypeError):
                continue
            if stamp and stamp.tzinfo:
                items.append((stamp, title))
    return sorted(items, key=lambda p: p[0], reverse=True)[:2]


def headlines(lang, now=None):
    hi = lang.startswith("hi")
    items = _bulletin("hi" if hi else "en", int(time.monotonic() // 240))
    if not items:
        raise ValueError("No dated headlines")
    stamp = items[0][0]
    stale = ((now or datetime.now(timezone.utc)) - stamp).total_seconds() > 2 * 86400
    lead = (
        ("बीबीसी हिंदी की सुर्खियाँ: " if hi else "From BBC World News: ")
        if not stale
        else (
            f"यह ताज़ा बुलेटिन नहीं है। {stamp.date()} की सुर्खियाँ: "
            if hi
            else f"I do not have a fresh bulletin. These headlines are from {stamp.date()}: "
        )
    )
    titles = ("। " if hi else ". ").join(t.rstrip(" ।.") for _, t in items)
    return dict(
        text=lead + titles + ("।" if hi else "."),
        source="BBC News",
        lang=lang,
        published=stamp.isoformat(),
    )


def public_search(topic, lang, token):
    if not token:
        return reply(
            "General web search needs a private Brave Search key. Without a key you can ask for world headlines or search Wikipedia.",
            "पूरे वेब पर खोज के लिए निजी ब्रेव सर्च की चाहिए। बिना की के दुनिया की खबरें या विकिपीडिया पर कोई विषय पूछ सकते हैं।",
            lang,
        )
    url = "https://api.search.brave.com/res/v1/web/search"
    data = fetch_json(
        url,
        {
            "q": topic[:220],
            "count": 3,
            "text_decorations": "false",
            "safesearch": "moderate",
            "search_lang": "hi" if re.search("[\u0900-\u097f]", topic) else "en",
        },
        search_token=token,
    )

    def clean(s, n):
        text = " ".join(unescape(re.sub("<[^>]*>", "", str(s or ""))).split())
        return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"

    bits = []
    for r in data.get("web", {}).get("results", [])[:2]:
        # Speak the source domain. Never navigate to or fetch an arbitrary result.
        site = urlsplit(str(r.get("url", ""))).hostname or ""
        title = clean(r.get("title"), 92)
        desc = clean(r.get("description"), 150)
        if title and site:
            bits.append(f"{site.removeprefix('www.')}: {title}. {desc}")
    if not bits:
        return reply(
            "No public web result was found. Try a more specific subject.",
            "वेब पर कोई नतीजा नहीं मिला। विषय थोड़ा साफ़ करके पूछिए।",
            lang,
            source="Brave Search",
        )
    return reply(
        "Brave Search found: " + " ".join(bits),
        "ब्रेव सर्च पर ये नतीजे मिले: " + " ".join(bits),
        lang,
        source="Brave Search",
    )


def get_topic(q):
    q = re.sub(
        r"^(?:(?:please|ज़रा|कृपया)\s+)?(?:search(?:\s+wikipedia)?(?:\s+for)?|look\s*up|wikipedia(?:\s+(?:par|pe|पर))?|tell me about|who (?:is|was|are)|what (?:is|was|are)|explain|बताओ|विकिपीडिया(?:\s+पर)?|मुझे)\s+",
        "",
        q,
        flags=re.I,
    )
    return re.sub(
        r"\s+(?:(?:ke|के)\s+(?:baare|bare|बारे)\s+(?:mein|me|में)(?:\s+(?:batao|बताओ|बताइए|बताइये))?|(?:kya|kaun|क्या|कौन)\s+(?:hai|hain|है|हैं)|(?:dhundo|खोजो|ढूँढो|ढूंढो))$",
        "",
        q,
        flags=re.I,
    ).strip(" ?!.।")[:180]


def wiki(topic, lang):
    langs = (
        ("hi", "en") if lang.startswith("hi") and re.search(r"[\u0900-\u097f]", topic) else ("en",)
    )
    for db in langs:
        params = {
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "generator": "search",
            "gsrsearch": topic,
            "gsrlimit": 2,
            "gsrnamespace": 0,
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "exsentences": 2,
        }
        data = fetch_json(f"https://{db}.wikipedia.org/w/api.php", params)
        for row in sorted(data.get("query", {}).get("pages", []), key=lambda r: r.get("index", 99)):
            text = " ".join(str(row.get("extract", "")).split())
            if text:
                # Speech should stop at a word, preferably a sentence boundary.
                if len(text) > 530:
                    cut = text[:525].rsplit(" ", 1)[0]
                    end = max(cut.rfind(". "), cut.rfind("। "))
                    text = cut[: end + 1] if end > 190 else cut + "…"
                return dict(
                    text=("विकिपीडिया के अनुसार, " if db == "hi" else "According to Wikipedia, ")
                    + text,
                    lang="hi-IN" if db == "hi" else "en-IN",
                    source="Wikipedia",
                    article=str(row.get("title", ""))[:160],
                )
    return reply(
        "I could not find a clear encyclopedia entry. Try the name of the person, place or subject.",
        "विकिपीडिया पर साफ़ जवाब नहीं मिला। व्यक्ति, जगह या विषय का नाम फिर से बोलिए।",
        lang,
        source="Wikipedia",
    )


def ask_provider(q, lang, history, key, model):
    messages = [
        {
            "role": "system",
            "content": "You are JARVIS, a calm, precise personal voice assistant. Answer in "
            + ("natural Hindi" if lang.startswith("hi") else "English")
            + ". Answer in two to four short spoken sentences. No markdown. You have no tools: never claim to perform actions, browse, or have fresh facts. For live weather or time suggest the built-in city command. Be honest if you do not know.",
        }
    ]
    for turn in (history or [])[-4:]:
        if (
            isinstance(turn, dict)
            and turn.get("role") in ("user", "assistant")
            and isinstance(turn.get("content"), str)
        ):
            messages.append({"role": turn["role"], "content": turn["content"][:440]})
    messages.append({"role": "user", "content": q})
    data = fetch_json(
        "https://openrouter.ai/api/v1/chat/completions",
        key=key,
        body={"model": model, "messages": messages, "max_tokens": 200, "temperature": 0.45},
    )
    text = " ".join(data["choices"][0]["message"]["content"].split())[:1050]
    if not text:
        raise ValueError("Empty answer")
    return dict(text=text, lang=lang, source="OpenRouter")


def answer(
    query,
    language="hi-IN",
    zone="UTC",
    *,
    pending="",
    history=None,
    key="",
    search_key="",
    model="openrouter/auto",
    now=None,
):
    lang = "hi-IN" if str(language).startswith("hi") else "en-IN"
    if not isinstance(query, str) or not 0 < len(query.strip()) <= MAX_QUERY:
        return reply("Please use one short command.", "एक छोटा आदेश बोलिए।", lang)
    q = norm(strip_wake(query))
    w = WEATHER.search(q)
    t = TIME.search(q)
    d = DATE.search(q)
    source = "lookup"
    try:
        broad_news = (
            re.fullmatch(
                r"(?:(?:read|give me|tell me|what are|what's|play) )?(?:(?:the|latest|today's|today|top|world|global|international|news) )*(?:news|headlines)(?: today| please)?",
                q,
            )
            or re.fullmatch(
                r"(?:आज |आज की |दुनिया की |आज दुनिया की |ताज़ा |ताजा |आज की ताज़ा |विश्व |वैश्विक )*(?:खबरें|ख़बरें|समाचार|सुर्खियाँ|सुर्खियां|न्यूज़|न्यूज)(?: सुनाओ| बताओ)?",
                q,
            )
            or re.fullmatch(
                r"(?:aaj ki |duniya ki |taaza |taza )*(?:khabre[iy]?n?|khabar|samachar|news)(?: sunao| batao)?",
                q,
            )
        )
        if broad_news:
            source = "BBC News"
            return headlines(lang, now)
        web = re.match(
            r"^(?:search (?:the )?(?:web|internet)(?: for)?|web search(?: for)?|(?:web|internet|वेब|इंटरनेट) (?:par|pe|पर))\s+(.+)$",
            q,
        )
        if web:
            source = "Brave Search"
            topic = re.sub(r"\s+(?:dhundo|khojo|खोजो|ढूँढो|ढूंढो)$", "", web[1])
            return public_search(topic, lang, search_key)
        if w or t or d or (pending == "weather" and q):
            pat = w or t or d
            city = location_hint(q, pat) if pat else q[:110]
            # IANA names can be used explicitly for time/date, never as URLs.
            if (
                (t or d)
                and city
                and "/" in city
                and re.fullmatch(r"[A-Za-z_+-]+(?:/[A-Za-z_+-]+){1,2}", city)
            ):
                match = zone_names().get(city.casefold())
                if match:
                    return clock(match, match.replace("_", " "), lang, bool(d), now)
            if not city:
                if w or pending == "weather":
                    return reply(
                        "Which city? Tap again and say its name.",
                        "किस शहर का मौसम? फिर टैप करके शहर का नाम बोलिए।",
                        lang,
                        follow="weather",
                    )
                try:
                    return clock(
                        str(zone)[:85],
                        str(zone).split("/")[-1].replace("_", " "),
                        lang,
                        bool(d),
                        now,
                    )
                except (ValueError, ZoneInfoNotFoundError):
                    return clock("UTC", "UTC", lang, bool(d), now)
            loc = place(city, "hi" if re.search("[\u0900-\u097f]", city) else "en")
            if not loc:
                return reply(
                    "I could not locate that city. Try its name followed by a comma and the country.",
                    "शहर नहीं मिला। शहर के नाम के साथ देश का नाम भी बताइए।",
                    lang,
                )
            if w or (not pat and pending == "weather"):
                source = "Open-Meteo"
                return conditions(loc, lang, now)
            return clock(loc[2], loc[0], lang, bool(d), now)
        if re.search(
            r"^(?:pay|transfer money|send money|delete files|run shell|execute command|payment karo|पैसे भेज|भुगतान कर)",
            q,
        ):
            return reply(
                "I can look up information, but I cannot make payments or control a device.",
                "मैं जानकारी ढूँढ सकता हूँ। भुगतान करना या किसी डिवाइस को नियंत्रित करना मेरे पास नहीं है।",
                lang,
            )
        if not q or q in {
            "help",
            "madad",
            "मदद",
            "commands",
            "कमांड",
            "hello",
            "हेलो",
            "नमस्ते",
            "hi",
            "namaste",
            "नमस्कार",
            "what can you do",
        }:
            return reply(
                "I am listening. Ask for the time in Tokyo, the weather in Delhi, or a Wikipedia topic. Tap once for each command.",
                "मैं तैयार हूँ। टोक्यो का समय, दिल्ली का मौसम या विकिपीडिया पर कोई विषय पूछिए। हर आदेश के लिए एक बार टैप कीजिए।",
                lang,
            )
        explicit = (
            bool(re.match(r"^(?:search|look\s*up|wikipedia|विकिपीडिया|खोजो)\b", q))
            or "विकिपीडिया" in q
        )
        if key and not explicit:
            source = "OpenRouter"
            return ask_provider(q, lang, history, key, model)
        topic = get_topic(q)
        if topic and (
            explicit
            or topic != q
            or (
                len(q.split()) <= 7
                and not re.match(
                    r"^(?:open |send |run |turn |delete |install |make |write |create |set |book |buy |खोल|भेज)",
                    q,
                )
            )
        ):
            source = "Wikipedia"
            return wiki(topic, lang)
        return reply(
            "This mode handles public facts, city time and weather. For example: search Wikipedia for the Moon. General conversation needs private AI setup.",
            "इस मोड में सार्वजनिक जानकारी, समय और मौसम पूछ सकते हैं। जैसे, चंद्रयान के बारे में बताओ। खुली बातचीत के लिए निजी ए आई सेटअप चाहिए।",
            lang,
        )
    except (
        HTTPError,
        URLError,
        OSError,
        TimeoutError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
        AttributeError,
        ZoneInfoNotFoundError,
    ):
        if source == "OpenRouter":
            return reply(
                "The private AI service is unavailable. Check the server key, model and balance. Time, weather and public lookups are separate.",
                "निजी ए आई सेवा से उत्तर नहीं मिला। सर्वर पर की, मॉडल और बैलेंस जाँचिए। समय और मौसम अलग सेवाएँ हैं।",
                lang,
                source="unavailable",
            )
        return reply(
            "I could not verify that information right now. Please try again; I will not guess.",
            "अभी इस जानकारी की पुष्टि नहीं हो पाई। कृपया फिर कोशिश कीजिए।",
            lang,
            source="unavailable",
        )


class RateLimit:
    """Bounded in-memory window. Do not persist queries or addresses."""

    def __init__(self, maximum=18, seconds=60):
        self.maximum = maximum
        self.seconds = seconds
        self.hits = {}
        self.lock = threading.Lock()

    def allow(self, identity):
        now = time.monotonic()
        with self.lock:
            self.hits = {
                k: [t for t in v if t > now - self.seconds]
                for k, v in self.hits.items()
                if v and v[-1] > now - self.seconds
            }
            hits = self.hits.get(identity, [])
            if len(hits) >= self.maximum or (not hits and len(self.hits) >= 1000):
                return False
            self.hits[identity] = hits + [now]
            return True
