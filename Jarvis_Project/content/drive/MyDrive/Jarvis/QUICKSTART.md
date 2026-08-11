# Quick Start Guide - JARVIS Enhancements

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 minute)
```bash
pip install -r jarvis_enhancements_requirements.txt
```

### Step 2: Review What's Included (2 minutes)
```bash
python jarvis_features_demo.py
```

This will display demonstrations of all 7 features.

### Step 3: Integrate into Your JARVIS (2 minutes)

**Option A: Quick Integration (Minimal)**
```python
# At the top of jarvis_interface.py, add:
from jarvis_document_qa import DocumentQAHandler
from jarvis_automation import SystemAutomationHandler
from jarvis_image_gen import ImageGenerationHandler
from jarvis_scheduling import SchedulingHandler
from jarvis_code_sandbox import CodeSandboxHandler
from jarvis_themes import ThemeManager

# In __init__ method, add:
self.document_qa_handler = DocumentQAHandler()
self.automation_handler = SystemAutomationHandler()
self.image_gen_handler = ImageGenerationHandler()
self.scheduling_handler = SchedulingHandler()
self.code_sandbox_handler = CodeSandboxHandler()
self.theme_manager = ThemeManager()
```

**Option B: Full Integration (Complete)**
See `INTEGRATION_GUIDE.md` for detailed step-by-step instructions.

---

## 🎯 Features at a Glance

### 1️⃣ Document Q&A
```python
# Upload PDF/DOCX and ask questions
result = document_qa_handler.add_document("report.pdf")
chunks = document_qa_handler.retrieve_relevant_chunks("What's the revenue?", result['doc_id'])
```

### 2️⃣ System Automation
```python
# Control your computer
automation_handler.take_screenshot()
automation_handler.search_web("python tutorial")
automation_handler.open_browser()
```

### 3️⃣ Image Generation
```python
# Create AI images
result = image_gen_handler.generate_image("Robot in space", backend="dall-e")
# Edit images
image_gen_handler.edit_image("photo.png", "brighten", factor=1.5)
```

### 4️⃣ Smart Reminders
```python
# Schedule reminders
scheduling_handler.add_reminder("Check email", delay_minutes=10, notification_type="voice")
# Schedule meeting with auto-reminders
scheduling_handler.schedule_meeting("Team standup", datetime.now() + timedelta(hours=1))
```

### 5️⃣ Model Selection
```python
# Add to your top bar UI:
# model_dropdown = ctk.CTkOptionMenu(top_bar, values=["groq", "google", "openai"])
current_model = "groq"  # User selects from dropdown
```

### 6️⃣ Code Sandbox
```python
# Run Python code safely
result = code_sandbox_handler.execute_code("x = 5; print(x**2)")
print(result['output'])  # "25"
```

### 7️⃣ Custom Themes
```python
# List themes
themes = theme_manager.list_themes()  # 8 built-in themes
# Switch theme
theme_manager.set_theme("Cyberpunk")
# Get colors
colors = theme_manager.get_all_colors()
```

---

## 📁 Files Reference

| File | Purpose | Lines | Features |
|------|---------|-------|----------|
| `jarvis_document_qa.py` | RAG with embeddings | 300+ | Upload PDFs/DOCX, semantic search |
| `jarvis_automation.py` | Computer control | 350+ | Take screenshots, open apps, web search |
| `jarvis_image_gen.py` | Image AI | 400+ | DALL-E, Stable Diffusion, PIL editing |
| `jarvis_scheduling.py` | Task scheduling | 400+ | Reminders, voice alerts, recurring tasks |
| `jarvis_code_sandbox.py` | Safe execution | 350+ | Run Python code, validation, history |
| `jarvis_themes.py` | UI customization | 500+ | 8 themes + custom theme creation |
| `INTEGRATION_GUIDE.md` | Setup instructions | 400+ | Step-by-step integration |
| `jarvis_features_demo.py` | Demo script | 500+ | Test all features |
| `FEATURES_SUMMARY.md` | Full documentation | 400+ | Complete API reference |

**Total: 2500+ lines of production code**

---

## 🔌 Integration Examples

### Add Feature to Plus Menu
```python
def show_plus_menu(self):
    items = [
        ("Upload Photo", "JPG, PNG or GIF", "📷", self.handle_photo_upload),
        # ADD THESE:
        ("🎨 Generate Image", "Create AI images", "✨", self.open_image_gen_dialog),
        ("⏰ Set Reminder", "Schedule a task", "🔔", self.open_reminder_dialog),
        ("💻 Run Code", "Execute Python", "▶️", self.open_code_sandbox_dialog),
    ]
```

