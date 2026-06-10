# jarvis_interface_voice_integration.py - Integration Example
# Add this to jarvis_interface.py to integrate voice activation with the main UI

"""
INTEGRATION EXAMPLE:
Add the following code to your jarvis_interface.py to integrate voice activation:
"""

# At the top of jarvis_interface.py, add these imports:
# from jarvis_voice_activation import VoiceActivationService
# from jarvis_lights import LightController, LightEffect, LightColor
# import threading

# In the JarvisInterface class __init__ method, add:
def init_voice_activation(self):
    """
    Initialize voice activation and lights
    Called from __init__ after UI is set up
    """
    try:
        # Create light controller
        self.light_controller = LightController("generic")
        
        # Create voice service with callback
        self.voice_service = VoiceActivationService(
            activation_callback=self.on_voice_activation,
            light_controller=self.light_controller
        )
        
        print("✅ Voice activation initialized")
        
    except Exception as e:
        print(f"⚠️ Voice activation not available: {e}")
        self.voice_service = None
        self.light_controller = None

def start_voice_listening(self):
    """
    Start background voice listening
    Can be called from menu or startup
    """
    if hasattr(self, 'voice_service') and self.voice_service:
        try:
            # Start in background thread
            thread = threading.Thread(target=self.voice_service.start_listening, daemon=True)
            thread.start()
            print("🎤 Voice activation started - Say 'Hey Jarvis'")
            self.update_status("Voice activation listening...")
        except Exception as e:
            print(f"Error starting voice: {e}")

def stop_voice_listening(self):
    """Stop voice listening"""
    if hasattr(self, 'voice_service') and self.voice_service:
        try:
            self.voice_service.stop_listening()
            print("Voice activation stopped")
            self.update_status("Voice activation stopped")
        except Exception as e:
            print(f"Error stopping voice: {e}")

def on_voice_activation(self):
    """
    Called when JARVIS is activated by voice
    Brings UI to focus and prepares for command
    """
    print("✨ JARVIS ACTIVATED by voice!")
    
    # Bring window to front
    try:
        if self.root:
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(self.root.attributes, '-topmost', False)
    except:
        pass
    
    # Play activation effect (already handled by light_controller)
    # Show activation feedback
    self.update_status("🎤 Voice Activated - Ready for command")
    
    # Optional: Flash UI or play sound
    self.flash_activation_effect()

def flash_activation_effect(self):
    """Visual feedback when voice activates"""
    try:
        import time
        # Quick UI flash (if using customtkinter)
        if hasattr(self, 'main_label'):
            original_color = self.main_label.cget("fg_color")
            self.main_label.configure(fg_color="cyan")
            self.root.after(200, lambda: self.main_label.configure(fg_color=original_color))
    except:
        pass

# Add UI controls for voice activation:
def add_voice_controls(self, parent_frame):
    """
    Add voice control buttons to UI
    Can be added to settings or main menu
    """
    import customtkinter as ctk
    
    voice_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    voice_frame.pack(pady=10, padx=10, fill="x")
    
    label = ctk.CTkLabel(voice_frame, text="Voice Activation", font=("Arial", 14, "bold"))
    label.pack(anchor="w", pady=(0, 5))
    
    button_frame = ctk.CTkFrame(voice_frame, fg_color="transparent")
    button_frame.pack(fill="x")
    
    start_btn = ctk.CTkButton(
        button_frame,
        text="🎤 Start Listening",
        command=self.start_voice_listening,
        fg_color="#1f6aa5",
        hover_color="#144a7a"
    )
    start_btn.pack(side="left", padx=5)
    
    stop_btn = ctk.CTkButton(
        button_frame,
        text="⏹ Stop Listening",
        command=self.stop_voice_listening,
        fg_color="#4a1f1f",
        hover_color="#7a1414"
    )
    stop_btn.pack(side="left", padx=5)
    
    info = ctk.CTkLabel(
        voice_frame,
        text="Say 'Hey Jarvis' to activate when listening is on",
        font=("Arial", 10),
        text_color="gray"
    )
    info.pack(anchor="w", pady=(5, 0))

# Example: Full integration in main UI
def full_integration_example():
    """
    Complete example of voice activation in UI
    """
    import customtkinter as ctk
    from jarvis_voice_activation import VoiceActivationService
    from jarvis_lights import LightController
    
    class JarvisWithVoice:
        def __init__(self, root):
            self.root = root
            self.light_controller = LightController("generic")
            
            # Create main UI
            self.setup_ui()
            
            # Initialize voice
            self.voice_service = VoiceActivationService(
                activation_callback=self.on_voice_activation,
                light_controller=self.light_controller
            )
            
            # Optional: Start voice listening automatically
            # self.start_voice_listening()
        
        def setup_ui(self):
            self.root.title("JARVIS - Iron Man AI")
            self.root.geometry("600x400")
            
            # Title
            title = ctk.CTkLabel(
                self.root,
                text="🤖 JARVIS",
                font=("Arial", 32, "bold"),
                text_color="#0066ff"
            )
            title.pack(pady=20)
            
            # Status
            self.status_label = ctk.CTkLabel(
                self.root,
                text="Ready for voice command",
                font=("Arial", 14)
            )
            self.status_label.pack(pady=10)
            
            # Voice controls
            self.add_voice_controls(self.root)
            
            # Settings
            self.add_light_controls(self.root)
        
        def on_voice_activation(self):
            self.root.lift()
            self.status_label.configure(text="✨ ACTIVATED - Listening for command...")
            self.root.after(3000, lambda: self.status_label.configure(
                text="Ready for voice command"
            ))
        
        def add_voice_controls(self, parent):
            frame = ctk.CTkFrame(parent)
            frame.pack(pady=10, padx=20, fill="x")
            
            btn_start = ctk.CTkButton(
                frame,
                text="🎤 Start Voice",
                command=self.start_voice_listening
            )
            btn_start.pack(side="left", padx=5)
            
            btn_stop = ctk.CTkButton(
                frame,
                text="⏹ Stop Voice",
                command=self.stop_voice_listening
            )
            btn_stop.pack(side="left", padx=5)
        
        def add_light_controls(self, parent):
            frame = ctk.CTkFrame(parent)
            frame.pack(pady=10, padx=20, fill="x")
            
            label = ctk.CTkLabel(frame, text="Light Controls", font=("Arial", 12, "bold"))
            label.pack(anchor="w")
            
            btn_light_on = ctk.CTkButton(
                frame,
                text="💡 Lights On",
                command=lambda: self.light_controller.turn_on()
            )
            btn_light_on.pack(side="left", padx=5, pady=5)
            
            btn_light_off = ctk.CTkButton(
                frame,
                text="🌙 Lights Off",
                command=lambda: self.light_controller.turn_off()
            )
            btn_light_off.pack(side="left", padx=5, pady=5)
        
        def start_voice_listening(self):
            threading.Thread(target=self.voice_service.start_listening, daemon=True).start()
            self.status_label.configure(text="🎤 Voice listening started...")
        
        def stop_voice_listening(self):
            self.voice_service.stop_listening()
            self.status_label.configure(text="Voice listening stopped")
    
    # Create and run
    root = ctk.CTk()
    app = JarvisWithVoice(root)
    root.mainloop()

if __name__ == "__main__":
    full_integration_example()
