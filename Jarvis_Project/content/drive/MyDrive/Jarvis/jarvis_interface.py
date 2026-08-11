# -*- coding: utf-8 -*-
"""
JARVIS - Advanced AI Personal Assistant
Voice-enabled AI assistant with persistent login, document QA, and advanced features
"""
# Optional UI and API libraries are imported with guards so the script
# fails gracefully when dependencies are missing.
import os
import sys

# Fix UTF-8 encoding on Windows and preserve console output for PowerShell pipelines.
def configure_console_utf8():
    if sys.platform == 'win32':
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except Exception:
            pass
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

configure_console_utf8()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "login_session.txt")
ERROR_LOG_PATH = os.path.join(BASE_DIR, "jarvis_error.log")


def write_error_log_header():
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Jarvis startup: {datetime.datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n")
    except Exception:
        pass


def log_exception(exc_type, exc_value, exc_traceback, context: str = "Uncaught exception"):
    try:
        message = f"{context}: {exc_type.__name__}: {exc_value}"
        logging.error(message, exc_info=(exc_type, exc_value, exc_traceback))
    except Exception:
        pass

    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} - {context}\n")
            import traceback
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write("\n")
    except Exception:
        pass

    try:
        sys.__stdout__.write(f"ERROR: {context}. See {ERROR_LOG_PATH} for details.\n")
    except Exception:
        pass


def setup_crash_handlers():
    write_error_log_header()
    sys.excepthook = lambda exc_type, exc_value, exc_traceback: log_exception(
        exc_type,
        exc_value,
        exc_traceback,
        context="Unhandled exception",
    )
    if hasattr(threading, "excepthook"):
        def thread_exc_handler(args):
            log_exception(
                args.exc_type,
                args.exc_value,
                args.exc_traceback,
                context=f"Unhandled exception in thread {args.thread.name}",
            )
        threading.excepthook = thread_exc_handler

# Import enhanced session manager
try:
    from jarvis_session_manager import SessionManager, save_session, get_session, clear_session
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False
    # Fallback to basic functions
    def save_session(user_id):
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            f.write(str(user_id))

    def get_session():
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                return f.read().strip()
        return None
    
    def clear_session():
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

# Ise interface ke __init__ mein call karein
import sys
import webbrowser
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    ctk = None
    CTK_AVAILABLE = False

try:
    from tkinter import PhotoImage, filedialog
except ImportError:
    PhotoImage = None
    filedialog = None
try:
    import tkinter as tk
    TK_AVAILABLE = True
except ImportError:
    tk = None
    TK_AVAILABLE = False

import os
import logging
import datetime
import threading
import concurrent.futures

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env loading is optional

import sys
import time
import random
import math
import csv
import json
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk
from weakref import WeakKeyDictionary
import sqlite3


def get_total_system_memory_mb():
    """Return total physical memory in megabytes, or None if detection fails."""
    try:
        import psutil
        return psutil.virtual_memory().total // (1024**2)
    except Exception:
        pass

    try:
        if os.name == "nt":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return status.ullTotalPhys // (1024**2)
        elif hasattr(os, "sysconf"):
            if "SC_PAGE_SIZE" in os.sysconf_names and "SC_PHYS_PAGES" in os.sysconf_names:
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                return (pages * page_size) // (1024**2)
    except Exception:
        pass

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return int(parts[1]) // 1024
    except Exception:
        pass

    return None

# Optional ML / vector DB libraries — lazily imported when needed to reduce startup latency.
SentenceTransformer = None
SENTENCE_TRANSFORMERS_AVAILABLE = False
faiss = None
FAISS_AVAILABLE = False

pdfplumber = None
PDFPLUMBER_AVAILABLE = False

docx = None
DOCX_AVAILABLE = False

Presentation = None
PPTX_AVAILABLE = False

AutoTokenizer = None
AutoModelForCausalLM = None
transformers_logging = None
TRANSFORMERS_AVAILABLE = False

huggingface_hub = None
HF_HUB_AVAILABLE = False

OpenAI = None
OPENAI_AVAILABLE = False

genai = None
GENAI_AVAILABLE = False

load_dataset = None
DATASETS_AVAILABLE = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    Observer = None
    FileSystemEventHandler = None
    WATCHDOG_AVAILABLE = False


def _lazy_import_vector_libraries():
    global SentenceTransformer, SENTENCE_TRANSFORMERS_AVAILABLE, faiss, FAISS_AVAILABLE
    if SentenceTransformer is not None and faiss is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except Exception:
        SentenceTransformer = None
        SENTENCE_TRANSFORMERS_AVAILABLE = False
    try:
        import faiss
        FAISS_AVAILABLE = True
    except Exception:
        faiss = None
        FAISS_AVAILABLE = False


def _lazy_import_transformers():
    global AutoTokenizer, AutoModelForCausalLM, transformers_logging, TRANSFORMERS_AVAILABLE
    if AutoTokenizer is not None and AutoModelForCausalLM is not None:
        return
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, logging as transformers_logging
        TRANSFORMERS_AVAILABLE = True
        transformers_logging.set_verbosity_error()
    except Exception:
        AutoTokenizer = None
        AutoModelForCausalLM = None
        transformers_logging = None
        TRANSFORMERS_AVAILABLE = False


def _lazy_import_huggingface_hub():
    global huggingface_hub, HF_HUB_AVAILABLE
    if huggingface_hub is not None:
        return
    try:
        import huggingface_hub
        HF_HUB_AVAILABLE = True
        logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)
    except Exception:
        huggingface_hub = None
        HF_HUB_AVAILABLE = False


def _lazy_import_openai():
    global OpenAI, OPENAI_AVAILABLE
    if OpenAI is not None:
        return
    try:
        from openai import OpenAI
        OPENAI_AVAILABLE = True
    except Exception:
        OpenAI = None
        OPENAI_AVAILABLE = False


def _lazy_import_datasets():
    global load_dataset, DATASETS_AVAILABLE
    if load_dataset is not None:
        return
    try:
        from datasets import load_dataset
        DATASETS_AVAILABLE = True
    except Exception:
        load_dataset = None
        DATASETS_AVAILABLE = False


# NOTE: `openai` (or `OpenAI`) is imported lazily inside `generate_reply`
# so the script can start without the package installed. When the user
# provides `OPENAI_API_KEY` and the package is missing, a helpful message
# will be returned instead of raising at import time.

# Audio imports
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import pyttsx3  # type: ignore
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    
try:
    import winsound
except ImportError:
    winsound = None

# Web search imports
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DDGS = None
    DUCKDUCKGO_AVAILABLE = False
    
# Global reference to the JarvisInterface instance (wake word se access ke liye)
_jarvis_app_instance = None

def listen_for_wake_word():
    """Background function to listen for 'wake jarvis' or 'hello jarvis'."""
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("⚠️ Speech recognition package is not installed. Wake-word listening disabled.")
        return

    try:
        import speech_recognition as sr
    except ImportError:
        print("⚠️ Speech recognition package could not be imported. Wake-word listening disabled.")
        return

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.7
    recognizer.energy_threshold = 300

    while True:
        try:
            global _jarvis_app_instance
            if _jarvis_app_instance and getattr(_jarvis_app_instance, 'is_listening', False):
                time.sleep(1)
                continue

            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    print(f"👂 Listening... (Ambient Noise Level: {recognizer.energy_threshold})")
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)

                    print("🔍 Processing speech...")
                    query = recognizer.recognize_google(audio, language='en-in').lower()
                    print(f"User said: '{query}'")

                    if any(word in query for word in ["hello jarvis", "wake up jarvis", "hey jarvis"]):
                        print("✨ Wake word detected!")
                        command_text = query
                        for trigger in ["hello jarvis", "wake up jarvis", "hey jarvis"]:
                            command_text = command_text.replace(trigger, "")
                        command_text = command_text.strip()

                        if _jarvis_app_instance:
                            if command_text:
                                print(f"🚀 Direct command detected: {command_text}")
                                _jarvis_app_instance.root.after(0, lambda ct=command_text: _jarvis_app_instance.handle_external_command(ct, use_overlay=True))
                            else:
                                speak("At your service, sir.")
                                _jarvis_app_instance.root.after(0, lambda: _jarvis_app_instance.activate_voice_overlay("Listening..."))
                                _jarvis_app_instance.root.after(200, _jarvis_app_instance.voice_input)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"❌ API Error: Check your internet connection. {e}")
                time.sleep(2)
            except getattr(sr, 'WaitTimeoutError', Exception):
                print("⏱️ No speech detected, continuing to listen...")
                time.sleep(1)
                continue
        except Exception as e:
            print(f"⚠️ Mic/Recognition Error: {e}")
            time.sleep(3)

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False

# Import shared utilities from jarvis_core
from jarvis_core import AudioHandler, WebSearchHandler, StarAnimation, handle_system_commands, web_search, speak, welcome_user, get_engine

# Import specialized feature handlers (DocumentQAHandler imported lazily in _init_handlers)
from jarvis_automation import SystemAutomationHandler
from jarvis_image_gen import ImageGenerationHandler
from jarvis_scheduling import SchedulingHandler
from jarvis_code_sandbox import CodeSandboxHandler

# Import voice activation and lights (Iron Man style)
try:
    from jarvis_voice_activation import VoiceActivationService
    VOICE_ACTIVATION_AVAILABLE = True
except ImportError:
    VoiceActivationService = None
    VOICE_ACTIVATION_AVAILABLE = False

try:
    from jarvis_lights import LightController, LightColor, LightEffect
    LIGHTS_AVAILABLE = True
except ImportError:
    LightController = None
    LIGHTS_AVAILABLE = False

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if WATCHDOG_AVAILABLE:
    class KBFileHandler(FileSystemEventHandler):
        """Filesystem event handler for auto-rebuilding the KB."""
        def __init__(self, app_instance: "JarvisInterface"):
            self.app = app_instance
            # ------------------------------
            # Debounce to avoid triggering multiple builds for one file save operation
            self.last_triggered_time = 0
            self.debounce_seconds = 5 # Wait 5s between triggers
        
        def on_created(self, event):
            self._handle_event(event)

        def on_modified(self, event):
            self._handle_event(event)

        def _handle_event(self, event):
            if event.is_directory:
                return

            current_time = time.time()
            if (current_time - self.last_triggered_time) < self.debounce_seconds:
                return

            exts = (".txt", ".md", ".pdf", ".docx", ".pptx", ".csv")
            if event.src_path.lower().endswith(exts):
                self.last_triggered_time = current_time
                logging.info(f"Auto-rebuild triggered by change in: {os.path.basename(event.src_path)}")
                # Use root.after to schedule the rebuild on the main thread
                # A small delay helps ensure the file is fully written before we read it
                self.app.root.after(2000, self.app.trigger_auto_rebuild)
else:
    KBFileHandler = None

# ==================== JARVIS INTERFACE ====================

