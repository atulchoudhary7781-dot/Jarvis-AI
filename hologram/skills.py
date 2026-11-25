"""Read-only voice skills shared by the desktop, preview and Streamlit hosts.

No files, sessions, credentials or code from the legacy desktop installation are
loaded. Provider destinations are constants, never command parameters.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
import zipfile
import unicodedata
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

from .calculator import calculate
from .chat import TERMS
from .chat import engine as companion

MAX_QUERY = 360
AGENT = (
    "JarvisAmber/1.0 (https://github.com/atulchoudhary7781-dot/Jarvis-AI; read-only voice lookup)"
)
DESTINATIONS = {
    "https://geocoding-api.open-meteo.com/v1/search",
    "https://api.open-meteo.com/v1/forecast",
    "https://api.openweathermap.org/data/2.5/weather",
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
    yaar zara jara dost bhai do na dena me abhi filhaal फिलहाल ज़रा जरा यार भाई दोस्त ना देना could would much and ka kaa ke ki ko mein mai abhi aaj aj kya hai hain h batao bataiye bata batana
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
    endpoint = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "timezone": "auto",
    }
    try:
        return fetch_json(endpoint, params)
    except HTTPError as exc:
        if not 500 <= exc.code <= 599:
            raise  # Don't retry rate limits, bad requests or authentication errors.
    except (URLError, TimeoutError):
        pass
    # One bounded retry for a transient network failure; never fabricate data
    # or silently present a stale cached observation as current.
    return fetch_json(endpoint, params)


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
        return reply(
            f"The date in {name} is {val}.",
            f"{hi_name} में आज {hi} है।",
            lang,
            zone=zone,
            topic="date",
        )
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
        f"It is {hhmm} in {name}.",
        f"{hi_name} में अभी {part} {hi_hour}{hi_min} हैं।",
        lang,
        zone=zone,
        topic="time",
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
            topic="weather",
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
        topic="weather",
    )


def openweather_conditions(loc, lang, key, now=None):
    """Current-weather backup; call only after the shared quota is reserved."""
    if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9]{16,128}", key):
        raise ValueError("Invalid weather configuration")
    name, country, _, lat, lon = loc
    data = fetch_json("https://api.openweathermap.org/data/2.5/weather", {
        "lat": lat, "lon": lon, "units": "metric", "appid": key,
    })
    temp = float(data["main"]["temp"])
    stamp = float(data["dt"])
    if not (math.isfinite(temp) and -100 <= temp <= 65 and math.isfinite(stamp)):
        raise ValueError("Invalid weather measurement")
    current_stamp = (now or datetime.now(timezone.utc)).timestamp()
    if not 0 <= stamp <= current_stamp + 300:
        raise ValueError("Invalid weather timestamp")
    observed = datetime.fromtimestamp(stamp, timezone.utc)
    age = current_stamp - stamp
    label = name if not country or name == country else f"{name}, {country}"
    hi_label = HI_CITY.get(name, name)
    if country and name != country:
        hi_label += ", " + HI_COUNTRY.get(country, country)
    if age > 4 * 3600:
        return reply(
            f"I do not have a fresh reading for {label}. OpenWeather's last report was {round(temp)} degrees Celsius at {observed.strftime('%H:%M UTC')}.",
            f"{hi_label} का ताज़ा मौसम नहीं मिला। ओपन वेदर की पिछली रिपोर्ट {observed.strftime('%H:%M UTC')} की है: {round(temp)} डिग्री सेल्सियस।",
            lang, source="OpenWeather", observed=observed.isoformat(), topic="weather",
        )
    # Speak only well-defined, whitelisted weather groups, never arbitrary
    # provider text. If no reliable condition is provided, say temperature only.
    rows = data.get("weather")
    code = rows[0].get("id") if isinstance(rows, list) and rows and isinstance(rows[0], dict) else None
    if type(code) is not int:
        code = None
    wmo = (95 if code is not None and 200 <= code <= 299 else
           51 if code is not None and 300 <= code <= 399 else
           61 if code is not None and 500 <= code <= 599 else
           71 if code is not None and 600 <= code <= 699 else
           45 if code == 741 else 0 if code == 800 else
           1 if code in (801, 802) else 3 if code in (803, 804) else None)
    en, hi = weather_words(wmo) if wmo is not None else ("", "")
    return reply(
        f"OpenWeather reports {round(temp)} degrees Celsius in {label}" + (f", with {en}" if en else "") + ".",
        f"ओपन वेदर के अनुसार {hi_label} में तापमान {round(temp)} डिग्री सेल्सियस है" + (f" और {hi}" if hi else "") + "।",
        lang, source="OpenWeather", observed=observed.isoformat(), topic="weather",
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
        r"^(?:(?:please|ज़रा|कृपया)\s+)?(?:search(?:\s+wikipedia)?(?:\s+for)?|look\s*up|wikipedia\s+search(?:\s+for)?|wikipedia(?:\s+(?:par|pe|पर))?|tell me about|who (?:is|was|are)|what (?:is|was|are)|explain|बताओ|विकिपीडिया(?:\s+पर)?|मुझे)\s+",
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


def wiki_title_matches(topic, title):
    """Reject unrelated search hits instead of presenting them as answers.

    Conservative title matching favors a clear refusal over confident nonsense;
    aliases or paraphrases may require a more specific user query.
    """
    def words(text):
        text = unicodedata.normalize("NFKC", str(text)).casefold()
        chars = (c if c.isalnum() or unicodedata.category(c).startswith("M") else " " for c in text)
        return [w for w in "".join(chars).split() if len(w) > 1]
    stop = {"the", "a", "an", "of", "in", "on", "for", "is", "are", "was", "were", "who", "what"}
    wanted = [w for w in words(topic) if w not in stop]
    found = set(words(title))
    return bool(wanted) and all(word in found for word in wanted)



def capital_article_matches(topic, title, text):
    """Accept only a direct, present-tense capital statement from the right page.

    Search rankings alone can mistake capital punishment for capital cities.
    When the source does not clearly state the relation, return no answer.
    """
    match = re.fullmatch(r"(?:the\s+)?capital\s+of\s+(?:the\s+)?([\w\s'-]{1,80})", topic, re.I)
    if not match:
        return None  # Not a capital-city question.
    country = re.escape(match.group(1).strip())
    title = str(title).strip()
    text = " ".join(str(text).split())
    if not title or not text:
        return False
    direct_title = re.fullmatch(r"(?:the\s+)?capital\s+of\s+(?:the\s+)?" + country, title, re.I)
    if direct_title and re.search(
        r"\b(?:the\s+)?(?:current\s+)?capital(?:\s+city)?\s+of\s+(?:the\s+)?"
        + country + r"\s+is\s+(?:the\s+city\s+of\s+)?[\w]", text, re.I
    ):
        return True
    # A city page must begin by saying that that city is the country's capital.
    return bool(re.search(
        r"^" + re.escape(title) + r"(?:\s*\([^)]{0,180}\))?\s+is\s+the\s+capital"
        r"(?:\s+city|\s+and\s+(?:(?:the\s+)?(?:largest|most populous)|a)\s+city)?"
        r"\s+of\s+(?:the\s+)?" + country + r"(?![\w])", text, re.I
    ))


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
            "gsrlimit": 10 if re.fullmatch(r"(?:the\s+)?capital\s+of\s+(?:the\s+)?[\w\s'-]{1,80}", topic, re.I) else 5,
            "gsrnamespace": 0,
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "exsentences": 2,
        }
        data = fetch_json(f"https://{db}.wikipedia.org/w/api.php", params)
        for row in sorted(data.get("query", {}).get("pages", []), key=lambda r: r.get("index", 99)):
            text = " ".join(str(row.get("extract", "")).split())
            capital_match = capital_article_matches(topic, row.get("title", ""), text)
            # Capital queries need stronger evidence than shared title words.
            if text and (capital_match if capital_match is not None else wiki_title_matches(topic, row.get("title", ""))):
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


# Only exact country aliases are translated; do not send private conversation
# or guess an entity from a fuzzy Hindi phrase.
_CAPITAL_COUNTRIES_HI = {
    "नेपाल": "Nepal", "भारत": "India", "इंडिया": "India",
    "जापान": "Japan", "फ्रांस": "France", "फ्राँस": "France",
    "फ़्रांस": "France", "जर्मनी": "Germany", "ब्राज़ील": "Brazil",
    "ब्राजील": "Brazil", "ऑस्ट्रेलिया": "Australia", "सिंगापुर": "Singapore",
}


def hindi_capital(q, lang):
    match = re.fullmatch(
        r"(?:बताओ\s+)?([\u0900-\u097f]+)\s+की\s+राजधानी\s+(?:क्या\s+है|कौन\s+सी\s+है|बताओ|बताइए)", q
    )
    if not match or match.group(1) not in _CAPITAL_COUNTRIES_HI:
        return None
    country = _CAPITAL_COUNTRIES_HI[match.group(1)]
    result = wiki("capital of " + country, "en-IN")
    city_en = result.get("article") if result.get("article") in HI_CITY else None
    # Some verified pages are titled "Capital of Japan" rather than "Tokyo".
    # Translate only a known, exact city at the start of the direct statement.
    if not city_en and result.get("article"):
        direct = re.match(
            r"^According to Wikipedia,\s*(?:the\s+)?(?:current\s+)?capital(?:\s+city)?\s+of\s+(?:the\s+)?"
            + re.escape(country) + r"\s+is\s+(?:the\s+city\s+of\s+)?(.+)",
            result.get("text", ""), re.I,
        )
        if direct:
            city_en = next((name for name in sorted(HI_CITY, key=len, reverse=True)
                            if re.match(re.escape(name) + r"(?![\w])", direct.group(1), re.I)), None)
    if city_en:
        return reply(f"According to Wikipedia, the capital of {country} is {city_en}.",
                     f"विकिपीडिया के अनुसार, {match.group(1)} की राजधानी {HI_CITY[city_en]} है।",
                     lang, source="Wikipedia", article=result["article"])
    # wiki() only returns a sourced match or an honest no-result response.
    if result.get("article"):
        return result
    return reply("I could not verify that capital right now.",
                 "अभी राजधानी की पक्की जानकारी नहीं मिली।", lang, source="Wikipedia")


def india_independence(q, lang):
    # Stable historical fact; use only narrowly specified full questions.
    if not (re.fullmatch(r"(?:in )?what year did india (?:become independent|gain independence)", q)
            or re.fullmatch(r"when did india (?:become independent|gain independence)", q)
            or re.fullmatch(r"भारत (?:को )?(?:आज़ादी|आजादी|स्वतंत्रता) कब (?:मिली|प्राप्त हुई)", q)):
        return None
    return reply("India became independent on 15 August 1947.",
                 "भारत 15 अगस्त 1947 को स्वतंत्र हुआ।", lang, source="local")


def ask_provider(q, lang, history, key, model):
    messages = [
        {
            "role": "system",
            "content": "You are Jarvis, an AI voice companion. Speak like a thoughtful friend: respond to the specific thing said, offer a concrete idea when useful, and do not pretend to be human. Answer in "
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
    chat_terms=None,
    weather_fallback=None,
):
    lang = "hi-IN" if str(language).startswith("hi") else "en-IN"
    if not isinstance(query, str) or not 0 < len(query.strip()) <= MAX_QUERY:
        return reply("Please use one short command.", "एक छोटा आदेश बोलिए।", lang)
    q = norm(strip_wake(query))
    w = WEATHER.search(q)
    t = TIME.search(q)
    d = DATE.search(q)
    story = bool(
        re.match(
            r"^(?:i(?:'m|'ve|'d)? |we |my (?:friend|family|day|first|date) |today i |maine |aaj maine |मैंने |आज मैंने |हमने |मेरा दोस्त )",
            q,
        )
    )
    request = bool(
        re.search(
            r"(?:want to know|batao|बताओ|जानना|tell me|what time|weather (?:in|for)|time (?:in|for))",
            q,
        )
    )
    if story and not request:
        w = t = d = None
        pending = ""
    if (
        pending == "weather"
        and not (w or t or d)
        and (
            len(q.split()) > 5
            or len(q) > 60
            or re.search(
                r"[<@:/]|(?<!\w)(?:why|how|what|hello|help|you|i|क्यों|मुझे|तुम|मेरा|कैसे)(?!\w)", q
            )
        )
    ):
        pending = ""
    source = "lookup"
    weather_stage = ""
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
        handled, result = calculate(q)
        if handled:
            if result is None:
                return reply(
                    "I could not calculate that safely. Try a simple expression, such as 17 times 23.",
                    "मैं इसे गणना नहीं कर पाया। 17 गुणा 23 जैसा सरल सवाल पूछिए।",
                    lang, source="Calculator",
                )
            approximate = result.startswith("~")
            number = result.lstrip("~")
            return reply(
                ("The answer is approximately " if approximate else "The answer is ") + number + ".",
                ("जवाब लगभग " if approximate else "जवाब है ") + number + "।",
                lang, source="Calculator",
            )
        history_fact = india_independence(q, lang)
        if history_fact:
            return history_fact
        capital_fact = hindi_capital(q, lang)
        if capital_fact:
            return capital_fact
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
                        "Which city? Just say its name.",
                        "किस शहर का मौसम जानना चाहेंगे?",
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
            if w or (not pat and pending == "weather"):
                weather_stage = "geocoding"
            loc = place(city, "hi" if re.search("[\u0900-\u097f]", city) else "en")
            if not loc:
                return reply(
                    "I could not locate that city. Try its name followed by a comma and the country.",
                    "शहर नहीं मिला। शहर के नाम के साथ देश का नाम भी बताइए।",
                    lang,
                )
            if w or (not pat and pending == "weather"):
                source = "Open-Meteo"
                weather_stage = "forecast"
                try:
                    return conditions(loc, lang, now)
                except HTTPError as exc:
                    if exc.code != 429 or weather_fallback is None:
                        raise
                    # A 429 is not retried at Open-Meteo. The server-controlled
                    # backup enforces a shared quota before using a secret.
                    weather_stage = "backup"
                    return weather_fallback(loc, lang, now)
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
            if q in {"help", "commands", "madad", "मदद", "कमांड", "what can you do"}:
                return reply(
                    "We can chat, look something up, or make a shortcut together. What sounds good?",
                    "बात करें, कुछ पता लगाएँ या नया शॉर्टकट बनाएँ? आज क्या करने का मन है?",
                    lang,
                    source="Built-in chat",
                )
            return reply(
                "Hey! How has your day been?",
                "अरे, कैसे हो? आज का दिन कैसा रहा?",
                lang,
                source="Built-in chat",
            )
        explicit = (
            bool(re.match(r"^(?:search|look\s*up|wikipedia|विकिपीडिया|खोजो)\b", q))
            or "विकिपीडिया" in q
        )
        if key and not explicit:
            source = "OpenRouter"
            return ask_provider(q, lang, history, key, model)
        topic = get_topic(q)
        # Only clearly requested public facts go to an encyclopedia. Ordinary
        # personal conversation is never used as a third-party search query.
        factual = re.match(
            r"^(?:who (?:is|was|are)|what (?:is|was|are)|tell me about|explain) ", q
        ) or re.search(
            r" (?:ke|के) (?:baare|bare|बारे) (?:mein|me|में)| (?:kaun|kya|कौन|क्या) (?:hai|है)$", q
        )
        personal = re.search(
            r"(?<!\w)(?:my|me|your|our|i|you|we|मेरा|मेरी|मुझे|तुम|तुम्हारा|आप|mera|meri|tum)(?!\w)", q
        )
        if topic and (
            explicit
            or (factual and not personal)
            or (q.startswith("tell me about ") and not re.search(r"\b(?:my|your|our)\b", topic))
        ):
            source = "Wikipedia"
            return wiki(topic, lang)
        if os.environ.get("JARVIS_CHAT_MODEL") and chat_terms != TERMS:
            return reply(
                "For open chat I use Gemma. Its terms and use restrictions are at slash terms; press L to read them. Do you agree for this tab?",
                "खुली बातचीत के लिए जेम्मा की शर्तें लागू हैं। इन्हें स्लैश टर्म्स पर पढ़ सकते हो, या एल दबाओ। इस टैब के लिए मंज़ूर है?",
                lang,
                source="Chat terms",
                terms=TERMS,
            )
        generated = companion.respond(query, lang, history)
        if generated:
            return generated
        return reply(
            "I’m here. My open-ended chat is taking a break, but we can still play a riddle, try a creative prompt, or make a shortcut together.",
            "सुन रहा हूँ। अभी खुलकर बातचीत वाला हिस्सा उपलब्ध नहीं है। चलो पहेली खेलें, कोई नया आइडिया सोचें या शॉर्टकट बनाएँ?",
            lang,
            source="Built-in chat",
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
    ) as exc:
        if weather_stage:
            # Diagnostics intentionally exclude queries, locations, URLs,
            # IP addresses, exception messages and any credentials.
            if isinstance(exc, HTTPError):
                category = "http_" + str(exc.code) if 100 <= exc.code <= 599 else "http_error"
            elif isinstance(exc, TimeoutError):
                category = "timeout"
            elif isinstance(exc, URLError):
                category = "timeout" if isinstance(exc.reason, TimeoutError) else "network_error"
            elif isinstance(exc, OSError):
                category = "network_error"
            else:
                category = "invalid_response"
            logging.getLogger("jarvis.weather").warning(
                "Weather failure: stage=%s category=%s", weather_stage, category
            )
        if source == "OpenRouter":
            return reply(
                "The private AI service is unavailable. Check the server key, model and balance. Time, weather and public lookups are separate.",
                "निजी ए आई सेवा से उत्तर नहीं मिला। सर्वर पर की, मॉडल और बैलेंस जाँचिए। समय और मौसम अलग सेवाएँ हैं।",
                lang,
                source="unavailable",
            )
        return reply(
            "I could not verify that information right now. Please try again; I will not guess.",
            "अभी पक्की जानकारी नहीं मिली। थोड़ी देर में फिर देख लें?",
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
