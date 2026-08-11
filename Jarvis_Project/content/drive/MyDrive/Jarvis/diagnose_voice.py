# diagnose_voice.py - Check what's working and what's not

import sys
import os

print("=" * 60)
print("🔍 JARVIS VOICE ACTIVATION DIAGNOSTIC")
print("=" * 60)
print()

# Test 1: Check Python Version
print("1️⃣ Python Version")
print(f"   Python: {sys.version}")
print(f"   Executable: {sys.executable}")
print()

# Test 2: Check SpeechRecognition
print("2️⃣ SpeechRecognition Module")
try:
    import speech_recognition as sr
    print("   ✅ INSTALLED")
    recognizer = sr.Recognizer()
    print(f"   Recognizer created: OK")
except ImportError as e:
    print(f"   ❌ NOT INSTALLED: {e}")
    print("   FIX: pip install SpeechRecognition")
print()

# Test 3: Check pyaudio
print("3️⃣ PyAudio Module")
try:
    import pyaudio
    print("   ✅ INSTALLED")
    pa = pyaudio.PyAudio()
    device_count = pa.get_device_count()
    print(f"   Devices found: {device_count}")
    
    if device_count > 0:
        print("   Available microphones:")
        for i in range(device_count):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"      {i}: {info['name']}")
    else:
        print("   ⚠️ No microphone found!")
    pa.terminate()
except ImportError as e:
    print(f"   ❌ NOT INSTALLED: {e}")
    print("   FIX: pip install pyaudio")
except Exception as e:
    print(f"   ⚠️ ERROR: {e}")
print()

# Test 4: Check pyttsx3
print("4️⃣ pyttsx3 Module")
try:
    import pyttsx3
    print("   ✅ INSTALLED")
    engine = pyttsx3.init()
    print("   Engine created: OK")
except ImportError as e:
    print(f"   ❌ NOT INSTALLED: {e}")
except Exception as e:
    print(f"   ⚠️ ERROR: {e}")
print()

# Test 5: Check jarvis_voice_activation
print("5️⃣ jarvis_voice_activation.py")
try:
    from jarvis_voice_activation import VoiceActivationService
    print("   ✅ MODULE LOADS")
except ImportError as e:
    print(f"   ❌ IMPORT ERROR: {e}")
except Exception as e:
    print(f"   ⚠️ ERROR: {e}")
print()

# Test 6: Check jarvis_lights
print("6️⃣ jarvis_lights.py")
try:
    from jarvis_lights import LightController
    print("   ✅ MODULE LOADS")
except ImportError as e:
    print(f"   ❌ IMPORT ERROR: {e}")
except Exception as e:
    print(f"   ⚠️ ERROR: {e}")
print()

# Test 7: Check Internet Connection
print("7️⃣ Internet Connection (for Google Speech API)")
try:
    import urllib.request
    urllib.request.urlopen("https://www.google.com", timeout=2)
    print("   ✅ CONNECTED")
except Exception as e:
    print(f"   ❌ NO CONNECTION: {e}")
print()

# Test 8: Try creating voice service
print("8️⃣ Creating Voice Activation Service")
try:
    from jarvis_voice_activation import VoiceActivationService
    service = VoiceActivationService()
    print("   ✅ Service created successfully")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 60)
print("SUMMARY:")
print("=" * 60)
print()
print("If all tests show ✅, then voice activation should work!")
print()
print("If any show ❌, follow the FIX instructions above")
print()
print("Run: python diagnose_voice.py")
print()
