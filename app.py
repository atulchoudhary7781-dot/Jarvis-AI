"""Streamlit entrypoint for the existing Jarvis-AI repository.

The frontend is a stable keyed, bidirectional component: no nested page reload
on a voice reply. Only the canvas is visible. The parent handles public lookups
and authenticated, optionally paid, conversation; no secrets go into the frame.
"""

import os
import re
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from hologram.skills import MAX_QUERY, RateLimit, answer, reply

st.set_page_config(
    page_title="J.A.R.V.I.S.",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a Bug": None, "About": None},
)
st.html("""<style>
html,body,#root,[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#020305!important;overflow:hidden!important}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],#MainMenu,footer{display:none!important}
[data-testid="stMainBlockContainer"],.block-container{margin:0!important;padding:0!important;max-width:none!important;width:100%!important;height:100dvh}
[data-testid="stVerticalBlock"]{gap:0!important}iframe[title*="amber_core"],[data-testid="stCustomComponentV1"] iframe{position:fixed!important;inset:0!important;display:block;z-index:2;width:100vw!important;height:100vh!important;height:100dvh!important;border:0!important;background:#020305!important}
</style>""")


def setting(key, default=""):
    if key in os.environ:
        return os.environ[key]
    try:
        return st.secrets.get(key, default)
    except (FileNotFoundError, KeyError):
        return default


@st.cache_resource
def public_limit():
    return RateLimit(70, 60)


component = components.declare_component(
    "amber_core", path=str(Path(__file__).parent / "hologram" / "ui")
)
owner = str(setting("OWNER_EMAIL", "")).strip().casefold()
auth = setting("auth", {}) if owner else {}
has_login = bool(
    auth
    and auth.get("client_id")
    and auth.get("server_metadata_url")
    and auth.get("cookie_secret")
    and auth.get("redirect_uri")
)
signed = False
verified = False
if owner and has_login:
    try:
        signed = bool(st.user.is_logged_in)
        verified = (
            signed
            and st.user.get("email_verified") is True
            and str(st.user.get("email", "")).casefold() == owner
        )
    except (AttributeError, KeyError, FileNotFoundError):
        pass
allowed = not owner or verified
gate = dict(ownerRequired=bool(owner), authorized=allowed, hasLogin=has_login, signedIn=signed)
req = component(
    contract="amber.v1",
    access=gate,
    result=st.session_state.get("amber_result"),
    key="amber-screen",
    default=None,
)
if isinstance(req, dict):
    rid = req.get("id")
    kind = req.get("kind")
    if (
        isinstance(rid, str)
        and re.fullmatch(r"[\w-]{1,80}", rid)
        and rid != st.session_state.get("amber_last")
    ):
        st.session_state.amber_last = rid
        if kind == "login" and owner and has_login and not signed:
            st.login()
        elif kind == "logout" and owner and has_login and signed:
            st.logout()
        elif kind == "command":
            lang = req.get("lang", "hi-IN")
            lang = "hi-IN" if isinstance(lang, str) and lang.startswith("hi") else "en-IN"
            if not allowed:
                r = reply(
                    "Only the signed-in owner can use this assistant.",
                    "केवल साइन इन किया हुआ मालिक इस असिस्टेंट को आदेश दे सकता है।",
                    lang,
                )
            elif (
                not isinstance(req.get("query"), str)
                or not 0 < len(req["query"].strip()) <= MAX_QUERY
            ):
                r = reply("Please use one short command.", "एक छोटा आदेश बोलिए।", lang)
            else:
                now = time.monotonic()
                hits = [t for t in st.session_state.get("amber_hits", []) if t > now - 60]
                if len(hits) >= 18 or not public_limit().allow("all"):
                    r = reply(
                        "Please wait a moment before the next command.",
                        "अगला आदेश देने से पहले थोड़ा रुकिए।",
                        lang,
                    )
                else:
                    st.session_state.amber_hits = hits + [now]
                    history = req.get("history", [])
                    history = history[-4:] if isinstance(history, list) else []
                    # Never spend the owner's key on anonymous public traffic.
                    key = setting("OPENROUTER_API_KEY", "") if verified else ""
                    r = answer(
                        req["query"],
                        lang,
                        req.get("zone", "UTC"),
                        pending=req.get("pending", ""),
                        history=history,
                        key=key,
                        search_key=setting("BRAVE_SEARCH_API_KEY", "") if verified else "",
                        model=setting("OPENROUTER_MODEL", "openrouter/auto"),
                    )
            st.session_state.amber_result = dict(r, id=rid)
            st.rerun()
