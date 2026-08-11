# 🤖 JARVIS AI — Web Version

<div align="center">

# **J A R V I S**

**Advanced AI Personal Assistant — Now on Web!**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_red.svg)](https://i9fm8n3pz2wn67bkro5y2q.streamlit.app/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter_API-Multi_Model-orange?style=for-the-badge)](https://openrouter.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

> **JARVIS** is your personal AI assistant with web search, multi-model intelligence, and beautiful Iron Man-inspired UI — now accessible from any browser!

</div>

---

## ✨ Features

| Feature | Description | Status |
|---------|-------------|--------|
| 💬 **AI Chat** | Intelligent conversations with multiple AI models | ✅ Active |
| 🔍 **Web Search** | Real-time internet search via DuckDuckGo | ✅ Active |
| 🎨 **Dark Theme** | Beautiful Iron Man-inspired UI design | ✅ Active |
| 📱 **Responsive** | Works on desktop, tablet & mobile | ✅ Active |
| 🤖 **Multi-Model** | Switch between GPT, Claude, Llama & more | ✅ Active |
| 🖼️ **Image Gen** | AI image generation (coming soon) | 🔜 Planned |
| 🎤 **Voice Control** | Voice input/output (coming soon) | 🔜 Planned |

---

## 🚀 Live Demo

### 👉 **Try JARVIS NOW:** [https://i9fm8n3pz2wn67bkro5y2q.streamlit.app/](https://i9fm8n3pz2wn67bkro5y2q.streamlit.app/)

No installation required! Just open the link and start chatting with JARVIS.

---

## 🚀 Quick Start

### Option 1: Deploy on Streamlit Cloud (Recommended)
1. Go to [streamlit.cloud](https://streamlit.cloud) and sign in with GitHub
2. Click **"New app"**
3. Connect repository: `atulchoudhary7781-dot/Jarvis-AI`
4. Main file path: `app.py`
5. In **Secrets**, add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```
6. Click **Deploy** 🎉

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/atulchoudhary7781-dot/Jarvis-AI.git
cd Jarvis-AI

# Create virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run!
streamlit run app.py
```

🎉 Open your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
Jarvis-AI/
│
├── 📄 app.py                 # Main Streamlit application (WEB VERSION)
├── ⚙️ requirements.txt       # Python dependencies  
├── 🔒 .gitignore              # Git ignore rules
│
├── 📦 Jarvis_Project/         # Original Desktop Version
│   ├── run_jarvis.py          # Desktop launcher
│   └── content/drive/MyDrive/Jarvis/
│       ├── jarvis_interface.py    # Original GUI (customtkinter)
│       ├── jarvis_core.py         # Core functionality
│       └── ...                    # Other modules
│
└── 📖 README.md              # You are here!
```

---

## 🛠️ Tech Stack

### Web Version (This Repo)
| Technology | Purpose |
|------------|---------|
| **Streamlit** | Web UI Framework |
| **OpenRouter API** | Multi-model AI Engine |
| **DuckDuckGo Search** | Web Search Integration |
| **Custom CSS** | Dark Theme Styling |

### Supported AI Models
- GPT-4 / GPT-4o (OpenAI)
- Claude 3.5 Sonnet (Anthropic)
- Llama 3.1 (Meta)
- Gemini (Google)
- And many more...

---

## ⚙️ Configuration

### API Key Setup

JARVIS needs an **OpenRouter API key** to work:

1. Get a free key from [OpenRouter](https://openrouter.ai/keys) 
2. Sign up → Dashboard → Keys → Create New Key

#### For Streamlit Cloud Deployment:
Go to your app → **Settings** → **Secrets** → Add:
```
OPENROUTER_API_KEY=your_api_key_here
```

#### For Local Development:
Create a `.env` file in the project root:
```
OPENROUTER_API_KEY=your_api_key_here
```

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Required |
| `MODEL` | AI model to use | `meta-llama/llama-3.1-8b-instruct` |

---

## 🎨 JARVIS Interface

### Web App Screenshots

```
┌──────────────────────────────────────────────┐
│  ┌────────────┐  ┌────────────────────────┐  │
│  │   SIDEBAR   │  │      CHAT AREA         │  │
│  │ ────────── │  │  ────────────────────  │  │
│  │            │  │                        │  │
│  │ 🆕 New Chat│  │  👤 Hello JARVIS!      │  │
│  │ 🔍 Search  │  │  🤖 How can I help?    │  │
│  │ 🎨 Images  │  │                        │  │
│  │ 📁 Projects│  │  👤 What can you do?   │  │
│  │ ⚙️ Settings│  │  🤖 I can search web,  │  │
│  │            │  │     chat & more!        │  │
│  │ ────────── │  │                        │  │
│  │            │  │  ┌──────────────────┐  │  │
│  │            │  │  │ Type message...  │  │  │
│  │            │  │  └──────────────────┘  │  │
│  └────────────┘  └────────────────────────┘  │
│                                              │
│  🔴 Iron Man Theme    🌙 Dark Mode           │
└──────────────────────────────────────────────┘
```

---

## 🔄 Migration: Desktop → Web

| Feature | Desktop | Web | Status |
|---------|---------|-----|--------|
| **AI Chat** | ✅ | ✅ | Fully migrated |
| **Dark Theme UI** | ✅ | ✅ | Same look & feel |
| **Sidebar Menu** | ✅ | ✅ | Identical layout |
| **Web Search** | ✅ | ✅ | DuckDuckGo integrated |
| **Voice Input** | ✅ | 🔜 | Coming soon |
| **Voice Output (TTS)** | ✅ | 🔜 | Coming soon |
| **System Automation** | ✅ | ❌ | Not possible in web |

---

## 📈 Roadmap

### Completed ✅
- [x] ☁️ Web version with Streamlit
- [x] 💬 Core chat functionality  
- [x] 🔍 Web search integration
- [x] 🎨 Dark theme UI (Iron Man style)
- [x] 📱 Responsive design
- [x] 🤖 Multi-model support

### Planned 🔜
- [ ] 🎤 Voice input (browser Speech API)
- [ ] 🔊 Text-to-speech output
- [ ] 🖼️ Image generation (DALL-E, Stable Diffusion)
- [ ] 📁 File upload & analysis
- [ ] 💾 Chat history & export
- [ ] 🧠 Long-term conversation memory
- [ ] 📱 Mobile PWA support
- [ ] 👥 Multi-user accounts

---

## 🤝 Contributing

Contributions welcome! Here's how:

1. **Fork** the repository
2. Create a **feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit**: `git commit -m 'Add amazing feature'`
4. **Push**: `git push origin feature/amazing-feature`
5. Open a **Pull Request**

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [OpenRouter](https://openrouter.ai/) for multi-model AI access
- [Streamlit](https://streamlit.io/) for amazing web framework
- Marvel Studios for JARVIS inspiration 🦾

---

<div align="center">

**Made with ❤️ by [Atul Choudhary](https://github.com/atulchoudhary7781-dot)**

⭐ **Star this repo if you found it helpful!** ⭐

*J.A.R.V.I.S: Just A Rather Very Intelligent System*

🔗 **Live App:** [https://i9fm8n3pz2wn67bkro5y2q.streamlit.app/](https://i9fm8n3pz2wn67bkro5y2q.streamlit.app/)

</div>
