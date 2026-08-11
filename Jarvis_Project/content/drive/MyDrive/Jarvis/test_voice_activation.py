# test_voice_activation.py - Test and Demo Script
# Run this to test voice activation and light features

import sys
import time
import threading
from jarvis_lights import LightController, LightColor, LightEffect
from jarvis_core import speak

def test_lights():
    """Test light effects"""
    print("\n" + "="*50)
    print("🎨 TESTING LIGHT EFFECTS")
    print("="*50 + "\n")
    
    lights = LightController("generic")
    
    # Test 1: Turn on
    print("Test 1: Turning lights ON (Blue)")
    lights.turn_on(LightColor.BLUE)
    time.sleep(1)
    
    # Test 2: Activation effect
    print("Test 2: ACTIVATION effect")
    lights.play_effect(LightEffect.ACTIVATION, LightColor.BLUE, duration=3)
    time.sleep(4)
    
    # Test 3: Breathing effect
    print("Test 3: BREATHING effect")
    lights.play_effect(LightEffect.BREATHING, LightColor.CYAN, duration=3)
    time.sleep(4)
    
    # Test 4: Pulse effect
    print("Test 4: PULSE effect")
    lights.play_effect(LightEffect.PULSE, LightColor.IRON_GOLD, duration=2)
    time.sleep(3)
    
    # Test 5: Rainbow effect
    print("Test 5: RAINBOW effect")
    lights.play_effect(LightEffect.RAINBOW, LightColor.BLUE, duration=4)
    time.sleep(5)
    
    # Test 6: Turn off
    print("Test 6: Turning lights OFF")
    lights.turn_off()
    
    print("\n✅ All light tests completed!")

def test_voice_activation():
    """Test voice activation"""
    print("\n" + "="*50)
    print("🎤 VOICE ACTIVATION TEST")
    print("="*50 + "\n")
    
    from jarvis_voice_activation import VoiceActivationService
    
    activation_count = [0]  # Use list to allow modification in nested function
    
    def on_activation():
        activation_count[0] += 1
        print(f"\n✨ JARVIS ACTIVATED! (Count: {activation_count[0]})")
        lights = LightController("generic")
        lights.play_effect(LightEffect.ACTIVATION, LightColor.BLUE, duration=3)
        speak("I am online and ready for your commands.")
    
    lights = LightController("generic")
    service = VoiceActivationService(
        activation_callback=on_activation,
        light_controller=lights,
        wake_words=["hey jarvis", "jarvis activate"]
    )
    
    print("🎤 Starting voice activation test...")
    print("Say 'Hey Jarvis' or 'Jarvis Activate' to trigger activation")
    print("Press Ctrl+C to stop\n")
    
    service.start_listening()
    
    try:
        # Run for 1 minute or until interrupted
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping test...")
    finally:
        service.stop_listening()
        print(f"\n✅ Voice activation test completed!")
        print(f"Total activations: {activation_count[0]}")

def test_wake_word_detector():
    """Test wake word detection"""
    print("\n" + "="*50)
    print("🔍 WAKE WORD DETECTOR TEST")
    print("="*50 + "\n")
    
    from jarvis_voice_activation import WakeWordDetector
    
    detector = WakeWordDetector(
        wake_words=["hey jarvis", "jarvis activate", "activate jarvis"]
    )
    
    test_phrases = [
        "hey jarvis",
        "HEY JARVIS",
        "Hey Jarvis, how are you",
        "jarvis activate",
        "activate jarvis now",
        "jarvis",
        "hey robot",
        "what is the time",
        "hey jarvisx",  # Fuzzy match test
    ]
    
    print("Testing wake word detection:\n")
    
    for phrase in test_phrases:
        detected = detector.detect(phrase)
        status = "✅ DETECTED" if detected else "❌ NOT detected"
        print(f"{status:20} | {phrase}")
    
    print("\n✅ Wake word detector test completed!")

def test_integration():
    """Show integration example"""
    print("\n" + "="*50)
    print("🔗 INTEGRATION EXAMPLE")
    print("="*50 + "\n")
    
    print("To integrate voice activation into your UI:\n")
    print("1. Import in your main interface:")
    print("   from jarvis_voice_activation import VoiceActivationService")
    print("   from jarvis_lights import LightController\n")
    
    print("2. Initialize in __init__:")
    print("   self.lights = LightController('generic')")
    print("   self.voice = VoiceActivationService(")
    print("       activation_callback=self.on_voice_activation,")
    print("       light_controller=self.lights")
    print("   )\n")
    
    print("3. Start listening:")
    print("   self.voice.start_listening()\n")
    
    print("4. Handle activation:")
    print("   def on_voice_activation(self):")
    print("       print('JARVIS Activated!')")
    print("       # Show UI, get next command, etc.\n")
    
    print("See: jarvis_interface_voice_integration.py for full example")

def show_system_info():
    """Show system information"""
    print("\n" + "="*50)
    print("💻 SYSTEM INFORMATION")
    print("="*50 + "\n")
    
    import platform
    import os
    
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Current Directory: {os.getcwd()}\n")
    
    # Check dependencies
    print("Checking dependencies:")
    
    deps = {
        "speech_recognition": "SpeechRecognition",
        "pyttsx3": "pyttsx3",
        "PIL": "Pillow",
    }
    
    optional_deps = {
        "phue": "Philips Hue support",
        "lifxlan": "LIFX lights support",
        "serial": "Arduino/Serial support",
    }
    
    for import_name, package_name in deps.items():
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} (required)")
    
    print("\nOptional dependencies:")
    for import_name, desc in optional_deps.items():
        try:
            __import__(import_name)
            print(f"  ✅ {desc}")
        except ImportError:
            print(f"  ⚠️  {desc} (optional)")

def main():
    """Main test menu"""
    print("\n" + "🤖 JARVIS VOICE ACTIVATION TEST SUITE 🤖".center(50, "="))
    print()
    
    while True:
        print("\nSelect a test to run:\n")
        print("1. Light Effects Test")
        print("2. Voice Activation Test")
        print("3. Wake Word Detector Test")
        print("4. System Information")
        print("5. Integration Example")
        print("6. Run All Tests")
        print("0. Exit\n")
        
        choice = input("Enter choice (0-6): ").strip()
        
        try:
            if choice == "1":
                test_lights()
            elif choice == "2":
                test_voice_activation()
            elif choice == "3":
                test_wake_word_detector()
            elif choice == "4":
                show_system_info()
            elif choice == "5":
                test_integration()
            elif choice == "6":
                show_system_info()
                test_lights()
                test_wake_word_detector()
                test_integration()
                print("\n✅ All tests completed!")
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print()

if __name__ == "__main__":
    main()
