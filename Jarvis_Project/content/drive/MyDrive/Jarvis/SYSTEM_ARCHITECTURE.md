# 🏗️ JARVIS Voice Activation - System Architecture

## System Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    JARVIS VOICE ACTIVATION SYSTEM               │
└─────────────────────────────────────────────────────────────────┘

╔═════════════════════════════════════════════════════════════════╗
║                    HARDWARE LAYER                               ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  Microphone        WiFi/Network        RGB Lights/Serial       ║
║      │                  │                      │                ║
│      ▼                  ▼                      ▼                │
║  ┌────────┐      ┌─────────────┐      ┌──────────────┐        ║
║  │  USB   │      │  Router/    │      │  Hue Bridge  │        ║
║  │  Audio │      │  WiFi       │      │  LIFX Hub    │        ║
║  │ Device │      │             │      │  Arduino     │        ║
║  └────────┘      └─────────────┘      └──────────────┘        ║
║                                                                 ║
╚═════════════════════════════════════════════════════════════════╝
              │                  │                      │
              ▼                  ▼                      ▼
┌────────────────────────────────────────────────────────────────┐
│              DRIVER/COMMUNICATION LAYER                        │
├────────────────────────────────────────────────────────────────┤
│ pyaudio         Google Cloud API    phue/lifxlan/pyserial    │
│ (Microphone)    (Speech Recognition)  (Light Control)         │
└────────────────────────────────────────────────────────────────┘
              │                  │                      │
              ▼                  ▼                      ▼
┌────────────────────────────────────────────────────────────────┐
│            SERVICE LAYER                                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  jarvis_voice_service.py                               │  │
│  │  (Background Service Manager)                          │  │
│  │  - Initialization                                      │  │
│  │  - Configuration Management                           │  │
│  │  - Service Lifecycle                                  │  │
│  │  - Logging & Tracking                                 │  │
│  └──────────────────┬─────────────────────────────────────┘  │
│                     │                                        │
│        ┌────────────┴───────────┐                           │
│        ▼                        ▼                           │
│  ┌──────────────┐        ┌──────────────┐                 │
│  │ Voice Svc    │        │ Light Ctrl   │                 │
│  └──────────────┘        └──────────────┘                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
              │                              │
              ▼                              ▼
┌────────────────────────────────────────────────────────────────┐
│          CORE MODULE LAYER                                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────┐                            │
│  │ jarvis_voice_activation.py   │                            │
│  │ ─────────────────────────────┤                            │
│  │ • VoiceActivationService     │                            │
│  │   - listen_loop()            │                            │
│  │   - check_wake_word()        │                            │
│  │   - on_activation()          │                            │
│  │ • WakeWordDetector           │                            │
│  │   - detect()                 │                            │
│  │   - _similarity()            │                            │
│  └──────────────────────────────┘                            │
│                                                                │
│  ┌──────────────────────────────┐                            │
│  │ jarvis_lights.py             │                            │
│  │ ─────────────────────────────┤                            │
│  │ • LightController            │                            │
│  │   - set_color()              │                            │
│  │   - play_effect()            │                            │
│  │   - _pulse_effect()          │                            │
│  │   - _breathing_effect()      │                            │
│  │ • LightColor (Enum)          │                            │
│  │ • LightEffect (Enum)         │                            │
│  └──────────────────────────────┘                            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────┐
│          APPLICATION LAYER                                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Main UI (jarvis_interface.py)                           │ │
│  │ - Optional integration                                  │ │
│  │ - Activation callback                                  │ │
│  │ - UI feedback                                          │ │
│  │ - Light controls                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Background Service (jarvis_voice_service.py --start)    │ │
│  │ - Runs independently                                    │ │
│  │ - No UI required                                        │ │
│  │ - Windows scheduled task                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Activation Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACTIVATION SEQUENCE                          │
└─────────────────────────────────────────────────────────────────┘

[User] "Hey Jarvis"
   │
   ▼
[Microphone]
   │
   ▼
[pyaudio - Audio Capture]
   │
   ▼
[Speech Recognition Service]
   │
   ├─► Google Cloud Speech-to-Text
   │
   ▼
[Text: "Hey Jarvis"]
   │
   ▼
[WakeWordDetector]
   │
   ├─► Exact Match Check ("hey jarvis")
   │
   ├─► Fuzzy Match (Levenshtein Distance)
   │
   ▼
