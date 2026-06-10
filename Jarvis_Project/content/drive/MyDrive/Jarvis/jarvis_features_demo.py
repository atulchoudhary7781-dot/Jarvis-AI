# jarvis_features_demo.py - Demonstration of all 7 enhanced features
# This script shows how to use each feature independently

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Import all feature handlers
try:
    from jarvis_document_qa import DocumentQAHandler
    from jarvis_automation import SystemAutomationHandler
    from jarvis_image_gen import ImageGenerationHandler
    from jarvis_scheduling import SchedulingHandler
    from jarvis_code_sandbox import CodeSandboxHandler
    from jarvis_themes import ThemeManager
except ImportError as e:
    print(f"Error importing feature modules: {e}")
    print("Make sure all jarvis_*.py files are in the same directory")
    sys.exit(1)


def demo_document_qa():
    """Demo: Feature 1 - Interactive Document Q&A (RAG)"""
    print("\n" + "="*60)
    print("FEATURE 1: Document Q&A with RAG")
    print("="*60)
    
    handler = DocumentQAHandler()
    
    # Show available file support
    print("\nSupported file formats:")
    print("  • PDF (.pdf) - via pdfplumber")
    print("  • Word Document (.docx) - via python-docx")
    print("  • Text (.txt) - native Python")
    
    # Example of adding a document
    print("\nExample Usage:")
    print("""
    # Add a document
    result = handler.add_document('/path/to/document.pdf')
    print(f"Added document: {result}")
    
    # Ask questions about the document
    doc_id = result['doc_id']
    relevant_chunks = handler.retrieve_relevant_chunks(
        "What is the main topic?", 
        doc_id,
        top_k=3
    )
    
    # Get formatted prompt for LLM
    prompt = handler.format_rag_prompt(
        query="What is the main topic?",
        doc_id=doc_id,
        relevant_chunks=relevant_chunks
    )
    # Send prompt to your LLM
    """)
    
    print("\nBenefits:")
    print("  ✓ Ground LLM responses in actual document content")
    print("  ✓ Avoid hallucinations with RAG")
    print("  ✓ Support multiple document formats")
    print("  ✓ Semantic search with embeddings")


def demo_system_automation():
    """Demo: Feature 2 - Personal Assistant & System Automation"""
    print("\n" + "="*60)
    print("FEATURE 2: System Automation with pyautogui")
    print("="*60)
    
    handler = SystemAutomationHandler()
    
    print("\nAvailable Automation Commands:")
    print("  • open_browser(url) - Open web browser")
    print("  • search_web(query, engine) - Search the web")
    print("  • take_screenshot() - Capture screen")
    print("  • open_file(path) - Open any file")
    print("  • open_folder(path) - Open folder")
    print("  • press_key(key) - Press keyboard key")
    print("  • type_text(text) - Type text")
    print("  • click(x, y) - Click location")
    print("  • scroll(direction, amount) - Scroll page")
    print("  • open_app(name) - Launch application")
    
    print(f"\nSystem Status:")
    print(f"  pyautogui available: {handler.pyautogui_enabled}")
    
    if not handler.pyautogui_enabled:
        print("\n  ⚠️  Note: Install pyautogui to enable automation")
        print("     pip install pyautogui")
    
    print("\nExample Usage:")
    print("""
    # Open browser and search
    result = handler.search_web("Python tutorials", engine="google")
    print(result)
    
    # Take a screenshot
    result = handler.take_screenshot()
    print(f"Screenshot saved to: {result['path']}")
    
    # Voice command handler
    command = "open my browser and search for news"
    result = handler.handle_voice_command(command)
    """)
    
    print(f"\nNote: Requires explicit user permissions for certain operations")


