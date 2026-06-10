# VOICE ACTIVATION QUICK START 🤖

## 30-Second Setup

### 1️⃣ Install Packages
```bash
pip install pyaudio SpeechRecognition pyttsx3
```

### 2️⃣ Start Voice Service
```bash
python jarvis_voice_service.py --start
```

### 3️⃣ Say "Hey Jarvis"
Talk to your microphone and say "Hey Jarvis"

### 4️⃣ See Lights Turn On! 💡
Your RGB lights activate with blue glow

---

## Full Setup (with Auto-Startup)

### Windows (with Administrator privileges)
```powershell
# Run as Administrator
setup_voice_activation.ps1
```

### Manual Setup
```bash
# 1. Install dependencies
pip install -r jarvis_enhancements_requirements.txt
pip install pyaudio pyserial phue lifxlan

# 2. Edit configuration (optional)
# - Edit jarvis_config.json
# - Choose light type (generic, philips_hue, lifx, serial)
# - Set light device IP or COM port

# 3. Start service
python jarvis_voice_service.py --start

# 4. Create startup task (optional)
python jarvis_voice_service.py --task
```

---

## Using Different Light Types

### Generic Lights (Testing - No Setup)
```bash
python jarvis_voice_service.py --start
# Lights shown in console output
```

### Philips Hue Lights
```json
// jarvis_config.json
{
  "light_type": "philips_hue",
  "hue_ip": "192.168.1.100"  // Your bridge IP
}
```

### LIFX Smart Lights
```json
// jarvis_config.json
{
  "light_type": "lifx"
  // Automatically discovers devices on network
}
```

### Arduino RGB (Serial)
```json
// jarvis_config.json
{
  "light_type": "serial",
  "serial_port": "COM3"  // Your Arduino COM port
}
```

---

## Integration with Main UI

Open `jarvis_interface.py` and add at the beginning:
```python
from jarvis_voice_activation import VoiceActivationService
from jarvis_lights import LightController

# In __init__:
self.light_controller = LightController("generic")
self.voice_service = VoiceActivationService(
    activation_callback=self.on_voice_activation,
    light_controller=self.light_controller
)
```

See `jarvis_interface_voice_integration.py` for full example.

---

## Control Commands

### Start Service
```bash
python jarvis_voice_service.py --start
```

### Stop Service
```bash
Ctrl+C  # In running terminal
```

### Create Auto-Startup
```bash
python jarvis_voice_service.py --task
# Run as Administrator
```

### Remove Auto-Startup
```bash
python jarvis_voice_service.py --remove-task
# Run as Administrator
```

### With Custom Config
```bash
python jarvis_voice_service.py --start --config my_config.json
```

---

## Customize Wake Words

Edit `jarvis_config.json`:
```json
{
  "wake_words": [
    "hey jarvis",
    "activate jarvis",
    "jarvis"
  ]
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Microphone not found | Check Settings > Privacy > Microphone access |
| "Hey Jarvis" not recognized | Speak clearly, reduce background noise |
| Lights not turning on | Check light_type in config, verify device connection |
| Service won't stay running | Run `setup_voice_activation.ps1` as Administrator |
| Command not recognized after activation | Speak within 10 seconds after activation |

---

## Light Effects

When activated, JARVIS plays:
1. **ACTIVATION effect** - Quick blue burst
2. **BREATHING effect** - Smooth glow for 3 seconds
3. **PULSE effect** - Pulsing light

---

## What's Included

✅ Always-listening voice activation
✅ "Hey Jarvis" wake word detection
✅ RGB light control (multiple types)
✅ Background service (runs even when UI closed)
✅ Windows auto-startup support
✅ Configuration file support
✅ Full integration examples

---

## Files Created

```
jarvis_voice_activation.py        → Voice detection engine
jarvis_lights.py                  → RGB light control
jarvis_voice_service.py           → Background service
jarvis_config.json                → Configuration file
start_voice_service.bat           → Quick launch script
setup_auto_startup.bat            → Setup auto-start
setup_voice_activation.ps1        → PowerShell setup
VOICE_ACTIVATION_GUIDE.md         → Full documentation
VOICE_ACTIVATION_QUICKSTART.md    → This file
jarvis_interface_voice_integration.py → Integration example
```

---

## Next Steps

1. ✅ Run setup
2. ✅ Start voice service
3. ✅ Say "Hey Jarvis"
4. ✅ Watch lights activate
5. ✅ Integrate with main UI

**Questions? See VOICE_ACTIVATION_GUIDE.md for detailed documentation.**

🎉 Enjoy your Iron Man-style JARVIS! 🤖
