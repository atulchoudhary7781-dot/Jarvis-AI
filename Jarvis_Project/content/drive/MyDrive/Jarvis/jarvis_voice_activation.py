# jarvis_voice_activation.py - Always-listening Voice Activation Service
# Mimics Iron Man's JARVIS with background wake-word detection
import speech_recognition as sr
import threading
import queue
import time
from typing import Callable, Optional
import logging
from jarvis_core import speak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceActivationService:
    """
    Always-listening background service that detects "Hey Jarvis" wake word
    Similar to Iron Man's JARVIS voice activation system
    """
    
    def __init__(self, 
                 activation_callback: Optional[Callable] = None,
                 light_controller=None,
                 wake_words=None,
                 language: str = 'en-IN',
                 sensitivity: float = 0.7):
        """
        Initialize the voice activation service
        
        Args:
            activation_callback: Function to call when JARVIS is activated
            light_controller: Light control module for RGB effects
            wake_words: List of wake word phrases
            language: Speech recognition language (e.g., 'en-IN' or 'en-US')
            sensitivity: Confidence threshold for wake word detection (0.0 to 1.0)
        """
        self.activation_callback = activation_callback
        self.light_controller = light_controller
        self.wake_words = wake_words or ["hey jarvis", "jarvis activate", "activate jarvis"]
        self.is_listening = False
        self.recognition_thread = None
        self.command_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.language = language
        self.sensitivity = sensitivity
        self.wake_detector = WakeWordDetector(self.wake_words)
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Lower starting threshold for much better sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8   # Wait slightly longer before ending a phrase
        
    def start_listening(self):
        """Start the background listening service"""
        if self.is_listening:
            logger.warning("Voice activation service already running")
            return
        
        self.is_listening = True
        self.stop_event.clear()
        self.recognition_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.recognition_thread.start()
        logger.info("🎤 Voice activation service started - listening for 'Hey Jarvis'...")
        speak("Voice activation service is online. Say 'Hey Jarvis' to activate me.")
        
    def stop_listening(self):
        """Stop the background listening service"""
        self.is_listening = False
        self.stop_event.set()
        if self.recognition_thread:
            self.recognition_thread.join(timeout=5)
        logger.info("Voice activation service stopped")
        
    def _listen_loop(self):
        """Main listening loop - continuously monitors for wake word"""
        with sr.Microphone() as source:
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.is_listening and not self.stop_event.is_set():
                try:
                    # Listen with timeout
                    audio = self.recognizer.listen(source, timeout=2.0, phrase_time_limit=5)
                    
                    # Try to recognize speech
                    try:
                        text = self.recognizer.recognize_google(audio, language=self.language).lower()
                        logger.debug(f"Recognized: {text}")
                        
                        # Check if wake word detected
                        if self._check_wake_word(text):
                            self._on_activation()
                            
                    except sr.UnknownValueError:
                        # Couldn't understand audio
                        pass
                    except sr.RequestError as e:
                        logger.error(f"Google API error: {e}")
                        time.sleep(2)  # Wait before retrying
                        
                except sr.RequestError:
                    logger.warning("Microphone unavailable, retrying...")
                    time.sleep(2)
                except Exception as e:
                    logger.debug(f"Listen loop error: {e}")
                    time.sleep(0.5)
    
    def _check_wake_word(self, text: str) -> bool:
        """Check if recognized text contains wake word"""
        return self.wake_detector.detect(text, threshold=self.sensitivity)
    
    def _on_activation(self):
        """Called when wake word is detected"""
        logger.info("✨ JARVIS ACTIVATED! 🤖")
        
        # Activate light effect
        if self.light_controller:
            try:
                self.light_controller.activate_response_lights()
            except Exception as e:
                logger.error(f"Light activation error: {e}")
        
        # Call user's callback
        if self.activation_callback:
            try:
                self.activation_callback()
            except Exception as e:
                logger.error(f"Activation callback error: {e}")
    
    def listen_for_command(self, timeout: float = 10.0) -> Optional[str]:
        """
        Listen for a voice command after activation
        
        Args:
            timeout: How long to listen in seconds
            
        Returns:
            Recognized text or None if timeout
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
                text = self.recognizer.recognize_google(audio, language=self.language)
                logger.info(f"Command received: {text}")
                return text
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand that.")
            return None
        except sr.RequestError as e:
            speak("Sorry, there was an error connecting to the speech service.")
            logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Command listening error: {e}")
            return None


class WakeWordDetector:
    """Advanced wake word detection using fuzzy matching"""
    
    def __init__(self, wake_words: list = None):
        self.wake_words = wake_words or ["hey jarvis", "jarvis"]
        
    def detect(self, text: str, threshold: float = 0.8) -> bool:
        """
        Detect wake word with fuzzy matching
        
        Args:
            text: Recognized text
            threshold: Confidence threshold (0.0 to 1.0)
            
        Returns:
            True if wake word detected
        """
        text_lower = text.lower().strip()
        
        for wake_word in self.wake_words:
            # Exact match
            if wake_word in text_lower:
                return True
            
            # Fuzzy match using Levenshtein distance
            similarity = self._similarity(text_lower, wake_word)
            if similarity >= threshold:
                return True
        
        return False
    
    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)"""
        longer = s1 if len(s1) > len(s2) else s2
        shorter = s2 if longer == s1 else s1
        
        if len(longer) == 0:
            return 1.0
        
        edit_distance = _levenshtein_distance(longer, shorter)
        return (len(longer) - edit_distance) / float(len(longer))


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


# Example usage
if __name__ == "__main__":
    from jarvis_lights import LightController
    
    # Initialize light controller
    lights = LightController()
    
    def on_activation():
        print("🔵 JARVIS ACTIVATED!")
        speak("I am online and ready for your commands.")
    
    # Create and start voice activation service
    service = VoiceActivationService(
        activation_callback=on_activation,
        light_controller=lights
    )
    
    service.start_listening()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop_listening()
        print("Service stopped")