[MATCH FOUND!]
   │
   ├──────────────────────────────────────────┐
   │                                          │
   ▼                                          ▼
[Light Effect]                        [Activation Callback]
   │                                          │
   ├─► LightController                        ├─► User-defined function
   │                                          │
   ├─► play_effect()                          ├─► on_voice_activation()
   │                                          │
   ├─► ACTIVATION effect                      ├─► Show UI
   │                                          │
   ├─► Blue color                             ├─► Prepare for input
   │                                          │
   └─► 3 seconds                              └─► Log event
   
   ▼
[Ready for Commands]
   │
   ▼
[Listen for Next Command] ──► listen_for_command(timeout=10)
   │
   ▼
[Process Command]
```

---

## Data Flow Diagram

```
CONFIG (jarvis_config.json)
   │
   ├─► light_type ─────────────────┐
   │                              │
   ├─► wake_words ──────────────┐ │
   │                            │ │
   ├─► mic_sensitivity ──────┐  │ │
   │                         │  │ │
   ▼                         │  │ │
                            │  │ │
VOICE ACTIVATION SERVICE    │  │ │
   │                         │  │ │
   ├─► Microphone Input ◄────┘  │ │
   │                           │ │
   ├─► Speech Recognition      │ │
   │                           │ │
   ├─► Wake Word Detection ◄───┘ │
   │                           │
   ├─► Activation Event        │
   │                           │
   ▼                           │
                              │
LIGHT CONTROLLER ◄────────────┘
   │
   ├─► Set Color
   │
   ├─► Play Effect
   │
   ▼
   Light Device (Serial/API)
   │
   ▼
   RGB Light Hardware
```

---

## Module Relationships Diagram

```
┌──────────────────────────────────────┐
│   jarvis_voice_service.py            │
│   (Main Service Entry Point)         │
└─────────────┬──────────────────────────┘
              │
              ├─► Imports ──────────────────────────────────┐
              │                                             │
              ▼                                             ▼
    ┌──────────────────────┐                    ┌──────────────────┐
    │ jarvis_core.py       │                    │ jarvis_config    │
    │                      │                    │ (JSON)           │
    │ - speak()            │                    │                  │
    │ - get_engine()       │                    │ - light_type     │
    └──────────────────────┘                    │ - wake_words     │
              ▲                                 │ - settings       │
              │                                 └──────────────────┘
              │
    ┌─────────┴──────────┐
    │                    │
    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│ Voice Service    │  │ Light Controller │
│                  │  │                  │
│ - listen()       │  │ - set_color()    │
│ - detect()       │  │ - play_effect()  │
│ - activate()     │  │ - turn_on/off()  │
└──────────────────┘  └──────────────────┘
    │                    │
    │                    │
    ▼                    ▼
[Google Cloud]    [Device APIs]
[Speech API]      [Hue/LIFX/Serial]
```

---

## Supported Hardware Architecture

```
JARVIS Voice Service (Core)
│
├─────────────────────────────────────────────────┐
│                                                 │
▼                                                 ▼
┌──────────────────────┐              ┌───────────────────────┐
│ Generic/Simulated    │              │ Real Hardware         │
│                      │              │                       │
│ Console Output       │              ├─► Philips Hue        │
│ (For Testing)        │              │   HTTP API            │
│                      │              │                       │
└──────────────────────┘              ├─► LIFX               │
                                      │   WiFi Protocol       │
                                      │                       │
                                      ├─► Arduino RGB        │
                                      │   Serial (COM)        │
                                      │   9600 Baud          │
                                      │                       │
                                      └───────────────────────┘
```

---

## File Structure Diagram

```
Jarvis Project Root
│
├── jarvis_interface.py              [Main UI - Optional]
│   └─ Can integrate voice service
│
├── 🎤 Voice Activation Files
│   ├── jarvis_voice_activation.py   [Core Voice Engine]
│   ├── jarvis_voice_service.py      [Background Service]
│   ├── jarvis_lights.py              [Light Control]
│   └── jarvis_config.json            [Configuration]
│
├── 🚀 Launch Scripts
│   ├── start_voice_service.bat       [Quick Launch]
│   ├── setup_auto_startup.bat        [Auto-Start Setup]
│   └── setup_voice_activation.ps1    [PowerShell Setup]
│
├── 🧪 Testing & Examples
│   ├── test_voice_activation.py      [Test Suite]
│   └── jarvis_interface_voice_integration.py  [Integration Example]
│
├── 📚 Documentation
│   ├── README_VOICE_ACTIVATION.md           [Main Guide]
│   ├── VOICE_ACTIVATION_GUIDE.md            [Detailed Setup]
│   ├── VOICE_ACTIVATION_QUICKSTART.md       [Quick Ref]
│   ├── IMPLEMENTATION_SUMMARY.md            [Summary]
│   └── SYSTEM_ARCHITECTURE.md               [This File]
│
└── Requirements
    └── jarvis_enhancements_requirements.txt  [Dependencies]
