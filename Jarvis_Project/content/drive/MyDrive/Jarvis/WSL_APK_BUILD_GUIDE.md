# JARVIS APK — WSL Build Guide
## From Python + Flet → Android APK

---

## Step 1 — WSL Setup (Ubuntu 22.04 recommended)

Open Windows Terminal → Ubuntu, then run:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3-pip python3-venv \
    git zip unzip \
    openjdk-17-jdk \
    libffi-dev libssl-dev \
    autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev \
    cmake build-essential
```

Verify Java:
```bash
java -version   # must show 17.x
```

---

## Step 2 — Create Virtual Environment

```bash
cd ~
python3 -m venv jarvis_env
source jarvis_env/bin/activate
```

---

## Step 3 — Install Flet & Buildozer

```bash
pip install flet buildozer cython
pip install --upgrade pip setuptools wheel
```

---

## Step 4 — Project Folder

```bash
mkdir ~/jarvis_apk
cd ~/jarvis_apk

# Copy your files here (from Windows, e.g. /mnt/c/Users/YourName/...)
cp /mnt/c/Users/YOUR_NAME/path/to/jarvis_flet.py .
cp /mnt/c/Users/YOUR_NAME/path/to/buildozer.spec .

# Also copy any support modules you have:
# jarvis_core.py, jarvis_document_qa.py, etc. (if available)
```

---

## Step 5 — Test Locally First (Desktop)

Always test on desktop before building APK:

```bash
pip install flet groq pyttsx3 SpeechRecognition duckduckgo-search pillow
python jarvis_flet.py
```

The JARVIS window should open. Send a test message.

---

## Step 6 — Build the APK

```bash
cd ~/jarvis_apk
buildozer android debug
```

**First build takes 20-40 minutes** (downloads Android SDK/NDK).
Subsequent builds: ~3-5 minutes.

The APK will be at:
```
~/jarvis_apk/bin/jarvis-1.0.0-arm64-v8a-debug.apk
```

---

## Step 7 — Install on Android Phone

### Option A — USB (ADB)
```bash
# Install ADB in WSL
sudo apt install android-tools-adb

# Enable USB Debugging on phone:
# Settings → About Phone → tap Build Number 7 times
# Settings → Developer Options → USB Debugging → ON

adb devices            # confirm phone is detected
adb install bin/jarvis-1.0.0-arm64-v8a-debug.apk
```

### Option B — File Transfer
1. Copy the `.apk` to your phone via USB cable or cloud
2. On your phone: Settings → Security → Allow Unknown Sources
3. Tap the APK to install

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `SDK not found` | Run `buildozer android debug` once — it auto-downloads |
| `Java not found` | `export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64` |
| `Cython error` | `pip install --upgrade cython` |
| `Permission denied` | `chmod +x ~/.buildozer/android/platform/android-sdk/...` |
| `faiss not found` | Remove `faiss` from buildozer.spec requirements (use remote API instead) |
| App crashes on start | Run `adb logcat \| grep python` to see Python traceback |

---

## Reduce APK Size (Optional)

Remove unused requirements from buildozer.spec:
- Remove `pyttsx3` if TTS is not needed (saves ~8MB)
- Keep `groq` and `requests` — they are small
- The final APK should be ~25-40MB

---

## Architecture Notes

Your JARVIS Flet app uses this architecture on Android:

```
Android APK
  └── Python runtime (embedded)
       └── jarvis_flet.py  ← your Flet UI
            ├── generate_reply()  → Groq API (cloud, via HTTPS)
            ├── voice input       → SpeechRecognition (Android mic)
            └── file attach       → Android file picker
```

Heavy back-end modules (faiss, sentence-transformers) are NOT
included in the APK — they don't compile for Android.
For Knowledge Base on mobile, expose it as a local FastAPI server
on your PC and call it from the phone over your local network.

---

## Quick FastAPI KB Server (optional)

```python
# kb_server.py — run on your PC
from fastapi import FastAPI
from jarvis_interface import create_vector_store

app = FastAPI()
store = create_vector_store()

@app.get("/search")
def search(q: str, k: int = 5):
    return store.search(q, k)

# Run: uvicorn kb_server:app --host 0.0.0.0 --port 8000
```

Then in jarvis_flet.py, replace the local KB call with:
```python
import requests
resp = requests.get("http://YOUR_PC_IP:8000/search", params={"q": query})
results = resp.json()
```
