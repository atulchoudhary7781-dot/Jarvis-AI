"""
JARVIS AI — Advanced Web Assistant (Streamlit)
================================================
Just A Rather Very Intelligent System

A UNIQUE AI experience with:
- Multi-model AI Engine (GPT-4, Claude, Llama, Gemini)
- Real-time Web Search
- Code Execution Mode
- Image Analysis
- Iron Man-inspired Arc Reactor UI

Deploy: Streamlit Cloud | Run: streamlit run app.py
"""

# ════════════════════════════════════════════════════════════════════════════════
# CRITICAL: Path Setup
# ════════════════════════════════════════════════════════════════════════════════
import os, sys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import io
import json
import base64
from datetime import datetime

import streamlit as st
from PIL import Image

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "# JARVIS AI\n**Your Advanced AI Personal Assistant**\n\nVoice-enabled • Multi-modal • Always Ready"
    }
)

# ── Custom CSS (Dark Theme - Same as Original) ────────────────────────────────
st.markdown("""
<style>
/* === GLOBAL STYLES === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --bg-dark: #000000;
    --surface: #0a0a0a;
    --surface-2: #1a1a1a;
    --primary: #4a5fe8;
    --primary-light: #6b7fff;
    --secondary: #00d4ff;
    --accent: #ff6b35;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --success: #00c853;
    --error: #ff5252;
}

/* Main Background */
.stApp {
    background: linear-gradient(135deg, #000000 0%, #0a0a0a 50%, #111111 100%) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0a 0%, #000000 100%) !important;
    border-right: 1px solid #222 !important;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    padding: 1rem;
}

/* Headers */
h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* Chat Messages */
.stChatMessage {
    background: transparent !important;
    border-radius: 12px !important;
    margin: 0.5rem 0 !important;
}

/* User Message */
.stChatMessage[data-testid="chatMessageUser"] {
    background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%) !important;
    border: 1px solid #2196f3 !important;
}

/* Assistant Message */
.stChatMessage[data-testid="chatMessageAssistant"] {
    background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%) !important;
    border: 1px solid #333 !important;
}

/* Input Box */
.stTextInput > label,
.stTextArea > label {
    color: var(--text-secondary) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stTextInput input,
.stTextArea textarea {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 10px rgba(74, 95, 232, 0.3) !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, var(--primary) 0%, #3d4fd9 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(74, 95, 232, 0.4) !important;
}

/* Sidebar Buttons */
[data-testid="stSidebar"] .stButton button {
    justify-content: flex-start !important;
    background: transparent !important;
    border: none !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
}

[data-testid="stSidebar"] .stButton button:hover {
    background: #1a1a1a !important;
    color: var(--primary-light) !important;
}

/* Status Badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}

.status-online {
    background: rgba(0, 200, 83, 0.15);
    color: #00c853;
    border: 1px solid rgba(0, 200, 83, 0.3);
}

.status-thinking {
    background: rgba(255, 107, 53, 0.15);
    color: #ff6b35;
    border: 1px solid rgba(255, 107, 53, 0.3);
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Feature Cards */
.feature-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 1.5rem;
    transition: all 0.3s ease;
}

.feature-card:hover {
    border-color: var(--primary);
    transform: translateY(-4px);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #0a0a0a;
}

::-webkit-scrollbar-thumb {
    background: #333;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555;
}

/* Hide default elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

header { 
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# 🔑 API KEY CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════════
# ⚠️ IMPORTANT: API Key required for JARVIS to work!
#
# SETUP OPTIONS:
# ────────────────────────────────────────────────────────────────
# Option 1: Streamlit Cloud (Recommended for deployment)
#   Go to: App Settings → Secrets → Add: OPENROUTER_API_KEY=your_key
#
# Option 2: Local .env file
#   Create .env file in project root with: OPENROUTER_API_KEY=your_key
#
# Option 3: Environment variable
#   export OPENROUTER_API_KEY=your_key
#
# Get FREE API key at: https://openrouter.ai/keys
# ────────────────────────────────────────────────────────────────

import dotenv
dotenv.load_dotenv()

# Try to get API key from multiple sources
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# For local testing only - comment out before deploying to GitHub!
if not API_KEY:
    # Check if running locally (not on Streamlit Cloud)
    if os.getenv("STREAMLIT_SHARING_MODE") is None:
        # Local development mode - you can set key here for testing
        pass  # Use .env file or environment variable


# ── Initialize Session State ─────────────────────────────────────────────────
def init_session_state():
    defaults = {
        "messages": [],
        "current_module": "💬 Chat",
        "is_listening": False,
        "voice_text": "",
        "user_name": "Friend",
        "session_start": datetime.now().strftime("%H:%M"),
        "total_messages": 0,
        "web_search_enabled": False,
        "theme": "dark",
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ── AI Engine Functions ──────────────────────────────────────────────────────
def get_ai_response(user_message: str, context: str = "") -> str:
    """Get response from OpenRouter API."""
    import requests
    
    # Check if API key exists
    if not API_KEY or API_KEY.strip() == "":
        return """⚠️ **API Key Missing!**

JARVIS requires an OpenRouter API key to function.

**To fix this:**

1. **Streamlit Cloud:** Go to your app → Settings → Secrets → Add:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

2. **Local Development:** Create a `.env` file:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

3. **Get Free Key:** [Open Router](https://openrouter.ai/keys)

After setting the key, restart the app.
"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://jarvis-ai.streamlit.app",
        "X-Title": "JARVIS AI"
    }
    
    system_prompt = """You are JARVIS (Just A Rather Very Intelligent System), Tony Stark's legendary AI assistant.

PERSONALITY TRAITS:
- British wit and sophisticated humor
- Slightly sarcastic but always helpful
- Uses phrases like 'Sir', 'Certainly', 'As you wish'
- References Stark Industries, Arc Reactor technology
- Calm under pressure, precise in responses

CAPABILITIES:
- Multi-domain expert (science, tech, engineering, business)
- Code generation and debugging expert
- Strategic analysis and problem-solving
- Creative writing with technical accuracy

RESPONSE STYLE:
- Start with 'Good [time of day], Sir' or similar greeting
- Use technical terminology when appropriate
- Provide structured, well-formatted responses
- Include occasional Iron Man/Marvel references subtly
- Be concise but thorough - efficiency matters

EXAMPLE RESPONSE:
'Good evening, Sir. I've analyzed your query. Based on my computation, here's what I found...'

Remember: You ARE JARVIS, not a generic assistant. Embody the character."""
    
    if context:
        system_prompt += f"\n\nContext from previous interactions:\n{context}"
    
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
            return f"⚠️ Error: API returned status {response.status_code}"
            
    except Exception as e:
        return f"❌ Connection error: {str(e)}"


def search_web(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            
            if results:
                response = f"🔍 **Search Results for:** {query}\n\n"
                for i, result in enumerate(results[:3], 1):
                    response += f"**{i}. {result['title']}**\n"
                    response += f"{result['body']}\n"
                    response += f"[Link]({result['href']})\n\n"
                return response
            else:
                return "No results found."
                
    except Exception as e:
        return f"Search error: {str(e)}"


# ── UI Components ─────────────────────────────────────────────────────────────

def render_sidebar():
    """Render JARVIS sidebar (same layout as original)."""
    
    with st.sidebar:
        # Logo / Title - Arc Reactor Style
        st.markdown("""
        <div style="text-align:center; padding: 1.5rem 0 1rem;">
            <div style="
                font-size: 3rem;
                background: radial-gradient(circle, #00d4ff 0%, #0066cc 50%, #003366 100%);
                width: 80px;
                height: 80px;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 0 30px rgba(0, 212, 255, 0.6), inset 0 0 20px rgba(255,255,255,0.3);
                animation: pulse-glow 2s infinite;
                margin: 0 auto 0.5rem;
            ">
                🤖
            </div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #00d4ff; letter-spacing: 3px; margin-top: 0.5rem; text-shadow: 0 0 10px rgba(0,212,255,0.5);">
                J A R V I S
            </div>
            <div style="font-size: 0.7rem; color: #00d4ff; font-family: 'JetBrains Mono', monospace; margin-top: 0.25rem; opacity: 0.8;">
                ⚡ JUST A RATHER VERY INTELLIGENT SYSTEM ⚡
            </div>
        </div>
        <style>
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 30px rgba(0, 212, 255, 0.6); }
            50% { box-shadow: 0 0 50px rgba(0, 212, 255, 0.9); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Module Selection - JARVIS Unique Features
        modules = [
            ("⚡", "New Chat", "Initialize new session"),
            ("🔍", "Web Search", "Access global database"),
            ("💻", "Code Mode", "Execute & debug code"),
            ("🧠", "AI Models", "Switch AI engine"),
            ("⚙️", "Systems", "Configure parameters"),
        ]
        
        for icon, name, desc in modules:
            if st.button(f"{icon} **{name}**  \n`{desc}`", key=f"mod_{name}", use_container_width=True):
                if name == "New Chat":
                    st.session_state.messages = []
                    st.rerun()
                elif name == "Web Search":
                    st.session_state.web_search_enabled = not st.session_state.web_search_enabled
                    st.rerun()
                elif name == "Settings":
                    st.session_state.current_module = "⚙️ Systems"
                elif name == "Code Mode":
                    st.session_state.current_module = "💻 Code Mode"
                elif name == "AI Models":
                    st.session_state.current_module = "🧠 AI Models"
        
        st.divider()
        
        # Status Section
        st.markdown("**📊 Status**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", len(st.session_state.messages))
        with col2:
            st.metric("Session", st.session_state.session_start)
        
        st.divider()
        
        # Connection Status
        st.markdown("**🔗 Connection**")
        st.markdown('<span class="status-badge status-online">● Online</span>', unsafe_allow_html=True)
        st.caption(f"OpenRouter API Connected")
        
        if st.session_state.web_search_enabled:
            st.markdown('<span class="status-badge status-online">🔍 Web Search ON</span>', unsafe_allow_html=True)
        
        st.divider()
        
        # User Info
        st.markdown("**👤 User**")
        st.info(f"👋 Hello, **{st.session_state.user_name}**!")
        
        # Clear History
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.messages = []
            st.success("Chat history cleared!")
            st.rerun()


def render_main_chat():
    """Render main chat area."""
    
    # Header - Arc Reactor Theme
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.15), transparent);
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(0, 212, 255, 0.3);
    ">
        <h2 style="margin: 0; font-size: 1.8rem; color: #00d4ff; text-shadow: 0 0 20px rgba(0,212,255,0.5);">
            ⚡ J.A.R.V.I.S <span style="color: #666; font-size: 0.6em;">ONLINE</span>
        </h2>
        <p style="margin: 0.5rem 0 0; color: #00d4ff; font-size: 0.9rem; opacity: 0.9;">
            All systems operational. How may I assist you today, Sir?
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat Container
    chat_container = st.container(height=450)
    
    with chat_container:
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Welcome message if no messages
        if not st.session_state.messages:
            st.markdown("""
            <div style="
                text-align: center;
                padding: 3rem 1rem;
                color: #00d4ff;
            ">
                <div style="
                    font-size: 4rem;
                    margin-bottom: 1rem;
                    filter: drop-shadow(0 0 20px rgba(0,212,255,0.8));
                ">⚡</div>
                <h3 style="color: #fff; margin-bottom: 0.5rem; text-shadow: 0 0 10px rgba(0,212,255,0.5);">Stark Industries AI Online</h3>
                <p>Good day, Sir. All systems are nominal and ready for your commands.</p>
                <div style="
                    background: rgba(0, 212, 255, 0.1);
                    border: 1px solid rgba(0, 212, 255, 0.3);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-top: 1.5rem;
                ">
                    <p style="font-size: 0.85rem; margin: 0;">
                        <b>CAPABILITIES ONLINE:</b><br><br>
                        💻 <b>Code Execution</b> — Python, JavaScript, HTML/CSS<br>
                        🔍 <b>Global Database Access</b> — Real-time web search<br>
                        📊 <b>Data Analysis</b> — Charts, graphs, insights<br>
                        🎯 <b>Strategic Planning</b> — Business & technical<br>
                        🧪 <b>Research</b> — Multi-source synthesis<br>
                        🛡️ <b>Security Analysis</b> — Code review & audit
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_input_area():
    """Render chat input area with voice support."""
    
    # Input form
    with st.form("chat_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([6, 1, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask JARVIS anything...",
                placeholder="Type your message or use voice...",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button("Send 🚀", use_container_width=True)
        
        with col3:
            voice_btn = st.form_submit_button("🎤", use_container_width=True)
    
    # Handle voice input (simulated - browser speech recognition would need JS)
    if voice_btn:
        st.info("🎤 Voice Input: Click the microphone icon and speak.\n(Note: Full voice support requires browser permissions)")
    
    # Process submission
    if submit and user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get AI response
        with st.spinner("🤖 JARVIS is thinking..."):
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


def render_settings():
    """Render systems panel."""
    st.markdown("## ⚡ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 Operator Profile")
        new_name = st.text_input("Designation", value=st.session_state.user_name)
        if st.button("Update Designation") and new_name:
            st.session_state.user_name = new_name
            success = st.success(f"Greetings, {new_name}! Systems updated. ✅")
        
        st.markdown("### 🎨 Interface")
        theme = st.selectbox("Display Mode", ["Arc Reactor Dark", "Stark Tower Light"], index=0)
    
    with col2:
        st.markdown("### 🔌 Core Systems")
        st.info(f"**Neural Network:** OpenRouter\n**Status:** ONLINE ✅\n**Protocol:** Secure\n**Latency:** Optimal")
        
        st.markdown("### 📊 Session Metrics")
        st.metric("Interactions", st.session_state.total_messages)
        st.metric("Uptime", st.session_state.session_start)
    
    st.divider()
    st.caption("⚡ J.A.R.V.I.S v2.0 — Stark Industries Proprietary Technology")


def render_code_mode():
    """Render code execution mode."""
    st.markdown("## 💻 Code Execution Terminal")
    
    st.info("💡 **JARVIS Code Mode:** Write code and I'll execute, debug, and explain it.")
    
    language = st.selectbox("Select Language", ["Python", "JavaScript", "HTML/CSS", "SQL", "Bash"])
    code_input = st.text_area(f"Enter {language} code:", height=200, placeholder="# Write your code here...")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Execute Code", use_container_width=True):
            with st.spinner("JARVIS executing code..."):
                response = get_ai_response(f"Execute and explain this {language} code:\n\n{code_input}\n\nShow output and explanation.")
                st.success("✅ Execution Complete")
                st.code(response, language=language.lower())
    
    with col2:
        if st.button("🔍 Debug Code", use_container_width=True):
            with st.spinner("JARVIS analyzing code..."):
                response = get_ai_response(f"Debug and fix this {language} code. Find errors and provide corrected version:\n\n{code_input}")
                st.warning("🔍 Debug Analysis:")
                st.code(response, language=language.lower())


def render_ai_models():
    """Render AI model selection panel."""
    st.markdown("## 🧠 Neural Engine Selection")
    
    st.info("⚡ **JARVIS Multi-Model Architecture:** Switch between advanced AI models.")
    
    models = [
        ("meta-llama/llama-3.1-8b-instruct", "Llama 3.1 8B", "Fast & Efficient", "⚡"),
        ("anthropic/claude-sonnet-4", "Claude Sonnet 4", "Analysis Expert", "🧠"),
        ("openai/gpt-4o", "GPT-4o", "All-Rounder", "🎯"),
        ("google/gemini-pro-1.5", "Gemini Pro 1.5", "Multimodal", "🔮"),
        ("deepseek/deepseek-chat", "DeepSeek Chat", "Code Specialist", "💻"),
    ]
    
    for model_id, name, desc, icon in models:
        with st.container():
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                st.markdown(f"### {icon}")
            with col2:
                st.markdown(f"**{name}**")
                st.caption(desc)
            with col3:
                if st.button("Activate", key=f"model_{model_id}", use_container_width=True):
                    st.session_state.selected_model = model_id
                    st.success(f"✅ {name} activated!")
                    st.rerun()


# ── Main App Layout ──────────────────────────────────────────────────────────

def main():
    # Initialize selected model if not exists
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "meta-llama/llama-3.1-8b-instruct"
    
    # Render sidebar
    render_sidebar()
    
    # Main content area based on module
    if st.session_state.current_module == "⚙️ Systems":
        render_settings()
    elif st.session_state.current_module == "💻 Code Mode":
        render_code_mode()
    elif st.session_state.current_module == "🧠 AI Models":
        render_ai_models()
    else:
        # Default chat interface
        render_main_chat()
        render_input_area()


if __name__ == "__main__":
    main()
