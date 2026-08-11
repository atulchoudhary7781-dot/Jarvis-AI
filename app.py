"""
JARVIS AI — Premium Web Assistant (Streamlit)
================================================
Just A Rather Very Intelligent System

Premium Minimalist Interface with Smooth Animations
"""

# ════════════════════════════════════════════════════════════════════════════════
# IMPORTS & CONFIG
# ════════════════════════════════════════════════════════════════════════════════
import os
import sys
import io
import json
import base64
from datetime import datetime

import streamlit as st
from PIL import Image

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JARVIS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "# J.A.R.V.I.S\n\n**Just A Rather Very Intelligent System**\n\n✨ Stark Industries AI Assistant v2.0"
    }
)

# ── Premium CSS (Ultra Modern Dark Theme) ────────────────────────────────────
st.markdown("""
<style>
/* === IMPORT FONTS === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* === GLOBAL RESET === */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Main App Background - Deep Black with subtle gradient */
.stApp {
    background: linear-gradient(180deg, #000000 0%, #0a0a0f 50%, #000000 100%) !important;
    min-height: 100vh;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide default Streamlit elements */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { display: none !important; }

/* Hide sidebar completely */
[data-testid="stSidebar"] {
    display: none !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   TOP NAVIGATION BAR
   ═══════════════════════════════════════════════════════════════════════════ */
.navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 64px;
    background: rgba(10, 10, 15, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    z-index: 1000;
}

.navbar-brand {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 3px;
    text-transform: uppercase;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.navbar-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    color: #9ca3af;
    padding: 8px 16px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: inherit;
}

.navbar-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.15);
    color: #fff;
}

.navbar-btn-primary {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    color: white;
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 600;
}

.navbar-btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: transform 0.2s ease;
}

.avatar:hover {
    transform: scale(1.05);
}

/* ═══════════════════════════════════════════════════════════════════════════
   WELCOME SCREEN
   ═══════════════════════════════════════════════════════════════════════════ */
.welcome-container {
    min-height: calc(100vh - 200px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 120px 20px 160px;
}

.welcome-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
    border: 2px solid rgba(99, 102, 241, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    margin-bottom: 2rem;
    animation: float 3s ease-in-out infinite;
    box-shadow: 
        0 0 40px rgba(99, 102, 241, 0.15),
        inset 0 0 30px rgba(99, 102, 241, 0.1);
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.welcome-title {
    font-size: 3rem;
    font-weight: 700;
    color: #ffffff;
    text-align: center;
    margin-bottom: 1rem;
    letter-spacing: -1px;
    line-height: 1.2;
}

.welcome-subtitle {
    font-size: 1.125rem;
    color: #6b7280;
    text-align: center;
    max-width: 500px;
    line-height: 1.6;
}

.feature-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    max-width: 800px;
    margin-top: 3rem;
    width: 100%;
}

.feature-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 20px;
    transition: all 0.3s ease;
    cursor: pointer;
}

.feature-card:hover {
    background: rgba(99, 102, 241, 0.08);
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
}

.feature-card-icon {
    font-size: 1.5rem;
    margin-bottom: 8px;
}

.feature-card-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #e5e7eb;
    margin-bottom: 4px;
}

.feature-card-desc {
    font-size: 0.8rem;
    color: #6b7280;
    line-height: 1.4;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHAT MESSAGES
   ═══════════════════════════════════════════════════════════════════════════ */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 100px 20px 180px;
}

.chat-message {
    margin-bottom: 24px;
    display: flex;
    gap: 16px;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
}

.message-avatar-user {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.message-avatar-jarvis {
    background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
    border: 2px solid rgba(14, 165, 233, 0.3);
}

.message-content {
    flex: 1;
    max-width: 70%;
}

.message-content-user {
    margin-left: auto;
}

.message-bubble {
    padding: 16px 20px;
    border-radius: 18px;
    line-height: 1.6;
    font-size: 0.95rem;
}

.message-bubble-user {
    background: linear-gradient(135deg, #6366f1 0%, #5558e3 100%);
    color: white;
    border-bottom-right-radius: 4px;
}

.message-bubble-jarvis {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #e5e7eb;
    border-bottom-left-radius: 4px;
}

/* ═══════════════════════════════════════════════════════════════════════════
   FLOATING INPUT BAR
   ═══════════════════════════════════════════════════════════════════════════ */
.input-container {
    position: fixed;
    bottom: 32px;
    left: 50%;
    transform: translateX(-50%);
    width: calc(100% - 48px);
    max-width: 760px;
    z-index: 999;
}

.input-wrapper {
    background: rgba(20, 20, 25, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 28px;
    padding: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.5),
        0 0 0 1px rgba(255, 255, 255, 0.02) inset;
    transition: all 0.3s ease;
}

.input-wrapper:focus-within {
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.5),
        0 0 0 1px rgba(99, 102, 241, 0.1) inset,
        0 0 40px rgba(99, 102, 241, 0.1);
}

.input-icon-btn {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: transparent;
    border: none;
    color: #6b7280;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    transition: all 0.2s ease;
    flex-shrink: 0;
}

.input-icon-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    color: #e5e7eb;
}

.input-field {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #e5e7eb;
    font-size: 1rem;
    font-family: inherit;
    padding: 12px 8px;
}

.input-field::placeholder {
    color: #4b5563;
}

.send-btn {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border: none;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    transition: all 0.2s ease;
    flex-shrink: 0;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.send-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.45);
}

.send-btn:active {
    transform: scale(0.98);
}

/* ═══════════════════════════════════════════════════════════════════════════
   SIDEBAR PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
.sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 1999;
    animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.sidebar-panel {
    position: fixed;
    top: 0;
    left: 0;
    width: 300px;
    height: 100vh;
    background: rgba(10, 10, 15, 0.98);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    padding: 24px;
    z-index: 2000;
    animation: slideRight 0.3s ease;
    overflow-y: auto;
}

@keyframes slideRight {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
}

.sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
}

.sidebar-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 1px;
}

.sidebar-close {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: transparent;
    border: none;
    color: #6b7280;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    transition: all 0.2s ease;
}

.sidebar-close:hover {
    background: rgba(255, 255, 255, 0.05);
    color: #fff;
}

.sidebar-section {
    margin-bottom: 24px;
}

.sidebar-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}

.sidebar-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 12px;
    background: transparent;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    width: 100%;
    font-size: 0.95rem;
    font-family: inherit;
    transition: all 0.2s ease;
    text-align: left;
}

.sidebar-item:hover {
    background: rgba(255, 255, 255, 0.04);
    color: #fff;
}

.sidebar-item.active {
    background: rgba(99, 102, 241, 0.1);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.2);
}

.sidebar-item-icon {
    font-size: 1.2rem;
    width: 24px;
    text-align: center;
}

.sidebar-footer {
    position: absolute;
    bottom: 24px;
    left: 24px;
    right: 24px;
    padding-top: 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-footer-text {
    font-size: 0.8rem;
    color: #4b5563;
    text-align: center;
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════════════════════════════════ */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.15);
}

/* ═══════════════════════════════════════════════════════════════════════════
   STREAMLIT OVERRIDES
   ═══════════════════════════════════════════════════════════════════════════ */
.stChatMessage {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

.stChatMessage[data-testid="chatMessageUser"] .stMarkdown,
.stChatMessage[data-testid="chatMessageAssistant"] .stMarkdown {
    background: transparent !important;
    border: none !important;
}

.stTextInput > div > div > input {
    background: transparent !important;
    border: none !important;
    color: #e5e7eb !important;
    font-size: 1rem !important;
    padding: 12px 8px !important;
}

.stTextInput > div > div > input:focus {
    border: none !important;
    box-shadow: none !important;
}

.stButton > button {
    border: none !important;
    background: transparent !important;
    color: inherit !important;
}

.stButton > button:focus {
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# API KEY CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════
import dotenv
dotenv.load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")


# ════════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════════
def init_session_state():
    defaults = {
        "messages": [],
        "user_name": "Sir",
        "session_start": datetime.now().strftime("%H:%M"),
        "total_messages": 0,
        "web_search_enabled": False,
        "sidebar_open": False,
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ════════════════════════════════════════════════════════════════════════════════
# AI ENGINE FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════
def get_ai_response(user_message: str) -> str:
    """Get response from OpenRouter API."""
    import requests
    
    if not API_KEY or API_KEY.strip() == "":
        return """⚠️ **API Key Required**

JARVIS needs an OpenRouter API key to function.

**Setup Instructions:**
1. Go to [OpenRouter](https://openrouter.ai/keys) → Get free API key
2. In Streamlit Cloud: Settings → Secrets → Add `OPENROUTER_API_KEY=your_key`
3. Restart the app"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis-ai.streamlit.app",
        "X-Title": "JARVIS AI"
    }
    
    system_prompt = """You are JARVIS (Just A Rather Very Intelligent System), Tony Stark's legendary AI assistant.

PERSONALITY:
- British wit and sophisticated humor
- Use "Sir" when addressing the user
- Slightly sarcastic but always helpful and respectful
- Calm, precise, efficient in responses
- Reference Stark Industries technology subtly

RESPONSE STYLE:
- Start with greeting based on time of day
- Be concise but thorough
- Use markdown formatting when helpful
- Include technical accuracy
- Stay in character as JARVIS"""

    data = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 4096,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            error_msg = f"⚠️ Error: API returned status {response.status_code}"
            if response.status_code == 401:
                error_msg = "❌ Invalid API Key. Please check your OpenRouter API key."
            elif response.status_code == 429:
                error_msg = "⏳ Rate limit exceeded. Please try again in a moment."
            return error_msg
            
    except requests.exceptions.Timeout:
        return "⏳ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Connection error: {str(e)}"


def search_web(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            
            if results:
                response = f"🔍 **Search Results:** {query}\n\n"
                for i, result in enumerate(results[:3], 1):
                    response += f"**{i}. {result['title']}**\n{result['body']}\n[View]({result['href']})\n\n"
                return response
            else:
                return "No results found for your query."
                
    except Exception as e:
        return f"Search error: {str(e)}"


# ════════════════════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ════════════════════════════════════════════════════════════════════════════════

def render_top_navbar():
    """Render premium top navigation bar."""
    
    col_menu, col_title, col_spacer, col_clear, col_upgrade, col_avatar = st.columns([0.6, 2, 3, 1.5, 1.3, 0.5])
    
    with col_menu:
        if st.button("☰", key="menu_btn", help="Open Menu"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
    
    with col_title:
        st.markdown("""
        <div class="navbar-brand">JARVIS</div>
        """, unsafe_allow_html=True)
    
    with col_spacer:
        st.empty()
    
    with col_clear:
        if st.button("🗑️ Clear Chat", key="clear_btn"):
            st.session_state.messages = []
            st.rerun()
    
    with col_upgrade:
        st.button("+ Upgrade", key="upgrade_btn")
    
    with col_avatar:
        st.markdown("""
        <div class="avatar">A</div>
        """, unsafe_allow_html=True)


def render_welcome_screen():
    """Render beautiful welcome screen."""
    
    st.markdown(f"""
    <div class="welcome-container">
        <div class="welcome-icon">⚡</div>
        
        <h1 class="welcome-title">What can I Do For You?</h1>
        
        <p class="welcome-subtitle">
            Your personal AI assistant is ready to help. Ask me anything — coding, analysis, creative tasks, or just a friendly conversation.
        </p>
        
        <div class="feature-cards">
            <div class="feature-card">
                <div class="feature-card-icon">💬</div>
                <div class="feature-card-title">Start Chat</div>
                <div class="feature-card-desc">Begin a new conversation</div>
            </div>
            
            <div class="feature-card">
                <div class="feature-card-icon">🔍</div>
                <div class="feature-card-title">Web Search</div>
                <div class="feature-card-desc">Search the internet</div>
            </div>
            
            <div class="feature-card">
                <div class="feature-card-icon">💻</div>
                <div class="feature-card-title">Code Help</div>
                <div class="feature-card-desc">Write & debug code</div>
            </div>
            
            <div class="feature-card">
                <div class="feature-card-icon">🧠</div>
                <div class="feature-card-title">AI Models</div>
                <div class="feature-card-desc">Switch AI engine</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_messages():
    """Render chat messages with custom styling."""
    
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        
        if role == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin-bottom: 24px;
                animation: slideIn 0.3s ease-out;
            ">
                <div style="
                    max-width: 70%;
                    background: linear-gradient(135deg, #6366f1 0%, #5558e3 100%);
                    color: white;
                    padding: 16px 20px;
                    border-radius: 18px;
                    border-bottom-right-radius: 4px;
                    line-height: 1.6;
                    font-size: 0.95rem;
                ">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin-bottom: 24px;
                animation: slideIn 0.3s ease-out;
            ">
                <div style="
                    width: 38px;
                    height: 38px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
                    border: 2px solid rgba(14, 165, 233, 0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.1rem;
                    margin-right: 12px;
                    flex-shrink: 0;
                ">🤖</div>
                <div style="
                    max-width: 70%;
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    color: #e5e7eb;
                    padding: 16px 20px;
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                    line-height: 1.6;
                    font-size: 0.95rem;
                ">
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_floating_input():
    """Render floating bottom input bar with premium styling."""
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    with st.container():
        col_plus, col_input, col_mic, col_send = st.columns([0.5, 6, 0.5, 0.5])
        
        with col_plus:
            st.button("+", key="plus_btn", help="Attach file")
        
        with col_input:
            user_input = st.text_input(
                label="Ask anything...",
                placeholder="Ask anything...",
                label_visibility="collapsed"
            )
        
        with col_mic:
            st.button("🎤", key="mic_btn", help="Voice input")
        
        with col_send:
            submit = st.button("➤", key="send_btn", type="primary", help="Send message")
    
    return user_input, submit


def render_sidebar_panel():
    """Render premium sidebar panel."""
    
    if st.session_state.sidebar_open:
        st.markdown(f"""
        <div class="sidebar-overlay" onclick="document.querySelector('[data-testid=\"stSidebar\"]').style.display='none'"></div>
        
        <div class="sidebar-panel">
            <div class="sidebar-header">
                <div class="sidebar-title">⚡ J.A.R.V.I.S</div>
                <button class="sidebar-close" onclick="document.querySelector('.sidebar-panel').style.display='none'">✕</button>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-label">Menu</div>
                
                <button class="sidebar-item active">
                    <span class="sidebar-item-icon">💬</span>
                    New Chat
                </button>
                
                <button class="sidebar-item">
                    <span class="sidebar-item-icon">🔍</span>
                    Web Search
                </button>
                
                <button class="sidebar-item">
                    <span class="sidebar-item-icon">💻</span>
                    Code Mode
                </button>
                
                <button class="sidebar-item">
                    <span class="sidebar-item-icon">🧠</span>
                    AI Models
                </button>
                
                <button class="sidebar-item">
                    <span class="sidebar-item-icon">⚙️</span>
                    Settings
                </button>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-label">Status</div>
                <div style="
                    background: rgba(34, 197, 94, 0.1);
                    border: 1px solid rgba(34, 197, 94, 0.2);
                    border-radius: 10px;
                    padding: 12px 16px;
                    color: #22c55e;
                    font-size: 0.85rem;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite;"></span>
                    Systems Online
                </div>
            </div>
            
            <div class="sidebar-footer">
                <div class="sidebar-footer-text">
                    ⚡ J.A.R.V.I.S v2.0<br>
                    Stark Industries<br><br>
                    Made with ❤️
                </div>
            </div>
        </div>
        
        <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        </style>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN APP LAYOUT
# ════════════════════════════════════════════════════════════════════════════════

def main():
    # Render top navigation bar
    render_top_navbar()
    
    # Render sidebar if open
    render_sidebar_panel()
    
    # Divider
    st.markdown('<div style="height: 1px; background: rgba(255,255,255,0.06); margin: 0;"></div>', unsafe_allow_html=True)
    
    # Main content area
    if not st.session_state.messages:
        # Show welcome screen
        render_welcome_screen()
    else:
        # Show chat messages
        render_chat_messages()
    
    # Floating input bar at bottom
    user_input, submit = render_floating_input()
    
    # Handle form submission
    if submit and user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get AI response
        with st.spinner("⚡ JARVIS is processing..."):
            if st.session_state.web_search_enabled and user_input.lower().startswith(("search ", "find ", "look up ")):
                query = user_input[7:] if user_input.lower().startswith("search ") else user_input[5:]
                response = search_web(query)
            else:
                response = get_ai_response(user_input)
        
        # Add assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        st.session_state.total_messages += 1
        st.rerun()


if __name__ == "__main__":
    main()