def demo_image_generation():
    """Demo: Feature 3 - Image Generation and Editing"""
    print("\n" + "="*60)
    print("FEATURE 3: AI Image Generation & Editing")
    print("="*60)
    
    handler = ImageGenerationHandler()
    status = handler.get_status()
    
    print("\nAvailable Backends:")
    print(f"  • DALL-E 3: {'✓ Available' if status['openai_dall_e'] else '✗ Not configured'}")
    print(f"  • Stable Diffusion: {'✓ Available' if status['huggingface_sd'] else '✗ Not configured'}")
    print(f"  • Local Image Editing (PIL): {'✓ Available' if status['pil_local_editing'] else '✗ Not available'}")
    
    print("\nGeneration Methods:")
    print("  • generate_image(prompt, backend='dall-e')")
    print("  • generate_image_dalle(prompt, size, quality)")
    print("  • generate_image_stable_diffusion(prompt, model_id)")
    
    print("\nImage Editing Operations:")
    print("  • blur - Apply Gaussian blur")
    print("  • sharpen - Enhance sharpness")
    print("  • brighten - Increase brightness")
    print("  • contrast - Adjust contrast")
    print("  • resize - Change image dimensions")
    print("  • rotate - Rotate image")
    
    print("\nExample Usage:")
    print("""
    # Generate image with DALL-E
    result = handler.generate_image(
        prompt="A serene mountain landscape at sunset",
        backend="dall-e",
        size="1024x1024",
        quality="hd"
    )
    if result["success"]:
        print(f"Image generated at: {result['images'][0]['url']}")
    
    # Edit local image
    result = handler.edit_image(
        image_path="/path/to/image.png",
        operation="brighten",
        factor=1.5
    )
    print(f"Edited image saved to: {result['output_path']}")
    """)
    
    print(f"\nSetup:")
    print("  1. Set OPENAI_API_KEY for DALL-E")
    print("  2. Set HF_API_KEY for Stable Diffusion")
    print("  3. Install requirements: pip install openai pillow")


def demo_smart_scheduling():
    """Demo: Feature 4 - Smart Scheduling & Reminders"""
    print("\n" + "="*60)
    print("FEATURE 4: Smart Scheduling & Reminders")
    print("="*60)
    
    handler = SchedulingHandler()
    
    print("\nReminder Types:")
    print("  • popup - Display notification in UI")
    print("  • sound - Play system sound alert")
    print("  • voice - Text-to-speech reminder")
    
    print("\nRecurrence Options:")
    print("  • None - One-time reminder")
    print("  • daily - Repeats every day")
    print("  • weekly - Repeats every week")
    print("  • monthly - Repeats monthly")
    
    print("\nExample Usage:")
    print("""
    # Simple reminder
    handler.add_reminder(
        title="Check emails",
        delay_minutes=10,
        message="Time to check your email",
        notification_type="voice"
    )
    
    # Recurring reminder
    handler.add_reminder(
        title="Daily standup",
        specific_time=datetime(2024, 3, 6, 9, 0),
        message="Daily team standup meeting",
        repeat="daily"
    )
    
    # Schedule meeting with auto-reminders
    handler.schedule_meeting(
        title="Team Meeting",
        meeting_time=datetime.now() + timedelta(hours=2),
        duration_minutes=60,
        reminders_before=[15, 5]  # Remind 15 and 5 mins before
    )
    
    # List active reminders
    reminders = handler.list_reminders()
    print(f"Active reminders: {len(reminders)}")
    
    # Snooze a reminder
    handler.snooze_reminder(task_id, minutes=5)
    
    # Cancel reminder
    handler.cancel_reminder(task_id)
    """)
    
    print(f"\nStatus: TTS {'Enabled' if handler.enable_voice else 'Disabled'}")


def demo_multi_model_selection():
    """Demo: Feature 5 - Multi-Model Selection"""
    print("\n" + "="*60)
    print("FEATURE 5: Multi-Model Selection")
    print("="*60)
    
    print("\nAvailable LLM Models:")
    print("  • groq - Fast inference, cost-effective")
    print("  • google - Advanced reasoning, longer context")
    print("  • openai - GPT-4, highest quality")
    
    print("\nUI Implementation:")
    print("""
    # Add to create_top_bar() method:
    self.model_var = ctk.StringVar(value="groq")
    self.model_dropdown = ctk.CTkOptionMenu(
        top_bar,
        values=["groq", "google", "openai"],
        variable=self.model_var,
        command=self.on_model_changed
    )
    
    # Handle model change
    def on_model_changed(self, selected_model):
        self.current_model = selected_model
        # Reinitialize LLM client based on selection
    """)
    
    print("\nBenefits:")
    print("  ✓ Switch models based on task (speed vs. quality)")
    print("  ✓ Cost optimization by using cheaper models when possible")
    print("  ✓ Access different model capabilities")
    print("  ✓ Easy A/B testing between models")


