"""
JARVIS AI — Premium Web Assistant (Streamlit)
================================================
Just A Rather Very Intelligent System
"""

# ════════════════════════════════════════════════════════════════════════════════
# IMPORTS & CONFIG
# ════════════════════════════════════════════════════════════════════════════════
import os
import requests
from datetime import datetime

import streamlit as st

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JARVIS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main Background */
.stApp {
    background-color: #000000;
}

/* Hide default elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { display: none; }

/* Hide sidebar */
[data-testid="stSidebar"] {
    display: none;
}

/* Chat Messages */
.stChatMessage {
    background: transparent !important;
    border: none !important;
    padding: 8px 0 !important;
}

/* User Message Bubble */
.stChatMessage[data-testid="chatMessageUser"] .stMarkdown {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    padding: 16px 20px !important;
    border-radius: 18px !important;
    border-bottom-right-radius: 4px !important;
}

/* Assistant Message Bubble */
.stChatMessage[data-testid="chatMessageAssistant"] .stMarkdown {
    background: rgba(255,255,255,0.05) !important;
    color: #e5e7eb !important;
    padding: 16px 20px !important;
    border-radius: 18px !important;
    border-bottom-left-radius: 4px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}

/* Input Field */
.stTextInput > div > div > input {
    background: #1a1a2e !important;
    border: 1px solid #333 !important;
    border-radius: 25px !important;
    color: white !important;
    font-size: 1rem !important;
    padding: 12px 20px !important;
}

.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 50% !important;
    width: 45px !important;
    height: 45px !important;
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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_messages" not in st.session_state:
    st.session_state.total_messages = 0


# ════════════════════════════════════════════════════════════════════════════════
# AI ENGINE FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════
def get_ai_response(user_message: str) -> str:
    """Get response from OpenRouter API."""
    
    if not API_KEY or API_KEY.strip() == "":
        return """**⚠️ API Key Required**

JARVIS needs an OpenRouter API key to function.

**Setup:**
1. Get free key at [OpenRouter](https://openrouter.ai/keys)
2. In Streamlit Cloud: Settings → Secrets → Add `OPENROUTER_API_KEY=your_key`
3. Restart the app"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis-ai.streamlit.app",
        "X-Title": "JARVIS AI"
    }
    
    system_prompt = """You are JARVIS (Just A Rather Very Intelligent System), Tony Stark's AI assistant.
- British wit, use "Sir" for user
- Slightly sarcastic but helpful
- Calm, precise, efficient responses
- Reference Stark Industries subtly"""

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
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 401:
            return "❌ **Invalid API Key** - Please check your OpenRouter key"
        elif response.status_code == 429:
            return "⏳ **Rate Limit** - Please wait a moment"
        else:
            return f"⚠️ Error: API status {response.status_code}"
            
    except Exception as e:
        return f"❌ Connection error: {str(e)}"


# ════════════════════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ════════════════════════════════════════════════════════════════════════════════

def render_header():
    """Render top header bar."""
    
    col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 3, 1.5, 1, 0.5])
    
    with col1:
        if st.button("☰"):
            pass
    
    with col2:
        st.markdown("**J A R V I S**")
    
    with col3:
        st.empty()
    
    with col4:
        if st.button("🗑️ Clear"):
            st.session_state.messages = []
            st.rerun()
    
    with col5:
        st.button("+ Upgrade")
    
    with col6:
        st.markdown("<div style='width:35px;height:35px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#ec4899);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;'>A</div>", unsafe_allow_html=True)


def render_welcome():
    """Render welcome screen when no messages."""
    
    st.markdown("---")
    
    # Center content
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 100px 20px;
        min-height: 60vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    ">
        <div style="
            font-size: 80px;
            margin-bottom: 30px;
            animation: float 3s ease-in-out infinite;
        ">⚡</div>
        
        <h1 style="
            font-size: 42px;
            font-weight: 700;
            color: white;
            margin-bottom: 15px;
            letter-spacing: -1px;
        ">What can I Do For You?</h1>
        
        <p style="
            font-size: 18px;
            color: #6b7280;
            max-width: 500px;
            line-height: 1.6;
            margin-bottom: 40px;
        ">
            Your personal AI assistant is ready to help.<br>
            Ask me anything — coding, analysis, or just chat!
        </p>
        
        <div style="
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 600px;
        ">
            <div style="
                background: rgba(99,102,241,0.1);
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 14px;
                padding: 18px 24px;
                text-align: left;
                width: 140px;
            ">
                <div style="font-size: 24px; margin-bottom: 8px;">💬</div>
                <div style="color: #e5e7eb; font-weight: 600; font-size: 14px;">New Chat</div>
                <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">Start fresh</div>
            </div>
            
            <div style="
                background: rgba(99,102,241,0.1);
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 14px;
                padding: 18px 24px;
                text-align: left;
                width: 140px;
            ">
                <div style="font-size: 24px; margin-bottom: 8px;">🔍</div>
                <div style="color: #e5e7eb; font-weight: 600; font-size: 14px;">Web Search</div>
                <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">Search internet</div>
            </div>
            
            <div style="
                background: rgba(99,102,241,0.1);
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 14px;
                padding: 18px 24px;
                text-align: left;
                width: 140px;
            ">
                <div style="font-size: 24px; margin-bottom: 8px;">💻</div>
                <div style="color: #e5e7eb; font-weight: 600; font-size: 14px;">Code Help</div>
                <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">Write code</div>
            </div>
            
            <div style="
                background: rgba(99,102,241,0.1);
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 14px;
                padding: 18px 24px;
                text-align: left;
                width: 140px;
            ">
                <div style="font-size: 24px; margin-bottom: 8px;">🧠</div>
                <div style="color: #e5e7eb; font-weight: 600; font-size: 14px;">AI Models</div>
                <div style="color: #6b7280; font-size: 12px; margin-top: 4px;">Switch engine</div>
            </div>
        </div>
    </div>
    
    <style>
    @keyframes float {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-10px); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def render_chat():
    """Render chat messages."""
    
    # Chat container
    chat_container = st.container(height=450)
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
                st.markdown(message["content"])


def render_input():
    """Render input area at bottom."""
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Input form
    with st.form("chat_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([0.5, 6, 0.5, 0.5])
        
        with c1:
            st.button("+")
        
        with c2:
            user_input = st.text_input(
                "Ask anything...",
                placeholder="Ask anything...",
                label_visibility="collapsed"
            )
        
        with c3:
            st.button("🎤")
        
        with c4:
            submit = st.button("➤", type="primary")
    
    return user_input, submit


# ════════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════════════

def main():
    # Header
    render_header()
    
    # Divider
    st.divider()
    
    # Main Content
    if not st.session_state.messages:
        render_welcome()
    else:
        render_chat()
    
    # Input Area
    user_input, submit = render_input()
    
    # Handle submission
    if submit and user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response
        with st.spinner("⚡ JARVIS is thinking..."):
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