```

---

## Execution Flow Diagram

```
START (Windows Scheduler or Manual)
   │
   ▼
jarvis_voice_service.py --start
   │
   ▼
JarvisBackgroundService.start_service()
   │
   ├─► Load Configuration
   │
   ├─► Initialize Light Controller
   │
   ├─► Create Voice Activation Service
   │
   ├─► Start Listening Loop
   │   │
   │   ├─► Continuous microphone monitoring
   │   │
   │   ├─► Speech recognition
   │   │
   │   ├─► Wake word detection
   │   │
   │   └─► On match: Call activation_callback()
   │
   ├─► Service Running Loop
   │   │
   │   └─► Keep alive, log events
   │
   │
[User Input: Ctrl+C]
   │
   ▼
JarvisBackgroundService.stop_service()
   │
   ├─► Stop listening
   │
   ├─► Turn off lights
   │
   ▼
EXIT
```

---

## Threading Model

```
Main Thread
│
├─► Configuration Loading
│
├─► Light Controller Init
│
├─► Voice Service Init
│
├─► Service Loop (sleeps)
│
│
Voice Recognition Thread (Daemon)
├─► Continuous listening
├─► Audio processing
├─► Speech-to-text
├─► Wake word detection
├─► Activation callback
│
│
Light Effect Thread (Daemon - Optional)
├─► ACTIVATION effect
├─► BREATHING effect
├─► PULSE effect
├─► etc.
│
│
Main UI Thread (Optional - if integrated)
├─► Display UI
├─► Handle user input
├─► Receive activation callback
├─► Show visual feedback
│
│
All threads:
├─► Listen to stop_event
├─► Graceful shutdown
└─► Resource cleanup
```

---

## Integration Points

```
╔════════════════════════════════════════════╗
║ JARVIS VOICE ACTIVATION SYSTEM              ║
╠════════════════════════════════════════════╣
║                                            ║
║ Integration Points:                        ║
║                                            ║
║ 1. Activation Callback                     ║
║    on_voice_activation()                   ║
║    └─► Custom user-defined function       ║
║                                            ║
║ 2. Light Controller                        ║
║    lights.play_effect()                    ║
║    lights.set_color()                      ║
║    └─► Custom light effects                ║
║                                            ║
║ 3. Configuration File                      ║
║    jarvis_config.json                      ║
║    └─► Runtime settings                    ║
║                                            ║
║ 4. Main UI (Optional)                      ║
║    jarvis_interface.py                     ║
║    └─► Receive activation events           ║
║                                            ║
║ 5. Command Processing                      ║
║    listen_for_command()                    ║
║    └─► Get next voice command              ║
║                                            ║
╚════════════════════════════════════════════╝
```

---

## System State Diagram

```
┌─────────────┐
│   STOPPED   │ ◄─── Initial State
└──────┬──────┘
       │ start_service()
       ▼
┌─────────────┐
│ INITIALIZING│
└──────┬──────┘
       │ setup complete
       ▼
┌──────────────────┐
│ LISTENING        │ ◄─── Continuous Listening for Wake Word
│ (Audio Input)    │
└────┬───────┬─────┘
     │       │
     │ Wake  │ No match
     │ Word? │ → Stay in LISTENING
     │       │
     │ YES   │
     ▼       │
┌───────────┐│
│ACTIVATING ││
│(Effect)   ││
└─────┬─────┘│
      │      │
      │ Done │
      ▼      │
┌────────────┘
│ LISTENING  (Return to listening, or handle command)
```

---

**This architecture enables a robust, always-listening JARVIS voice activation system that integrates seamlessly with existing JARVIS UI while operating independently!** 🤖✨
