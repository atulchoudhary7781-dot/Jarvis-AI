# jarvis_core.py - Shared utilities and classes for JARVIS
# Contains common functionality used across multiple modules
import warnings
import speech_recognition as sr
import pyttsx3
import os
import threading
import time
import random
import math
import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

_engine = None
_engine_lock = threading.Lock()

def _safe_pyttsx3_init():
    if not PYTTSX3_AVAILABLE:
        return None

    if os.name == "nt":
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            try:
                import comtypes
                comtypes.CoInitialize()
            except Exception:
                pass

    try:
        return pyttsx3.init()
    except Exception:
        return None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _safe_pyttsx3_init()
    return _engine

def activate_jarvis():
    print("Core: Jarvis is now active and processing...")
    # Wake word listener is handled by the main interface logic

if __name__ == "__main__":
    activate_jarvis()

def welcome_user():
    engine = get_engine()
    if not engine:
        return
    
    with _engine_lock:
        try:
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[0].id) # 0 for male, 1 for female

            hour = int(datetime.datetime.now().hour)
            if hour >= 0 and hour < 12:
                wish = "Good Morning!"
            elif hour >= 12 and hour < 18:
                wish = "Good Afternoon!"
            else:
                wish = "Good Evening!"
                
            engine.say(f"{wish}. I am Jarvis, your personal AI assistant. System is now online and ready for your command.")
            engine.runAndWait()
        except RuntimeError:
            # Engine loop already started, skip this call
            print("Warning: Could not speak welcome message (engine busy)")
            pass

def speak(text):
    print(f"Jarvis: {text}")
    engine = get_engine()
    if engine:
        with _engine_lock:
            try:
                engine.say(text)
                engine.runAndWait()
            except RuntimeError:
                # Engine loop already started, skip this call
                pass

# Ise interface ke __init__ mein call karein

# Audio imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import winsound
except ImportError:
    winsound = None

# Web search imports
try:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DDGS = None
    DUCKDUCKGO_AVAILABLE = False

# PyAutoGUI imports
PYAUTOGUI_AVAILABLE = False # Initialize to False by default
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e: # Catch a broader exception for display-related issues
    print(f"Warning: Could not import pyautogui due to: {e}")
    print("PyAutoGUI features will be disabled. This is common in headless environments like Colab.")
    PYAUTOGUI_AVAILABLE = False

# Optional pycaw for volume control
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

class AudioHandler:
    """Minimal audio handler stub used by the application when advanced audio packages are not available.
    Provides a compatible interface with `listen_to_audio()` and `speak()` but does not require external packages.
    """
    def __init__(self):
        # indicate if we can use speech_recognition / pyttsx3 functionality
        self.available = SPEECH_RECOGNITION_AVAILABLE
        self.recognizer = None
        self.engine = None
        self.engine_lock = threading.Lock()
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                # Accuracy improvements
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8  # Allow natural pauses
                self.recognizer.phrase_threshold = 0.3 # Filter out brief noise
                self.recognizer.non_speaking_duration = 0.4
            except Exception:
                self.recognizer = None
                self.available = False

        if PYTTSX3_AVAILABLE:
            self.engine = _safe_pyttsx3_init()

    def listen_to_audio(self) -> Optional[str]:
        """Listen to the system microphone and return recognized text.

        Returns:
            - recognized text (str) on success
            - a short message string starting with 'Error:' on recognizer errors
            - None when no microphone or configuration is available
        """
        if not self.available or self.recognizer is None:
            return "Error: Speech Recognition library not initialized properly."

        try:
            # Check if Microphone class is available (requires PyAudio)
            if not hasattr(sr, 'Microphone'):
                return "Error: Could not find PyAudio; check installation. Please run 'pip install pyaudio'."

            # Device list check
            mic_list = sr.Microphone.list_microphone_names()
            if not mic_list:
                return "Error: No microphone devices detected on this system."

            # Use the default system microphone. This requires PyAudio or equivalent backend.
            with sr.Microphone() as source:
                # short ambient noise adjustment
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                except Exception:
                    pass
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=20)
                except sr.WaitTimeoutError:
                    return "Sorry, I didn't hear anything."

            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except (AttributeError, ImportError) as e:
                if "pyaudio" in str(e).lower():
                    return "Error: Could not find PyAudio; check installation. Please run 'pip install pyaudio'."
                return f"Error: {e}"
            except sr.UnknownValueError:
                return "Sorry, I didn't catch that."
            except sr.RequestError as e:
                return f"Error: Speech recognition request failed: {e}"
            except Exception as e:
                return f"Error: {e}"
        except (AttributeError, ImportError):
            return "Error: Could not find PyAudio; check installation. Please run 'pip install pyaudio'."
        except Exception as e:
            # Common failure: no microphone, backend missing, or permission denied
            return f"Error: Microphone access failed: {e}"

    def get_voices(self) -> List[Dict[str, Any]]:
        """Return a list of available system voices."""
        if not PYTTSX3_AVAILABLE:
            return []
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name} for v in voices]
        except Exception:
            return []

    def speak(self, text: str, voice_id: str = None) -> None:
        # Prefer system TTS engine if available, otherwise print to console
        if PYTTSX3_AVAILABLE and self.engine:
            with self.engine_lock:
                try:
                    # Attempt to set voice/rate properties to match the main interface
                    try:
                        if voice_id:
                            self.engine.setProperty('voice', voice_id)
                        else:
                            voices = self.engine.getProperty('voices')
                            selected_voice_id = None
                            preferred_voices = ["Zira", "David"]
                            for name in preferred_voices:
                                for voice in voices:
                                    if name in voice.name:
                                        selected_voice_id = voice.id
                                        break
                                if selected_voice_id:
                                    break
                            if not selected_voice_id and len(voices) > 1:
                                selected_voice_id = voices[1].id
                            if selected_voice_id:
                                self.engine.setProperty('voice', selected_voice_id)
                        self.engine.setProperty('rate', 175)
                    except Exception:
                        pass

                    self.engine.say(text)
                    self.engine.runAndWait()
                    return
                except RuntimeError:
                    # Engine run loop already started
                    print(f"Warning: Could not speak message (engine busy)")
                    pass
                except Exception as e:
                    print(f"TTS Error: {e}")

        # Fallback
        print(f"🤖 JARVIS: {text}")

    def stop_speaking(self):
        """Stop the text-to-speech engine if it is currently speaking."""
        if PYTTSX3_AVAILABLE and self.engine:
            with self.engine_lock:
                try:
                    self.engine.stop()
                except Exception:
                    pass

