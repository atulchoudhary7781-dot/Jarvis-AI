# JARVIS Features Integration Guide
# This file documents how to integrate the 7 new features into jarvis_interface.py

## INTEGRATION STEPS

### 1. ADD IMPORTS AT BEGINNING OF jarvis_interface.py

Add these imports near the top of the file (after existing imports):

```python
# New feature modules
from jarvis_document_qa import DocumentQAHandler
from jarvis_automation import SystemAutomationHandler
from jarvis_image_gen import ImageGenerationHandler
from jarvis_scheduling import SchedulingHandler
from jarvis_code_sandbox import CodeSandboxHandler
from jarvis_themes import ThemeManager
```

### 2. INITIALIZE HANDLERS IN __init__ METHOD

In the JarvisInterface.__init__ method, add after existing initializations:

```python
def __init__(self):
    # ... existing code ...
    
    # Initialize new feature handlers
    self.document_qa_handler = DocumentQAHandler()
    self.automation_handler = SystemAutomationHandler()
    self.image_gen_handler = ImageGenerationHandler()
    self.scheduling_handler = SchedulingHandler()
    self.code_sandbox_handler = CodeSandboxHandler()
    self.theme_manager = ThemeManager()
    
    # Set callback for reminders
    self.scheduling_handler.set_notification_callback(self.handle_reminder_notification)
    
    # Current LLM model (for feature 5)
    self.current_model = "groq"  # Default model
    self.available_models = ["groq", "google", "openai"]
```

### 3. MODIFY create_top_bar() METHOD

Add Model Selector dropdown to the top bar:

```python
def create_top_bar(self):
    # ... existing code ...
    
    # ADD MODEL SELECTOR (before Clear Chat button or after JARVIS button)
    self.model_var = ctk.StringVar(value=self.current_model)
    self.model_dropdown = ctk.CTkOptionMenu(
        top_bar,
        values=self.available_models,
        variable=self.model_var,
        font=("Arial", 12),
        fg_color="#1a1a1a",
        button_color="#4a5fe8",
        button_hover_color="#3a4fd8",
        dropdown_fg_color="#1a1a1a",
        command=self.on_model_changed
    )
    self.model_dropdown.grid(row=0, column=2, padx=10, pady=10, sticky="w")
    
    # ... rest of create_top_bar ...
```

### 4. ADD MODEL CHANGE HANDLER

Add this method to the JarvisInterface class:

```python
def on_model_changed(self, selected_model: str):
    """Handle LLM model selection change."""
    self.current_model = selected_model
    print(f"Switched to model: {selected_model}")
    # You can add logic here to reinitialize the LLM client
```

### 5. MODIFY show_plus_menu() METHOD

Update the items list to include new features:

```python
def show_plus_menu(self):
    # ... existing code to create menu ...
    
    # Update items list to include new features:
    items = [
        ("Upload Photo", "JPG, PNG or GIF", "📷", self.handle_photo_upload),
        ("Google Drive", "Import from cloud", "☁️", self.handle_drive_upload),
        ("Attach File", "PDF, DOCX or TXT", "📎", self.handle_file_attach),
        ("📄 Document Chat", "Ask about uploaded docs", "🤖", self.open_document_qa_dialog),
        ("🎨 Generate Image", "Create AI images", "✨", self.open_image_gen_dialog),
        ("⚙️ Automation", "Control your computer", "🖥️", self.open_automation_dialog),
        ("⏰ Set Reminder", "Schedule a task", "🔔", self.open_reminder_dialog),
        ("💻 Run Code", "Execute Python snippets", "▶️", self.open_code_sandbox_dialog),
    ]
    
    # ... rest of show_plus_menu ...
```

### 6. ADD NEW DIALOG HANDLERS

Add these methods to the JarvisInterface class:

```python
def open_document_qa_dialog(self):
    """Open Document Q&A interface for RAG."""
    # This would create a new window to upload and chat with documents
    print("Opening Document Q&A...")
    self._cleanup_plus_menu()

def open_image_gen_dialog(self):
    """Open Image Generation interface."""
    print("Opening Image Generator...")
    self._cleanup_plus_menu()

def open_automation_dialog(self):
    """Open System Automation interface."""
    print("Opening Automation Controls...")
    self._cleanup_plus_menu()

def open_reminder_dialog(self):
    """Open Reminder/Scheduling interface."""
    print("Opening Scheduler...")
    self._cleanup_plus_menu()

def open_code_sandbox_dialog(self):
    """Open Code Sandbox interface."""
    print("Opening Code Sandbox...")
    self._cleanup_plus_menu()

def handle_reminder_notification(self, notification_data: dict):
    """Handle reminder notifications from scheduling handler."""
    # Display reminder in chat or as popup
    task_id = notification_data.get("task_id")
    title = notification_data.get("title")
    message = notification_data.get("message")
    
    reminder_text = f"🔔 **REMINDER**: {title}\n{message}"
    self.add_to_chat_history(reminder_text, "assistant")
```

### 7. INTEGRATE FEATURES INTO generate_reply()

Update the generate_reply method to handle special commands:

