"""
JARVIS AI — Simple Working Version
===================================
"""

import os
import requests
import streamlit as st

# Page Config
st.set_page_config(
    page_title="JARVIS",
    page_icon="⚡",
    layout="wide"
)

# Simple CSS
st.markdown("""
<style>
.stApp {
    background-color: #000000;
}
[data-testid="stSidebar"] {
    background-color: #0a0a0a;
}
</style>
""", unsafe_allow_html=True)

# API Key
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("⚡ JARVIS")
    st.caption("Just A Rather Very Intelligent System")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.markdown("**Status:** 🟢 Online")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")

# Header
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    st.empty()
with col2:
    st.markdown("<h2 style='text-align:center; color:white;'>⚡ J A R V I S</h2>", unsafe_allow_html=True)
with col3:
    st.empty()

st.divider()

# Main Chat Area
if not st.session_state.messages:
    # Welcome Screen
    st.markdown("""
    <div style='text-align:center; padding:80px 20px;'>
        <h1 style='color:white; font-size:36px;'>What can I Do For You?</h1>
        <p style='color:#888; font-size:18px; margin-top:20px;'>Your personal AI assistant is ready to help!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Show Messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Input Area
user_input = st.chat_input("Ask JARVIS anything...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)
    
    # Get AI Response
    with st.spinner("⚡ JARVIS is thinking..."):
        if not API_KEY:
            response = """**⚠️ API Key Missing!**

Please add your OpenRouter API key:

1. Go to [OpenRouter](https://openrouter.ai/keys) and get a free key
2. In Streamlit Cloud → Settings → Secrets → Add:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```
3. Restart the app"""
        else:
            try:
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "meta-llama/llama-3.1-8b-instruct",
                    "messages": [
                        {"role": "system", "content": "You are JARVIS, Tony Stark's AI assistant. Use British wit, call user 'Sir', be helpful and slightly sarcastic."},
                        {"role": "user", "content": user_input}
                    ]
                }
                
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if res.status_code == 200:
                    response = res.json()["choices"][0]["message"]["content"]
                elif res.status_code == 401:
                    response = "❌ Invalid API Key! Please check your key in Streamlit Secrets."
                else:
                    response = f"⚠️ Error: {res.status_code}"
                    
            except Exception as e:
                response = f"❌ Error: {str(e)}"
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with st.chat_message("assistant"):
        st.write(response)