class WebSearchHandler:
    """Handles web search functionality for retrieving current information."""

    def __init__(self):
        self.available = DUCKDUCKGO_AVAILABLE
        self.ddgs = None
        if self.available:
            # Suppress the duckduckgo_search rename warning
            warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to ddgs.*", category=RuntimeWarning)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    self.ddgs = DDGS()
            except Exception:
                self.available = False

    def search(self, query: str, max_results: int = 5) -> str:
        """Search the web and return formatted results."""
        if not self.available or not self.ddgs:
            return "Web search is not available. Please install duckduckgo-search."

        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            if not results:
                return f"No search results found for: {query}"

            formatted = f"Web search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                url = result.get('href', 'No URL')
                formatted += f"{i}. {title}\n   {body}\n   {url}\n\n"

            return formatted
        except Exception as e:
            return f"Error performing web search: {e}"

def web_search(query):
    """Fast web search function for Jarvis."""
    if not DUCKDUCKGO_AVAILABLE or DDGS is None:
        return "Sir, the search library is not installed."
    try:
        with DDGS() as ddgs:
            # max_results=2 rakha hai taaki response fast aaye
            results = [r for r in ddgs.text(query, max_results=2)]
            if results:
                # Pehle result ka summary return karega
                return f"According to the web: {results[0]['body']}"
            return "Sir, I couldn't find any live information on that."
    except Exception:
        return "I'm having trouble connecting to the internet, sir."