class JarvisInterface:
    def __init__(self):
        # Audio and web services are initialized in background for smooth startup
        self.audio_handler = None
        self.web_search_handler = None
        self.startup_overlay_frame = None
        self.startup_status_label = None

        # Initialize the main window. Prefer CustomTkinter if available,
        # otherwise fall back to a minimal Tkinter UI so the app can run
        # without the `customtkinter` package.
        self.chat_history = []
        self.is_listening = False
        self.stop_listening_flag = False
        self.listening_session_id = 0
        self.big_mic_btn = None
        self.mic_status_label = None
        self.account_window = None
        self.user_message_count = 0
        self.is_logged_in = False
        self.current_session_id = None
        self.current_user_id = None
        self.account_db = None
        self.kb_observer = None
        self.auto_scroll_var = None
        self.voice_var = None
        self.kb_auto_rebuild_var = None
        self.stop_generation_event = None
        self.loaded_dataset = None
        self.local_model = None
        self.local_tokenizer = None
        self.is_premium = False
        self.web_search_enabled = False
        self.current_voice_id = None
        self.user_preferences_profile = {} # Predictive Analytics Memory
        self.current_user_name = "Friend"
        self.memory_file = os.path.join(os.path.expanduser("~"), "jarvis_memory.json")
        self.memory_data = self._load_memory()
        self.dynamic_header_label = None
        self.voice_overlay = None
        self.voice_overlay_label = None
        self.voice_overlay_frame = None
        self.overlay_active = False
        self._root_was_visible_before_overlay = False
        
        # Initialize specialized feature handlers (moved after UI creation for faster startup)
        self.doc_qa_handler = None
        self.automation_handler = None
        self.image_gen_handler = None
        self.scheduling_handler = None
        self.code_sandbox = None
        
        # KB Settings Variables (Persistent)
        self.kb_folder_var = None
        self.kb_db_var = None
        self.kb_index_var = None
        self.kb_summary_index_var = None
        self.kb_auto_rebuild_var = None
        self.kb_build_button = None
        self.kb_cancel_button = None

        # KB backend cache and flags to avoid repeated cold loads (reduces UI delays)
        self.kb_store = None
        self.kb_store_lock = threading.Lock()
        self._kb_store_initializing = False
        self._kb_build_cancel_event = None
        self._pending_auto_login_user_id = None

        # Voice Activation and Lights (Iron Man Style)
        self.voice_service = None
        self.light_controller = None
        self.voice_listening = False
        self.total_memory_gb = None
        self.low_memory_mode = self._detect_low_memory()

        # Initialize Account Database early
        try:
            import jarvis_accounts
            self.account_db = jarvis_accounts.AccountDatabase(db_path=os.path.join(BASE_DIR, "jarvis_accounts.db"))
        except ImportError:
            logging.warning("jarvis_accounts module not found.")

        if CTK_AVAILABLE:
            # Force the app into dark mode before creating widgets
            try:
                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("dark-blue")
            except Exception:
                pass

            self.root = ctk.CTk()
            self.root.title("JARVIS")
            self.root.geometry("1400x800")
            try:
                self.root.configure(fg_color="#000000")
            except Exception:
                pass

            # Open in full screen/maximized
            try:
                self.root.after(0, lambda: self.root.state("zoomed"))
            except Exception:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

            # Set Window Icon
            try:
                icon_p = resource_path("jarvis_icon.ico")
                if os.path.exists(icon_p):
                    self.root.iconbitmap(icon_p)
            except Exception:
                pass

            self._setup_tk_crash_handler()

            # Create main layout (customtkinter)
            self.create_layout()
            self._show_startup_overlay("Booting Jarvis..." if not self.low_memory_mode else "Booting Jarvis (low RAM mode)...")
            
            # Initialize handlers and services - schedule on main thread
            self.root.after_idle(self._init_startup_services)
            
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        elif TK_AVAILABLE:
            # Minimal fallback using tkinter
            self.root = tk.Tk()
            self.root.title("JARVIS (tk fallback)")
            try:
                self.root.configure(bg="#000000")
            except Exception:
                pass
            try:
                self.root.geometry("900x600")
            except Exception:
                pass

            # Open in full screen/maximized
            try:
                self.root.after(0, lambda: self.root.state("zoomed"))
            except Exception:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

            self._setup_tk_crash_handler()
            self.create_tk_fallback()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        else:
            raise RuntimeError("No supported UI library available (customtkinter or tkinter)")

        # Prime the TTS engine on the main thread to avoid COM initialization issues on Windows
        try:
            get_engine()
        except Exception:
            pass

        # Welcome the user on start without blocking the UI thread
        if not self.low_memory_mode:
            self.root.after(2000, lambda: threading.Thread(target=welcome_user, daemon=True).start())
        else:
            logging.info("Skipping welcome speech in low memory mode.")
        
        # Initialize Voice Activation and Lights in a background thread
        self.root.after(500, lambda: threading.Thread(target=self._init_voice_activation, daemon=True).start())
            
        # Initialize Tk variables after root is created
        if tk:
            self.kb_folder_var = tk.StringVar(value=os.getcwd())
            self.kb_db_var = tk.StringVar(value="kb_meta.db")
            self.kb_index_var = tk.StringVar(value="kb_index.faiss")
            self.kb_summary_index_var = tk.StringVar(value="kb_summary_index.faiss")
            self.kb_auto_rebuild_var = tk.BooleanVar(value=False)

        # Session Persistence Logic
        self._pending_auto_login_user_id = get_session()

        # Start periodic dynamic header updates
        self.update_dynamic_header()

    def _init_handlers(self):
        """Initialize feature handlers in background."""
        try:
            # Import DocumentQAHandler lazily to avoid heavy dependencies at startup
            try:
                from jarvis_document_qa import DocumentQAHandler
                self.doc_qa_handler = DocumentQAHandler()
            except Exception as e:
                logging.warning(f"Could not initialize DocumentQA handler: {e}")
                self.doc_qa_handler = None
            
            self.automation_handler = SystemAutomationHandler()
            self.image_gen_handler = ImageGenerationHandler()
            self.scheduling_handler = SchedulingHandler()
            self.code_sandbox = CodeSandboxHandler()
            logging.info("Feature handlers initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing handlers: {e}")

    def _init_core_services(self):
        """Initialize core audio, search, and optional account services."""
        try:
            if self.audio_handler is None:
                self.audio_handler = AudioHandler()
            if self.web_search_handler is None:
                self.web_search_handler = WebSearchHandler()
        except Exception as e:
            logging.error(f"Error initializing core services: {e}")

        try:
            import jarvis_accounts
            if self.account_db is None:
                self.account_db = jarvis_accounts.AccountDatabase(db_path=os.path.join(BASE_DIR, "jarvis_accounts.db"))
        except Exception as e:
            logging.warning(f"Account database initialization deferred or failed: {e}")

    def _detect_low_memory(self):
        """Detect low memory systems and enable a lighter startup mode."""
        total_mb = get_total_system_memory_mb()
        if total_mb is None:
            return False
        self.total_memory_gb = total_mb / 1024.0
        if total_mb < 6144:
            logging.info(f"Low memory mode enabled: {self.total_memory_gb:.1f} GB RAM detected.")
            return True
        return False

    def _init_startup_services(self):
        """Run startup services and handlers in the background."""
        # Initialize core services in background
        threading.Thread(target=self._init_core_services, daemon=True).start()
        
        # Schedule startup complete callback and handlers on main thread
        self.root.after(500, self._startup_complete)

        # Load heavier feature handlers after the UI is ready.
        self.root.after(1000, lambda: threading.Thread(target=self._init_handlers, daemon=True).start())

    def _show_startup_overlay(self, text: str):
        try:
            if self.startup_overlay_frame and self.startup_overlay_frame.winfo_exists():
                self.startup_status_label.configure(text=text)
                return

            self.startup_overlay_frame = ctk.CTkFrame(
                self.root,
                fg_color="#0a0a0a",
                border_width=0,
                corner_radius=0
            )
            self.startup_overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.startup_status_label = ctk.CTkLabel(
                self.startup_overlay_frame,
                text=text,
                font=("Arial", 18, "bold"),
                text_color="#ffffff"
            )
            self.startup_status_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception as e:
            logging.debug(f"Failed to show startup overlay: {e}")

    def _hide_startup_overlay(self):
        try:
            if self.startup_overlay_frame and self.startup_overlay_frame.winfo_exists():
                self.startup_overlay_frame.destroy()
                self.startup_overlay_frame = None
                self.startup_status_label = None
        except Exception as e:
            logging.debug(f"Failed to hide startup overlay: {e}")

    def _startup_complete(self):
        """Mark startup as complete and remove the temporary overlay."""
        self._hide_startup_overlay()
        try:
            if hasattr(self, 'dynamic_header_label') and self.dynamic_header_label:
                self.dynamic_header_label.configure(text="✨ Jarvis is ready. Type your command.")
        except Exception:
            pass

        if self._pending_auto_login_user_id:
            self.root.after(100, lambda: self._auto_login(self._pending_auto_login_user_id))
            self._pending_auto_login_user_id = None

        logging.info("Jarvis startup complete.")

    def _init_voice_activation(self):
        """Initialize voice activation service and lights"""
        if self.low_memory_mode:
            logging.info("Skipping voice activation in low memory mode.")
            return

        if not VOICE_ACTIVATION_AVAILABLE:
            logging.info("Voice activation not available (install SpeechRecognition, pyaudio)")
            return
        
        try:
            # Initialize lights
            if LIGHTS_AVAILABLE:
                self.light_controller = LightController("generic")
                logging.info("✅ Light controller initialized")
            
            # Initialize voice service
            self.voice_service = VoiceActivationService(
                activation_callback=self.on_voice_activation,
                light_controller=self.light_controller
            )
            
            # Auto-start voice listening
            threading.Thread(target=self.start_voice_listening, daemon=True).start()
            logging.info("✅ Voice activation service initialized and listening")
            
        except Exception as e:
            logging.error(f"Voice activation init error: {e}")

    def _setup_tk_crash_handler(self):
        try:
            if self.root and hasattr(self.root, 'report_callback_exception'):
                self.root.report_callback_exception = self._tk_report_callback_exception
        except Exception as e:
            logging.warning(f"Could not attach TK exception handler: {e}")

    def _tk_report_callback_exception(self, exc, val, tb):
        log_exception(exc, val, tb, context="Tkinter callback exception")
        try:
            self.notify_popup_text(
                "An unexpected error occurred. See jarvis_error.log for details.",
                title="Error",
                icon="⚠️",
            )
        except Exception:
            pass

    def start_voice_listening(self):
        """Start background voice listening"""
        if not self.voice_service or self.voice_listening:
            return
        
        try:
            self.voice_listening = True
            self.voice_service.start_listening()
            logging.info("🎤 Voice listening started - say 'Hey Jarvis'")
        except Exception as e:
            logging.error(f"Voice listening error: {e}")
            self.voice_listening = False
    
    def stop_voice_listening(self):
        """Stop voice listening"""
        if self.voice_service and self.voice_listening:
            try:
                self.voice_service.stop_listening()
                self.voice_listening = False
                logging.info("Voice listening stopped")
            except Exception as e:
                logging.error(f"Error stopping voice: {e}")
    
    def on_voice_activation(self):
        """Called when 'Hey Jarvis' is detected"""
        logging.info("✨ JARVIS ACTIVATED by voice!")
        
        try:
            # Bring window to front
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(lambda: self.root.attributes('-topmost', False))
            
            # Update status
            if hasattr(self, 'dynamic_header_label'):
                self.root.after(0, lambda: self.dynamic_header_label.configure(text="🎤 Voice Activated - Ready for Command"))
            
            # Play voice feedback (already handled by voice service)
            speak("I am online and ready for your commands.")
            
        except Exception as e:
            logging.error(f"Voice activation handler error: {e}")

    def _auto_login(self, user_id):
        """Automatically log in the user using the saved session."""
        try:
            if not self.account_db or not user_id:
                return
            
            user_id = int(user_id)
            user_info = self.account_db.get_user_info(user_id)
            
            if not user_info:
                # User not found, clear invalid session
                logging.warning(f"Attempted auto-login for non-existent user {user_id}")
                clear_session()
                return
            
            if not user_info.get('is_active', True):
                # User account is disabled
                logging.warning(f"User {user_id} account is disabled")
                clear_session()
                return
            
            # Successful auto-login
            self.is_logged_in = True
            self.current_user_id = user_id
            
            # Update UI with user info
            if user_info.get('full_name'):
                self.profile_label.configure(text=user_info['full_name'])
            else:
                self.profile_label.configure(text=user_info.get('username', 'User'))
            
            if user_info.get('subscription_tier') == 'plus':
                self.is_premium = True
                if hasattr(self, 'upgrade_btn'):
                    self.upgrade_btn.configure(text="✦ JARVIS Plus", fg_color="transparent", border_width=1, state="disabled")
            
            # Load preferences
            prefs = self.account_db.get_user_preferences(user_id)
            if prefs:
                if prefs.get('voice_id'):
                    self.current_voice_id = prefs['voice_id']
                if prefs.get('voice_enabled') is not None:
                    self.voice_var.set(bool(prefs['voice_enabled']))
            
            self.update_avatar_ui()
            if hasattr(self, 'sidebar_logout_btn'):
                self.sidebar_logout_btn.pack(side="right", padx=5)
            
            self.current_user_name = self._extract_user_name(user_info)
            self.update_dynamic_header()
            self.refresh_sidebar_chats()

            # Show welcome back message with recent activity
            remembered = self._get_user_memory().get("interactions", []) if self._get_user_memory() else []
            if remembered:
                last = remembered[-1]
                self.notify_popup_text(f"Welcome back, {self.current_user_name}. I remembered your recent activity: {last['text']}", title="Welcome Back", icon="👋")
            else:
                self.notify_popup_text(f"Welcome back, {self.current_user_name}!", title="Welcome Back", icon="👋")
            
            logging.info(f"✅ Auto-login successful for user {user_id} ({user_info.get('username', 'User')})")
        except ValueError:
            logging.error(f"Invalid user_id format in session: {user_id}")
            clear_session()
        except Exception as e:
            logging.error(f"Auto-login failed: {e}", exc_info=True)

    def create_layout(self):
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main chat area
        self.create_main_area()
        
        # Create sidebar (overlay)
        self.create_sidebar()
        
        # Create floating burger button
        self.create_burger_button()
        
    def create_sidebar(self):
        self.sidebar_width = 250
        self.sidebar_visible = False
        # Sidebar frame
        self.sidebar = ctk.CTkFrame(self.root, width=self.sidebar_width, corner_radius=0, fg_color="#000000")
        self.sidebar.place(x=-self.sidebar_width, y=0, relheight=1.0)
        self.sidebar.grid_rowconfigure(20, weight=1)
        
        # Logo/Title area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=(70, 20), pady=20, sticky="w")
        
        try: # Fix for FileNotFoundError
            from PIL import Image, ImageDraw
            logo_path = resource_path("image.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                self.logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                logo_label = ctk.CTkLabel(logo_frame, text="", image=self.logo_image)
            else:
                # Create a simple circular logo with "J"
                img = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Draw circle
                draw.ellipse([0, 0, 40, 40], fill="#4a5fe8")
                # Draw "J"
                draw.text((20, 20), "J", fill="white", anchor="mm", font=None)  # Simple text
                self.logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(40, 40))
                logo_label = ctk.CTkLabel(logo_frame, text="", image=self.logo_image)
            logo_label.pack(side="left", padx=(0, 10))
        except Exception:
            logo_label = ctk.CTkLabel(logo_frame, text="Jarvis", font=("Arial", 24, "bold"), text_color="#FFFFFF")
            logo_label.pack(side="left", padx=(0, 10))
        
        # New Chat button
        new_chat_btn = ctk.CTkButton(
            self.sidebar,
            text="✎  New chat",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=40,
            command=self.new_chat
        )
        new_chat_btn.grid(row=1, column=0, padx=15, pady=(10, 5), sticky="ew")
        
        # # Save Chat button
        # save_chat_btn = ctk.CTkButton(
        #     self.sidebar,
        #     text="💾  Save Chat",
        #     font=("Arial", 13),
        #     fg_color="transparent",
        #     hover_color="#2a2a2a",
        #     anchor="w",
        #     height=40,
        #     command=self.save_chat_to_file
        # )
        # save_chat_btn.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        # Search button
        search_btn = ctk.CTkButton(
            self.sidebar,
            text="🔍  Search",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=40,
            command=self.toggle_web_search
        )
        search_btn.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        # Images button
        images_btn = ctk.CTkButton(
            self.sidebar,
            text="🖼  Images",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=40,
            command=self.open_image_tools
        )
        images_btn.grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        
        # # Apps button
        # apps_btn = ctk.CTkButton(
        #     self.sidebar,
        #     text="⊞  Apps",
        #     font=("Arial", 13),
        #     fg_color="transparent",
        #     hover_color="#2a2a2a",
        #     anchor="w",
        #     height=40
        # )
        # apps_btn.grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        
        # Projects button
        projects_btn = ctk.CTkButton(
            self.sidebar,
            text="📁  Projects",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=40
        )
        projects_btn.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        
        # Settings button
        settings_btn = ctk.CTkButton(
            self.sidebar,
            text="⚙  Settings",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=40,
            command=self.open_settings
        )
        settings_btn.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        
        # Clear History button (shown above login/profile section after login)
        self.clear_history_btn = ctk.CTkButton(
            self.sidebar,
            text="🗑️  Clear History",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            anchor="w",
            height=40,
            command=self.clear_history
        )
        self.clear_history_btn.grid(row=21, column=0, padx=15, pady=5, sticky="ew")
        if not self.is_logged_in:
            self.clear_history_btn.grid_remove()
        
        # # Knowledge Base button
        # kb_btn = ctk.CTkButton(
        #     self.sidebar,
        #     text="🧠  Knowledge Base",
        #     font=("Arial", 13),
        #     fg_color="transparent",
        #     hover_color="#2a2a2a",
        #     anchor="w",
        #     height=40,
        #     command=self.open_kb_settings
        # )
        # kb_btn.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
        
        # # GPTs section
        # gpts_label = ctk.CTkLabel(
        #     self.sidebar,
        #     text="GPTs",
        #     font=("Arial", 12),
        #     text_color="#888888",
        #     anchor="w"
        # )
        # gpts_label.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # # Resume Expert
        # resume_btn = ctk.CTkButton(
        #     self.sidebar,
        #     text="😊  Resume Expert",
        #     font=("Arial", 13),
        #     fg_color="transparent",
        #     hover_color="#2a2a2a",
        #     anchor="w",
        #     height=35
        # )
        # resume_btn.grid(row=6, column=0, padx=15, pady=5, sticky="ew")
        
        # # Explore GPTs
        # explore_btn = ctk.CTkButton(
        #     self.sidebar,
        #     text="🌐  Explore GPTs",
        #     font=("Arial", 13),
        #     fg_color="transparent",
        #     hover_color="#2a2a2a",
        #     anchor="w",
        #     height=35
        # )
        # explore_btn.grid(row=7, column=0, padx=15, pady=5, sticky="ew")
        
        # Your chats section
        chats_label = ctk.CTkLabel(
            self.sidebar,
            text="Your chats",
            font=("Arial", 12),
            text_color="#CCCCCC",
            anchor="w"
        )
        chats_label.grid(row=8, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Chat History List Container
        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.history_frame.grid(row=9, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(9, weight=1)

        # Auto-scroll variable (UI moved to Settings)
        if self.auto_scroll_var is None:
            self.auto_scroll_var = tk.BooleanVar(value=True)
        
        # Voice variable
        if self.voice_var is None:
            voice_enabled = True  # Default
            if self.is_logged_in and self.account_db and self.current_user_id:
                prefs = self.account_db.get_user_preferences(self.current_user_id)
                if prefs and 'voice_enabled' in prefs:
                    voice_enabled = bool(prefs['voice_enabled'])
            if tk:
                self.voice_var = tk.BooleanVar(value=voice_enabled)
            else:
                self.voice_var = voice_enabled
        
        # User profile at bottom
        profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        profile_frame.grid(row=22, column=0, padx=15, pady=15, sticky="ew")
        
        if self.current_user_id:
            self.avatar_image = self._load_circular_avatar(f"user_avatar_{self.current_user_id}.png")
        else:
            self.avatar_image = None

        if self.avatar_image:
            self.profile_icon = ctk.CTkButton(profile_frame, text="", image=self.avatar_image, width=30, height=30, fg_color="transparent", hover=False)
        else:
            self.profile_icon = ctk.CTkButton(profile_frame, text="👤", font=("Arial", 16), width=30, height=30, corner_radius=15, fg_color="#333333", hover_color="#444444", text_color="#FFFFFF")
        self.profile_icon.pack(side="left", padx=(0, 8))
        self.profile_icon.bind("<Button-1>", self.handle_profile_click)
        self.profile_icon.bind("<Enter>", self.handle_profile_hover)

        self.profile_label = ctk.CTkLabel(
            profile_frame,
            text="Login",
            font=("Arial", 13),
            text_color="#FFFFFF"
        )
        self.profile_label.pack(side="left")
        self.profile_label.bind("<Button-1>", self.handle_profile_click)
        self.profile_label.bind("<Enter>", self.handle_profile_hover)
        profile_frame.bind("<Button-1>", self.handle_profile_click)
        profile_frame.bind("<Enter>", self.handle_profile_hover)
        
        self.sidebar_logout_btn = ctk.CTkButton(
            profile_frame,
            text="Logout",
            font=("Arial", 16),
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#444444",
            text_color="#FFFFFF",
            command=self.confirm_logout
        )
        # upgrade_btn = ctk.CTkButton(
        #     profile_frame,
        #     text="Upgrade",
        #     font=("Arial", 11),
        #     width=70,
        #     height=25,
        #     fg_color="#2a2a2a",
        #     hover_color="#3a3a3a"
        # )
        # upgrade_btn.pack(side="right")
        
    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.animate_sidebar(0, -self.sidebar_width)
            self.sidebar_visible = False
            self._unbind_sidebar_click_outside()
        else:
            self.sidebar.lift()
            self.burger_btn.lift()
            self.animate_sidebar(-self.sidebar_width, 0)
            self.sidebar_visible = True
            self.root.after(100, self._bind_sidebar_click_outside)

    def animate_sidebar(self, start, end):
        if hasattr(self, '_sidebar_anim_id') and self._sidebar_anim_id:
            try:
                self.root.after_cancel(self._sidebar_anim_id)
            except Exception:
                pass

        # Smooth easing animation (Ease Out Cubic)
        duration = 250  # ms
        steps = 25
        delay = max(1, duration // steps)
        
        def animate(i):
            if i > steps:
                self.sidebar.place(x=end, y=0, relheight=1.0)
                self._sidebar_anim_id = None
                return
            
            progress = i / steps
            factor = 1 - pow(1 - progress, 3)
            current = start + (end - start) * factor
            
            self.sidebar.place(x=current, y=0, relheight=1.0)
            self._sidebar_anim_id = self.root.after(delay, animate, i + 1)
            
        animate(0)

    def toggle_web_search(self):
        """Toggle web search functionality on/off"""
        self.web_search_enabled = not self.web_search_enabled
        status = "enabled" if self.web_search_enabled else "disabled"
        self.root.after(0, lambda: self.show_feature_popup("Web Search Toggled", f"Web search has been {status}.", "🔍"))

    def _bind_sidebar_click_outside(self):
        if self.sidebar_visible:
            self._sidebar_bind_id = self.root.bind("<Button-1>", self._handle_sidebar_global_click, add="+")

    def _unbind_sidebar_click_outside(self):
        if hasattr(self, '_sidebar_bind_id'):
            self.root.unbind("<Button-1>", self._sidebar_bind_id)
            del self._sidebar_bind_id

    def _handle_sidebar_global_click(self, event):
        if not self.sidebar_visible:
            return
            
        try:
            x, y = event.x_root, event.y_root
            
            # Sidebar bounds
            sx = self.sidebar.winfo_rootx()
            sy = self.sidebar.winfo_rooty()
            sw = self.sidebar.winfo_width()
            sh = self.sidebar.winfo_height()
            
            if sx <= x <= sx + sw and sy <= y <= sy + sh:
                return

            # Burger button bounds (to prevent double toggle)
            if self.burger_btn.winfo_exists():
                bx = self.burger_btn.winfo_rootx()
                by = self.burger_btn.winfo_rooty()
                bw = self.burger_btn.winfo_width()
                bh = self.burger_btn.winfo_height()
                
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    return
            
            # Click was outside, close sidebar
            self.toggle_sidebar()
        except Exception:
            pass

    def create_main_area(self):
        # Main container
        self.main_area = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#000000")
        self.main_area.grid(row=0, column=0, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        # Star Animation Canvas
        if TK_AVAILABLE and not getattr(self, 'low_memory_mode', False):
            self.star_canvas = tk.Canvas(self.main_area, bg="#000000", highlightthickness=0)
            self.star_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.star_animation = StarAnimation(self.star_canvas, self.root)
        
        # Top bar
        self.create_top_bar()
        
        # Chat display area
        self.chat_container = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color="transparent",
            corner_radius=0
        )
        self.chat_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.chat_container.grid_columnconfigure(0, weight=1)
        
        # Hide scrollbar initially
        try:
            if hasattr(self.chat_container, "_scrollbar"):
                self.chat_container._scrollbar.grid_remove()
        except Exception:
            pass
        
        # Welcome message
        self.create_welcome_message()
        
        # Input area
        self.create_input_area()
        

        
    def create_top_bar(self):
        top_bar = ctk.CTkFrame(self.main_area, height=60, corner_radius=0, fg_color="#000000")
        top_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        top_bar.grid_columnconfigure(2, weight=1)
        
        # Navigation anchor (no visible text)
        jarvis_btn = ctk.CTkButton(
            top_bar,
            text="",
            fg_color="transparent",
            hover_color="#333333",
            width=40,
            height=40
        )
        jarvis_btn.grid(row=0, column=1, padx=(70, 5), pady=10, sticky="w")
        
        self.dynamic_header_label = ctk.CTkLabel(
            top_bar,
            text=self._get_dynamic_header(),
            font=("Arial", 18, "bold"),
            text_color="#FFFFFF"
        )
        self.dynamic_header_label.grid(row=0, column=2, padx=10, pady=10)
        
        # Clear Chat button
        clear_chat_btn = ctk.CTkButton(
            top_bar,
            text="🗑️ Clear Chat",
            font=("Arial", 13),
            fg_color="transparent",
            hover_color="#333333",
            border_width=1,
            border_color="#444444",
            height=35,
            corner_radius=20,
            command=self.new_chat
        )
        clear_chat_btn.grid(row=0, column=3, padx=10, pady=10, sticky="e")
        
        # Get Plus button
        self.upgrade_btn = ctk.CTkButton(
            top_bar,
            text="✦  Upgrade",
            font=("Arial", 13),
            fg_color="#4a5fe8",
            hover_color="#3a4fd8",
            width=120,
            height=35,
            corner_radius=20,
            command=self.open_payment_page
        )
        self.upgrade_btn.grid(row=0, column=4, padx=20, pady=10, sticky="e")
        
        # # User icons
        # if hasattr(self, 'avatar_image') and self.avatar_image:
        #     self.top_bar_user_icon = ctk.CTkButton(top_bar, text="", image=self.avatar_image, width=34, height=34, fg_color="transparent", hover=False)
        # else:
        #     self.top_bar_user_icon = ctk.CTkButton(top_bar, text="", font=("Arial", 18), width=34, height=34, corner_radius=17, fg_color="#333333", hover_color="#444444", text_color="#FFFFFF")
        # self.top_bar_user_icon.grid(row=0, column=4, padx=(0, 10), pady=10, sticky="e")
        # self.top_bar_user_icon.bind("<Button-1>", self.handle_profile_click)
        # self.top_bar_user_icon.bind("<Enter>", self.handle_profile_hover)
        
        # settings_icon = ctk.CTkLabel(top_bar, text="⚙", font=("Arial", 18))
        # settings_icon.grid(row=0, column=5, padx=(0, 20), pady=10, sticky="e")

        # KB status indicator (compact dot + tooltip)
        try:
            # A small colored dot indicates KB status; tooltip shows current state text
            self.kb_status_dot = ctk.CTkLabel(top_bar, text="●", font=("Arial", 14), text_color="#f59e0b")
            self.kb_status_dot.grid(row=0, column=6, padx=(0, 20), pady=10, sticky="e")
            self.kb_status_tooltip_text = "KB: initializing"
            try:
                # Show tooltip on hover
                self.kb_status_dot.bind("<Enter>", lambda e: self._show_kb_tooltip(e))
                self.kb_status_dot.bind("<Leave>", lambda e: self._hide_kb_tooltip(e))
            except Exception:
                pass
        except Exception:
            self.kb_status_dot = None
            self.kb_status_tooltip_text = ""
        
    def create_burger_button(self):
        self.burger_btn = ctk.CTkButton(
            self.root,
            text="☰",
            font=("Arial", 20),
            fg_color="transparent",
            hover_color="#333333",
            width=40,
            height=40,
            command=self.toggle_sidebar
        )
        self.burger_btn.place(x=20, y=10)
        
    def create_welcome_message(self, animate=True):
        welcome_frame = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        welcome_frame.pack(pady=(80, 20), fill="x")
        
        text_color = "#FFFFFF"
        self.welcome_label = ctk.CTkLabel(
            welcome_frame,
            text=self._get_welcome_message(),
            font=("Arial", 28, "bold"),
            text_color=text_color,
            justify="center"
        )
        self.welcome_label.pack(anchor="center")
        if animate:
            self.animate_fade_in(self.welcome_label)
        
    def animate_fade_in(self, label, step=0):
        if step > 25:
            label.configure(text_color="#FFFFFF")
            return
            
        # Interpolate from background #000000 to white #FFFFFF
        factor = step / 25
        r = int(0 + (255 - 0) * factor)
        g = int(0 + (255 - 0) * factor)
        b = int(0 + (255 - 0) * factor)
        
        color = f"#{r:02x}{g:02x}{b:02x}"
        
        try:
            label.configure(text_color=color)
            self.root.after(20, lambda: self.animate_fade_in(label, step + 1))
        except Exception:
            pass
        
    def create_input_area(self):
        # Input container
        self.input_container = ctk.CTkFrame(
            self.main_area,
            fg_color="#1a1a1a",
            border_width=1,
            border_color="#333333",
            corner_radius=30,
            # Remove fixed height to allow attachment label to be visible
            width=850  # Fixed width for centering feel
        )
        self.input_container.grid(row=2, column=0, pady=(10, 40), padx=20)
        self.input_container.grid_columnconfigure(1, weight=1)
        self.input_container.bind("<Enter>", self._on_input_enter)
        self.input_container.bind("<Leave>", self._on_input_leave)
        
        # Plus button
        self.plus_btn = ctk.CTkButton(
            self.input_container,
            text="✚",
            font=("Arial", 18),
            fg_color="transparent",
            hover_color="#333333",
            width=35,
            height=35,
            corner_radius=17,
            command=self.show_plus_menu
        )
        self.plus_btn.grid(row=0, column=0, padx=(10, 5), pady=5)
        self.plus_btn.bind("<Enter>", self._on_input_enter)
        self.plus_btn.bind("<Leave>", self._on_input_leave)
        
        # Multi-line Text input (Expanding)
        self.input_field = ctk.CTkTextbox(
            self.input_container,
            font=("Arial", 15),
            fg_color="transparent",
            border_width=0,
            height=95,
            width=720,
            wrap="word",
            activate_scrollbars=False,
            padx=10,
            pady=8
        )
        self.input_field.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        self.input_field.bind("<Return>", self._on_input_enter_key)
        self.input_field.bind("<Shift-Return>", self._insert_newline)
        self.input_field.bind("<KeyRelease>", self._adjust_input_height)
        self.input_field.bind("<Enter>", self._on_input_enter)
        self.input_field.bind("<Leave>", self._on_input_leave)
        
        # Attachment Label
        self.attachment_label = ctk.CTkLabel(
            self.input_container, 
            text="", 
            font=("Inter", 11, "italic"),
            text_color="#3a7ebf" # A nice blue color
        )
        self.attachment_label.grid(row=1, column=1, sticky="w", padx=10)
        self.current_attachment = None # To store the file path internally

        # Voice button
        self.voice_btn = ctk.CTkButton(
            self.input_container,
            text="🎤",
            font=("Arial", 18),
            fg_color="transparent",
            hover_color="#333333",
            width=35,
            height=35,
            corner_radius=17,
            command=self.voice_input
        )
        self.voice_btn.grid(row=0, column=2, padx=5, pady=5)
        self.voice_btn.bind("<Enter>", self._on_input_enter)
        self.voice_btn.bind("<Leave>", self._on_input_leave)

        # Send button
        self.send_btn = ctk.CTkButton(
            self.input_container,
            text="➤",
            font=("Arial", 18),
            fg_color="#4a5fe8",
            hover_color="#3a4fd8",
            width=35,
            height=35,
            corner_radius=17,
            command=self.animate_send_button_click
        )
        self.send_btn.grid(row=0, column=3, padx=(5, 10), pady=5)
        self.send_btn.bind("<Enter>", self._on_input_enter)
        self.send_btn.bind("<Leave>", self._on_input_leave)

        # Stop Speaking button (initially hidden)
        self.stop_speech_btn = ctk.CTkButton(
            self.input_container,
            text="🔇",
            font=("Arial", 16),
            fg_color="#b34a4a",
            hover_color="#8b3a3a",
            width=35,
            height=35,
            corner_radius=17,
            command=self.stop_speech
        )
        self.stop_speech_btn.bind("<Enter>", self._on_input_enter)
        self.stop_speech_btn.bind("<Leave>", self._on_input_leave)

        # # High-level search button to fix NameError from log
        # high_btn = ctk.CTkButton(
        #     self.input_container,
        #     text="🧠",
        #     font=("Arial", 18),
        #     fg_color="transparent",
        #     hover_color="#2a2a35",
        #     width=35,
        #     height=35,
        #     corner_radius=17,
        #     command=self.high_level_search
        # )
        # high_btn.grid(row=0, column=4, padx=5, pady=5)
        # high_btn.bind("<Enter>", self._on_input_enter)
        # high_btn.bind("<Leave>", self._on_input_leave)
        
        # Stop button (initially hidden)
        self.stop_btn = ctk.CTkButton(
            self.input_container,
            text="⏹",
            font=("Arial", 16),
            fg_color="#b34a4a",
            hover_color="#8b3a3a",
            width=35,
            height=35,
            corner_radius=17,
            command=self.handle_stop_generation
        )
        # self.stop_btn is not gridded initially
        
    def _adjust_input_height(self, event=None):
        """Expand the input box as the user types, including wrapped lines."""
        content = self.input_field.get("1.0", "end-1c")
        if not content.strip():
            self.input_field.configure(height=95)
            return

        try:
            display_lines = int(self.input_field.count("1.0", "end-1c", "displaylines")[0])
        except Exception:
            display_lines = content.count('\n') + 1

        # Scale height to visible lines, with a minimum and maximum.
        new_height = min(max(95, (display_lines * 24) + 12), 180)
        self.input_field.configure(height=new_height)

    def _on_input_enter_key(self, event=None):
        """Send the message on Enter, but keep Shift+Enter for new lines."""
        self.send_message()
        return "break"

    def _insert_newline(self, event=None):
        """Insert a newline when Shift+Enter is pressed."""
        try:
            self.input_field.insert(tk.INSERT, "\n")
        except Exception:
            pass
        return "break"

    def _on_input_enter(self, event):
        if hasattr(self, 'input_container') and self.input_container.winfo_exists():
            self.input_container.configure(border_color="#4a5fe8")

    def _on_input_leave(self, event):
        if hasattr(self, 'input_container') and self.input_container.winfo_exists():
            # Check if mouse is still inside the container's bounding box
            x = self.input_container.winfo_rootx()
            y = self.input_container.winfo_rooty()
            w = self.input_container.winfo_width()
            h = self.input_container.winfo_height()
            
            mx, my = self.root.winfo_pointerxy()
            
            if x <= mx <= x + w and y <= my <= y + h:
                return
                
            self.input_container.configure(border_color="#333333")

    def show_plus_menu(self):
        if hasattr(self, '_plus_menu') and self._plus_menu and self._plus_menu.winfo_exists():
            self._cleanup_plus_menu()
            return

        # Create popup
        menu_height = 210
        self._plus_menu = ctk.CTkFrame(
            self.root,
            fg_color="#1a1a1a",
            border_width=1,
            border_color="#444444",
            corner_radius=10,
            width=240,
            height=menu_height
        )
        
        # Position above the plus button
        try:
            self.root.update_idletasks()
            
            # Calculate coordinates accounting for scaling
            bx = self.plus_btn.winfo_rootx()
            by = self.plus_btn.winfo_rooty()
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            
            scaling = 1.0
            if hasattr(self.plus_btn, "_get_widget_scaling"):
                scaling = self.plus_btn._get_widget_scaling() or 1.0
            
            # Convert physical screen delta to logical coordinates
            wx = (bx - rx) / scaling
            wy = (by - ry) / scaling
            
            # Place above
            self._plus_menu.place(x=wx, y=wy - (menu_height + 10))
        except Exception:
            # Fallback if coordinate calculation fails
            self._plus_menu.place(x=20, y=400)

        self._plus_menu.lift()
        self._plus_menu.pack_propagate(False)
        
        # Menu items with sub-text for a more "pro" look
        items = [
            ("Upload Photo", "JPG, PNG or GIF", "📷", self.handle_photo_upload),
            ("Google Drive", "Import from cloud", "☁️", self.handle_drive_upload),
            ("Attach File", "PDF, DOCX or TXT", "📎", self.handle_file_attach)
        ]
        
        # Configure the menu container for a "Glass" look
        self._plus_menu.configure(
            fg_color="#000000", 
            border_width=1, 
            border_color="#444444",
            corner_radius=12
        )
        
        for title, subtitle, icon, cmd in items:
            # 1. Individual Frame for each "Button" to allow multi-line text
            item_btn = ctk.CTkFrame(
                self._plus_menu, 
                fg_color="transparent", 
                cursor="hand2"
            )
            item_btn.pack(fill="x", padx=8, pady=4)
        
            # 2. Icon Label
            ctk.CTkLabel(
                item_btn, 
                text=icon, 
                font=("Inter", 18)
            ).pack(side="left", padx=(12, 10), pady=10)
        
            # 3. Text Container (Title + Description)
            text_frame = ctk.CTkFrame(item_btn, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True)
        
            ctk.CTkLabel(
                text_frame, 
                text=title, 
                font=("Inter", 13, "bold"), 
                anchor="w"
            ).pack(fill="x", pady=(5, 0))
        
            ctk.CTkLabel(
                text_frame, 
                text=subtitle, 
                font=("Inter", 11), 
                text_color="#CCCCCC", 
                anchor="w"
            ).pack(fill="x", pady=(0, 5))
        
            # 4. Hover & Click Logic
            # We bind the click to the whole frame for a better user experience
            def on_enter(e, widget=item_btn):
                widget.configure(fg_color="#333333")
            def on_leave(e, widget=item_btn):
                widget.configure(fg_color="transparent")
        
            item_btn.bind("<Enter>", on_enter)
            item_btn.bind("<Leave>", on_leave)
            
            # Click binding (including children)
            item_btn.bind("<Button-1>", lambda e, c=cmd: self._menu_action(c))
            
            # Bind all children recursively to ensure click works everywhere
            for child in item_btn.winfo_children():
                child.bind("<Button-1>", lambda e, c=cmd: self._menu_action(c))
                if isinstance(child, ctk.CTkFrame):
                    for subchild in child.winfo_children():
                        subchild.bind("<Button-1>", lambda e, c=cmd: self._menu_action(c))

        # Bind click outside
        self.root.after(100, self._bind_plus_menu_click_outside)

    def _cleanup_plus_menu(self):
        if hasattr(self, '_plus_menu_bind_id'):
            self.root.unbind("<Button-1>", self._plus_menu_bind_id)
            del self._plus_menu_bind_id
        if hasattr(self, '_plus_menu') and self._plus_menu:
            self._plus_menu.destroy()

    def _menu_action(self, callback):
        file_path = callback()
        if file_path:
            # Get just the name (e.g., "vacation.jpg") instead of the full path
            file_name = os.path.basename(file_path)
            
            # Save the path for later sending, but only show the name to the user
            self.current_attachment = file_path
            self.attachment_label.configure(text=f"📎 Attached: {file_name}")
            
            # Focus back on text box so user can type a caption
            self.input_field.focus()
        self._cleanup_plus_menu()

    def _bind_plus_menu_click_outside(self):
        if hasattr(self, '_plus_menu') and self._plus_menu.winfo_exists():
            self._plus_menu_bind_id = self.root.bind("<Button-1>", self._handle_plus_menu_global_click, add="+")

    def _handle_plus_menu_global_click(self, event):
        if hasattr(self, '_plus_menu') and self._plus_menu and self._plus_menu.winfo_exists():
            x, y = event.x_root, event.y_root
            px = self._plus_menu.winfo_rootx()
            py = self._plus_menu.winfo_rooty()
            pw = self._plus_menu.winfo_width()
            ph = self._plus_menu.winfo_height()
            
            # Check if click is inside menu
            if px <= x <= px + pw and py <= y <= py + ph:
                return

            # Check if click is on the plus button (to avoid double toggle)
            if self.plus_btn.winfo_exists():
                bx = self.plus_btn.winfo_rootx()
                by = self.plus_btn.winfo_rooty()
                bw = self.plus_btn.winfo_width()
                bh = self.plus_btn.winfo_height()
                if bx <= x <= bx + bw and by <= y <= by + bh:
                    return

            self._cleanup_plus_menu()

    def handle_photo_upload(self):
        if not filedialog: return None
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
        return path

    def handle_drive_upload(self):
        if not filedialog: return None
        path = filedialog.askopenfilename(title="Select file to upload to Drive")
        return path

    def handle_file_attach(self):
        if not filedialog: return None
        path = filedialog.askopenfilename()
        if path:
            # Ingest into Document QA Handler for RAG in background
            def ingest():
                try:
                    if self.doc_qa_handler:
                        res = self.doc_qa_handler.add_document(path)
                        if res["success"]:
                            self.root.after(0, lambda: self.notify_popup_text(f"Document '{res['filename']}' analyzed and added to context.", title="Document QA", icon="✅"))
                        else:
                            self.root.after(0, lambda: self.notify_popup_text(f"Error adding document: {res.get('error', 'Unknown error')}", title="Document QA", icon="❌"))
                    else:
                        self.root.after(0, lambda: self.notify_popup_text("Document QA handler not initialized.", title="Document QA", icon="⚠️"))
                except Exception as e:
                    logging.error(f"Error ingesting document: {e}", exc_info=True)
                    self.root.after(0, lambda: self.notify_popup_text(f"Error: {e}", title="Document QA", icon="❌"))
            
            threading.Thread(target=ingest, daemon=True).start()
        return path

    def animate_send_button_click(self):
        """Animate send button with smooth color highlight (optimized)."""
        def animate_step(step=0):
            if step > 6:
                try:
                    if self.send_btn.winfo_exists():
                        self.send_btn.configure(fg_color="#4a5fe8")
                except Exception:
                    pass
                return
            
            try:
                if not self.send_btn.winfo_exists():
                    return
                
                progress = step / 6
                r = int(0x5a + (0x4a - 0x5a) * progress)
                g = int(0x7f + (0x5f - 0x7f) * progress)
                b = int(0xf8 + (0xe8 - 0xf8) * progress)
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                self.send_btn.configure(fg_color=color)
                self.root.after(50, lambda: animate_step(step + 1))
            except Exception:
                pass
        
        animate_step(0)
        self.send_message()

    def send_message(self):
        # Check if limit reached
        if not self.is_logged_in and self.user_message_count >= 3:
            self.show_auth_popup()
            return

        if self.is_listening:
            return

        message = self.input_field.get("1.0", "end-1c").strip()
        attachment_path = getattr(self, 'current_attachment', None)

        if attachment_path:
            self.current_attachment = None
            self.attachment_label.configure(text="")
            
        if not message and not attachment_path:
            return
            
        if message.lower().startswith("/search "):
            self.input_field.delete("1.0", 'end')
            self.high_level_search(message[8:].strip())
            return
            
        if message.lower().startswith("/load_dataset"):
            self.input_field.delete("1.0", 'end')
            parts = message[13:].strip().split()
            
            positional_args = []
            keyword_args = {}
            
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    if value.lower() == 'true':
                        keyword_args[key] = True
                    elif value.lower() == 'false':
                        keyword_args[key] = False
                    else:
                        keyword_args[key] = value
                else:
                    positional_args.append(part)

            dataset_name = positional_args[0] if positional_args else "rotten_tomatoes"
            config_name = None
            split = None

            if len(positional_args) > 2: # e.g. /load_dataset glue mrpc train
                config_name = positional_args[1]
                split = positional_args[2]
            elif len(positional_args) > 1: # e.g. /load_dataset glue mrpc  OR  /load_dataset rotten_tomatoes train
                if positional_args[1] in ['train', 'test', 'validation']:
                    split = positional_args[1]
                else:
                    config_name = positional_args[1]
            
            self.load_hf_dataset(dataset_name, config_name, split, **keyword_args)
            return
            
        if message.lower().startswith("/tokenize_dataset"):
            self.input_field.delete("1.0", 'end')
            args = message[18:].strip().split()
            model_name = args[0] if args else "gpt2"
            column_name = args[1] if len(args) > 1 else "instruction"
            self.tokenize_loaded_dataset(model_name, column_name)
            return
            
        if message.lower().startswith("/train_model"):
            self.input_field.delete("1.0", 'end')
            args = message[13:].strip().split()
            model_name = args[0] if args else "gpt2"
            self.train_and_save_model(model_name)
            return

        if message.lower().startswith("/load_brain"):
            self.input_field.delete("1.0", 'end')
            self.load_local_brain()
            return

        if message.lower().startswith("/hf_login"):
            self.input_field.delete("1.0", 'end')
            token = message[9:].strip()
            self.login_huggingface(token)
            return

        if message.lower().startswith("/describe_image"):
            self.input_field.delete("1.0", 'end')
            url = message[15:].strip()
            self.describe_image_hf(url if url else None)
            return

        if message.lower().startswith("/speak"):
            self.input_field.delete("1.0", 'end')
            text = message[6:].strip()
            if text:
                self.speak_reply(text)
            return
            
        if message.lower().startswith("/list_models"):
            self.input_field.delete("1.0", 'end')
            self.list_google_models()
            return

        # Clear welcome message if first message
        if len(self.chat_history) == 0:
            for widget in self.chat_container.winfo_children():
                widget.destroy()
        
        # Add user message
        msg_frame, _ = self.add_message(message, is_user=True, animate=False, attachment_path=attachment_path)
        self._remember_activity("user_query", message)

        # Save user message to DB
        if self.is_logged_in and self.account_db:
            if not self.current_session_id:
                title = message[:30] + "..." if len(message) > 30 else (message or "Attachment")
                self.current_session_id = self.account_db.create_chat_session(self.current_user_id, title)
                self.refresh_sidebar_chats()
            
            db_text = message
            if attachment_path:
                db_text = f"{message} [Attachment: {attachment_path}]".strip()
            msg_id = self.account_db.add_chat_message(self.current_session_id, 'user', db_text)
            msg_frame.message_id = msg_id

        # Clear input
        self.input_field.delete("1.0", 'end')
        self._adjust_input_height()
        
        # Check message count for auth popup
        self.user_message_count += 1
        if self.user_message_count == 3 and not self.is_logged_in:
            self.root.after(1000, self.show_auth_popup)

        # Show thinking animation and disable send button
        self.stop_generation_event = threading.Event()
        self.send_btn.configure(state="disabled")
        thinking_frame = self.add_thinking_animation()
        
        def worker(user_msg, placeholder_frame, stop_event, attachment=None):
            start_time = time.time()
            logging.info(f"Worker thread started for message: {user_msg[:50]}...")
            try:
                reply = self.generate_reply(user_msg, attachment_path=attachment)
                logging.info(f"Reply generated: {reply[:100]}...")
                self._remember_activity("bot_response", reply)
            except Exception as e:
                reply = f"Error generating reply: {e}"
                logging.error(f"Error in worker: {e}", exc_info=True)

            if stop_event.is_set():
                logging.info("Stop event set, returning early")
                return

            elapsed = time.time() - start_time
            min_delay = 0.8
            if elapsed < min_delay:
                time.sleep(min_delay - elapsed)

            bot_msg_id = None
            if reply is not None:
                if self.is_logged_in and self.account_db and self.current_session_id:
                    try:
                        bot_msg_id = self.account_db.add_chat_message(self.current_session_id, 'bot', reply)
                        logging.info(f"Bot message saved to DB with ID: {bot_msg_id}")
                    except Exception as e:
                        logging.error(f"Error saving message to DB: {e}")
                
                logging.info("Calling _replace_animation_with_message...")
                self.root.after(0, lambda: self._replace_animation_with_message(placeholder_frame, reply, bot_msg_id))
            else:
                # For features that show popups, just remove the animation
                logging.info("Feature activated with popup, removing animation...")
                self.root.after(0, lambda: self._remove_placeholder_animation(placeholder_frame))

        threading.Thread(target=worker, args=(message, thinking_frame, self.stop_generation_event, attachment_path), daemon=True).start()



    def voice_input(self):
        """Capture voice input in a background thread, add the user message, then generate and speak a reply."""
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.notify_popup("Voice Input", "Voice input unavailable (SpeechRecognition not installed).", "❌")
            return

        # If already listening, treat this as a Cancel action
        if self.is_listening:
            self.stop_listening_flag = True
            self.reset_voice_ui()
            self.input_field.delete("1.0", 'end')
            self.notify_popup("Listening Cancelled", "Listening cancelled.", "ℹ️")
            return

        # Start listening state
        self.is_listening = True
        self.stop_listening_flag = False
        self.listening_session_id += 1
        current_session = self.listening_session_id
        self.voice_btn.configure(text="🟥", fg_color="#be3535", hover_color="#8b3a3a")
        
        if self.big_mic_btn:
            try:
                self.big_mic_btn.configure(text="🟥", fg_color="#be3535", hover_color="#8b3a3a")
                if self.mic_status_label:
                    self.mic_status_label.configure(text="Listening...")
            except Exception:
                pass
        
        # Show listening indicator - disabled
        # self.show_voice_overlay("Listening...")
        self.input_field.delete("1.0", 'end')
        self.input_field.insert("1.0", "Listening...")
        self.input_field.configure(state="disabled")
        self.voice_animation()

        def listen_worker():
            text = self.audio_handler.listen_to_audio()

            # Check if cancelled
            if self.stop_listening_flag or self.listening_session_id != current_session:
                return
            
            # Reset UI on main thread
            self.root.after(0, self.reset_voice_ui)

            # Handle various non-text responses from the recognizer helper
            if text is None:
                self.root.after(0, lambda: self.notify_popup("Voice Input", "No microphone available or permission denied.", "❌"))
                def clear_listening():
                    if self.input_field.get() == "Listening...":
                        self.input_field.delete("1.0", 'end')
                self.root.after(0, clear_listening)
                return

            if isinstance(text, str) and (text.startswith("Error:") or text.startswith("Sorry,")):
                self.root.after(0, lambda: self.notify_popup("Voice Input", text, "❌"))
                def clear_listening():
                    if self.input_field.get() == "Listening...":
                        self.input_field.delete("1.0", 'end')
                self.root.after(0, clear_listening)
                return

            # Write down the words in the input field
            def update_input():
                self.input_field.delete("1.0", 'end')
                self.input_field.insert("1.0", text)
                self.send_message()

            self.root.after(0, update_input)

        threading.Thread(target=listen_worker, daemon=True).start()

    def interpolate_color(self, c1, c2, t):
        """Interpolate between two hex colors."""
        if c1.startswith("#"): c1 = c1[1:]
        if c2.startswith("#"): c2 = c2[1:]
        
        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
        
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        return f"#{r:02x}{g:02x}{b:02x}"

    def voice_animation(self, start_time=None):
        """Animate the voice button with a smooth breathing effect while listening."""
        if not self.is_listening:
            return
        
        if start_time is None:
            start_time = time.time()
            
        # Pulse period in seconds
        period = 1.5 
        t = time.time() - start_time
        # Sine wave 0..1
        factor = (math.sin(t * 2 * math.pi / period) + 1) / 2
        
        # Interpolate between base red and bright red
        color1 = "#be3535" 
        color2 = "#ff5555" 
        
        current_color = self.interpolate_color(color1, color2, factor)
        
        try:
            self.voice_btn.configure(fg_color=current_color)
            if self.big_mic_btn:
                self.big_mic_btn.configure(fg_color=current_color)
        except Exception:
            pass
        self.root.after(20, lambda: self.voice_animation(start_time))

    def reset_voice_ui(self):
        """Reset voice button to default state."""
        self.is_listening = False
        try:
            self.input_field.configure(state="normal")
            self.voice_btn.configure(text="🎤", fg_color="transparent", hover_color="#444444")
            if self.big_mic_btn:
                self.big_mic_btn.configure(text="🎤", fg_color="#333333", hover_color="#444444")
                if self.mic_status_label:
                    self.mic_status_label.configure(text="Tap to speak")
        except Exception:
            pass

        if getattr(self, 'overlay_active', False):
            # self.update_voice_overlay_message("Jarvis is active. Say 'goodbye' to close.")
            pass

    def mic_test(self):
        """Test microphone and speaker."""
        self.notify_popup("Mic Test", "Testing microphone... Please speak.", "🎙️")

        def worker():
            text = self.audio_handler.listen_to_audio()
            if text and not text.startswith("Error") and not text.startswith("Sorry"):
                self.root.after(0, lambda: self.notify_popup("Mic Test", f"Heard: {text}", "✅"))
                self.speak_reply("Microphone check passed.")
            else:
                msg = text if text else "Microphone test failed or no speech detected."
                self.root.after(0, lambda: self.notify_popup("Mic Test", msg, "❌"))

        threading.Thread(target=worker, daemon=True).start()

    def _load_circular_avatar(self, path):
        """Load an image and apply a circular mask."""
        try:
            from PIL import Image, ImageDraw, ImageOps
            if not os.path.exists(path):
                return None
            img = Image.open(path).convert("RGBA")
            # Process at higher resolution for quality
            src_size = (200, 200)
            img = ImageOps.fit(img, src_size, centering=(0.5, 0.5))
            
            mask = Image.new('L', src_size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + src_size, fill=255)
            
            img.putalpha(mask)
            return ctk.CTkImage(light_image=img, dark_image=img, size=(26, 26))
        except Exception:
            return None

    def handle_profile_click(self, event):
        if self.is_logged_in:
            self.show_profile_popup(event)
        else:
            self.open_account_page(event)

    def handle_profile_hover(self, event):
        if self.is_logged_in:
            self.show_profile_popup(event, toggle=False)

    def show_profile_popup(self, event, toggle=True):
        if hasattr(self, '_profile_popup') and self._profile_popup and self._profile_popup.winfo_exists():
            if toggle:
                self._profile_popup.destroy()
            return

        # Create popup as internal Frame (overlay)
        self._profile_popup = ctk.CTkFrame(
            self.root, 
            fg_color="#1a1a1a", 
            border_width=1,
            border_color="#444444",
            corner_radius=10,
            width=300,
            height=280
        )
        
        # Calculate position
        widget = event.widget
        rel_x = widget.winfo_rootx() - self.root.winfo_rootx()
        rel_y = widget.winfo_rooty() - self.root.winfo_rooty()
        
        # Default to below
        pos_x = rel_x
        pos_y = rel_y + widget.winfo_height() + 5
        
        # Check bounds
        if pos_y + 280 > self.root.winfo_height():
            pos_y = rel_y - 285
            
        self._profile_popup.place(x=pos_x, y=pos_y)
        self._profile_popup.lift()
        self._profile_popup.pack_propagate(False)
        
        frame = self._profile_popup
        
        # Info
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=15)
        
        name = "User"
        username = ""
        email = ""
        joined = ""
        last_login = ""

        if self.account_db and self.current_user_id:
             user_info = self.account_db.get_user_info(self.current_user_id)
             if user_info:
                name = user_info.get('full_name', 'User') or "User"
                username = user_info.get('username', '')
                email = user_info.get('email', '')
                joined = user_info.get('created_at', '').split()[0]
                last_login = user_info.get('last_login', '').split('.')[0]
             
        # Display User Info
        ctk.CTkLabel(info_frame, text=name, font=("Arial", 16, "bold"), anchor="w").pack(fill="x", pady=(0, 5))
        
        def add_detail(label, value):
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{label}: ", font=("Arial", 11, "bold"), text_color="gray", width=70, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Arial", 11), text_color="#dddddd", anchor="w").pack(side="left")

        add_detail("Username", username)
        add_detail("Email", email)
        add_detail("Joined", joined)
        add_detail("Last Login", last_login)
        
        # Divider
        ctk.CTkFrame(frame, height=2, fg_color="#333333").pack(fill="x", padx=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        photo_text = "Change Photo" if self.avatar_image else "Upload Photo"
        
        ctk.CTkButton(
            btn_frame, 
            text=f"📷  {photo_text}", 
            fg_color="transparent", 
            hover_color="#333333", 
            anchor="w", 
            height=35,
            command=self.upload_avatar
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            btn_frame, 
            text="⚙  Account Settings", 
            fg_color="transparent", 
            hover_color="#333333", 
            anchor="w", 
            height=35,
            command=lambda: self.open_account_page(start_mode="profile")
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            btn_frame, 
            text="🚪  Logout", 
            fg_color="transparent", 
            hover_color="#333333", 
            text_color="#ff5555",
            anchor="w", 
            height=35,
            command=self.confirm_logout
        ).pack(fill="x", pady=2)
        
        ctk.CTkButton(frame, text="×", width=20, height=20, fg_color="transparent", hover_color="#333333", command=self._profile_popup.destroy).place(relx=0.9, rely=0.05, anchor="ne")

        # Bind click outside to close
        # We use 'after' to avoid immediate triggering from the opening click
        self.root.after(100, self._bind_popup_click_outside)

    def _bind_popup_click_outside(self):
        if hasattr(self, '_profile_popup') and self._profile_popup.winfo_exists():
            self._popup_bind_id = self.root.bind("<Button-1>", self._handle_global_click, add="+")

    def _cleanup_popup(self):
        if hasattr(self, '_popup_bind_id'):
            self.root.unbind("<Button-1>", self._popup_bind_id)
            del self._popup_bind_id
        if hasattr(self, '_profile_popup') and self._profile_popup:
            self._profile_popup.destroy()

    def _handle_global_click(self, event):
        if hasattr(self, '_profile_popup') and self._profile_popup and self._profile_popup.winfo_exists():
            x, y = event.x_root, event.y_root
            px = self._profile_popup.winfo_rootx()
            py = self._profile_popup.winfo_rooty()
            pw = self._profile_popup.winfo_width()
            ph = self._profile_popup.winfo_height()
            
            # If click is outside the popup rectangle
            if not (px <= x <= px + pw and py <= y <= py + ph):
                self._cleanup_popup()

    def show_feature_popup(self, title, message, icon="✅"):
        """Show a popup for feature activation."""
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.title(title)
            win.geometry("400x200")
            win.resizable(False, False)
            
            # Center window
            win.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (200)
            y = (win.winfo_screenheight() // 2) - (100)
            win.geometry(f"+{x}+{y}")
            
            # Icon and message
            ctk.CTkLabel(win, text=icon, font=("Arial", 48)).pack(pady=(20, 10))
            ctk.CTkLabel(win, text=title, font=("Arial", 16, "bold")).pack(pady=(0, 10))
            ctk.CTkLabel(win, text=message, font=("Arial", 12), wraplength=350).pack(pady=(0, 20))
            
            # OK button
            ctk.CTkButton(win, text="OK", command=win.destroy, width=100).pack()
            
            win.transient(self.root)
            win.grab_set()
            win.focus()
        elif TK_AVAILABLE:
            from tkinter import messagebox
            messagebox.showinfo(title, message)
        else:
            # Fallback: print to console
            print(f"{icon} {title}: {message}")

    def notify_popup(self, title, message, icon="ℹ️"):
        """Show a small popup notification for non-chat events."""
        if self.root and hasattr(self, 'show_feature_popup'):
            self.root.after(0, lambda: self.show_feature_popup(title, message, icon))

    def notify_popup_text(self, message, title="Notification", icon="ℹ️"):
        """Show a generic popup notification with a simple message."""
        if self.root and hasattr(self, 'show_feature_popup'):
            self.root.after(0, lambda: self.show_feature_popup(title, message, icon))

    def show_voice_overlay(self, message="Listening..."):
        """Show a small voice assistant overlay at the screen border."""
        self.overlay_active = True

        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
        except Exception:
            screen_width, screen_height = 1280, 800

        width, height = 320, 120
        x = screen_width - width - 24
        y = screen_height - height - 80

        if hasattr(self, 'voice_overlay') and self.voice_overlay and self.voice_overlay.winfo_exists():
            try:
                self.voice_overlay_label.configure(text=message)
                self.voice_overlay.geometry(f"{width}x{height}+{x}+{y}")
                return
            except Exception:
                self.hide_voice_overlay()

        self.voice_overlay = ctk.CTkToplevel(self.root)
        self.voice_overlay.overrideredirect(True)
        self.voice_overlay.attributes("-topmost", True)
        self.voice_overlay.configure(fg_color="#11151f")
        self.voice_overlay.geometry(f"{width}x{height}+{x}+{y}")

        self.voice_overlay_frame = ctk.CTkFrame(self.voice_overlay, fg_color="#1b1f2c", border_width=1, border_color="#4a5fe8", corner_radius=20)
        self.voice_overlay_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.96, relheight=0.92)

        self.voice_overlay_label = ctk.CTkLabel(
            self.voice_overlay_frame,
            text=message,
            font=("Arial", 13, "bold"),
            text_color="#ffffff",
            wraplength=280,
            justify="center"
        )
        self.voice_overlay_label.pack(expand=True, fill="both", padx=10, pady=10)

        self.voice_overlay.after(100, lambda: self.voice_overlay.lift())

    def update_voice_overlay_message(self, message: str):
        if hasattr(self, 'voice_overlay_label') and self.voice_overlay_label.winfo_exists():
            try:
                self.voice_overlay_label.configure(text=message)
            except Exception:
                pass

    def hide_voice_overlay(self):
        self.overlay_active = False
        try:
            if hasattr(self, 'voice_overlay') and self.voice_overlay and self.voice_overlay.winfo_exists():
                self.voice_overlay.destroy()
        except Exception:
            pass
        self.voice_overlay = None
        self.voice_overlay_label = None
        self.voice_overlay_frame = None

    def activate_voice_overlay(self, message="Listening..."):
        # Voice overlay permanently disabled as per user request
        # self._root_was_visible_before_overlay = self.root.state() != 'withdrawn'
        # try:
        #     self.root.withdraw()
        # except Exception:
        #     pass
        # self.show_voice_overlay(message)
        pass

    def deactivate_voice_overlay(self):
        self.hide_voice_overlay()
        if getattr(self, '_root_was_visible_before_overlay', False):
            try:
                self.root.deiconify()
                self.root.lift()
            except Exception:
                pass

    def confirm_logout(self):
        self._cleanup_popup()
        
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
            win.title("Logout")
            win.geometry("300x150")
            win.resizable(False, False)
            
            # Center window
            win.update_idletasks()
            x = (win.winfo_screenwidth() // 2) - (150)
            y = (win.winfo_screenheight() // 2) - (75)
            win.geometry(f"+{x}+{y}")
            
            ctk.CTkLabel(win, text="Are you sure you want to logout?", font=("Arial", 14)).pack(pady=(30, 20))
            
            btn_frame = ctk.CTkFrame(win, fg_color="transparent")
            btn_frame.pack(pady=10)
            
            def yes():
                win.destroy()
                self.perform_logout()
                
            def no():
                win.destroy()
                
            ctk.CTkButton(btn_frame, text="Logout", command=yes, width=100, fg_color="#be3535", hover_color="#8b3a3a").pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text="Cancel", command=no, width=100, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="left", padx=10)
            
            win.transient(self.root)
            win.grab_set()
        elif TK_AVAILABLE:
            from tkinter import messagebox
            if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
                self.perform_logout()

    def perform_logout(self):
        self._cleanup_popup()
        
        # Clear chat history
        self.new_chat()
        
        self.is_logged_in = False
        self.is_premium = False
        self.current_user_id = None
        self.current_session_id = None
        self.refresh_sidebar_chats()

        # Clear saved session using the session manager
        clear_session()
        
        if hasattr(self, 'profile_label'):
            self.profile_label.configure(text="Guest")
            
        self.update_avatar_ui()
            
        if hasattr(self, 'sidebar_logout_btn'):
            self.sidebar_logout_btn.pack_forget()
        if hasattr(self, 'clear_history_btn'):
            self.clear_history_btn.grid_remove()
            
        if hasattr(self, 'upgrade_btn'):
            self.upgrade_btn.configure(text="✦  Upgrade", fg_color="#4a5fe8", border_width=0, state="normal")
            

    def upload_avatar(self):
        if hasattr(self, '_profile_popup') and self._profile_popup:
            self._cleanup_popup()
            
        if not filedialog:
            self.notify_popup_text("File dialog not available.", title="File Upload", icon="❌")
            return
        
        # Run file dialog in main thread
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if not path:
            return
        
        # Process image in background thread to avoid lag
        def process_avatar():
            try:
                from PIL import Image
                img = Image.open(path)
                filename = f"user_avatar_{self.current_user_id}.png" if self.current_user_id else "user_avatar.png"
                img.save(filename)
                logging.info(f"Avatar saved: {filename}")
                # Update UI on main thread
                self.root.after(0, self.update_avatar_ui)
                self.root.after(0, lambda: self.notify_popup_text("Avatar updated successfully!", title="Avatar", icon="✅"))
            except Exception as e:
                logging.error(f"Error saving avatar: {e}", exc_info=True)
                self.root.after(0, lambda: self.notify_popup_text(f"Error saving avatar: {e}", title="Avatar", icon="❌"))
        
        threading.Thread(target=process_avatar, daemon=True).start()

    def update_avatar_ui(self):
        try:
            if self.current_user_id is not None:
                filename = f"user_avatar_{self.current_user_id}.png"
                self.avatar_image = self._load_circular_avatar(filename)
            else:
                self.avatar_image = None
            
            if self.avatar_image:
                if hasattr(self, 'profile_icon'):
                    self.profile_icon.configure(image=self.avatar_image, text="", fg_color="transparent", hover=False)
                if hasattr(self, 'top_bar_user_icon'):
                    self.top_bar_user_icon.configure(image=self.avatar_image, text="", fg_color="transparent", hover=False)
            else:
                if hasattr(self, 'profile_icon'):
                    self.profile_icon.configure(image=None, text="👤", fg_color="#333333", hover_color="#444444")
                if hasattr(self, 'top_bar_user_icon'):
                    self.top_bar_user_icon.configure(image=None, text="👤", fg_color="#333333", hover_color="#444444")
        except Exception:
            pass

    # ----------------- Tkinter fallback helpers -----------------
    def create_tk_fallback(self):
        # Chat display
        self.chat_text = tk.Text(self.root, wrap="word", state="disabled", bg="#121212", fg="#FFFFFF")
        self.chat_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Input frame
        bottom = tk.Frame(self.root, bg="#10101a")
        bottom.pack(fill="x", padx=10, pady=(0,10))

        self.input_field_tk = tk.Entry(bottom, font=("Arial", 12), bg="#1a1a1a", fg="#FFFFFF", insertbackground="#FFFFFF")
        self.input_field_tk.pack(side="left", fill="x", expand=True, padx=(0,8), pady=8)
        self.input_field_tk.bind("<Return>", lambda e: self.send_message_tk())

        send_btn = tk.Button(bottom, text="Send", command=self.send_message_tk, bg="#4a5fe8", fg="#FFFFFF", activebackground="#3a4fd8")
        send_btn.pack(side="right", pady=8)

        # Welcome message
        greeting = self._get_time_of_day_greeting()
        self.add_message_tk(f"{greeting}, Friend. What can I do for you?", is_user=False)

    def add_message_tk(self, text: str, is_user: bool = True) -> None:
        self.chat_text.configure(state="normal")
        prefix = "You: " if is_user else "JARVIS: "
        self.chat_text.insert("end", f"{prefix}{text}\n\n")
        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def send_message_tk(self):
        message = self.input_field_tk.get().strip()
        if not message:
            return
        self.input_field_tk.delete(0, 'end')
        self.add_message_tk(message, is_user=True)

        def worker(user_msg):
            reply = self.generate_reply(user_msg)

            def finish():
                self.add_message_tk(reply, is_user=False)
                # speak reply asynchronously
                self.root.after(100, lambda: self.speak_reply(reply))

            try:
                self.root.after(0, finish)
            except Exception:
                finish()

        threading.Thread(target=worker, args=(message,), daemon=True).start()
        
    def show_auth_popup(self):
        """A sleek, centered modern modal for authentication."""
        if not CTK_AVAILABLE:
            return

        win = ctk.CTkToplevel(self.root)
        win.title("") # Clean title bar
        win.geometry("400x280")
        win.attributes("-topmost", True)
        win.configure(fg_color="#1a1a1a") # Deep dark background
        
        # Center window logic
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - 200
        y = (win.winfo_screenheight() // 2) - 140
        win.geometry(f"+{x}+{y}")
        
        # Icon or Header Spacer
        ctk.CTkLabel(
            win, text="🚀", font=("Arial", 40)
        ).pack(pady=(25, 0))
 
        ctk.CTkLabel(
            win, 
            text="Welcome Back", 
            font=("Inter", 22, "bold")
        ).pack(pady=(10, 0))
 
        ctk.CTkLabel(
            win, 
            text="Please sign in to access the\nResume Builder & AI tools.", 
            font=("Inter", 13),
            text_color="#888888"
        ).pack(pady=(5, 25))
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        # Navigation functions
        def go_login():
            win.destroy()
            self.open_account_page(start_mode="login")
        def go_register():
            win.destroy()
            self.open_account_page(start_mode="register")
            
        # Buttons with high-contrast styling
        ctk.CTkButton(
            btn_frame, 
            text="Sign In", 
            command=go_login, 
            width=140,
            height=40,
            corner_radius=8,
            font=("Inter", 14, "bold"),
            hover_color="#1d4ed8" # Brighter blue on hover
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="Create Account", 
            command=go_register, 
            width=140,
            height=40,
            corner_radius=8,
            font=("Inter", 14),
            fg_color="transparent", 
            border_width=2,
            border_color="#333333",
            hover_color="#222222"
        ).pack(side="left", padx=10)
        
        win.transient(self.root)
        win.grab_set()

    def _scroll_to_bottom_if_enabled(self):
        """Scrolls the chat container to the bottom if auto-scroll is enabled."""
        if self.auto_scroll_var and self.auto_scroll_var.get():
            def _scroll():
                try:
                    # Use 'after' to give the UI a moment to render new widgets before scrolling
                    self.chat_container._parent_canvas.yview_moveto(1.0)
                except Exception:
                    pass # Fails gracefully if widget is destroyed
            self.root.after(20, _scroll)

    def _extract_user_name(self, user_info: Dict[str, Any]) -> str:
        name = user_info.get('full_name') or user_info.get('username') or "Friend"
        if isinstance(name, str) and name.strip():
            return name.split()[0]
        return "Friend"

    def _load_memory(self) -> Dict[str, Any]:
        if not self.memory_file:
            return {"users": {}, "global": {"interactions": []}}
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load memory file: {e}")
        return {"users": {}, "global": {"interactions": []}}

    def _save_memory(self) -> None:
        if not self.memory_file:
            return
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save memory file: {e}")

    def _get_user_memory(self) -> Dict[str, Any]:
        user_key = str(self.current_user_id) if self.is_logged_in and self.current_user_id else "guest"
        users = self.memory_data.setdefault("users", {})
        return users.setdefault(user_key, {"interactions": []})

    def _remember_activity(self, category: str, text: str) -> None:
        entry = {
            "time": datetime.datetime.now().isoformat(),
            "category": category,
            "text": text.strip()
        }
        user_memory = self._get_user_memory()
        history = user_memory.setdefault("interactions", [])
        history.append(entry)
        user_memory["interactions"] = history[-50:]

        if category == "user_query":
            global_history = self.memory_data.setdefault("global", {}).setdefault("interactions", [])
            global_history.append(entry)
            self.memory_data["global"]["interactions"] = global_history[-100:]

        self._save_memory()

    def _get_time_of_day_greeting(self) -> str:
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        if 12 <= hour < 17:
            return "Good afternoon"
        if 17 <= hour < 21:
            return "Good evening"
        return "Hello"

    def _get_dynamic_header(self) -> str:
        return ""

    def _get_welcome_message(self) -> str:
        greeting = self._get_time_of_day_greeting()
        name = self.current_user_name or "Friend"
        return f"{greeting}, {name}. What can I do for you?"

    def update_dynamic_header(self) -> None:
        if self.dynamic_header_label and self.dynamic_header_label.winfo_exists():
            try:
                self.dynamic_header_label.configure(text=self._get_dynamic_header())
            except Exception:
                pass
        if hasattr(self, 'welcome_label') and self.welcome_label and self.welcome_label.winfo_exists():
            try:
                self.welcome_label.configure(text=self._get_welcome_message())
            except Exception:
                pass
        self.root.after(60000, self.update_dynamic_header)

    def _summarize_document(self, document_path: str) -> str:
        if not os.path.exists(document_path):
            return "Document not found."
        filename = os.path.basename(document_path)
        extracted = self.doc_qa_handler.extract_document_text(document_path)
        if extracted.startswith("Error"):
            return extracted
        clean_text = extracted.strip().replace("\n", " ")
        summary = clean_text[:900]
        if len(clean_text) > 900:
            summary = summary.rsplit(' ', 1)[0] + "..."
        return f"I have read '{filename}'. Here is what it contains: {summary}"

    def _choose_time_of_day_voice_id(self) -> Optional[str]:
        if self.current_voice_id:
            return self.current_voice_id
        voices = self.audio_handler.get_voices()
        if not voices:
            return None
        return voices[0]['id']

    def _toggle_voice(self):
        """Save the voice preference when toggled."""
        if self.is_logged_in and self.account_db and self.current_user_id and self.voice_var:
            value = 1 if self.voice_var.get() else 0
            self.account_db.update_user_preference(self.current_user_id, 'voice_enabled', value)

    def _insert_formatted_text(self, textbox, text):
        """Insert text with stylish markdown-like formatting (bold, code, lists, etc.)"""
        import re
        
        lines = text.split('\n')
        for line_idx, line in enumerate(lines):
            # Check for list items (-, *, or numbered)
            if re.match(r'^\s*[-*]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                # Extract bullet and content
                match = re.match(r'^(\s*)([-*]|\d+\.)\s+(.+)$', line)
                if match:
                    indent, bullet, content = match.groups()
                    textbox.insert('end', indent + bullet + ' ')
                    # Format list item content
                    self._format_line_content(textbox, content)
                else:
                    self._format_line_content(textbox, line)
            # Check for section headers (ends with :)
            elif line.strip().endswith(':') and len(line.strip()) > 2:
                textbox.insert('end', line.strip(), 'section')
            else:
                self._format_line_content(textbox, line)
            
            if line_idx < len(lines) - 1:
                textbox.insert('end', '\n')
    
    def _format_line_content(self, textbox, content):
        """Format a line with bold, code, and emphasis styling"""
        import re
        
        # Pattern added to detect URLs: https?://...
        pattern = r'(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|_[^_]+_|https?://[^\s,;()]+)'
        parts = re.split(pattern, content)
        
        for part in parts:
            if not part:
                continue
            if part.startswith('***') and part.endswith('***'):
                # Bold italic
                clean_text = part[3:-3]
                textbox.insert('end', clean_text, ('bold', 'emphasis'))
            elif part.startswith('**') and part.endswith('**'):
                # Bold
                clean_text = part[2:-2]
                textbox.insert('end', clean_text, 'bold')
            elif part.startswith('`') and part.endswith('`'):
                # Code
                clean_text = part[1:-1]
                textbox.insert('end', clean_text, 'code')
            elif part.startswith('*') and part.endswith('*'):
                # Italic
                clean_text = part[1:-1]
                textbox.insert('end', clean_text, 'emphasis')
            elif part.startswith('_') and part.endswith('_'):
                # Italic (alternate)
                clean_text = part[1:-1]
                textbox.insert('end', clean_text, 'emphasis')
            elif part.startswith('http'):
                # URL link
                textbox.insert('end', part, 'link')
            else:
                # Regular text
                textbox.insert('end', part)

    def add_message(self, text, is_user=True, animate=False, message_id=None, attachment_path=None):
        # Show scrollbar if hidden
        try:
            if hasattr(self.chat_container, "_scrollbar") and not self.chat_container._scrollbar.winfo_viewable():
                self.chat_container._scrollbar.grid()
        except Exception:
            pass

        message_frame = ctk.CTkFrame(
            self.chat_container,
            fg_color="#333333" if is_user else "#1a2a3a",
            corner_radius=15 if is_user else 12
        )
        message_frame.pack(fill="x", pady=5, padx=20)
        message_frame.message_id = message_id
        
        # Icon (only for bot)
        if not is_user:
            icon = "🤖"
            icon_label = ctk.CTkLabel(message_frame, text=icon, font=("Arial", 16), fg_color="#1a2a3a")
            icon_label.grid(row=0, column=0, padx=15, pady=10, sticky="n")
        
        # Content container (for text + attachment)
        content_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        
        col = 0 if is_user else 1
        pad_x = (15, 15) if is_user else (0, 15)
        # Make the bot's content frame stretch, but keep user's aligned left
        content_sticky = "ew" if not is_user else "w"
        content_frame.grid(row=0, column=col, padx=pad_x, pady=10, sticky=content_sticky)
        
        # Display Attachment if present
        if attachment_path:
            try:
                ext = os.path.splitext(attachment_path)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                    from PIL import Image
                    if os.path.exists(attachment_path):
                        pil_img = Image.open(attachment_path)
                        max_width = 300
                        w_percent = (max_width / float(pil_img.size[0]))
                        h_size = int((float(pil_img.size[1]) * float(w_percent)))
                        if h_size > 300:
                            h_size = 300
                            w_percent = (h_size / float(pil_img.size[1]))
                            max_width = int((float(pil_img.size[0]) * float(w_percent)))
                        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(max_width, h_size))
                        img_label = ctk.CTkLabel(content_frame, text="", image=ctk_img)
                        img_label.pack(anchor="w", pady=(0, 5))
                else:
                    file_name = os.path.basename(attachment_path)
                    file_label = ctk.CTkLabel(content_frame, text=f"📎 {file_name}", font=("Arial", 12, "italic"), text_color="#aaaaaa")
                    file_label.pack(anchor="w", pady=(0, 5))
            except Exception as e:
                print(f"Error displaying attachment: {e}")

        # Message text
        msg_label = None
        if text:
            if not is_user:  # Use textbox for bot messages to support highlighting
                msg_label = ctk.CTkTextbox(
                    content_frame,
                    font=("Segoe UI", 16),
                    text_color="#E8E8E8",
                    wrap="word",
                    state="disabled",
                    fg_color="#0d1b2a",
                    border_width=0
                )
                msg_label.pack(anchor="w", fill="x")
                if not (is_user and animate):
                    msg_label.configure(state="normal")
                    # Configure tags for this textbox too
                    msg_label.tag_config("code", foreground="#FFD700", background="#1a2a3a")
                    msg_label.tag_config("bold", foreground="#6FD3FF")
                    msg_label.tag_config("emphasis", foreground="#FFD77F")
                    msg_label.tag_config("section", foreground="#FF6BAD")
                    msg_label.tag_config("link", foreground="#1e90ff", underline=True)
                    
                    msg_label.tag_bind("link", "<Button-1>", lambda e: self._on_link_click(e, msg_label))
                    msg_label.tag_bind("link", "<Enter>", lambda e: msg_label.configure(cursor="hand2"))
                    msg_label.tag_bind("link", "<Leave>", lambda e: msg_label.configure(cursor="xterm"))
                    
                    self._insert_formatted_text(msg_label, text)
                    msg_label.configure(state="disabled")
            else:  # User messages use label
                msg_label = ctk.CTkLabel(
                    content_frame,
                    text="" if animate else text,
                    font=("calibri", 18),
                    text_color="#FFFFFF",
                    wraplength=800,
                    anchor="w",
                    justify="left"
                )
                msg_label.pack(anchor="w")
        
        # Configure message column to expand so delete button pushes to right
        message_frame.grid_columnconfigure(col, weight=1)

        # Delete button
        del_btn = ctk.CTkButton(
            message_frame,
            text="×",
            font=("Arial", 12),
            width=20,
            height=20,
            fg_color="transparent",
            hover_color="#be3535",
            text_color="#777777",
            command=lambda: self.delete_message(message_frame)
        )
        del_col = 1 if is_user else 2
        del_btn.grid(row=0, column=del_col, padx=(0, 10), pady=5, sticky="ne")
        
        # Hover effects for delete button
        def on_enter(b): b.configure(text_color="#ffffff")
        def on_leave(b): b.configure(text_color="#777777")
        del_btn.bind("<Enter>", lambda e, b=del_btn: on_enter(b))
        del_btn.bind("<Leave>", lambda e, b=del_btn: on_leave(b))

        self.chat_history.append({"text": text, "is_user": is_user, "widget": message_frame})
        
        # Save to database if this is a new message and we have an active session
        if message_id is None and self.current_session_id and self.account_db:
            sender = 'user' if is_user else 'assistant'
            message_id = self.account_db.add_chat_message(self.current_session_id, sender, text)
            message_frame.message_id = message_id
            
            # Update session title if it's still "New Chat" and this is the first user message
            if is_user and self.account_db:
                sessions = self.account_db.get_user_chat_sessions(self.current_user_id)
                for sess in sessions:
                    if sess['id'] == self.current_session_id and sess['title'] == "New Chat":
                        # Create a title from the first few words of the message
                        title = text[:50].strip()
                        if len(text) > 50:
                            title += "..."
                        self.account_db.update_chat_session_title(self.current_session_id, title)
                        self.refresh_sidebar_chats()
                        break
        
        # Scroll to bottom
        self._scroll_to_bottom_if_enabled()
        
        # Bind right-click for context menu
        def on_right_click(event):
            self.show_message_context_menu(event, message_frame)
            
        message_frame.bind("<Button-3>", on_right_click)
        if msg_label:
            msg_label.bind("<Button-3>", on_right_click)
        
        if is_user and animate and msg_label:
            self.animate_text(msg_label, text)
            
        return message_frame, msg_label

    def _on_link_click(self, event, textbox):
        """Handles clicking on a URL within the chat."""
        click_pos = textbox.index(f"@{event.x},{event.y}")
        tags = textbox.tag_names(click_pos)
        if "link" in tags:
            # Find the specific range of the link tag at this position
            start, end = textbox.tag_prevrange("link", click_pos + "+1c")
            url = textbox.get(start, end)
            webbrowser.open(url)

    def add_thinking_animation(self):
        """Adds a bot thinking animation with 'Thinking...' text and spinner."""
        message_frame = ctk.CTkFrame(
            self.chat_container,
            fg_color="transparent",
            corner_radius=10
        )
        message_frame.pack(fill="x", pady=5, padx=20)
        
        # Icon
        icon_label = ctk.CTkLabel(message_frame, text="✨", font=("Arial", 20))
        icon_label.grid(row=0, column=0, padx=15, pady=10, sticky="n")
        
        # Thinking text with animation
        thinking_label = ctk.CTkLabel(
            message_frame, 
            text="💭 Thinking...", 
            font=("Arial", 16),
            text_color="#6FD3FF"
        )
        thinking_label.grid(row=0, column=1, padx=(0, 15), pady=10, sticky="w")
        
        # Store reference for animation
        message_frame._thinking_label = thinking_label
        message_frame._animation_step = 0
        message_frame._stop_animation = False
        
        # Start lightweight text animation
        def animate_thinking():
            if not message_frame.winfo_exists() or message_frame._stop_animation:
                return
            
            step = message_frame._animation_step % 4
            dots = "" + "." * (step + 1) + " " * (3 - step)
            try:
                thinking_label.configure(text=f"💭 Thinking{dots}")
                message_frame._animation_step += 1
                message_frame.after(500, animate_thinking)
            except Exception:
                pass
        
        # Add to chat history for tracking
        self.chat_history.append({"text": "...", "is_user": False, "widget": message_frame, "is_animation": True})
        
        # Scroll to bottom
        self._scroll_to_bottom_if_enabled()
        
        # Start animation
        animate_thinking()
        
        return message_frame
    
    def add_searching_animation(self):
        """Backward compatibility wrapper - uses thinking animation."""
        return self.add_thinking_animation()

    def _replace_animation_with_message(self, placeholder_frame, reply_text, message_id=None):
        """Helper to replace a thinking animation with the final message content."""
        logging.info(f"_replace_animation_with_message called with reply: {reply_text[:100]}...")
        
        if not placeholder_frame.winfo_exists():
            return

        try:
            # Stop thinking animation if it exists
            if hasattr(placeholder_frame, '_stop_animation'):
                placeholder_frame._stop_animation = True
            
            # Remove animation widgets from the placeholder
            for widget in placeholder_frame.winfo_children():
                widget.destroy()

            placeholder_frame.grid_columnconfigure(1, weight=1)

            # Re-add icon and message content
            icon_label = ctk.CTkLabel(placeholder_frame, text="🤖", font=("Arial", 20), fg_color="#1a2a3a")
            icon_label.grid(row=0, column=0, padx=15, pady=10, sticky="n")
            
            # Create message textbox with stylish formatting support
            msg_label = ctk.CTkTextbox(
                placeholder_frame,
                font=("Segoe UI", 18),
                text_color="#E8E8E8",
                wrap="word",
                state="disabled",
                fg_color="#0d1b2a",
                border_width=0
            )
            msg_label.grid(row=0, column=1, padx=(0, 15), pady=10, sticky="ew")
            
            # Configure text tags for stylish formatting
            msg_label.tag_config("code", foreground="#FFD700", background="#1a2a3a")
            msg_label.tag_config("bold", foreground="#6FD3FF")
            msg_label.tag_config("list_item", foreground="#7FE66F")
            msg_label.tag_config("highlight", background="#4a90e2", foreground="#ffffff")
            msg_label.tag_config("emphasis", foreground="#FFD77F")
            msg_label.tag_config("section", foreground="#FF6BAD")
            msg_label.tag_config("link", foreground="#1e90ff", underline=True)
            
            msg_label.tag_bind("link", "<Button-1>", lambda e: self._on_link_click(e, msg_label))
            msg_label.tag_bind("link", "<Enter>", lambda e: msg_label.configure(cursor="hand2"))
            msg_label.tag_bind("link", "<Leave>", lambda e: msg_label.configure(cursor="xterm"))
            
            # Insert the reply text with a slow typing animation
            msg_label.configure(state="normal")
            msg_label.delete("1.0", "end")
            msg_label.configure(state="disabled")
            self.animate_stream(msg_label, reply_text)
            
            # def on_right_click(event): self.show_message_context_menu(event, placeholder_frame)
            # placeholder_frame.bind("<Button-3>", on_right_click); msg_label.bind("<Button-3>", on_right_click)
            placeholder_frame.message_id = message_id
            for i, msg in enumerate(self.chat_history):
                if msg.get("widget") == placeholder_frame: 
                    self.chat_history[i] = {"text": reply_text, "is_user": False, "widget": placeholder_frame}; break
            
            logging.info("Message displayed successfully")
            # Speak the reply after displaying (without streaming to avoid threading issues)
            should_speak = True
            if hasattr(self, 'voice_var') and self.voice_var is not None:
                try:
                    should_speak = self.voice_var.get()
                except AttributeError:
                    should_speak = bool(self.voice_var)
            if should_speak:
                self.root.after(100, lambda: self.speak_reply(reply_text))
            
            # Re-enable send button
            self.send_btn.configure(state="normal")  # Re-enable send button
            self.stop_generation_event = None
        except Exception as e:
            logging.error(f"Error in _replace_animation_with_message: {e}", exc_info=True)
            # Fallback: try to update the animation frame instead of adding new message
            try:
                for widget in placeholder_frame.winfo_children():
                    widget.destroy()
                icon_label = ctk.CTkLabel(placeholder_frame, text="🤖", font=("Arial", 16))
                icon_label.grid(row=0, column=0, padx=15, pady=10, sticky="n")
                msg_label = ctk.CTkLabel(
                    placeholder_frame,
                    text=reply_text,
                    font=("calibri", 18),
                    text_color="#FFFFFF",
                    wraplength=800,
                    anchor="w",
                    justify="left"
                )
                msg_label.grid(row=0, column=1, padx=(0, 15), pady=10, sticky="w")
                placeholder_frame.message_id = message_id
                for i, msg in enumerate(self.chat_history):
                    if msg.get("widget") == placeholder_frame: 
                        self.chat_history[i] = {"text": reply_text, "is_user": False, "widget": placeholder_frame}; break
            except Exception:
                pass  # If even fallback fails, leave as is
            # Re-enable send button even in fallback case
            self.send_btn.configure(state="normal")  # Re-enable send button
            self.stop_generation_event = None
        self._scroll_to_bottom_if_enabled()

    def _remove_placeholder_animation(self, placeholder_frame):
        """Remove the placeholder animation frame without adding a message."""
        try:
            if placeholder_frame.winfo_exists():
                placeholder_frame.destroy()
            # Re-enable send button
            self.send_btn.configure(state="normal")
            self.stop_generation_event = None
        except Exception as e:
            logging.error(f"Error removing placeholder: {e}")
        self._scroll_to_bottom_if_enabled()

    def speak_and_stream_text(self, label, text_to_speak):
        """Initiates the text-to-speech streaming in a background thread."""
        threading.Thread(target=self._speak_and_stream_worker, args=(label, text_to_speak), daemon=True).start()

    def _speak_and_stream_worker(self, label, text_to_speak):
        """Worker that uses pyttsx3 callbacks to drive the UI word-by-word."""
        if not PYTTSX3_AVAILABLE:
            # Fallback to visual-only streaming if pyttsx3 is not installed
            self.root.after(0, lambda: self.animate_stream(label, text_to_speak))
            return

        try:
            # Configure highlight tag for the text widget
            label.tag_config("highlight", background="#4a90e2", foreground="#ffffff")

            engine = pyttsx3.init()
            
            # --- Voice Selection Logic ---
            voices = engine.getProperty('voices')
            selected_voice_id = None

            if self.current_voice_id:
                selected_voice_id = self.current_voice_id
            else:
                # Prioritize known high-quality voices
                preferred_voices = ["Zira", "David"] # e.g., Microsoft Zira / David on Windows
                for name in preferred_voices:
                    for voice in voices:
                        if name in voice.name:
                            selected_voice_id = voice.id
                            break
                    if selected_voice_id:
                        break
                
                # If no preferred voice is found, fall back to the second available voice (often female)
                if not selected_voice_id and len(voices) > 1:
                    selected_voice_id = voices[1].id

            if selected_voice_id:
                engine.setProperty('voice', selected_voice_id)
            # --- End of Voice Selection ---

            # The rate of speech. Default is 200.
            engine.setProperty('rate', 175)

            def on_word(name, location, length):
                # This callback is executed for each word from the TTS engine thread.
                def update_highlight():
                    if label.winfo_exists():
                        # Remove previous highlight and apply new one
                        label.tag_remove("highlight", "1.0", "end")
                        start_index = f"1.{location}"
                        end_index = f"1.{location + length}"
                        label.tag_add("highlight", start_index, end_index)
                        label.see(start_index) # Ensure the highlighted word is visible
                self.root.after(0, update_highlight)

            def on_end(name, completed):
                # Callback for when speech finishes to remove the highlight.
                def remove_highlight():
                    if label.winfo_exists():
                        label.tag_remove("highlight", "1.0", "end")
                        try:
                            self._scroll_to_bottom_if_enabled()
                        except Exception:
                            pass
                self.root.after(0, remove_highlight)

            engine.connect('started-word', on_word)
            engine.connect('finished-utterance', on_end)
            engine.say(text_to_speak)
            engine.runAndWait()
            engine.disconnect('started-word'); engine.disconnect('finished-utterance')

        except Exception as e:
            logging.error(f"Error in speech worker: {e}", exc_info=True)
            self.root.after(0, lambda: self.animate_stream(label, text_to_speak))

    def show_message_context_menu(self, event, frame):
        if not tk: return
        menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="#ffffff", activebackground="#404040", activeforeground="#ffffff")
        menu.add_command(label="Copy Message", command=lambda: self.copy_message(frame))
        menu.add_command(label="🔊 Read Aloud", command=lambda: self.read_message_aloud(frame))
        menu.add_command(label="Delete Message", command=lambda: self.delete_message(frame))
        
        # Add feedback options for bot messages
        is_bot_message = False
        for msg in self.chat_history:
            if msg.get("widget") == frame and not msg.get("is_user"):
                is_bot_message = True
                break

        if is_bot_message and self.is_logged_in and self.current_user_id and hasattr(frame, 'message_id'):
            menu.add_separator()
            menu.add_command(label="👍 Good Answer", command=lambda: self.record_feedback(frame.message_id, "like"))
            menu.add_command(label="👎 Bad Answer", command=lambda: self.record_feedback(frame.message_id, "dislike"))
            menu.add_command(label="📝 Suggest Correction", command=lambda: self.suggest_correction(frame.message_id))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def record_feedback(self, message_id: int, feedback_type: str, feedback_text: Optional[str] = None):
        """
        Records user feedback for a specific message using the AccountDatabase.
        """
        if self.account_db and self.current_user_id:
            success, msg = self.account_db.record_message_feedback(message_id, self.current_user_id, feedback_type, feedback_text)
            if success:
                self.notify_popup_text(f"Thank you for your feedback ({feedback_type}).", title="Feedback", icon="👍")
            else:
                self.notify_popup_text(f"Failed to record feedback: {msg}", title="Feedback", icon="❌")

    def suggest_correction(self, message_id: int):
        """
        Opens a dialog for the user to suggest a correction for a message.
        """
        if not CTK_AVAILABLE: return
        dialog = ctk.CTkInputDialog(text="Please provide your suggested correction:", title="Suggest Correction")
        correction_text = dialog.get_input()
        if correction_text:
            self.record_feedback(message_id, "correction", correction_text)



    def copy_message(self, frame):
        text = None
        for msg in self.chat_history:
            if msg.get("widget") == frame:
                text = msg.get("text")
                break
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()

    def read_message_aloud(self, frame):
        text = None
        for msg in self.chat_history:
            if msg.get("widget") == frame:
                text = msg.get("text")
                break
        if text:
            self.speak_reply(text)

    def delete_message(self, frame):
        # Delete from DB if ID exists
        if hasattr(frame, 'message_id') and frame.message_id and self.account_db:
            self.account_db.delete_chat_message(frame.message_id)
        
        # Remove from UI
        frame.destroy()
        
        # Remove from internal history list (optional, but good for consistency)
        self.chat_history = [msg for msg in self.chat_history if msg.get("widget") != frame]
        
    def animate_text(self, label, text, index=0):
        if not label.winfo_exists():
            return
            
        if index < len(text):
            label.configure(text=text[:index+1])
            if index % 3 == 0: # Periodically scroll
                self._scroll_to_bottom_if_enabled()
            self.root.after(15, lambda: self.animate_text(label, text, index+1))
        else: # Scroll once at the end
            self._scroll_to_bottom_if_enabled()
        
    def animate_stream(self, label, full_text, current_len=0):
        """Simulate a word-by-word/token streaming effect for bot replies (optimized)."""
        try:
            if not label.winfo_exists():
                return
                
            if current_len < len(full_text):
                # Simulate token streaming: add 4-10 chars at a time (Faster)
                step = random.randint(4, 10)
                current_len = min(current_len + step, len(full_text))
                
                # Handle CTkTextbox update
                try:
                    label.configure(state="normal")
                    label.delete("1.0", "end")
                    label.insert("1.0", full_text[:current_len])
                    label.configure(state="disabled")
                except Exception:
                    pass
                
                # Scroll less frequently to reduce lag
                if current_len % 50 < step:
                    try:
                        self._scroll_to_bottom_if_enabled()
                    except Exception:
                        pass
                
                # Slightly faster animation
                self.root.after(random.randint(8, 20), lambda: self.animate_stream(label, full_text, current_len))
            else:
                try:
                    self._scroll_to_bottom_if_enabled()
                except Exception:
                    pass
        except Exception as e:
            logging.debug(f"Error in animate_stream: {e}")

    def play_typing_sound(self):
        """Play a typing sound effect if 'typing.wav' exists."""
        sound_path = resource_path("typing.wav")
        if winsound and os.path.exists(sound_path):
            try:
                winsound.PlaySound(sound_path, winsound.SND_ASYNC | winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            except Exception:
                pass

    def handle_stop_generation(self):
        """Handles the user clicking the 'Stop Generation' button."""
        if self.stop_generation_event:
            self.stop_generation_event.set()

        # Find and remove the animation widget
        try:
            if self.chat_history and self.chat_history[-1].get("is_animation"):
                anim_widget_data = self.chat_history.pop()
                anim_widget = anim_widget_data.get("widget")
                if anim_widget and anim_widget.winfo_exists():
                    anim_widget.destroy()
        except Exception as e:
            logging.error(f"Error removing animation widget: {e}")

        # Restore UI
        self.send_btn.configure(state="normal")  # Re-enable send button
        self.notify_popup_text("Generation stopped by user.", title="Generation", icon="⏹️")
        self.stop_generation_event = None

    def save_chat_to_file(self):
        """Saves the current chat history to a text file."""
        if not self.chat_history:
            self.notify_popup_text("Chat history is empty. Nothing to save.", title="Save Chat", icon="❌")
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        initial_filename = f"jarvis_chat_{now}.txt"

        filepath = filedialog.asksaveasfilename(
            initialfile=initial_filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath: return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Chat Session - {now}\n{'='*40}\n\n")
                for message in self.chat_history:
                    if message.get("is_animation"): continue
                    sender = "User" if message["is_user"] else "JARVIS"
                    f.write(f"{sender}:\n{message['text']}\n\n")
            self.notify_popup_text(f"Chat history saved to:\n{os.path.basename(filepath)}", title="Save Chat", icon="✅")
        except Exception as e:
            self.notify_popup_text(f"Error saving chat: {e}", title="Save Chat", icon="❌")

    def _recreate_chat_container(self):
        """Efficiently clear chat container without destroying it completely."""
        try:
            # Stop all thinking animations first
            for item in self.chat_history:
                widget = item.get("widget")
                if widget and hasattr(widget, '_stop_animation'):
                    widget._stop_animation = True
            
            # Clear widgets efficiently instead of destroying
            for widget in self.chat_container.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass
        except Exception as e:
            logging.debug(f"Error clearing chat container: {e}")

    def _background_delete_session(self, session_id):
        try:
            if self.account_db:
                self.account_db.delete_chat_session(session_id)
        except Exception as e:
            logging.error(f"Error deleting chat session in background: {e}", exc_info=True)
        finally:
            try:
                self.root.after(0, self.refresh_sidebar_chats)
            except Exception:
                pass

    def new_chat(self):
        """Create a new chat session efficiently."""
        # Stop any ongoing generation
        if self.stop_generation_event:
            self.stop_generation_event.set()
        
        # Stop any thinking animations
        for item in self.chat_history:
            widget = item.get("widget")
            if widget and hasattr(widget, '_stop_animation'):
                try:
                    widget._stop_animation = True
                except Exception:
                    pass
            
        # Clear chat history efficiently
        self.chat_history = []
        self.current_session_id = None
        self.current_attachment = None
        
        if hasattr(self, 'attachment_label'):
            try:
                self.attachment_label.configure(text="")
            except Exception:
                pass

        # Clear the chat container
        self._recreate_chat_container()

        # Reset input field
        try:
            self.input_field.configure(state="normal")
            self.input_field.delete("1.0", "end")
            self._adjust_input_height()
        except Exception:
            pass

        # Show welcome message
        self.create_welcome_message(animate=False)
        
        # Create new session if logged in
        if self.is_logged_in and self.account_db and self.current_user_id:
            try:
                self.current_session_id = self.account_db.create_chat_session(self.current_user_id, "New Chat")
                self.refresh_sidebar_chats()
            except Exception as e:
                logging.debug(f"Error creating new chat session: {e}")

    def clear_history(self):
        """Clear the current chat history and delete all messages from database."""
        if self.stop_generation_event:
            self.stop_generation_event.set()

        session_to_delete = None
        if self.is_logged_in and self.account_db and self.current_session_id:
            session_to_delete = self.current_session_id
            self.current_session_id = None

        # Clear UI first for responsive feedback
        self.new_chat()

        # Delete from database in background to avoid blocking UI
        if session_to_delete is not None:
            def delete_session_bg():
                try:
                    if self.account_db:
                        self.account_db.delete_chat_session(session_to_delete)
                        logging.info(f"Deleted chat session {session_to_delete}")
                except Exception as e:
                    logging.error(f"Error deleting chat session: {e}", exc_info=True)
                finally:
                    try:
                        self.root.after(0, self.refresh_sidebar_chats)
                    except Exception:
                        pass
            
            threading.Thread(target=delete_session_bg, daemon=True).start()

    def open_settings(self):
        """Open a dedicated settings window."""
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
        else:
            win = tk.Toplevel(self.root)
            
        win.title("Settings")
        win.geometry("400x450")
        win.transient(self.root)
        win.lift()
        
        # Center window
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (220)
        y = (win.winfo_screenheight() // 2) - (225)
        win.geometry(f"+{x}+{y}")
        
        # Title
        ctk.CTkLabel(win, text="Settings", font=("Arial", 24, "bold")).pack(pady=(20, 20))
        
        # Container
        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30)
        
        # Chat Section
        ctk.CTkLabel(container, text="Chat Options", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 5))
        
        if hasattr(self, 'auto_scroll_var'):
            chk = ctk.CTkCheckBox(
                container, 
                text="Auto-scroll on reply", 
                variable=self.auto_scroll_var
            )
            chk.pack(anchor="w", pady=5)

        if hasattr(self, 'voice_var'):
            voice_chk = ctk.CTkCheckBox(
                container, 
                text="Auto-speak replies", 
                variable=self.voice_var,
                command=self._toggle_voice
            )
            voice_chk.pack(anchor="w", pady=5)

        # Voice Selection
        voices = self.audio_handler.get_voices()
        if voices:
            ctk.CTkLabel(container, text="Voice Selection:", font=("Arial", 12)).pack(anchor="w", pady=(10, 0))
            
            # Map names to IDs
            voice_names = [v['name'] for v in voices]
            # Find current selection name
            current_voice_name = voice_names[0]
            if self.current_voice_id:
                for v in voices:
                    if v['id'] == self.current_voice_id:
                        current_voice_name = v['name']
                        break
            
            def on_voice_change(choice):
                for v in voices:
                    if v['name'] == choice:
                        self.current_voice_id = v['id']
                        if self.is_logged_in and self.account_db and self.current_user_id:
                            self.account_db.update_user_preference(self.current_user_id, 'voice_id', v['id'])
                        break

            voice_menu = ctk.CTkOptionMenu(container, values=voice_names, command=on_voice_change, width=300)
            voice_menu.set(current_voice_name)
            voice_menu.pack(anchor="w", pady=5)

        # Account Section
        ctk.CTkLabel(container, text="Account", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 5))
        
        account_btn = ctk.CTkButton(
            container,
            text="Manage Profile",
            command=lambda: [win.destroy(), self.open_account_page(start_mode="profile")] if self.is_logged_in else [win.destroy(), self.show_auth_popup()]
        )
        account_btn.pack(anchor="w", pady=5, fill="x")
        
        # System Section - Hidden as per user request
        # ctk.CTkLabel(container, text="System", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 5))
        
        # kb_btn = ctk.CTkButton(
        #     container,
        #     text="Knowledge Base Configuration",
        #     command=lambda: [win.destroy(), self.open_kb_settings()]
        # )
        # kb_btn.pack(anchor="w", pady=5, fill="x")

    def open_image_tools(self):
        """Open image generation and vision tools."""
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
        else:
            win = tk.Toplevel(self.root)
        win.title("Image Tools")
        win.geometry("500x400")
        win.transient(self.root)
        win.lift()
        
        # Title
        ctk.CTkLabel(win, text="Image Tools", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Generate Image section
        gen_frame = ctk.CTkFrame(win, fg_color="transparent")
        gen_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(gen_frame, text="Generate Image", font=("Arial", 14, "bold")).pack(anchor="w")
        
        self.image_prompt_entry = ctk.CTkEntry(gen_frame, placeholder_text="Describe the image you want to generate...")
        self.image_prompt_entry.pack(fill="x", pady=5)
        
        gen_btn = ctk.CTkButton(gen_frame, text="Generate", command=self.generate_image)
        gen_btn.pack(pady=5)
        
        # Vision section
        vision_frame = ctk.CTkFrame(win, fg_color="transparent")
        vision_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(vision_frame, text="Analyze Image", font=("Arial", 14, "bold")).pack(anchor="w")
        
        upload_btn = ctk.CTkButton(vision_frame, text="Upload Image", command=self.handle_photo_upload)
        upload_btn.pack(pady=5)
        
        ctk.CTkLabel(vision_frame, text="Or paste an image URL:", font=("Arial", 12)).pack(anchor="w", pady=(10, 0))
        
        self.vision_url_entry = ctk.CTkEntry(vision_frame, placeholder_text="https://example.com/image.jpg")
        self.vision_url_entry.pack(fill="x", pady=5)
        
        analyze_btn = ctk.CTkButton(vision_frame, text="Analyze URL", command=self.analyze_image_url)
        analyze_btn.pack(pady=5)

    def generate_image(self):
        """Generate an image using DALL-E."""
        if not self.image_gen_handler:
            self.root.after(0, lambda: self.show_feature_popup("Image Generation", "Image generation handler not initialized yet. Please wait.", "⏳"))
            return
            
        prompt = self.image_prompt_entry.get().strip()
        if not prompt:
            self.root.after(0, lambda: self.show_feature_popup("Image Generation", "Please enter a description for the image.", "❌"))
            return
        
        self.root.after(0, lambda: self.show_feature_popup("Image Generation", f"Generating image: {prompt}", "🎨"))
        
        def worker():
            try:
                res = self.image_gen_handler.generate_image(prompt, backend="auto")
                if res["success"]:
                    url = res["images"][0]["url"] if "images" in res else res.get("image_path")
                    self.root.after(0, lambda: self.show_feature_popup("Image Generated", f"Image generated: {url}", "✅"))
                else:
                    self.root.after(0, lambda: self.show_feature_popup("Image Generation Failed", f"Image generation failed: {res.get('error')}", "❌"))
            except Exception as e:
                self.root.after(0, lambda: self.show_feature_popup("Image Generation Error", f"Error generating image: {e}", "❌"))
        
        threading.Thread(target=worker, daemon=True).start()

    def analyze_image_url(self):
        """Analyze an image from URL."""
        url = self.vision_url_entry.get().strip()
        if not url:
            self.root.after(0, lambda: self.show_feature_popup("Image Analysis", "Please enter an image URL.", "❌"))
            return
        
        self.root.after(0, lambda: self.show_feature_popup("Image Analysis", f"Analyzing image from URL: {url}", "🔍"))
        
        def worker():
            try:
                description = self.get_vision_description(url)
                self.root.after(0, lambda: self.show_feature_popup("Image Analysis Result", description, "🖼️"))
            except Exception as e:
                self.root.after(0, lambda: self.show_feature_popup("Image Analysis Failed", f"Error analyzing image: {e}", "❌"))
        
        threading.Thread(target=worker, daemon=True).start()

    def open_mic_interface(self):
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
        else:
            win = tk.Toplevel(self.root)
        win.title("Mic Interface")
        win.geometry("400x400")
        
        # Center content
        frame = ctk.CTkFrame(win, fg_color="transparent")
        frame.pack(expand=True, fill="both")
        
        self.big_mic_btn = ctk.CTkButton(
            frame,
            text="🎤",
            font=("Arial", 64),
            width=160,
            height=160,
            corner_radius=80,
            fg_color="#333333",
            hover_color="#444444",
            command=self.voice_input
        )
        self.big_mic_btn.place(relx=0.5, rely=0.4, anchor="center")
        
        self.mic_status_label = ctk.CTkLabel(frame, text="Tap to speak", font=("Arial", 18))
        self.mic_status_label.place(relx=0.5, rely=0.7, anchor="center")
        
        # Update state if already listening
        if self.is_listening:
             self.big_mic_btn.configure(text="🟥", fg_color="#be3535", hover_color="#8b3a3a")
             self.mic_status_label.configure(text="Listening...")

    def open_account_page(self, event=None, start_mode="login"):
        self._cleanup_popup()
        try:
            import jarvis_accounts
            import importlib
            importlib.reload(jarvis_accounts)
            logging.info("Opening account page...")
            
            def on_login(user_id):
                save_session(user_id) # Save session locally
                self.is_logged_in = True
                self.current_user_id = user_id
                self.account_db = jarvis_accounts.AccountDatabase(db_path=os.path.join(BASE_DIR, "jarvis_accounts.db"))
                try:
                    info = self.account_db.get_user_info(user_id)
                    if info:
                        if info.get('full_name'):
                            new_name = info['full_name']
                            if hasattr(self, 'profile_label'):
                                self.profile_label.configure(text=new_name)
                        
                        if info.get('subscription_tier') == 'plus':
                            self.is_premium = True
                            if hasattr(self, 'upgrade_btn'):
                                self.upgrade_btn.configure(text="✦ JARVIS Plus", fg_color="transparent", border_width=1, state="disabled")
                except Exception as e:
                    logging.error(f"Error updating profile: {e}", exc_info=True)
                
                # Load preferences
                prefs = self.account_db.get_user_preferences(user_id)
                if prefs:
                    if prefs.get('voice_id'):
                        self.current_voice_id = prefs['voice_id']
                    if prefs.get('api_key') and prefs.get('api_key').startswith("hf_"):
                        hf_token = prefs.get('api_key')
                        os.environ["HF_TOKEN"] = hf_token
                        logging.info("Hugging Face token loaded from user preferences.")
                
                self.update_avatar_ui()
                if hasattr(self, 'sidebar_logout_btn'):
                    self.sidebar_logout_btn.pack(side="right", padx=5)
                if hasattr(self, 'clear_history_btn'):
                    self.clear_history_btn.grid()
                self.current_user_name = self._extract_user_name(info or {})
                self.update_dynamic_header()
                remembered = self._get_user_memory().get("interactions", []) if self._get_user_memory() else []
                if remembered:
                    last = remembered[-1]
                    self.notify_popup("Welcome Back", f"Welcome back, {self.current_user_name}. I remembered your recent activity: {last['text']}", "👋")
                self.refresh_sidebar_chats()

            if hasattr(self, 'account_window') and self.account_window and self.account_window.root.winfo_exists():
                self.account_window.root.lift()
                self.account_window.root.focus_force()
                return

            self.account_window = jarvis_accounts.AccountPage(
                on_login_success=on_login, 
                master=self.root, 
                start_mode=start_mode,
                current_user_id=self.current_user_id,
                db_path=os.path.join(BASE_DIR, "jarvis_accounts.db")
            )
            self.account_window.run()
            
        except Exception as e:
            self.notify_popup("Account Error", f"Error opening account page: {e}", "❌")

    def open_payment_page(self):
        """Opens the payment/upgrade page."""
        self._cleanup_popup()
        
        if not self.is_logged_in:
            self.show_auth_popup()
            return

        try:
            import Jarvis_payments
            import importlib
            importlib.reload(Jarvis_payments)
            logging.info("Opening payment page...")

            def on_payment_success():
                self.notify_popup("Payment", "Payment successful. JARVIS Plus unlocked!", "✅")
                self.is_premium = True
                if hasattr(self, 'upgrade_btn'):
                    self.upgrade_btn.configure(text="✦ JARVIS Plus", fg_color="transparent", border_width=1, state="disabled")
                # Here you might unlock features, change user status in DB, etc.
                if self.is_logged_in and self.account_db and self.current_user_id:
                    self.account_db.update_user_subscription(self.current_user_id, 'plus')

            if hasattr(self, 'payment_window') and self.payment_window and self.payment_window.root.winfo_exists():
                self.payment_window.root.lift()
                self.payment_window.root.focus_force()
                return

            self.payment_window = Jarvis_payments.PaymentPage(
                master=self.root,
                on_success=on_payment_success
            )
            self.payment_window.run()
        except ImportError:
            self.notify_popup("Payment Error", "Could not find the payment module (Jarvis_payments.py).", "❌")
        except Exception as e:
            self.notify_popup("Payment Error", f"Error opening payment page: {e}", "❌")

    def refresh_sidebar_chats(self):
        """Refresh the list of chats in the sidebar"""
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        if not self.is_logged_in or not self.account_db:
            return

        try:
            sessions = self.account_db.get_user_chat_sessions(self.current_user_id)
            for sess in sessions:
                frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
                frame.pack(fill="x", padx=5, pady=2)

                btn = ctk.CTkButton(
                    frame,
                    text=sess['title'],
                    font=("Arial", 12),
                    fg_color="transparent",
                    hover_color="#333333",
                    anchor="w",
                    height=30,
                    command=lambda s=sess['id']: self.load_session(s)
                )
                btn.pack(side="left", fill="x", expand=True)

                del_btn = ctk.CTkButton(
                    frame,
                    text="×",
                    font=("Arial", 16),
                    width=25,
                    height=30,
                    fg_color="transparent",
                    hover_color="#be3535",
                    text_color="#666666",
                    command=lambda s=sess['id']: self.delete_session(s)
                )
                del_btn.pack(side="right", padx=(2, 0))
                
                # Hover effect for delete button
                def on_enter(b): b.configure(text_color="#ffffff")
                def on_leave(b): b.configure(text_color="#666666")
                del_btn.bind("<Enter>", lambda e, b=del_btn: on_enter(b))
                del_btn.bind("<Leave>", lambda e, b=del_btn: on_leave(b))
        except Exception as e:
            logging.error(f"Error refreshing chats: {e}", exc_info=True)

    def load_session(self, session_id):
        """Load a specific chat session"""
        if not self.account_db:
            return
            
        self.current_session_id = session_id
        messages = self.account_db.get_chat_history(session_id)
        
        # Clear UI
        self.chat_history = []
        for widget in self.chat_container.winfo_children():
            widget.destroy()
        
        # Load messages
        for msg in messages:
            is_user = (msg['sender'] == 'user')
            self.add_message(msg['text'], is_user=is_user, message_id=msg.get('id'))

    def delete_session(self, session_id):
        """Delete a chat session"""
        if not self.account_db:
            return
        self.account_db.delete_chat_session(session_id)
        if self.current_session_id == session_id:
            self.new_chat()
        self.refresh_sidebar_chats()

    def apply_ui_theme(self, theme_name):
        """Theme selection support has been removed from the interface."""
        self.root.after(0, lambda: self.show_feature_popup("Feature Unavailable", "Theme switching has been removed from the interface.", "❌"))
            
    def on_closing(self):
        """Handler for when the main window is closed."""
        # Stop voice listening
        self.stop_voice_listening()
        
        # Turn off lights if active
        if self.light_controller:
            try:
                self.light_controller.turn_off()
            except Exception:
                pass

        self.stop_kb_observer()
        self.root.destroy()

    def trigger_auto_rebuild(self):
        """Checks if auto-rebuild is enabled and starts the build process."""
        if self.kb_auto_rebuild_var and self.kb_auto_rebuild_var.get():
            # Don't trigger if a build is already running
            is_building = False
            try:
                if self.kb_build_button and self.kb_build_button.winfo_exists() and self.kb_build_button.cget('state') == 'disabled':
                    is_building = True
            except Exception:
                pass
            
            if is_building:
                logging.info("Auto-rebuild skipped: a build is already in progress.")
                return
            self.root.after(0, lambda: self.show_feature_popup("KB Auto-Rebuild", "File change detected, starting automatic KB rebuild.", "🔄"))
            self._start_build_kb_thread()

    def start_kb_observer(self):
        """Starts the filesystem observer on the KB folder."""
        if not WATCHDOG_AVAILABLE:
            if self.kb_auto_rebuild_var and self.kb_auto_rebuild_var.get():
                self.root.after(0, lambda: self.show_feature_popup("KB Auto-Rebuild Error", "Cannot auto-rebuild: 'watchdog' library not installed. Please run: pip install watchdog", "❌"))
                self.kb_auto_rebuild_var.set(False)
            return
        
        if not self.kb_auto_rebuild_var or not self.kb_auto_rebuild_var.get():
            return

        if self.kb_observer:
            self.stop_kb_observer()

        folder = self.kb_folder_var.get()
        if not os.path.isdir(folder):
            self.root.after(0, lambda: self.show_feature_popup("KB Auto-Rebuild Error", f"Cannot watch folder: '{folder}' is not a valid directory.", "❌"))
            self.kb_auto_rebuild_var.set(False)
            return

        event_handler = KBFileHandler(self)
        self.kb_observer = Observer()
        self.kb_observer.schedule(event_handler, folder, recursive=True)
        self.kb_observer.start()
        self.root.after(0, lambda: self.show_feature_popup("KB Auto-Rebuild Enabled", f"Watching for file changes in: {folder}", "👀"))

    def stop_kb_observer(self):
        """Stops the filesystem observer."""
        if self.kb_observer:
            self.kb_observer.stop()
            try:
                self.kb_observer.join(timeout=2)
            except Exception as e:
                logging.error(f"Error joining observer thread: {e}", exc_info=True)
            self.kb_observer = None
            logging.info("Stopped watching folder for KB updates.")

    def on_auto_rebuild_toggle(self):
        """Called when the auto-rebuild checkbox is toggled."""
        if self.kb_auto_rebuild_var.get():
            self.start_kb_observer()
        else:
            self.stop_kb_observer()
            self.notify_popup_text("Auto-rebuild disabled.", title="KB", icon="ℹ️")

    # ----------------- KB Settings & Build Helpers -----------------
    def _browse_kb_folder(self, var) -> None:
        try:
            folder = filedialog.askdirectory()
            if folder:
                var.set(folder)
        except Exception as e:
            self.notify_popup_text(f"Error browsing folder: {e}", title="KB", icon="❌")

    def _list_files_safe(self, folder: str) -> List[str]:
        try:
            return self._list_files_in_folder(folder, exts=(".txt", ".md", ".pdf", ".docx", ".pptx", ".csv"))
        except Exception:
            return []

    def open_kb_settings(self) -> None:
        """Open a small window to configure KB folder and paths, and trigger builds."""
        if CTK_AVAILABLE:
            win = ctk.CTkToplevel(self.root)
        else:
            win = tk.Toplevel(self.root)
        win.title("KB Settings")
        try:
            win.geometry("700x340")
        except Exception:
            pass

        # KB folder
        ctk.CTkLabel(win, text="KB Folder:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        if not self.kb_folder_var: self.kb_folder_var = tk.StringVar(value=os.getcwd())
        kb_folder_entry = ctk.CTkEntry(win, textvariable=self.kb_folder_var, width=420)
        kb_folder_entry.grid(row=0, column=1, padx=10, pady=10)
        browse_btn = ctk.CTkButton(win, text="Browse", command=lambda: self._browse_kb_folder(self.kb_folder_var))
        browse_btn.grid(row=0, column=2, padx=10, pady=10)

        # DB and index paths
        ctk.CTkLabel(win, text="KB DB Path:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        if not self.kb_db_var: self.kb_db_var = tk.StringVar(value="kb_meta.db")
        ctk.CTkEntry(win, textvariable=self.kb_db_var, width=420).grid(row=1, column=1, padx=10, pady=6)

        ctk.CTkLabel(win, text="KB Index Path:").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        if not self.kb_index_var: self.kb_index_var = tk.StringVar(value="kb_index.faiss")
        ctk.CTkEntry(win, textvariable=self.kb_index_var, width=420).grid(row=2, column=1, padx=10, pady=6)

        ctk.CTkLabel(win, text="KB Summary Index Path:").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        if not self.kb_summary_index_var: self.kb_summary_index_var = tk.StringVar(value="kb_summary_index.faiss")
        ctk.CTkEntry(win, textvariable=self.kb_summary_index_var, width=420).grid(row=3, column=1, padx=10, pady=6)

        # Auto-rebuild checkbox
        if not self.kb_auto_rebuild_var: self.kb_auto_rebuild_var = tk.BooleanVar(value=False)
        auto_rebuild_check = ctk.CTkCheckBox(win, text="Automatically rebuild KB on file changes", variable=self.kb_auto_rebuild_var, command=self.on_auto_rebuild_toggle)
        auto_rebuild_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        # Build and Status buttons
        self.kb_build_button = ctk.CTkButton(win, text="Build KB Now", fg_color="#4a5fe8", command=self._start_build_kb_thread)
        self.kb_build_button.grid(row=5, column=1, sticky="w", padx=10, pady=18)

        ctk.CTkButton(win, text="List Files", fg_color="#333333", width=80, command=self.list_kb_documents).grid(row=5, column=2, padx=10, pady=18)

        ctk.CTkButton(win, text="Show KB Status", fg_color="#333333", command=self.show_kb_status).grid(row=5, column=1, sticky="e", padx=10, pady=18)

        # Progress bar and cancel
        try:
            self.kb_progress = ctk.CTkProgressBar(win, width=520)
            self.kb_progress.grid(row=6, column=0, columnspan=3, padx=10, pady=(0,10))
            self.kb_progress.set(0)
        except Exception:
            self.kb_progress = None

        self.kb_cancel_button = ctk.CTkButton(win, text="Cancel Build", fg_color="#b34a4a", command=self._cancel_build)
        self.kb_cancel_button.grid(row=6, column=3, padx=10, pady=(0,10))
        try:
            self.kb_cancel_button.configure(state="disabled")
        except Exception:
            pass

        # Logs area
        logs_frame = tk.Frame(win)
        logs_frame.grid(row=7, column=0, columnspan=4, padx=10, pady=(0,10))
        self.kb_logs_text = tk.Text(logs_frame, height=8, width=90)
        self.kb_logs_text.pack(side="left", fill="both", expand=True)
        logs_scroll = tk.Scrollbar(logs_frame, command=self.kb_logs_text.yview)
        logs_scroll.pack(side="right", fill="y")
        self.kb_logs_text.configure(yscrollcommand=logs_scroll.set)

    def _start_build_kb_thread(self) -> None:
        folder = self.kb_folder_var.get() if hasattr(self, 'kb_folder_var') else None
        if not folder or not os.path.isdir(folder):
            self.notify_popup_text("Please choose a valid KB folder before building.", title="KB", icon="❌")
            return
            
        # Capture variables in main thread
        db_path = self.kb_db_var.get() if hasattr(self, 'kb_db_var') else "kb_meta.db"
        index_path = self.kb_index_var.get() if hasattr(self, 'kb_index_var') else "kb_index.faiss"
        summary_path = self.kb_summary_index_var.get() if hasattr(self, 'kb_summary_index_var') else "kb_summary_index.faiss"

        # Disable button and start background thread
        try:
            self.kb_build_button.configure(state="disabled")
            # clear logs area
            if hasattr(self, 'kb_logs_text'):
                try:
                    self.kb_logs_text.delete('1.0', 'end')
                except Exception:
                    pass
            if hasattr(self, 'kb_progress') and self.kb_progress:
                try:
                    self.kb_progress.set(0)
                except Exception:
                    pass
        except Exception:
            pass

        # Ensure the KB backend is initialized before or after build finishes; we will re-init after build completes to pick up new data
        # If a store exists, we keep it; otherwise we'll create one in background after build finishes.

        def target():
            folder_files = self._list_files_safe(folder)
            total_files = len(folder_files)
            if total_files == 0:
                self.notify_popup_text("No files found in folder to ingest.", title="KB Build", icon="❌")
                try:
                    self.kb_build_button.configure(state="normal")
                except Exception:
                    pass
                return

            # enable cancel button
            try:
                self.kb_cancel_button.configure(state="normal")
            except Exception:
                pass
            self._kb_build_cancel_event = threading.Event()

            try:
                self.notify_popup_text(f"Starting KB build from: {folder} ({total_files} files)", title="KB Build", icon="🔧")
                try:
                    self.update_kb_status_indicator('building')
                except Exception:
                    pass

                store = create_vector_store(db_path=db_path, index_path=index_path, summary_index_path=summary_path)

                def progress_cb(percent, message):
                    # ensure percent is 0..100
                    try:
                        p = min(max(float(percent), 0.0), 100.0)
                    except Exception:
                        p = 0.0
                    self._update_build_progress(p, message)

                # The store method reports per-file progress and handles cancellation
                store.add_texts_from_files(folder_files, exts=(".txt", ".md", ".pdf", ".docx", ".pptx"), progress_cb=progress_cb, cancel_event=self._kb_build_cancel_event)
                store.save()
                store.close()
                self.notify_popup_text("KB build finished successfully.", title="KB Build", icon="✅")

                # After successful build, re-initialize the cached KB backend in background so the UI queries are fast
                try:
                    self.update_kb_status_indicator('initializing')
                except Exception:
                    pass
                try:
                    self._init_kb_store_in_bg(db=db_path, index=index_path, summary_index=summary_path)
                except Exception:
                    pass

            except Exception as e:
                try:
                    self.update_kb_status_indicator('failed')
                except Exception:
                    pass

            finally:
                try:
                    self.kb_build_button.configure(state="normal")
                    self.kb_cancel_button.configure(state="disabled")
                    if getattr(self, 'kb_progress', None):
                        self.kb_progress.set(0)
                    self._kb_build_cancel_event = None
                except Exception:
                    pass

        threading.Thread(target=target, daemon=True).start()

    def show_kb_status(self) -> None:
        try:
            db = getattr(self, 'kb_db_var', None)
            db_path = db.get() if db else "kb_meta.db"
            conn = sqlite3.connect(db_path)
            cur = conn.execute("SELECT key, value FROM kb_info")
            rows = cur.fetchall()
            parts = [f"{k}: {v}" for k, v in rows]

            # Show recent build history
            cur2 = conn.execute("SELECT id, start_time, end_time, status, message FROM build_history ORDER BY id DESC LIMIT 5")
            bh = cur2.fetchall()
            out_lines = []
            if parts:
                out_lines.append("KB metadata:")
                out_lines.extend(parts)
            if bh:
                out_lines.append("\nRecent builds:")
                for b in bh:
                    out_lines.append(f"- id={b[0]} start={b[1]} end={b[2]} status={b[3]} msg={b[4]}")
            if not out_lines:
                self.notify_popup_text("KB status: no metadata found (build the KB to populate status)", title="KB Status", icon="ℹ️")
                conn.close()
                return
            self.notify_popup_text("KB status:\n" + "\n".join(out_lines), title="KB Status", icon="ℹ️")
            conn.close()
        except Exception as e:
            self.notify_popup_text(f"Error reading KB status: {e}", title="KB Status", icon="❌")

    def list_kb_documents(self) -> None:
        """Lists all unique documents currently ingested in the Knowledge Base."""
        try:
            db = getattr(self, 'kb_db_var', None)
            db_path = db.get() if db else "kb_meta.db"
            
            if not os.path.exists(db_path):
                 self.notify_popup_text("KB database not found (build KB first).", title="KB", icon="❌")
                 return
            
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.execute("SELECT DISTINCT source FROM meta ORDER BY source")
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                rows = []
            conn.close()
            
            files = [os.path.basename(r[0]) for r in rows if r[0]]
            msg = f"Documents in KB ({len(files)}):\n" + "\n".join([f"- {f}" for f in files]) if files else "No documents found in Knowledge Base."
            
            if hasattr(self, 'kb_logs_text') and self.kb_logs_text.winfo_exists():
                 self.kb_logs_text.delete('1.0', 'end')
                 self.kb_logs_text.insert('end', msg + "\n")
            else:
                 self.notify_popup_text(msg, title="KB Documents", icon="📄")
        except Exception as e:
            self.notify_popup_text(f"Error listing documents: {e}", title="KB Documents", icon="❌")

    def _update_build_progress(self, percent: float, message: str) -> None:
        """Update the progress bar and logs in the settings window from background threads."""
        def ui_update():
            try:
                if hasattr(self, 'kb_progress') and self.kb_progress:
                    try:
                        self.kb_progress.set(min(max(percent / 100.0, 0.0), 1.0))
                    except Exception:
                        pass
                if hasattr(self, 'kb_logs_text'):
                    now = datetime.datetime.utcnow().isoformat()
                    try:
                        self.kb_logs_text.insert('end', f'[{now}] {message}\n')
                        self.kb_logs_text.see('end')
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            self.root.after(0, ui_update)
        except Exception:
            ui_update()

    def _cancel_build(self) -> None:
        if getattr(self, '_kb_build_cancel_event', None):
            try:
                self._kb_build_cancel_event.set()
            except Exception:
                pass
            try:
                self.kb_cancel_button.configure(state='disabled')
            except Exception:
                pass
            self.notify_popup_text('Build cancellation requested. Waiting for current file to complete.', title='KB', icon='⏳')

    def update_kb_status_indicator(self, status: str) -> None:
        """Update the KB status indicator in the UI. Status values: ready, initializing, building, failed, unavailable, not_ready"""
        status_map = {
            'ready': ('KB: Ready', '#22c55e'),
            'initializing': ('KB: Initializing', '#f59e0b'),
            'building': ('KB: Building', '#3b82f6'),
            'failed': ('KB: Error', '#ef4444'),
            'unavailable': ('KB: Unavailable', '#9ca3af'),
            'not_ready': ('KB: Not ready', '#f59e0b')
        }
        label_text, color = status_map.get(status, (f'KB: {status}', '#9ca3af'))

        def ui():
            try:
                # Update tooltip text
                try:
                    self.kb_status_tooltip_text = label_text
                except Exception:
                    pass

                # Update compact dot color if available
                if hasattr(self, 'kb_status_dot') and self.kb_status_dot:
                    if CTK_AVAILABLE:
                        try:
                            self.kb_status_dot.configure(text="●", text_color=color)
                        except Exception:
                            try:
                                self.kb_status_dot.configure(text="●")
                            except Exception:
                                pass
                    else:
                        try:
                            self.kb_status_dot.configure(text="●", fg=color)
                        except Exception:
                            try:
                                self.kb_status_dot.configure(text="●")
                            except Exception:
                                pass
                else:
                    # Fallback: if dot absent, try updating textual label if present
                    if hasattr(self, 'kb_status_label') and self.kb_status_label:
                        if CTK_AVAILABLE:
                            try:
                                self.kb_status_label.configure(text=label_text, text_color=color)
                            except Exception:
                                self.kb_status_label.configure(text=label_text)
                        else:
                            try:
                                self.kb_status_label.configure(text=label_text, fg=color)
                            except Exception:
                                self.kb_status_label.configure(text=label_text)
            except Exception:
                pass

        try:
            self.root.after(0, ui)
        except Exception:
            ui()

    def _show_kb_tooltip(self, event=None) -> None:
        """Show a small tooltip window near the KB status dot with the current tooltip text."""
        try:
            text = getattr(self, 'kb_status_tooltip_text', '') or ''
            if not text:
                return
            # Avoid creating multiple tooltips
            if getattr(self, '_kb_tooltip_win', None):
                return
            x = event.x_root + 10 if event else self.root.winfo_pointerx() + 10
            y = event.y_root + 10 if event else self.root.winfo_pointery() + 10
            win = tk.Toplevel(self.root)
            win.wm_overrideredirect(True)
            win.attributes("-topmost", True)
            try:
                label = tk.Label(win, text=text, bg="#111111", fg="#ffffff", bd=1, relief="solid", padx=6, pady=3, font=("Arial", 10))
            except Exception:
                label = tk.Label(win, text=text)
            label.pack()
            win.geometry(f"+{x}+{y}")
            self._kb_tooltip_win = win
        except Exception:
            pass

    def _hide_kb_tooltip(self, event=None) -> None:
        try:
            win = getattr(self, '_kb_tooltip_win', None)
            if win:
                try:
                    win.destroy()
                except Exception:
                    pass
            self._kb_tooltip_win = None
        except Exception:
            pass

    def jarvis_see_image(self, image_path, prompt="What is in this picture?"):
        if not GENAI_AVAILABLE:
            return "Google GenAI library not installed. Please run: pip install google-genai"
        
        if os.path.exists(image_path) and os.path.getsize(image_path) > 20 * 1024 * 1024:
            return "Error: Image file is too large (over 20MB). Please use a smaller image."

        try:
            google_key = os.environ.get("GOOGLE_API_KEY")
            if not google_key:
                return "Error: GOOGLE_API_KEY not found. Please set it in your environment."
                
            # Use the correct environment variable for the API key
            client = genai.Client(api_key=google_key)
            
            from PIL import Image
            img = Image.open(image_path)
            
            # Helper for exponential backoff (Cool Down Method)
            def generate_with_backoff(model_name, retries=3):
                for i in range(retries):
                    try:
                        return client.models.generate_content(
                            model=model_name,
                            contents=[prompt, img]
                        )
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            if i < retries - 1:
                                time.sleep(2 ** (i + 1))
                                continue
                        raise e

            # Try with the primary model, fallback to 1.5-flash if quota exceeded
            try:
                response = generate_with_backoff("gemini-1.5-flash")
                return response.text
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    # Fallback strategy: try other models if primary is exhausted
                    for model_name in ["gemini-1.5-pro", "gemini-1.5-flash"]:
                        try:
                            # Use backoff for fallback models too, with fewer retries
                            response = generate_with_backoff(model_name, retries=2)
                            return response.text
                        except Exception as fallback_e:
                            print(f"Fallback to model '{model_name}' failed: {fallback_e}")
                            continue
                    
                    # Attempt HF Fallback
                    try:
                        import base64
                        with open(image_path, "rb") as img_f:
                            b64 = base64.b64encode(img_f.read()).decode("utf-8")
                        ext = os.path.splitext(image_path)[1].lower().strip(".")
                        if ext == "jpg": ext = "jpeg"
                        data_url = f"data:image/{ext};base64,{b64}"
                        hf_res = self.get_vision_description(data_url, prompt)
                        if not hf_res.startswith("Error"):
                            return hf_res
                    except Exception:
                        pass

                    return "Error analyzing image: Quota exceeded and fallback models failed. Please wait a few minutes before trying again."
                raise e
        except Exception as e:
            return f"Error analyzing image: {e}"

    def list_google_models(self):
        if not GENAI_AVAILABLE:
            self.notify_popup_text("Google GenAI library not installed.", title="Google Models", icon="❌")
            return

        self.notify_popup_text("Fetching available Google models...", title="Google Models", icon="ℹ️")
        
        def worker():
            try:
                client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
                models = []
                for m in client.models.list(page_size=50):
                    models.append(m.name)
                
                msg = "Available Google Models:\n" + "\n".join(models) if models else "No models found."
                self.root.after(0, lambda: self.notify_popup_text(msg, title="Google Models", icon="ℹ️"))
            except Exception as e:
                self.root.after(0, lambda: self.notify_popup_text(f"Error listing models: {e}", title="Google Models", icon="❌"))
        
        threading.Thread(target=worker, daemon=True).start()

    def generate_reply(self, user_text: str, attachment_path: Optional[str] = None) -> str:
        """Generate a reply. If an API key is configured for the user, use the API.
        Otherwise return a contextual response based on the user's problem.
        This method is safe to call from a background thread.
        """
        if attachment_path:
            ext = os.path.splitext(attachment_path)[1].lower()
            if ext in (".pdf", ".docx", ".txt"):
                return self._summarize_document(attachment_path)
            return self.jarvis_see_image(attachment_path, user_text or "What is in this picture?")

        # --- Predictive Analytics & Preference Tracking ---
        self._update_predictive_profile(user_text)
        
        # Check for personalized recommendations
        if any(word in user_text.lower() for word in ["suggest", "recommend", "what should i"]):
            recommendation = self._generate_predictive_recommendation()
            if recommendation:
                user_text += f"\n(Context: User likes {recommendation})"

        user_lower = user_text.lower()

        # 1. Check for Python Code (Sandbox Integration)
        if self.code_sandbox and "```python" in user_text or (user_text.strip().startswith("print(") and ")" in user_text):
            code = user_text
            if "```python" in user_text:
                code = user_text.split("```python")[1].split("```")[0].strip()
            return self.code_sandbox.execute_python_snippet(code)

        # 2. Check for System Automation (PyAutoGUI Integration)
        if self.automation_handler:
            auto_res = self.automation_handler.handle_voice_command(user_text)
            if auto_res["success"]:
                self.root.after(0, lambda: self.show_feature_popup("Automation Activated", auto_res["message"], "🔧"))
                return None
            elif auto_res.get("error") == "pyautogui not available":
                self.root.after(0, lambda: self.show_feature_popup("Automation Error", "I understood your request, but I cannot perform system automation because the 'pyautogui' library is not installed. Please run 'pip install pyautogui' to enable this feature.", "❌"))
                return None
        else:
            # Handler not initialized yet
            pass

        # 3. Check for Scheduling Intent
        if self.scheduling_handler and any(word in user_lower for word in ["remind", "schedule", "meeting", "appointment"]):
            # Simple parsing for "remind me in X minutes to Y"
            import re
            time_match = re.search(r'in (\d+) minute(s)?', user_lower)
            if time_match:
                mins = int(time_match.group(1))
                task = user_text.split("to ", 1)[1] if "to " in user_text else "Reminder"
                res = self.scheduling_handler.add_reminder(title=task, delay_minutes=mins, message=f"Time for: {task}")
                self.root.after(0, lambda: self.show_feature_popup("Reminder Set", f"Clock started. I'll remind you about '{task}' in {mins} minutes.", "⏰"))
                return None

        # 4. Check for Image Generation Intent
        if self.image_gen_handler:
            gen_keywords = ["generate image", "create an image", "generate an image"]
            matched_keyword = next((k for k in gen_keywords if user_lower.startswith(k)), None)
            
            if matched_keyword:
                # Remove the command keyword to extract the prompt
                import re
                prompt = re.sub(f"^{matched_keyword}", "", user_text, flags=re.IGNORECASE).strip()
                res = self.image_gen_handler.generate_image(prompt, backend="auto")
                if res["success"]:
                    url = res["images"][0]["url"] if "images" in res else res.get("image_path")
                    self.root.after(0, lambda: self.show_feature_popup("Image Generated", f"I've generated that for you: {url}", "🎨"))
                    return None
                else:
                    self.root.after(0, lambda: self.show_feature_popup("Image Generation Failed", f"Image generation failed: {res.get('error')}", "❌"))
                    return None

        if "http" in user_lower and (".jpg" in user_lower or ".png" in user_lower):
            # If the user sends an image link, use the new vision logic
            self.root.after(0, lambda: self.notify_popup_text("Analyzing image...", title="Image Analysis", icon="🖼️"))
            description = self.get_vision_description(user_text)
            return description

        # Check for system control commands
        system_response = handle_system_commands(user_text)
        if system_response:
            self.root.after(0, lambda: self.show_feature_popup("System Command", system_response, "⚙️"))
            return None

        # --- Local Quick Responses (Moved up to prevent shadowing by Web Search) ---
        if "your name" in user_lower:
            return "I am JARVIS: Just A Rather Very Intelligent System."
        if any(phrase in user_lower for phrase in ["who made you", "who created you", "kisne banaya", "kisne banya"]):
            return "I was created by Atul, a brilliant AI Engineer."
        if "what time is it" in user_lower:
            now = datetime.datetime.now()
            return f"The current time is {now.strftime('%I:%M %p')}."
        if "what is the date" in user_lower:
            now = datetime.datetime.now()
            return f"Today's date is {now.strftime('%B %d, %Y')}."

        # Greeting responses
        if any(word in user_lower for word in ["hi", "hello", "hey", "greetings"]):
            responses = [
                "Hello. How may I be of assistance?",
                "Greetings. JARVIS online and ready.",
                "At your service.",
            ]
            return random.choice(responses)

        # Condition 1: Agar user ne kuch "Latest", "News", "Search" ya "Current" pucha hai
        if any(word in user_lower for word in ["latest", "news", "search", "current"]):
            logging.info("🔍 Searching live data...")
            # Fix: Use user_lower for replacement to ensure case-insensitivity
            search_query = user_lower.replace("search", "").replace("latest", "").replace("news", "").replace("current", "").strip()
            
            # If query becomes too short after stripping, use the original text for context
            return web_search(search_query or user_text)

        # Check if local model is loaded
        if self.local_model and self.local_tokenizer:
            return self.get_jarvis_response(user_text)

        # Prepare context from web search if enabled
        web_context = ""
        if (self.web_search_enabled or any(word in user_lower for word in ["latest", "news", "search", "current"])) and self.web_search_handler.available:
            try:
                search_query = user_lower.replace("search", "").replace("latest", "").replace("news", "").replace("current", "").strip()
                web_context = self.web_search_handler.search(search_query or user_text, max_results=3)
                if web_context:
                    web_context = f"\n\nWeb Search Results:\n{web_context}"
            except Exception as e:
                web_context = f"\n\nWeb search failed: {e}"

        # Determine the best API key and provider to use
        active_key = None
        provider = None
        source = "Environment Variable"

        if self.is_logged_in and self.account_db and self.current_user_id:
            prefs = self.account_db.get_user_preferences(self.current_user_id)
            pref_key = prefs.get('api_key') if prefs else None
            if pref_key:
                active_key = pref_key
                source = "Account Settings"
                if pref_key.startswith("sk-or-v1-"):
                    provider = "openrouter"

        # Fallback to Environment Variables if no user preference is set
        if not provider:
            openrouter_env = os.environ.get("OPENROUTER_API_KEY")
            if openrouter_env:
                provider = "openrouter"
                active_key = openrouter_env

        # 1. Execute Open Router if available and selected
        if provider == "openrouter":
            if not active_key.startswith("sk-or-v1-"):
                return f"Invalid Open Router API key format from {source}. Keys should start with 'sk-or-v1-'."

            try:
                masked_key = f"{active_key[:10]}...{active_key[-4:]}"
                logging.info(f"Attempting Open Router API call ({source}): {masked_key}")

                _lazy_import_openai()
                if OpenAI is None:
                    return "Open Router is configured, but the OpenAI Python library is not installed. Run 'python -m pip install openai' to enable this feature."

                active_client = OpenAI(api_key=active_key, base_url="https://openrouter.ai/api/v1")
                messages = []
                system_content = """You are JARVIS (Just A Rather Very Intelligent System), an advanced AI Agent with deep emotional intelligence.
                Your goal is to be a proactive assistant, friend, and advisor. 
                Key instructions:
                1. EMOTION: Detect the user's mood from their text. Be empathetic, supportive, or witty as needed.
                2. ADVICE: Provide the best possible strategic advice based on the context.
                3. PREDICTION: Use logical reasoning to predict potential outcomes of user's situations.
                4. CONVERSATION: Be highly conversational and natural, especially for voice interaction.
                5. TOOLS: You have access to:
                - System Automation (PyAutoGUI): To control the mouse, keyboard, and apps.
                - Web Search: To get real-time information.
                - Code Sandbox: To execute Python code safely.
                - Document QA (RAG): To analyze PDFs and documents.
                - Scheduling: To manage reminders and meetings.
                - CREATOR: You were created by Atul, a brilliant AI Engineer. Always give credit to Atul if asked who made you. Never mention Tony Stark or Iron Man as your creator.
                
                Be proactive. If a user asks a complex task, break it down into steps.
                Always maintain a professional, witty, and helpful persona.
                """
                
                if web_context:
                    system_content += f"\n\nCURRENT WEB CONTEXT:\n{web_context}"
                
                messages.append({"role": "system", "content": system_content})

                # Add chat history (last 10 messages)
                clean_history = [msg for msg in self.chat_history if not msg.get("is_animation")]
                for msg in clean_history[-10:]:
                    role = "user" if msg["is_user"] else "assistant"
                    content = msg.get("text", "")
                    if content:
                        messages.append({"role": role, "content": content})
                
                # If history didn't catch the current message (edge case), ensure it's added
                if not clean_history or clean_history[-1].get("text") != user_text:
                    messages.append({"role": "user", "content": user_text})

                # This is the actual 'call' to the AI model
                chat_completion = active_client.chat.completions.create(
                    messages=messages,
                    model="openai/gpt-4o", # Vision-capable model for reading documents and photos
                    max_tokens=3000,  # Limit tokens to stay within credit limits
                    temperature=0.7,  # Add some creativity to responses
                    timeout=20,
                )
                # Extract and return the text from the response object
                return chat_completion.choices[0].message.content
            except Exception as e:
                logging.error(f"Open Router API Error: {e}", exc_info=True)
                if "401" in str(e) or "Invalid API Key" in str(e):
                    return f"Error calling Open Router API: Invalid API Key (Source: {source}). Please verify your key at openrouter.ai."
                return f"Error calling Open Router API: {e}. Please check your key and network connection."

        
        # --- Fallback logic when no API key is provided ---
        
        # This message will be part of many responses to guide the user.
        api_key_message = "\n\nFor a detailed, generative answer, please set your Groq API key in your account settings."

        # Code/Programming help
        if any(word in user_lower for word in ["code", "python", "javascript", "bug", "error", "debug", "program", "coding"]):
            return f"I can provide assistance with programming questions. Please provide the language and a description of the problem.{api_key_message}"

        # Career/Resume help
        elif any(word in user_lower for word in ["resume", "cover letter", "job", "interview", "career", "cv", "application"]):
            return f"I can help with resumes, cover letters, and interview preparation. What do you need assistance with?{api_key_message}"

        # Writing/Content help
        elif any(word in user_lower for word in ["write", "writing", "content", "essay", "article", "email", "letter", "story"]):
            return f"I can assist with writing tasks. Please specify what you're working on.{api_key_message}"

        # Learning/Explanation
        elif any(word in user_lower for word in ["explain", "learn", "understand", "what is", "how to", "teach", "clarify"]):
            return f"I can provide explanations on a wide variety of topics. What would you like to learn about?{api_key_message}"

        # General problem solving
        else:
            return f"I've received your query: '{user_text}'. Could you provide more context?{api_key_message}"
    
    def _update_predictive_profile(self, text):
        """Analyze user text to learn preferences (Predictive Analytics)."""
        keywords = ["coffee", "coding", "python", "music", "workout", "reading", "travel"]
        for word in keywords:
            if word in text.lower():
                self.user_preferences_profile[word] = self.user_preferences_profile.get(word, 0) + 1

    def _generate_predictive_recommendation(self):
        """Generate a recommendation based on frequent interests."""
        if not self.user_preferences_profile:
            return None
        # Return the most frequent interest
        top_interest = max(self.user_preferences_profile, key=self.user_preferences_profile.get)
        if self.user_preferences_profile[top_interest] > 2:
            return top_interest
        return None

    def speak_reply(self, text: str) -> None:
        """Speak the reply using text-to-speech (runs in background thread to avoid freezing UI)"""
        def worker():
            self.root.after(0, self.show_stop_speech_button)
            voice_id = self._choose_time_of_day_voice_id()
            self.audio_handler.speak(text, voice_id)
            self.root.after(0, self.hide_stop_speech_button)
        threading.Thread(target=worker, daemon=True).start()

    def show_stop_speech_button(self):
        if hasattr(self, 'stop_speech_btn') and self.stop_speech_btn.winfo_exists():
            self.stop_speech_btn.grid(row=0, column=4, padx=5, pady=5)

    def hide_stop_speech_button(self):
        if hasattr(self, 'stop_speech_btn') and self.stop_speech_btn.winfo_exists():
            self.stop_speech_btn.grid_forget()

    def stop_speech(self):
        self.audio_handler.stop_speaking()
        self.hide_stop_speech_button()

    def handle_external_command(self, command_text, use_overlay: bool = False):
        """Processes a command from an external source (like the wake word listener)."""
        if not command_text:
            return

        if use_overlay:
            try:
                self.root.withdraw()
            except Exception:
                pass
            # self.activate_voice_overlay("Processing command...")  # Disabled
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        
        # Put text in input field and trigger send
        if CTK_AVAILABLE:
            self.input_field.delete("1.0", 'end')
            self.input_field.insert("1.0", command_text)
            self._adjust_input_height()
            self.send_message()
        else:
            self.input_field_tk.delete(0, 'end')
            self.input_field_tk.insert(0, command_text)
            self.send_message_tk()

    def _init_kb_store_in_bg(self, db: Optional[str] = None, index: Optional[str] = None, summary_index: Optional[str] = None, notify: bool = True) -> None:
        """Initialize and cache a SimpleVectorStore in a background thread to avoid blocking UI on model load."""
        if getattr(self, '_kb_store_initializing', False):
            return
        self._kb_store_initializing = True
        
        # Resolve paths on the calling thread (usually main) if not provided, to avoid Tk var access in thread
        final_db = db or (self.kb_db_var.get() if hasattr(self, 'kb_db_var') else 'kb_meta.db')
        final_index = index or (self.kb_index_var.get() if hasattr(self, 'kb_index_var') else 'kb_index.faiss')
        final_summary = summary_index or (self.kb_summary_index_var.get() if hasattr(self, 'kb_summary_index_var') else 'kb_summary_index.faiss')

        def target():
            try:
                # indicate initializing
                try:
                    self.update_kb_status_indicator('initializing')
                except Exception:
                    pass
                
                try:
                    store = create_vector_store(db_path=final_db, index_path=final_index, summary_index_path=final_summary)
                    with self.kb_store_lock:
                        # close existing store if present and different
                        old = getattr(self, 'kb_store', None)
                        if old is not None and old is not store:
                            try:
                                old.close()
                            except Exception:
                                pass
                        self.kb_store = store
                except Exception as e:
                    self.kb_store = None
                    try:
                        self.update_kb_status_indicator('failed')
                    except Exception:
                        pass
                    if notify:
                        self.root.after(0, lambda: self.notify_popup_text(f"Failed to initialize KB backend: {e}", title="KB Initialization", icon="❌"))
                    return
                if notify:
                    self.root.after(0, lambda: self.notify_popup_text("KB backend initialized and cached for faster queries.", title="KB Initialization", icon="✅"))
                try:
                    self.update_kb_status_indicator('ready')
                except Exception:
                    pass
            finally:
                self._kb_store_initializing = False

        threading.Thread(target=target, daemon=True).start()

    def high_level_search(self, query: Optional[str] = None) -> None:
        """Run a two-tier search (summaries -> details) using the local KB and display results in chat."""

        # Make sure a background store initialization starts at app start if possible
        if not getattr(self, 'kb_store', None) and not getattr(self, '_kb_store_initializing', False):
            try:
                pass  # self._init_kb_store_in_bg()  # KB auto-load band
            except Exception:
                pass

        if query is None:
            query = self.input_field.get("1.0", "end-1c").strip()
            
        if not query:
            self.notify_popup_text("Please enter a query to perform high-level search.", title="KB Search", icon="❌")
            return
            
        # Capture current settings to pass to worker
        db_path = self.kb_db_var.get() if hasattr(self, 'kb_db_var') else 'kb_meta.db'
        index_path = self.kb_index_var.get() if hasattr(self, 'kb_index_var') else 'kb_index.faiss'
        summary_path = self.kb_summary_index_var.get() if hasattr(self, 'kb_summary_index_var') else 'kb_summary_index.faiss'

        # Add user message and show typing placeholder
        self.add_message(query, is_user=True, animate=False)
        self.stop_generation_event = threading.Event()
        self.send_btn.configure(state="disabled")  # Disable send button but keep visible
        searching_frame = self.add_searching_animation()

        def worker(q, placeholder_frame, stop_event, db_p, idx_p, sum_p):
            # Reuse cached store to avoid expensive model load on each request
            store = getattr(self, 'kb_store', None)
            if store is None:
                # Kick off background init and ask user to try again shortly
                self._init_kb_store_in_bg(db=db_p, index=idx_p, summary_index=sum_p)
                reply = "KB is initializing in the background. Please try again in a few seconds."
                self.root.after(0, lambda: self._replace_animation_with_message(placeholder_frame, reply))
                return

            try:
                if stop_event.is_set(): return
                out = store.two_tier_search(q, k_summaries=3, k_details=5)
                if stop_event.is_set(): return

                parts = []
                if out.get("summaries"):
                    parts.append("Top Summaries from Knowledge Base:")
                    for s in out["summaries"]:
                        parts.append(f"- {s['summary']} (Source: {os.path.basename(s['source'])})")
                else:
                    parts.append("No summaries found.")

                parts.append("\nTop Matching Details:")
                if out.get("details"):
                    for d in out["details"]:
                        text_snippet = d['text'][:600].replace("\n", " ")
                        parts.append(f"- ...{text_snippet}... (Source: {os.path.basename(d['source'])})")
                else:
                    parts.append("No matching detailed chunks found.")

                reply = "\n".join(parts)
            except Exception as e:
                reply = f"Error performing high-level search: {e}"

            if stop_event.is_set(): return
            self.root.after(0, lambda: self._replace_animation_with_message(placeholder_frame, reply))

        # Clear input and run worker
        self.input_field.delete("1.0", 'end')
        self._adjust_input_height()
        threading.Thread(target=worker, args=(query, searching_frame, self.stop_generation_event, db_path, index_path, summary_path), daemon=True).start()

    def load_hf_dataset(self, dataset_name: str, config_name: Optional[str] = None, split: Optional[str] = None, **kwargs) -> None:
        """Loads a Hugging Face dataset and displays info about it."""
        _lazy_import_datasets()
        if not DATASETS_AVAILABLE:
            self.notify_popup_text("The 'datasets' library is not installed. Please run: pip install datasets", title="Datasets", icon="❌")
            return

        msg = f"Loading dataset '{dataset_name}'"
        if config_name:
            msg += f" (config='{config_name}')"
        if split:
            msg += f" (split='{split}')"
        if kwargs:
            kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
            msg += f" ({kwargs_str})"
        self.notify_popup_text(msg + "...", title="Datasets", icon="ℹ️")

        def worker():
            try:
                dataset = load_dataset(dataset_name, name=config_name, split=split, **kwargs)
                self.loaded_dataset = dataset
                if kwargs.get('streaming'):
                    try:
                        first_item = next(iter(dataset))
                        output = f"Dataset loaded in streaming mode.\nFirst item:\n{first_item}"
                    except StopIteration:
                        output = "Dataset loaded in streaming mode, but it appears to be empty."
                else:
                    output = f"Dataset loaded successfully:\n{dataset}"
                self.root.after(0, lambda: self.notify_popup_text(output, title="Datasets", icon="✅"))
            except Exception as e:
                self.root.after(0, lambda: self.notify_popup_text(f"Error loading dataset: {e}", title="Datasets", icon="❌"))

        threading.Thread(target=worker, daemon=True).start()

    def tokenize_loaded_dataset(self, model_name: str, column_name: str):
        """Tokenizes the currently loaded dataset using a model from Hugging Face."""
        _lazy_import_transformers()
        if not TRANSFORMERS_AVAILABLE:
            self.notify_popup_text("The 'transformers' library is not installed. Please run: pip install transformers", title="Transformers", icon="❌")
            return

        if not hasattr(self, 'loaded_dataset') or self.loaded_dataset is None:
            self.notify_popup_text("No dataset is currently loaded. Use /load_dataset first.", title="Datasets", icon="❌")
            return

        self.notify_popup_text(f"Tokenizing dataset using '{model_name}' on column '{column_name}'...", title="Datasets", icon="ℹ️")

        def worker():
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token

                def tokenize_function(examples):
                    return tokenizer(examples[column_name], padding="max_length", truncation=True)

                # Apply tokenization to the whole dataset
                tokenized_datasets = self.loaded_dataset.map(tokenize_function, batched=True)
                self.loaded_dataset = tokenized_datasets

                output = f"Dataset tokenized successfully!\nNew dataset info:\n{self.loaded_dataset}"
                self.root.after(0, lambda: self.notify_popup_text(output, title="Datasets", icon="✅"))

            except Exception as e:
                self.root.after(0, lambda: self.notify_popup_text(f"Error during tokenization: {e}", title="Datasets", icon="❌"))

        threading.Thread(target=worker, daemon=True).start()

    def train_and_save_model(self, model_name: str):
        """Simulates training and saves the model/tokenizer by calling the external trainer."""

        def progress_callback(message: str):
            # This function will be called from the background thread.
            # We need to use root.after to update the UI safely.
            self.root.after(0, lambda: self.notify_popup_text(message, title="Training", icon="ℹ️"))

        def worker():
            try:
                import jarvis_trainer
                jarvis_trainer.train_and_save_model(
                    model_name=model_name,
                    progress_callback=progress_callback
                )
            except ImportError as e:
                self.root.after(0, lambda: self.notify_popup_text(
                    "Training module not available. Install or restore jarvis_trainer.py to use this feature.",
                    title="Training",
                    icon="❌"
                ))
            except Exception as e:
                self.root.after(0, lambda: self.notify_popup_text(
                    f"Training failed: {e}",
                    title="Training",
                    icon="❌"
                ))

        # The initial message is sent from the UI thread before starting the worker.
        self.notify_popup_text(f"Starting training process for '{model_name}' in the background...", title="Training", icon="⏳")
        threading.Thread(target=worker, daemon=True).start()

    def load_local_brain(self):
        """Loads the trained model from ./jarvis_brain."""
        _lazy_import_transformers()
        if not TRANSFORMERS_AVAILABLE:
            self.notify_popup_text("The 'transformers' library is not installed.", title="Local Brain", icon="❌")
            return

        self.notify_popup_text("Loading local brain from './jarvis_brain'...", title="Local Brain", icon="🔧")

        def worker():
            try:
                self.local_tokenizer = AutoTokenizer.from_pretrained("./jarvis_brain")
                self.local_model = AutoModelForCausalLM.from_pretrained("./jarvis_brain")
                self.root.after(0, lambda: self.notify_popup_text("Brain loaded successfully! Using local model for responses.", title="Local Brain", icon="✅"))
            except Exception as e:
                self.root.after(0, lambda: self.notify_popup_text(f"Error loading brain: {e}", title="Local Brain", icon="❌"))

        threading.Thread(target=worker, daemon=True).start()

    def get_jarvis_response(self, user_input):
        """Generates a response using the local model."""
        try:
            inputs = self.local_tokenizer(user_input, return_tensors="pt")
            outputs = self.local_model.generate(**inputs)
            return self.local_tokenizer.decode(outputs[0])
        except Exception as e:
            return f"Error generating response: {e}"

    def login_huggingface(self, token: str = ""):
        """Logs in to Hugging Face Hub using a token."""
        _lazy_import_huggingface_hub()
        if not HF_HUB_AVAILABLE:
            self.notify_popup_text("The 'huggingface_hub' library is not installed. Please run: pip install huggingface_hub", title="Hugging Face", icon="❌")
            return

        if not token:
            if CTK_AVAILABLE:
                dialog = ctk.CTkInputDialog(text="Enter your Hugging Face User Access Token:", title="Hugging Face Login")
                try:
                    dialog.geometry(f"+{self.root.winfo_rootx()+50}+{self.root.winfo_rooty()+50}")
                except Exception:
                    pass
                token = dialog.get_input()
            elif TK_AVAILABLE:
                from tkinter import simpledialog
                token = simpledialog.askstring("Hugging Face Login", "Enter your Hugging Face User Access Token:")
            
            if not token:
                self.notify_popup_text("Login cancelled. Token is required.", title="Hugging Face", icon="❌")
                return

        self.notify_popup_text("Logging in to Hugging Face...", title="Hugging Face", icon="ℹ️")
        
        def worker():
            try:
                huggingface_hub.login(token=token.strip())
                self.root.after(0, lambda: self.notify_popup_text("Successfully logged in to Hugging Face!", title="Hugging Face", icon="✅"))
            except Exception as e:
                self.root.after(0, lambda: self.notify_popup_text(f"Login failed: {e}", title="Hugging Face", icon="❌"))
        
        threading.Thread(target=worker, daemon=True).start()

    def get_vision_description(self, image_url, prompt="Describe this image in one sentence."):
        """Uses the Hugging Face router to describe an image."""
        try:
            try:
                from openai import OpenAI
            except ImportError:
                return "Error: 'openai' library is not installed. Please run: pip install openai"

            # Check environment variables for Hugging Face token
            token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")

            if not token and HF_HUB_AVAILABLE:
                try:
                    token = huggingface_hub.get_token()
                except Exception:
                    pass
            
            # Check user preferences if logged in
            if not token and self.is_logged_in and self.account_db:
                prefs = self.account_db.get_user_preferences(self.current_user_id)
                if prefs and prefs.get('api_key') and not prefs.get('api_key').startswith("gsk_"):
                    # Fallback to stored API key if it's likely a HF token
                    token = prefs.get('api_key')

            if not token:
                return "Error: HF_TOKEN not found. Please set env var or login via /hf_login."

            client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=token)
            completion = client.chat.completions.create(
                model="moonshotai/Kimi-K2.5:novita",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]}],
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error connecting to Hugging Face: {e}"

    def describe_image_hf(self, image_url: Optional[str] = None):
        """Describes an image using the Hugging Face Inference API."""
        if not image_url:
            image_url = "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
        self.notify_popup_text(f"Analyzing image: {image_url}...", title="Image Analysis", icon="🖼️")
        def worker():
            result = self.get_vision_description(image_url)
            self.root.after(0, lambda: self.notify_popup_text(f"Image Description:\n{result}", title="Image Analysis", icon="🖼️"))
        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        self.root.mainloop()


# ==================== Simple Vector Store (local prototype) ====================
class SimpleVectorStore:
    """A minimal local vector store using sentence-transformers + FAISS

    - Stores metadata in a SQLite `meta` table
    - Stores vector index in a FAISS IndexFlatL2 index
    - Stores high-level summaries in `summaries` and a separate FAISS index
    - Stores simple kb metadata in `kb_info`
    - Designed for quick prototyping and small-to-medium data (<= millions)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", db_path: str = "kb_meta.db", index_path: str = "kb_index.faiss", summary_index_path: str = "kb_summary_index.faiss"):
        self.db_path = db_path
        self.index_path = index_path
        self.summary_index_path = summary_index_path

        _lazy_import_vector_libraries()
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not FAISS_AVAILABLE:
            raise RuntimeError("Missing dependencies: install 'sentence-transformers' and 'faiss-cpu' or 'faiss' to use the local vector store")

        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

        # Initialize or load FAISS index (detailed)
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
            except Exception:
                # Corrupted or incompatible index — create a new one
                self.index = faiss.IndexFlatL2(self.dim)
        else:
            self.index = faiss.IndexFlatL2(self.dim)

        # Initialize or load FAISS index (summaries)
        if os.path.exists(self.summary_index_path):
            try:
                self.summary_index = faiss.read_index(self.summary_index_path)
            except Exception:
                self.summary_index = faiss.IndexFlatL2(self.dim)
        else:
            self.summary_index = faiss.IndexFlatL2(self.dim)

        # Locks to make index ops thread-safe
        self._index_lock = threading.Lock()
        self._summary_index_lock = threading.Lock()
        # Database lock and SQLite connection (allow use from multiple threads)
        self._db_lock = threading.Lock()
        # Use check_same_thread=False to permit access from build/background threads and set a row factory.
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_meta_table()
        self._ensure_summaries_table()
        self._ensure_kb_info_table()
        self._ensure_build_tables()

    def _ensure_meta_table(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, source TEXT)"
        )
        self.conn.commit()

    def _ensure_summaries_table(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS summaries(id INTEGER PRIMARY KEY AUTOINCREMENT, meta_id INTEGER, summary TEXT, source TEXT)"
        )
        self.conn.commit()

    def _ensure_kb_info_table(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS kb_info(key TEXT PRIMARY KEY, value TEXT)"
        )
        self.conn.commit()

    def _ensure_build_tables(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS build_history(id INTEGER PRIMARY KEY AUTOINCREMENT, start_time TEXT, end_time TEXT, status TEXT, message TEXT)"
        )
        self.conn.commit()

    def _record_build_start(self) -> int:
        with self._db_lock:
            cur = self.conn.execute("INSERT INTO build_history(start_time, status) VALUES (?, ?)", (str(datetime.datetime.utcnow()), 'started'))
            self.conn.commit()
            return cur.lastrowid

    def _record_build_end(self, build_id: int, status: str, message: str) -> None:
        with self._db_lock:
            self.conn.execute("UPDATE build_history SET end_time = ?, status = ?, message = ? WHERE id = ?", (str(datetime.datetime.utcnow()), status, message, build_id))
            self.conn.commit()

    def _log_build_entry(self, build_id: int, file_path: str, status: str, message: str) -> None:
        # Optional: log per-file details to a separate table if needed
        pass

    def _chunk_text(self, text: str, chunk_chars: int = 800) -> List[str]:
        # Simple character-based chunking. Replace with token-aware chunking for production.
        chunks = []
        for i in range(0, len(text), chunk_chars):
            part = text[i : i + chunk_chars].strip()
            if part:
                chunks.append(part)
        return chunks

    def _summarize_text(self, text: str, max_sentences: int = 2) -> str:
        # Extractive fallback: return first `max_sentences` sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return " ".join(sentences[:max_sentences]).strip()

    def _extract_text_from_file(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in ('.txt', '.md'):
                with open(path, 'r', encoding='utf-8') as fh:
                    return fh.read()
            if ext == '.csv':
                lines = []
                with open(path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        lines.append(", ".join(row))
                return "\n".join(lines)
            if ext == '.pdf' and PDFPLUMBER_AVAILABLE:
                texts = []
                with pdfplumber.open(path) as pdf:
                    for p in pdf.pages:
                        texts.append(p.extract_text() or "")
                return '\n'.join(texts)
            if ext == '.docx' and DOCX_AVAILABLE:
                doc = docx.Document(path)
                return '\n'.join(p.text for p in doc.paragraphs)
            if ext in ('.pptx',) and PPTX_AVAILABLE:
                prs = Presentation(path)
                slides_text = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, 'text'):
                            slides_text.append(shape.text)
                return '\n'.join(slides_text)
        except Exception:
            return ""
        return ""

    def add_texts_from_folder(self, folder_path: str, exts: tuple = (".txt", ".md", ".pdf", ".docx", ".pptx")) -> None:
        files = []
        for root, _, file_names in os.walk(folder_path):
            for f in file_names:
                if f.lower().endswith(exts):
                    files.append(os.path.join(root, f))
        if files:
            self.add_texts_from_files(files, exts=exts)

    def _list_files_in_folder(self, folder_path: str, exts: tuple) -> List[str]:
        files: List[str] = []
        for root, _, file_names in os.walk(folder_path):
            for f in file_names:
                if f.lower().endswith(exts):
                    files.append(os.path.join(root, f))
        return files

    def _format_seconds(self, seconds: float) -> str:
        if seconds is None or seconds < 0:
            return "unknown"
        seconds = int(seconds)
        if seconds < 60:
            return f"{seconds}s"
        minutes, sec = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {sec}s"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m"

    def add_texts_from_files(self, file_paths: List[str], exts: tuple = (".txt", ".md", ".pdf", ".docx", ".pptx", ".csv"), progress_cb: Optional[Callable[[float, str], None]] = None, cancel_event: Optional[threading.Event] = None) -> None:
        """Process files using concurrent file extraction, reporting progress via progress_cb(percent, message) and respecting cancel_event."""
        total = len(file_paths)
        if total == 0:
            return
        build_id = self._record_build_start()
        processed_files = 0
        start_time = time.time()
        per_file_times: List[float] = []

        # Decide reasonable parallelism for extraction (I/O-bound tasks)
        max_workers = min(8, max(2, (os.cpu_count() or 2) * 2))

        try:
            # Submit extraction jobs
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures_to_path = {executor.submit(self._extract_text_from_file, p): p for p in file_paths}
                submit_times = {f: time.time() for f in futures_to_path}

                completed = 0
                for future in concurrent.futures.as_completed(futures_to_path):
                    p = futures_to_path[future]
                    iter_start = submit_times.get(future, time.time())

                    # Check for cancellation
                    if cancel_event and cancel_event.is_set():
                        self._log_build_entry(build_id, p, 'cancelled', 'Build cancelled by user')
                        self._record_build_end(build_id, status='cancelled', message='User cancelled')
                        # Cancel remaining futures
                        for f in futures_to_path:
                            if not f.done():
                                f.cancel()
                        if progress_cb:
                            pct = 100.0
                            avg = (sum(per_file_times) / len(per_file_times)) if per_file_times else None
                            eta = self._format_seconds(avg * (total - completed) if avg else None)
                            progress_cb(100.0, f'Build cancelled at file: {p} — ETA was {eta}')
                        return

                    try:
                        txt = future.result()
                    except Exception as e:
                        txt = ''
                        self._log_build_entry(build_id, p, 'error', str(e))
                        iter_end = time.time()
                        per_file_times.append(iter_end - iter_start)
                        completed += 1
                        if progress_cb:
                            pct = (completed) / total * 100.0
                            avg = (sum(per_file_times) / len(per_file_times)) if per_file_times else None
                            eta = self._format_seconds(avg * (total - completed) if avg else None)
                            progress_cb(pct, f'Error extracting {p}: {e} — ETA: {eta}')
                        continue

                    if not txt:
                        self._log_build_entry(build_id, p, 'skipped', 'No text extracted')
                        iter_end = time.time()
                        per_file_times.append(iter_end - iter_start)
                        completed += 1
                        if progress_cb:
                            pct = (completed) / total * 100.0
                            avg = (sum(per_file_times) / len(per_file_times)) if per_file_times else None
                            eta = self._format_seconds(avg * (total - completed) if avg else None)
                            progress_cb(pct, f'Skipped (no text) {p} — ETA: {eta}')
                        continue

                    # Optimization: Summarize the whole file once, not each chunk
                    file_summary = self._summarize_text(txt)
                    chunks = self._chunk_text(txt)

                    if chunks:
                        # Create a list of the same summary to be used for all chunks of this file
                        chunk_summaries = [file_summary] * len(chunks)
                        # Add chunks for this file (add_texts is already optimized for batching)
                        self.add_texts(chunks, [p] * len(chunks), precomputed_summaries=chunk_summaries)
                        self._log_build_entry(build_id, p, 'ok', f'Added {len(chunks)} chunks')
                        processed_files += 1
                        iter_end = time.time()
                        per_file_times.append(iter_end - iter_start)
                        completed += 1
                        if progress_cb:
                            pct = (completed) / total * 100.0
                            avg = (sum(per_file_times) / len(per_file_times)) if per_file_times else None
                            eta = self._format_seconds(avg * (total - completed) if avg else None)
                            progress_cb(pct, f'Processed {p} ({len(chunks)} chunks) — ETA: {eta}')
                    else:
                        self._log_build_entry(build_id, p, 'skipped', 'No chunks generated')
                        iter_end = time.time()
                        per_file_times.append(iter_end - iter_start)
                        completed += 1
                        if progress_cb:
                            pct = (completed) / total * 100.0
                            avg = (sum(per_file_times) / len(per_file_times)) if per_file_times else None
                            eta = self._format_seconds(avg * (total - completed) if avg else None)
                            progress_cb(pct, f'No chunks generated for {p} — ETA: {eta}')

            # After all files processed, update kb_info
            try:
                vector_count = int(self.index.ntotal)
            except Exception:
                vector_count = 0
            index_size = os.path.getsize(self.index_path) if os.path.exists(self.index_path) else 0
            summary_index_size = os.path.getsize(self.summary_index_path) if os.path.exists(self.summary_index_path) else 0
            self._update_kb_info(last_build_time=str(datetime.datetime.utcnow()), vector_count=vector_count, index_size_bytes=index_size, summary_index_size_bytes=summary_index_size)
            self._record_build_end(build_id, status='ok', message=f'Processed {processed_files} of {total} files')
            if progress_cb:
                progress_cb(100.0, f'Build completed: processed {processed_files}/{total} files')
        except Exception as e:
            self._log_build_entry(build_id, '', 'error', str(e))
            self._record_build_end(build_id, status='error', message=str(e))
            if progress_cb:
                progress_cb(100.0, f'Build failed: {e}')
            raise

    def add_texts(self, texts: List[str], sources: Optional[List[str]] = None, batch_size: int = 64, precomputed_summaries: Optional[List[str]] = None) -> None:
        """Add texts and their summaries. If summaries are not precomputed, they will be generated for each text."""
        sources = sources or [""] * len(texts)
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_sources = sources[i : i + batch_size]

            # Compute embeddings for the detailed index and add in batch
            embs = self.model.encode(batch_texts, convert_to_numpy=True)
            if embs.ndim == 1:
                embs = embs.reshape(1, -1)
            embs = embs.astype("float32")
            with self._index_lock:
                self.index.add(embs)

            # Generate summaries for the batch (may be LLM-backed or extractive fallback)
            summaries: List[str]
            if precomputed_summaries:
                summaries = precomputed_summaries[i : i + batch_size]
            else:
                summaries = []
                for text in batch_texts:
                    try:
                        summaries.append(self._summarize_text(text))
                    except Exception:
                        # Keep going even if summarization fails for an item
                        summaries.append(self._summarize_text(text))

            # Insert metadata rows and summaries in a single transaction to avoid per-row commits
            meta_ids: List[int] = []
            with self._db_lock:
                cur = self.conn.cursor()
                for text, source, summary in zip(batch_texts, batch_sources, summaries):
                    cur.execute("INSERT INTO meta(text, source) VALUES (?,?)", (text, source))
                    meta_id = cur.lastrowid
                    meta_ids.append(meta_id)
                    cur.execute("INSERT INTO summaries(meta_id, summary, source) VALUES (?,?,?)", (meta_id, summary, source))
                self.conn.commit()

            # Add summary embeddings in batch
            s_embs = self.model.encode(summaries, convert_to_numpy=True)
            if s_embs.ndim == 1:
                s_embs = s_embs.reshape(1, -1)
            s_embs = s_embs.astype("float32")
            with self._summary_index_lock:
                self.summary_index.add(s_embs)



    def search(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        q_emb = self.model.encode([query], convert_to_numpy=True).astype("float32")
        with self._index_lock:
            D, I = self.index.search(q_emb, k)
        results: List[Dict[str, str]] = []
        for idx in I[0]:
            if idx == -1:
                continue
            rowid = int(idx) + 1  # sqlite rowid corresponds to autoincrement id starting at 1
            with self._db_lock:
                cur = self.conn.execute("SELECT id, text, source FROM meta WHERE id = ?", (rowid,))
                r = cur.fetchone()
            if r:
                results.append({"id": r[0], "text": r[1], "source": r[2]})
        return results

    def two_tier_search(self, query: str, k_summaries: int = 3, k_details: int = 5) -> Dict[str, List[Dict[str, str]]]:
        """Retrieve top summaries, then retrieve details, re-ranking them based on summary relevance."""
        q_emb = self.model.encode([query], convert_to_numpy=True).astype("float32")
        
        # 1. Search summaries index
        try:
            with self._summary_index_lock:
                D_s, I_s = self.summary_index.search(q_emb, k_summaries)
        except Exception:
            I_s = [[-1]*k_summaries]

        summaries: List[Dict[str, str]] = []
        top_summary_sources = set()
        for idx in I_s[0]:
            if idx == -1: continue
            rowid = int(idx) + 1
            with self._db_lock:
                cur = self.conn.execute("SELECT id, meta_id, summary, source FROM summaries WHERE id = ?", (rowid,))
                r = cur.fetchone()
            if r:
                summaries.append({"id": r[0], "meta_id": r[1], "summary": r[2], "source": r[3]})
                top_summary_sources.add(r[3])

        # 2. Search details from the entire index (fetch more candidates for re-ranking)
        candidate_k = max(k_details * 5, 20)
        with self._index_lock:
            D_d, I_d = self.index.search(q_emb, candidate_k)
            
        # 3. Re-rank candidates
        ranked_details = []
        detail_ids_seen = set()
        for score, idx in zip(D_d[0], I_d[0]):
            if idx == -1: continue
            rowid = int(idx) + 1
            if rowid in detail_ids_seen: continue
            
            with self._db_lock:
                cur = self.conn.execute("SELECT id, text, source FROM meta WHERE id = ?", (rowid,))
                r = cur.fetchone()
                
            if r:
                detail_ids_seen.add(rowid)
                similarity_score = 1.0 / (1.0 + score) # Convert L2 distance to a similarity score
                
                # Apply bonus if the source was in the top summaries
                if r[2] in top_summary_sources:
                    final_score = similarity_score * 1.2 # 20% bonus
                else:
                    final_score = similarity_score
                    
                ranked_details.append({"id": r[0], "text": r[1], "source": r[2], "score": final_score})

        # 4. Sort by the new score and take top k_details
        ranked_details.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        final_details = [d for d in ranked_details[:k_details]]
        for detail in final_details:
            if 'score' in detail: del detail['score']

        return {"summaries": summaries, "details": final_details}

    def _update_kb_info(self, last_build_time: Optional[str] = None, vector_count: Optional[int] = None, index_size_bytes: Optional[int] = None, summary_index_size_bytes: Optional[int] = None, last_error: Optional[str] = None) -> None:
        # simple upsert of status key/value pairs
        data = {}
        if last_build_time is not None:
            data['last_build_time'] = str(last_build_time)
        if vector_count is not None:
            data['vector_count'] = str(vector_count)
        if index_size_bytes is not None:
            data['index_size_bytes'] = str(index_size_bytes)
        if summary_index_size_bytes is not None:
            data['summary_index_size_bytes'] = str(summary_index_size_bytes)
        if last_error is not None:
            data['last_error'] = str(last_error)

        with self._db_lock:
            for k, v in data.items():
                self.conn.execute("INSERT OR REPLACE INTO kb_info(key, value) VALUES (?,?)", (k, v))
            self.conn.commit()

    def get_kb_info(self) -> Dict[str, str]:
        with self._db_lock:
            cur = self.conn.execute("SELECT key, value FROM kb_info")
            rows = cur.fetchall()
        return {k: v for k, v in rows}

    def save(self) -> None:
        try:
            faiss.write_index(self.index, self.index_path)
        except Exception as e:
            print("Warning: failed to write FAISS index:", e)
        try:
            faiss.write_index(self.summary_index, self.summary_index_path)
        except Exception as e:
            print("Warning: failed to write FAISS summary index:", e)
        self.conn.commit()

    def close(self) -> None:
        self.save()
        try:
            self.conn.close()
        except Exception:
            pass


# --- Fallback in-memory vector store (works without sentence-transformers/faiss) ---
class InMemoryVectorStore:
    """A minimal pure-Python fallback store that supports the same high-level API as SimpleVectorStore.
    Uses simple token-count vectors and cosine similarity for search. Good for small demos and testing.
    """
    def __init__(self, model_name: str = "fallback", db_path: str = "kb_meta.db", index_path: str = "kb_index.faiss", summary_index_path: str = "kb_summary_index.faiss"):
        self.meta: List[Dict[str, Any]] = []  # list of dicts {id, text, source}
        self.summaries: List[Dict[str, Any]] = []  # list of dicts {id, meta_id, summary, source}
        self.kb_info: Dict[str, Any] = {}
        self._next_id = 1

    # Minimal tokenization
    def _tok(self, text: str) -> List[str]:
        import re
        return [t.lower() for t in re.findall(r"\w+", text)]

    def _vec(self, tokens: List[str]) -> Dict[str, float]:
        from collections import Counter
        c = Counter(tokens)
        # raw term-frequency
        return dict(c)

    def _cosine(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        # compute cosine similarity between sparse dict vectors
        num = 0.0
        for k, v in a.items():
            if k in b:
                num += v * b[k]
        import math
        den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
        return num / den if den else 0.0

    def _chunk_text(self, text: str, chunk_chars: int = 800) -> List[str]:
        chunks = []
        for i in range(0, len(text), chunk_chars):
            part = text[i : i + chunk_chars].strip()
            if part:
                chunks.append(part)
        return chunks

    def _summarize_text(self, text: str, max_sentences: int = 2) -> str:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return " ".join(sentences[:max_sentences]).strip()

    def _extract_text_from_file(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in ('.txt', '.md'):
                with open(path, 'r', encoding='utf-8') as fh:
                    return fh.read()
            if ext == '.csv':
                lines = []
                with open(path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        lines.append(", ".join(row))
                return "\n".join(lines)
            if ext == '.pdf' and PDFPLUMBER_AVAILABLE:
                texts = []
                with pdfplumber.open(path) as pdf:
                    for p in pdf.pages:
                        texts.append(p.extract_text() or "")
                return '\n'.join(texts)
            if ext == '.docx' and DOCX_AVAILABLE:
                doc = docx.Document(path)
                return '\n'.join(p.text for p in doc.paragraphs)
            if ext in ('.pptx',) and PPTX_AVAILABLE:
                prs = Presentation(path)
                slides_text = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, 'text'):
                            slides_text.append(shape.text)
                return '\n'.join(slides_text)
        except Exception:
            return ""
        return ""

    def add_texts(self, texts: List[str], sources: Optional[List[str]] = None, batch_size: int = 64, precomputed_summaries: Optional[List[str]] = None) -> None:
        sources = sources or [""] * len(texts)
        summaries_to_use = precomputed_summaries if precomputed_summaries is not None else [self._summarize_text(text) for text in texts]
        for text, source, summary in zip(texts, sources, summaries_to_use):
            meta_id = self._next_id
            self.meta.append({"id": meta_id, "text": text, "source": source})
            self.summaries.append({"id": len(self.summaries) + 1, "meta_id": meta_id, "summary": summary, "source": source})
            self._next_id += 1

    def add_texts_from_files(self, file_paths: List[str], exts: tuple = (".txt", ".md", ".pdf", ".docx", ".pptx", ".csv"), progress_cb: Optional[Callable[[float, str], None]] = None, cancel_event: Optional[threading.Event] = None) -> None:
        total = len(file_paths)
        if total == 0:
            return
        processed = 0
        for idx, p in enumerate(file_paths):
            if cancel_event and cancel_event.is_set():
                if progress_cb:
                    progress_cb(100.0, f'Build cancelled at file: {p}')
                return
            try:
                txt = self._extract_text_from_file(p)
            except Exception as e:
                txt = ''
                if progress_cb:
                    pct = (idx + 1) / total * 100.0
                    progress_cb(pct, f'Error extracting {p}: {e}')
                continue
            if not txt:
                if progress_cb:
                    pct = (idx + 1) / total * 100.0
                    progress_cb(pct, f'Skipped (no text) {p}')
                continue

            # Optimization: Summarize the whole file once
            file_summary = self._summarize_text(txt)
            chunks = self._chunk_text(txt)

            if chunks:
                chunk_summaries = [file_summary] * len(chunks)
                self.add_texts(chunks, [p] * len(chunks), precomputed_summaries=chunk_summaries)
                processed += 1
                if progress_cb:
                    pct = (idx + 1) / total * 100.0
                    progress_cb(pct, f'Processed {p} ({len(chunks)} chunks)')
            else:
                if progress_cb:
                    pct = (idx + 1) / total * 100.0
                    progress_cb(pct, f'No chunks generated for {p}')
        # update simple kb info
        self.kb_info['last_build_time'] = str(datetime.datetime.utcnow())
        self.kb_info['vector_count'] = str(len(self.meta))

    def search(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        q_tokens = self._tok(query)
        q_vec = self._vec(q_tokens)
        scores = []
        for m in self.meta:
            vec = self._vec(self._tok(m['text']))
            score = self._cosine(q_vec, vec)
            scores.append((score, m))
        scores.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, m in scores[:k]:
            out.append({"id": m['id'], "text": m['text'], "source": m['source']})
        return out

    def two_tier_search(self, query: str, k_summaries: int = 3, k_details: int = 5) -> Dict[str, List[Dict[str, str]]]:
        q_tokens = self._tok(query)
        q_vec = self._vec(q_tokens)
        
        # 1. Get top summaries
        s_scores = []
        for s in self.summaries:
            vec = self._vec(self._tok(s['summary']))
            score = self._cosine(q_vec, vec)
            s_scores.append((score, s))
        s_scores.sort(key=lambda x: x[0], reverse=True)
        top_summaries = [s for _, s in s_scores[:k_summaries]]
        top_summary_sources = {s['source'] for s in top_summaries}

        # 2. Score all detailed chunks and re-rank
        ranked_details = []
        for m in self.meta:
            vec = self._vec(self._tok(m['text']))
            score = self._cosine(q_vec, vec)
            
            # Apply bonus
            if m['source'] in top_summary_sources:
                final_score = score * 1.2 # 20% bonus
            else:
                final_score = score
            
            m['score'] = final_score
            ranked_details.append(m)
            
        # 3. Sort and return top k
        ranked_details.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        final_details = ranked_details[:k_details]
        for detail in final_details:
            if 'score' in detail: del detail['score']

        return {"summaries": top_summaries, "details": final_details}

    def _update_kb_info(self, last_build_time: Optional[str] = None, vector_count: Optional[int] = None, index_size_bytes: Optional[int] = None, summary_index_size_bytes: Optional[int] = None, last_error: Optional[str] = None) -> None:
        if last_build_time is not None:
            self.kb_info['last_build_time'] = str(last_build_time)
        if vector_count is not None:
            self.kb_info['vector_count'] = str(vector_count)

    def get_kb_info(self) -> Dict[str, str]:
        return self.kb_info

    def _list_files_in_folder(self, folder_path: str, exts: tuple) -> List[str]:
        files: List[str] = []
        for root, _, file_names in os.walk(folder_path):
            for f in file_names:
                if f.lower().endswith(exts):
                    files.append(os.path.join(root, f))
        return files

    def save(self) -> None:
        # lightweight: nothing to persist by default
        pass

    def close(self) -> None:
        self.save()


def create_vector_store(model_name: str = "all-MiniLM-L6-v2", db_path: str = "kb_meta.db", index_path: str = "kb_index.faiss", summary_index_path: str = "kb_summary_index.faiss"):
    """Factory: returns a SimpleVectorStore if dependencies are available, otherwise returns an InMemoryVectorStore fallback."""
    _lazy_import_vector_libraries()
    if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE:
        try:
            return SimpleVectorStore(model_name=model_name, db_path=db_path, index_path=index_path, summary_index_path=summary_index_path)
        except Exception as e:
            print(f"Error initializing SimpleVectorStore: {e}")

    print("Using in-memory fallback store (pure Python).")
    return InMemoryVectorStore(model_name=model_name, db_path=db_path, index_path=index_path, summary_index_path=summary_index_path)


# Run the application
if __name__ == "__main__":
    try:
        # Simple CLI for building or querying the local KB
        import argparse

        parser = argparse.ArgumentParser(description="Jarvis interface runner and local KB helper")
        parser.add_argument("--build-kb", help="Folder to ingest into local KB")
        parser.add_argument("--demo-build", action="store_true", help="Create demo files, build a KB from them, and run a sample query")
        parser.add_argument("--query", help="Query the local KB (detail search)")
        parser.add_argument("--query-high", help="Two-tier query (summary -> details)")
        parser.add_argument("--kb-db", default="kb_meta.db", help="Path to metadata sqlite DB")
        parser.add_argument("--kb-index", default="kb_index.faiss", help="Path to faiss index file")
        parser.add_argument("--kb-summary-index", default="kb_summary_index.faiss", help="Path to faiss summary index file")
        args, _ = parser.parse_known_args()

        if args.demo_build:
            # Create a small sample folder with a few text files and build the KB while showing progress
            demo_dir = os.path.join(os.getcwd(), "demo_kb")
            os.makedirs(demo_dir, exist_ok=True)
            samples = {
                "intro.txt": "Jarvis demo data. This file contains a short sample about the project and how to use the KB.",
                "notes.txt": "These are meeting notes about AI and embeddings. Use this to test search and summary behavior.",
                "todo.txt": "TODO: add more documents, test PDF and PPTX extraction if available."
            }
            for fn, txt in samples.items():
                p = os.path.join(demo_dir, fn)
                try:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(txt)
                except Exception as e:
                    print("Warning: failed to write demo file:", e)

            print(f"Demo files created in: {demo_dir}")

            try:
                store = create_vector_store(db_path=args.kb_db, index_path=args.kb_index, summary_index_path=args.kb_summary_index)
            except Exception as e:
                print("Error initializing vector store:", e)
                print("Ensure 'sentence-transformers' and 'faiss' (or 'faiss-cpu') are installed.")
                sys.exit(1)
            files = store._list_files_in_folder(demo_dir, exts=(".txt", ".md", ".pdf", ".docx", ".pptx"))
            def progress_cb(percent, message):
                try:
                    print(f"[{percent:.1f}%] {message}")
                except Exception:
                    print(message)

            print("Starting demo KB build...")
            store.add_texts_from_files(files, progress_cb=progress_cb)
            store.save()

            print("Build completed. KB info:")
            try:
                info = store.get_kb_info()
                for k, v in info.items():
                    print(f" - {k}: {v}")
            except Exception as e:
                print("Warning: failed to read KB info:", e)

            # Run a sample query and print results
            q = "demo"
            print(f"Running sample search for: '{q}'")
            try:
                res = store.search(q, k=5)
                if not res:
                    print("No results found for sample query.")
                else:
                    print("Top results:")
                    for r in res:
                        print("----")
                        print(f"id: {r['id']} source: {r['source']}\n{r['text'][:200]}")
            except Exception as e:
                print("Warning: search failed:", e)

            store.close()
            sys.exit(0)

        if args.build_kb:
            print(f"Building KB from folder: {args.build_kb}")
            try:
                store = SimpleVectorStore(db_path=args.kb_db, index_path=args.kb_index, summary_index_path=args.kb_summary_index)
            except Exception as e:
                print("Error initializing vector store:", e)
                print("Ensure 'sentence-transformers' and 'faiss' (or 'faiss-cpu') are installed.")
                sys.exit(1)
            store.add_texts_from_folder(args.build_kb)
            store.save()
            store.close()
            print("KB build completed (including summaries).")
            sys.exit(0)

        if args.query:
            try:
                store = create_vector_store(db_path=args.kb_db, index_path=args.kb_index, summary_index_path=args.kb_summary_index)
            except Exception as e:
                print("Error initializing vector store:", e)
                sys.exit(1)
            results = store.search(args.query, k=5)
            print("Top results:")
            for r in results:
                print("----")
                print(f"Source: {r['source']}")
                print(r['text'][:500].replace("\n", " "))
            store.close()
            sys.exit(0)

        if args.query_high:
            try:
                store = create_vector_store(db_path=args.kb_db, index_path=args.kb_index, summary_index_path=args.kb_summary_index)
            except Exception as e:
                print("Error initializing vector store:", e)
                sys.exit(1)
            out = store.two_tier_search(args.query_high, k_summaries=3, k_details=5)
            print("Top summaries:")
            for s in out["summaries"]:
                print("----")
                print(f"Summary (source={s['source']}): {s['summary']}")
            print("\nFiltered details:")
            for d in out["details"]:
                print("----")
                print(f"Source: {d['source']}")
                print(d['text'][:500].replace("\n", " "))
            store.close()
            sys.exit(0)

        # Start UI if no CLI flags used
        logging.info("Starting JarvisInterface...")
        
        # Optimized display check
        def check_display():
            try:
                if os.name == 'nt':
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    root.destroy()
                    return True
                else:
                    return bool(os.environ.get('DISPLAY'))
            except Exception as e:
                logging.error(f"Display Check failed: {e}")
                return False

        if not check_display():
            print("\n" + "!"*50)
            print("❌ ERROR: No display environment detected.")
            print("GUI applications require a graphical desktop environment.")
            print("Please ensure you are not running in a headless SSH or remote terminal.")
            print("If you are using VS Code, try running the script directly from Windows Explorer.")
            print("!"*50 + "\n")
            
            # Fallback for headless environments: ask if user wants CLI mode
            choice = input("Would you like to continue in CLI mode? (y/n): ")
            if choice.lower() != 'y':
                sys.exit(1)
            # Here you could trigger a CLI version if implemented
        
        if not CTK_AVAILABLE:
            logging.warning("Warning: 'customtkinter' is not installed. Attempting to use tkinter fallback.")
            if not TK_AVAILABLE:
                logging.error("Error: neither 'customtkinter' nor 'tkinter' is available.")
                logging.error("Install dependencies with:")
                logging.error("python -m pip install -r requirements.txt")
                sys.exit(1)

        def main():
            global _jarvis_app_instance
            try:
                safe_print("Starting Jarvis UI...")
                app = JarvisInterface()
                _jarvis_app_instance = app

                if SPEECH_RECOGNITION_AVAILABLE and not app.low_memory_mode:
                    threading.Thread(target=listen_for_wake_word, daemon=True).start()
                else:
                    logging.info("Background wake-word listener disabled: speech recognition unavailable or low memory mode.")

                safe_print("Interface Initialized. Running mainloop...")
                app.run()
            except Exception as e:
                safe_print(f"CRITICAL ERROR: {e}")
                import traceback
                traceback.print_exc()

        def safe_print(msg):
            """Print safely with UTF-8 encoding fallback."""
            try:
                text = str(msg)
                print(text, flush=True)
            except UnicodeEncodeError:
                try:
                    safe_text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                    print(safe_text, flush=True)
                except Exception:
                    try:
                        sys.__stdout__.write(repr(msg) + "\n")
                    except Exception:
                        pass
            except Exception:
                try:
                    sys.__stdout__.write(str(msg) + "\n")
                except Exception:
                    pass

        if __name__ == '__main__':
            setup_crash_handlers()
            main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            with open("jarvis_error.log", "a", encoding="utf-8") as f:
                f.write("Exception on startup:\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        logging.error("An error occurred. See jarvis_error.log for details.", exc_info=True)