def demo_code_sandbox():
    """Demo: Feature 6 - Code Execution Sandbox"""
    print("\n" + "="*60)
    print("FEATURE 6: Code Execution Sandbox")
    print("="*60)
    
    handler = CodeSandboxHandler()
    
    print("\nSandbox Features:")
    print("  • Safe isolated execution (subprocess)")
    print("  • Timeout protection (default 30s)")
    print("  • Blocks dangerous operations")
    print("  • Captures stdout/stderr")
    print("  • Execution history tracking")
    
    print("\nBlocked Operations:")
    print("  • os.system() - System commands")
    print("  • subprocess - Spawning processes")
    print("  • shutil - File operations")
    print("  • socket - Network access")
    print("  • exec/eval - Dynamic code execution")
    
    print("\nExample Usage:")
    print("""
    # Execute Python code
    result = handler.execute_code('''
x = 5
y = 10
result = x * y + 10
print(f"Result: {result}")
list_comp = [i**2 for i in range(5)]
print(f"Squares: {list_comp}")
    ''', timeout=10)
    
    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")
    print(f"Time: {result['execution_time']}s")
    
    # Validate code safety
    validation = handler.validate_code(code)
    print(f"Safe: {validation['is_safe']}")
    print(f"Imports: {validation['imports']}")
    """)
    
    print("\nConfiguration:")
    print(f"  • Max timeout: {handler.max_timeout} seconds")
    print(f"  • Max code lines: {handler.max_lines}")
    print("  • Configurable when creating handler")


def demo_ui_themes():
    """Demo: Feature 7 - Enhanced UI Customization"""
    print("\n" + "="*60)
    print("FEATURE 7: UI Themes & Customization")
    print("="*60)
    
    manager = ThemeManager()
    
    print("\nBuilt-in Themes:")
    for i, (name, desc) in enumerate(manager.list_themes().items(), 1):
        print(f"  {i}. {name}: {desc}")
    
    print("\nExample Usage:")
    print("""
    # List available themes
    themes = manager.list_themes()
    
    # Switch theme
    manager.set_theme("Cyberpunk")
    
    # Get theme colors
    colors = manager.get_all_colors("Ocean")
    primary = manager.primary_color("Forest")
    
    # Create custom theme
    manager.create_custom_theme(
        name="MyTheme",
        base_theme="Classic",
        colors={
            "primary_color": "#ff0000",
            "background": "#1a1a1a"
        },
        description="Custom red theme"
    )
    
    # Export/Import themes
    json_str = manager.export_theme("MyTheme")
    manager.import_theme_json(json_str, "ImportedTheme")
    """)
    
    print("\nTheme Color Keys:")
    print("  • primary_color - Main button color")
    print("  • primary_hover - Button hover state")
    print("  • background - Main background")
    print("  • sidebar_bg - Sidebar color")
    print("  • text_primary - Main text color")
    print("  • text_secondary - Secondary text")
    print("  • accent - Accent highlights")
    print("  • border_color - Border color")
    print("  • chat_user_bg - User message background")
    print("  • chat_assistant_bg - Assistant message background")
    
    print("\nUI Integration:")
    print("""
    # Add to Settings window
    theme_dropdown = ctk.CTkOptionMenu(
        settings_frame,
        values=list(manager.list_themes().keys()),
        command=self.apply_theme
    )
    """)


def run_all_demos():
    """Run all feature demonstrations"""
    print("\n" + "█"*60)
    print("█ JARVIS ENHANCEMENTS - FEATURE DEMONSTRATIONS")
    print("█"*60)
    
    demos = [
        ("Document Q&A (RAG)", demo_document_qa),
        ("System Automation", demo_system_automation),
        ("Image Generation", demo_image_generation),
        ("Smart Scheduling", demo_smart_scheduling),
        ("Multi-Model Selection", demo_multi_model_selection),
        ("Code Sandbox", demo_code_sandbox),
        ("UI Themes", demo_ui_themes),
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            demo_func()
        except Exception as e:
            print(f"\n⚠️  Error in {name} demo: {e}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\n✅ Demonstrated {len(demos)} enhancement features")
    print("\nNext Steps:")
    print("  1. Review INTEGRATION_GUIDE.md for implementation details")
    print("  2. Install dependencies: pip install -r jarvis_enhancements_requirements.txt")
    print("  3. Integrate handlers into jarvis_interface.py")
    print("  4. Set environment variables for API access")
    print("  5. Test each feature individually")
    print("\nFor questions or issues, refer to specific module docstrings")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_demos()