class StarAnimation:
    """Handles the animated star field background."""

    def __init__(self, canvas, root):
        self.canvas = canvas
        self.root = root
        self.stars = []
        self.shooting_star = None
        self.animation_id = None
        self.init_stars()
        self.animate_stars()

    def init_stars(self):
        if not self.canvas:
            return
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        for _ in range(100):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.random() * 2
            speed = random.random() * 0.5 + 0.1
            # Draw star (white dot)
            star = self.canvas.create_oval(x, y, x+size, y+size, fill="white", outline="")
            self.stars.append({"id": star, "speed": speed})
        self.shooting_star = None

    def animate_stars(self):
        if not self.canvas:
            return
        width = self.canvas.winfo_width()
        if width <= 1:
            width = self.root.winfo_screenwidth()
        height = self.canvas.winfo_height()
        if height <= 1:
            height = self.root.winfo_screenheight()

        for star in self.stars:
            self.canvas.move(star["id"], 0, star["speed"])
            coords = self.canvas.coords(star["id"]) if star["id"] in self.canvas.find_all() else []
            if coords[1] > height:
                new_x = random.randint(0, width)
                self.canvas.coords(star["id"], new_x, 0, new_x+2, 2)

        # Shooting star logic
        if self.shooting_star:
            self.canvas.move(self.shooting_star["id"], self.shooting_star["vx"], self.shooting_star["vy"])
            coords = self.canvas.coords(self.shooting_star["id"]) if self.shooting_star["id"] in self.canvas.find_all() else []
            # Check if out of bounds
            if not coords or (coords[0] > width and coords[2] > width) or (coords[1] > height and coords[3] > height):
                self.canvas.delete(self.shooting_star["id"])
                self.shooting_star = None
        elif random.random() < 0.01:  # 1% chance per frame
            # Create new shooting star
            if random.choice([True, False]):
                sx = random.randint(0, width)
                sy = -50
            else:
                sx = -50
                sy = random.randint(0, height // 2)

            length = random.randint(40, 100)
            speed = random.randint(20, 40)

            # Create line (tail -> head)
            star_id = self.canvas.create_line(sx, sy, sx + length, sy + length, fill="#aaddff", width=2)
            self.shooting_star = {"id": star_id, "vx": speed, "vy": speed}

        self.animation_id = self.root.after(20, self.animate_stars)

    def stop(self):
        """Stop the animation."""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

def handle_system_commands(user_text: str) -> Optional[str]:
    """Handle system control commands and return response if handled."""
    user_lower = user_text.lower()

    # Open applications
    if "open chrome" in user_lower or "open google chrome" in user_lower:
        try:
            os.system("start chrome")
            return "Opening Google Chrome."
        except Exception as e:
            return f"Error opening Chrome: {e}"

    if "open notepad" in user_lower:
        try:
            os.system("notepad")
            return "Opening Notepad."
        except Exception as e:
            return f"Error opening Notepad: {e}"

    if "open calculator" in user_lower:
        try:
            os.system("calc")
            return "Opening Calculator."
        except Exception as e:
            return f"Error opening Calculator: {e}"

    # Volume control (Windows)
    if "increase volume" in user_lower or "volume up" in user_lower:
        if not PYCAW_AVAILABLE:
            return "Volume control requires pycaw library. Please run: pip install pycaw"
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_volume = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(min(1.0, current_volume + 0.1), None)
            return "Volume increased."
        except Exception as e:
            return f"Error adjusting volume: {e}"

    if "decrease volume" in user_lower or "volume down" in user_lower:
        if not PYCAW_AVAILABLE:
            return "Volume control requires pycaw library. Please run: pip install pycaw"
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_volume = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(max(0.0, current_volume - 0.1), None)
            return "Volume decreased."
        except Exception as e:
            return f"Error adjusting volume: {e}"

    # Screenshot
    if "take screenshot" in user_lower or "screenshot" in user_lower:
        try:
            if PYAUTOGUI_AVAILABLE:
                screenshot = pyautogui.screenshot()
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                screenshot.save(filename)
                return f"Screenshot saved as {filename}."
            else:
                return "Screenshot functionality requires pyautogui. Please install it."
        except Exception as e:
            return f"Error taking screenshot: {e}"

    # Mouse control
    if "move mouse" in user_lower:
        try:
            if PYAUTOGUI_AVAILABLE:
                # Parse coordinates if provided
                import re
                coords = re.findall(r'\d+', user_text)
                if len(coords) >= 2:
                    x, y = int(coords[0]), int(coords[1])
                    pyautogui.moveTo(x, y)
                    return f"Mouse moved to ({x}, {y})."
                else:
                    return "Please specify coordinates like 'move mouse to 100 200'."
            else:
                return "Mouse control requires pyautogui. Please install it."
        except Exception as e:
            return f"Error moving mouse: {e}"

    # Typing
    if "type" in user_lower:
        try:
            if PYAUTOGUI_AVAILABLE:
                text_to_type = user_text.split("type", 1)[1].strip()
                pyautogui.write(text_to_type)
                return f"Typed: {text_to_type}"
            else:
                return "Typing functionality requires pyautogui. Please install it."
        except Exception as e:
            return f"Error typing: {e}"

    return None  # Not a system command

def start_jarvis_tasks():
    print("Core: Jarvis Active Mode Started...")
    audio = AudioHandler()
    
    while True:
        # User ki voice command lene ke liye
        query = audio.listen_to_audio()
        if not query or query.startswith("Error:") or query.startswith("Sorry"):
            continue
            
        user_query = query.lower()
        print(f"User command: {user_query}")

        if 'stop' in user_query or 'exit' in user_query:
            speak("Going offline. Have a nice day, sir!")
            break

        # Handle quick local info before checking internet
        if "time" in user_query and "what" in user_query:
            now = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The time is {now}, sir.")
            continue

        # Internet Search Logic
        if any(word in user_query for word in ["latest", "news", "search", "current"]):
            print("🔍 Searching live data...")
            search_term = user_query.replace("search", "").replace("latest", "").replace("news", "").replace("current", "").strip()
            speak("Searching live data, sir...")
            info = web_search(search_term)
            print(info)
            speak(info)
        else:
            # Condition 2: Baaki sab ke liye Logic
            print("🧠 Using AI Brain...")
            # System control commands check karein
            response = handle_system_commands(user_query)
            if response:
                speak(response)