```python
def generate_reply(self, user_text: str, attachment_path: Optional[str] = None) -> str:
    # ... existing code ...
    
    # Check for special feature commands
    if user_text.lower().startswith("run code:"):
        code = user_text.replace("run code:", "").strip()
        result = self.code_sandbox_handler.execute_python_snippet(code)
        return result
    
    elif user_text.lower().startswith("remind me"):
        # Parse reminder request and add reminder
        # Example: "remind me to check email in 10 minutes"
        return self.parse_and_add_reminder(user_text)
    
    elif user_text.lower().startswith("generate image"):
        # Parse image generation request
        prompt = user_text.replace("generate image", "").strip()
        result = self.image_gen_handler.generate_image(prompt)
        if result["success"]:
            return f"Image generated! Check your JARVIS_Generated_Images folder."
        else:
            return f"Failed to generate image: {result.get('error')}"
    
    elif user_text.lower().startswith("ask document"):
        # Query loaded documents
        # Parse which document and what question
        parts = user_text.split(":")
        if len(parts) > 1:
            question = parts[1].strip()
            return self.query_loaded_document(question)
    
    # ... rest of existing code ...
```

### 8. ADD HELPER METHODS FOR FEATURE INTEGRATION

```python
def parse_and_add_reminder(self, text: str) -> str:
    """Parse natural language reminder and schedule it."""
    import re
    
    # Simple parsing for "remind me to [action] in [time]"
    match = re.search(r'remind me to (.+?) in (\d+)\s*(minutes?|hours?)', text.lower())
    if match:
        action = match.group(1)
        amount = int(match.group(2))
        unit = match.group(3)
        
        minutes = amount
        if 'hour' in unit:
            minutes = amount * 60
        
        result = self.scheduling_handler.add_reminder(
            title=action.capitalize(),
            delay_minutes=minutes
        )
        return f"✅ Reminder set: {action} in {amount} {unit}"
    
    return "❌ Could not parse reminder. Use format: 'remind me to [action] in [time]'"

def query_loaded_document(self, question: str) -> str:
    """Query a loaded document using RAG."""
    documents = self.document_qa_handler.list_documents()
    if not documents:
        return "No documents loaded. Please upload a PDF or DOCX first."
    
    # Use first document as default
    doc_id = documents[0]["id"]
    chunks = self.document_qa_handler.retrieve_relevant_chunks(question, doc_id)
    
    if not chunks:
        return "No relevant information found in the document."
    
    prompt = self.document_qa_handler.format_rag_prompt(question, doc_id, chunks)
    
    # Feed prompt to LLM
    # This would call your existing LLM integration with the RAG prompt
    return prompt
```

### 9. UPDATE open_settings() METHOD

Add settings for new features:

```python
def open_settings(self):
    # ... existing settings ...
    
    # Add Theme Selection
    theme_label = ctk.CTkLabel(settings_frame, text="UI Theme:", font=("Arial", 12))
    theme_var = ctk.StringVar(value=self.theme_manager.current_theme)
    theme_dropdown = ctk.CTkOptionMenu(
        settings_frame,
        values=list(self.theme_manager.list_themes().keys()),
        variable=theme_var,
        command=lambda x: self.apply_theme(x)
    )
    
    # Add Automation Settings
    automation_enabled = ctk.CTkCheckBox(
        settings_frame,
        text="Enable System Automation",
        variable=ctk.BooleanVar(value=True)
    )
    
    # Add Scheduling Settings
    reminders_enabled = ctk.CTkCheckBox(
        settings_frame,
        text="Enable Reminders",
        variable=ctk.BooleanVar(value=True)
    )
```

### 10. ADD THEME APPLICATION METHOD

```python
def apply_theme(self, theme_name: str):
    """Apply selected theme to the entire interface."""
    self.theme_manager.set_theme(theme_name)
    theme_colors = self.theme_manager.get_all_colors()
    
    # Update root colors
    if CTK_AVAILABLE:
        ctk.set_default_color_theme(theme_name.lower())
    
    # Refresh UI components
    # This would require updating all widget colors
    print(f"Theme changed to: {theme_name}")
```

## FEATURE USAGE EXAMPLES

### Example 1: Document Q&A
```
User: "Upload a PDF and ask JARVIS about its contents"
JARVIS: Loads the PDF, chunks it, and answers questions using RAG
```

### Example 2: System Automation
```
User: "Take a screenshot and save it to my Projects folder"
JARVIS: Uses pyautogui to take screenshot and save it
```

### Example 3: Image Generation
```
User: "Generate image: A futuristic city with flying cars"
JARVIS: Calls DALL-E API and generates the image
```

### Example 4: Smart Reminders
```
User: "Remind me to check email in 10 minutes"
JARVIS: Sets a reminder that will notify in 10 minutes
```

### Example 5: Model Selection
```
User: Clicks model dropdown to switch from Groq to Google Gemini
JARVIS: Switches LLM backend and subsequent responses use the new model
```

### Example 6: Code Sandbox
```
User: "run code: print('Hello'; x = 5; print(x*2))"
JARVIS: Executes code in sandbox and shows output
```

### Example 7: UI Themes
```
User: Goes to Settings and selects "Cyberpunk" theme
JARVIS: UI changes to neon colors and futuristic aesthetic
```

## DEPENDENCIES TO INSTALL

Add to requirements.txt:
```
pdfplumber>=0.10.0
python-docx>=0.8.11
pyautogui>=0.9.53
openai>=1.0.0
sentence-transformers>=2.0.0
Pillow>=10.0.0
```

## TESTING THE INTEGRATION

1. Install all feature modules: `pip install -r requirements.txt`
2. Add the import statements to jarvis_interface.py
3. Initialize handlers in __init__
4. Modify create_top_bar() to add model selector
5. Modify show_plus_menu() to add feature buttons
6. Test each feature individually

## NOTES

- All feature modules are independent and can be used separately
- Error handling is built into each module
- Features gracefully degrade if optional dependencies are missing
- Set environment variables for API keys: OPENAI_API_KEY, HF_API_KEY, GROQ_API_KEY
- Check jarvis_*.py files for detailed API documentation
