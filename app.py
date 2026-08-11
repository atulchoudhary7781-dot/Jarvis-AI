"""
JARVIS AI — Advanced Web Assistant (Streamlit)
================================================
Just A Rather Very Intelligent System

Clean Minimalist Interface - Like ChatGPT but JARVIS styled!
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
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "# J.A.R.V.I.S\n\n**Just A Rather Very Intelligent System**\n\nStark Industries AI Assistant"
    }
)

# ── Custom CSS (Minimalist Dark Theme) ────────────────────────────────────────
st.markdown("""
<style>
/* === GLOBAL RESET === */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

/* Main App Background - Pure Black */
.stApp {
    background: #000000 !important;
    min-height: 100vh;
}

/* Hide default Streamlit elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { 
    display: none !important;
}

/* Hide sidebar completely - we'll use custom nav */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Chat Messages Styling */
.stChatMessage {
    background: transparent !important;
    border: none !important;
    padding: 1rem 0;
}

.stChatMessage[data-testid="chatMessageUser"] {
    background: transparent !important;
    border: none !important;
}

.stChatMessage[data-testid="chatMessageUser"] .stMarkdown {
    background: #1a1a2e !important;
    padding: 1rem 1.5rem;
    border-radius: 18px;
    color: #ffffff;
}

.stChatMessage[data-testid="chatMessageAssistant"] {
    background: transparent !important;
    border: none !important;
}

.stChatMessage[data-testid="chatMessageAssistant"] .stMarkdown {
    background: #0d0d0d !important;
    padding: 1rem 1.5rem;
    border-radius: 18px;
    border: 1px solid #222;
    color: #e0e0e0;
}

/* Input Area Styling */
.stTextInput > div > div > input {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    border-radius: 25px !important;
    color: #fff !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}

/* Button Styling */
.stButton > button {
    border-radius: 20px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

/* Primary Button (Send/Action) */
.primary-btn {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50% !important;
    width: 40px !important;
    height: 40px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.primary-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

/* Secondary Button (Clear/Menu) */
.secondary-btn {
    background: transparent !important;
    color: #888 !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
}

.secondary-btn:hover {
    background: #1a1a1a !important;
    color: #fff !important;
    border-color: #444 !important;
}

/* Upgrade Button */
.upgrade-btn {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.25rem !important;
    font-weight: 600 !important;
}

.upgrade-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
}

/* Container for main content */
.main-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 1rem;
}

/* Welcome Text */
.welcome-text {
    text-align: center;
    color: #fff;
    font-size: 2rem;
    font-weight: 500;
    margin-top: 15vh;
    letter-spacing: -0.5px;
}

/* Floating Input Container */
.floating-input {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 800px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 30px;
    padding: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    z-index: 1000;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.floating-input:focus-within {
    border-color: #6366f1;
    box-shadow: 0 10px 40px rgba(99, 102, 241, 0.2);
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555;
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
    """Render top navigation bar - exactly like the image."""
    
    col_menu, col_title, col_spacer, col_clear, col_upgrade, col_avatar = st.columns([0.5, 2, 3, 1.5, 1.2, 0.5])
    
    with col_menu:
        if st.button("☰", key="menu_btn", help="Menu"):
            st.session_state.sidebar_open = not st.session_state.sidebar_open
    
    with col_title:
        st.markdown("""
        <div style="
            font-size: 1.1rem;
            font-weight: 600;
            color: #fff;
            padding-top: 0.5rem;
            letter-spacing: 1px;
        ">JARVIS</div>
        """, unsafe_allow_html=True)
    
    with col_spacer:
        st.empty()
    
    with col_clear:
        if st.button("🗑️ Clear Chat", key="clear_btn"):
            st.session_state.messages = []
            st.rerun()
    
    with col_upgrade:
        st.button("+ Upgrade", key="upgrade_btn", type="primary")
    
    with col_avatar:
        st.markdown("""
        <div style="
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            margin-top: 0.25rem;
        ">A</div>
        """, unsafe_allow_html=True)


def render_welcome_screen():
    """Render centered 'What can I Do For You?' message."""
    
    st.markdown(f"""
    <div class="main-container">
        <div class="welcome-text">
            What can I Do For You?
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_messages():
    """Render chat messages area."""
    
    chat_container = st.container(height=450)
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
                st.markdown(message["content"])


def render_floating_input():
    """Render floating bottom input bar - exactly like the image."""
    
    # Add some space at bottom for the fixed input
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
            submit = st.button("➤", key="send_btn", type="primary", help="Send")
    
    return user_input, submit


def render_sidebar_panel():
    """Render collapsible sidebar panel."""
    
    if st.session_state.sidebar_open:
        with st.container():
            st.markdown("""
            <div style="
                position: fixed;
                left: 0;
                top: 0;
                width: 280px;
                height: 100vh;
                background: #0a0a0a;
                border-right: 1px solid #222;
                padding: 1.5rem;
                z-index: 999;
            ">
                <h3 style="color: #fff; margin-bottom: 1.5rem;">✨ Features</h3>
                
                <div style="margin-bottom: 1rem;">
                    <button style="
                        width: 100%;
                        padding: 0.75rem;
                        background: #1a1a1a;
                        border: 1px solid #333;
                        border-radius: 10px;
                        color: #fff;
                        cursor: pointer;
                        text-align: left;
                    ">💬 New Chat</button>
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <button style="
                        width: 100%;
                        padding: 0.75rem;
                        background: transparent;
                        border: 1px solid transparent;
                        border-radius: 10px;
                        color: #888;
                        cursor: pointer;
                        text-align: left;
                    ">🔍 Web Search</button>
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <button style="
                        width: 100%;
                        padding: 0.75rem;
                        background: transparent;
                        border: 1px solid transparent;
                        border-radius: 10px;
                        color: #888;
                        cursor: pointer;
                        text-align: left;
                    ">💻 Code Mode</button>
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <button style="
                        width: 100%;
                        padding: 0.75rem;
                        background: transparent;
                        border: 1px solid transparent;
                        border-radius: 10px;
                        color: #888;
                        cursor: pointer;
                        text-align: left;
                    ">🧠 AI Models</button>
                </div>
                
                <div style="position: absolute; bottom: 1.5rem; left: 1.5rem; right: 1.5rem;">
                    <hr style="border-color: #222; margin: 1rem 0;">
                    <p style="color: #555; font-size: 0.85rem;">J.A.R.V.I.S v2.0</p>
                    <p style="color: #444; font-size: 0.75rem;">Stark Industries</p>
                </div>
            </div>
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
    st.divider()
    
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
        with st.spinner("JARVIS is processing..."):
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