### Handle Special Commands
```python
def generate_reply(self, user_text: str) -> str:
    # Check for feature commands
    if user_text.startswith("run code:"):
        code = user_text.replace("run code:", "")
        return self.code_sandbox_handler.execute_python_snippet(code)
    
    if user_text.startswith("remind me"):
        return self.parse_and_add_reminder(user_text)
    
    if user_text.startswith("generate image"):
        prompt = user_text.replace("generate image", "").strip()
        result = self.image_gen_handler.generate_image(prompt)
        return f"Image generated!" if result["success"] else result.get("error")
```

### Add Theme Selector to Settings
```python
def open_settings(self):
    theme_dropdown = ctk.CTkOptionMenu(
        settings_frame,
        values=list(self.theme_manager.list_themes().keys()),
        command=lambda x: self.apply_theme(x)
    )
```

---

## 🔐 Security & Requirements

### Minimum Requirements
- Python 3.8+
- customtkinter (already used)
- Core modules (pdfplumber, pyautogui, openai, etc.)

### API Keys (Optional)
```bash
# For AI features, set these environment variables:
export OPENAI_API_KEY="sk-..."         # For DALL-E image generation
export GOOGLE_API_KEY="..."            # For Google Gemini
export HF_API_KEY="hf_..."             # For Hugging Face models
export GROQ_API_KEY="gsk_..."          # For Groq (already used?)
```

### Safety Notes
- ✅ Code sandbox blocks dangerous operations
- ✅ File operations restricted to user directories
- ⚠️ Automation requires user oversight
- ⚠️ Never store API keys in code

---

## 🧪 Testing Each Feature

```bash
# 1. Run demo to see all features
python jarvis_features_demo.py

# 2. Test document Q&A
python -c "from jarvis_document_qa import DocumentQAHandler; print('✓ Document QA OK')"

# 3. Test automation
python -c "from jarvis_automation import SystemAutomationHandler; print('✓ Automation OK')"

# 4. Test image gen
python -c "from jarvis_image_gen import ImageGenerationHandler; print('✓ Image Gen OK')"

# 5. Test scheduling
python -c "from jarvis_scheduling import SchedulingHandler; print('✓ Scheduling OK')"

# 6. Test code sandbox
python -c "from jarvis_code_sandbox import CodeSandboxHandler; print('✓ Code Sandbox OK')"

# 7. Test themes
python -c "from jarvis_themes import ThemeManager; print('✓ Themes OK')"
```

---

## 📞 Common Questions

**Q: Do I need all API keys?**
A: No, features gracefully degrade. DALL-E will fall back to Stable Diffusion. Code sandbox and scheduling work without any keys.

**Q: Can I customize the themes?**
A: Yes! Use `ThemeManager.create_custom_theme()` to design your own theme.

**Q: Is code execution safe?**
A: Yes, it runs in a sandbox with 30-second timeout and blocks dangerous operations.

**Q: Do I need to integrate all 7 features?**
A: No, each module is independent. Use only what you need.

**Q: Can I use these features without the UI?**
A: Yes! Each handler works standalone:
```python
from jarvis_scheduling import SchedulingHandler
handler = SchedulingHandler()
handler.add_reminder("Test", delay_minutes=1)
```

---

## 🚀 Next Steps

1. ✅ Install dependencies: `pip install -r jarvis_enhancements_requirements.txt`
2. ✅ Run demo: `python jarvis_features_demo.py`
3. ✅ Read `INTEGRATION_GUIDE.md` for detailed setup
4. ✅ Choose integration approach (minimal or full)
5. ✅ Test each feature before deploying
6. ✅ Set environment variables for API access
7. ✅ Enjoy your enhanced JARVIS! 🎉

---

## 📌 Pro Tips

- **Theme Customization**: Create a "MyCompany" brand theme
- **Automation Safety**: Start with screenshot, expand gradually
- **Code Sandbox**: Great for educational/tutorial mode
- **Document QA**: Train on your own documents
- **Reminders**: Set daily reminders for important tasks
- **Model Selection**: Use cheaper models for simple tasks

---

**Ready to enhance your JARVIS? Start with `pip install -r jarvis_enhancements_requirements.txt` and go! 🚀**
