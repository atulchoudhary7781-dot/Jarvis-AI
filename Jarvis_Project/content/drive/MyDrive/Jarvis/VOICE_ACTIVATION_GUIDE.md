# JARVIS Voice Activation Setup Guide - Iron Man Style! 🤖

## Overview

This guide sets up JARVIS to work like Iron Man's AI assistant with:
- **Always-listening voice activation** (says "Hey Jarvis" to activate)
- **RGB light effects** that turn on when activated
- **Background service** that runs even when UI is closed
- **Auto-startup** capability

---

## Quick Start (5 minutes)

### 1. Install Additional Dependencies

```bash
pip install -r jarvis_enhancements_requirements.txt
pip install pyaudio  # For microphone input
```

For Windows, also install:
```bash
pip install pywin32
```

### 2. Configure Lights (Optional)

**For Generic/Simulated Lights (Testing):**
No additional setup needed - will simulate in console.

**For Philips Hue Lights:**
```bash
pip install phue
```
Edit `jarvis_config.json` and set:
```json
{
  "light_type": "philips_hue",
  "hue_ip": "YOUR_HUE_BRIDGE_IP"
}
```

**For LIFX Smart Lights:**
```bash
pip install lifxlan
```
Edit `jarvis_config.json` and set:
```json
{
  "light_type": "lifx"
}
```

**For Arduino/Serial RGB Lights:**
```bash
pip install pyserial
```
Edit `jarvis_config.json` and set:
```json
{
  "light_type": "serial",
  "serial_port": "COM3"
}
```
Update `COM3` to your actual serial port.

### 3. Run JARVIS Background Service

**Option A: Manual Start (Testing)**
```bash
python jarvis_voice_service.py --start
```

**Option B: Use Batch Script**
Double-click: `start_voice_service.bat`

**Option C: Auto-Startup (Windows Only)**
Run as Administrator:
```bash
setup_auto_startup.bat
```

---

## How It Works

### Wake Word Detection
JARVIS continuously listens for:
- "Hey Jarvis"
- "Jarvis Activate"
- "Activate Jarvis"

### Upon Activation:
1. **Lights turn on** with a blue glow effect
2. **JARVIS speaks** "I am online and ready"
3. **Ready for commands** via voice

### Light Effects Available

| Effect | Description |
|--------|-------------|
| **ACTIVATION** | Quick burst - used on wake-up |
| **BREATHING** | Smooth fade in/out |
| **PULSE** | Pulsing effect |
| **STROBE** | Fast flashing |
| **GLOW** | Slow fade |
| **RAINBOW** | Color cycling |

### Colors Available

| Color | RGB Code | Use Case |
|-------|----------|----------|
| BLUE | (0, 100, 255) | Default JARVIS |
| CYAN | (0, 255, 255) | Listening mode |
| IRON_GOLD | (255, 200, 0) | Processing |
| IRON_RED | (255, 30, 30) | Alert/Warning |
| PURPLE | (200, 0, 255) | Special mode |
| GREEN | (0, 255, 0) | Success |

---

## Configuration

### Edit `jarvis_config.json`

```json
{
  "light_type": "generic",           // Light device type
  "wake_words": [                    // Custom wake words
    "hey jarvis",
    "jarvis activate"
  ],
  "mic_sensitivity": 4000,           // Microphone sensitivity
  "speak_activation": true,          // Speak when activated
  "light_on_activation": true,       // Lights turn on
  "hue_ip": "192.168.1.100",        // Philips Hue IP
  "serial_port": "COM3",             // Arduino serial port
  "activation_light_duration": 3.0   // Light effect duration
}
```

---

## Integration with Main JARVIS UI

### Method 1: Integrated Launch

Edit `jarvis_interface.py` to include voice service initialization:

```python
from jarvis_voice_activation import VoiceActivationService
from jarvis_lights import LightController

class JarvisInterface:
    def __init__(self):
        # ... existing code ...
        
        # Initialize voice activation
        self.light_controller = LightController("generic")
        self.voice_service = VoiceActivationService(
            activation_callback=self.on_voice_activation,
            light_controller=self.light_controller
        )
    
    def on_voice_activation(self):
        """Called when JARVIS is activated by voice"""
        print("JARVIS Activated!")
        # Handle activation - show UI, take command, etc.
```

### Method 2: Separate Background Service

Keep voice service running separately in the background while UI runs independently.

---

## Usage Examples

### Start Voice Service
```bash
python jarvis_voice_service.py --start
```

### Create Startup Task (Admin Required)
```bash
python jarvis_voice_service.py --task
```

### Remove Startup Task
```bash
python jarvis_voice_service.py --remove-task
```

### Custom Configuration File
```bash
python jarvis_voice_service.py --start --config my_config.json
```

---

## Advanced: Hardware Setup

### Arduino RGB LED Setup

**Hardware Needed:**
- Arduino board
- RGB LED (common cathode or common anode)
- 3x 220Ω resistors
- Jumper wires
- USB cable

**Arduino Code:**
```cpp
#define RED_PIN 9
#define GREEN_PIN 10
#define BLUE_PIN 11

void setup() {
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    if (data.startsWith("RGB:")) {
      int r = data.substring(4, data.indexOf(',')).toInt();
      int g = data.substring(data.indexOf(',') + 1, data.lastIndexOf(',')).toInt();
      int b = data.substring(data.lastIndexOf(',') + 1).toInt();
      
      analogWrite(RED_PIN, r);
      analogWrite(GREEN_PIN, g);
      analogWrite(BLUE_PIN, b);
    }
  }
}
```

### Philips Hue Bridge Setup

1. Get your Hue Bridge IP:
   - Visit: https://discovery.meethue.com/
   - Find "internalipaddress"

2. Add to `jarvis_config.json`:
```json
{
  "light_type": "philips_hue",
  "hue_ip": "192.168.1.100"
}
```

3. Press physical Hue Bridge button on first run

---

## Troubleshooting

### Microphone Not Working
- Check system microphone permissions
- Test with: `python -m pyaudio`
- Ensure microphone is not muted
- Adjust `mic_sensitivity` in config (lower = more sensitive)

### Voice Not Recognized
- Speak clearly near microphone
- Reduce background noise
- Test with: `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_indexes())"`
- Check internet connection (uses Google Speech API)

### Lights Not Working
- For Philips Hue: Verify bridge IP, press physical button
- For LIFX: Ensure WiFi connection, restart device
- For Serial: Check COM port in Device Manager
- For Generic: Verify console output

### Service Won't Start at Startup
- Run `setup_auto_startup.bat` as Administrator
- Check Task Scheduler: Search "Task Scheduler"
- Look for "JARVIS Background Service"
- Verify Python path is correct

---

## Security & Privacy Notes

- Speech data is sent to Google Cloud Speech-to-Text API
- Local microphone access required
- Consider using offline speech recognition for privacy:
  ```bash
  pip install vosk
  ```

---

## Uninstall / Cleanup

### Stop Background Service
```bash
python jarvis_voice_service.py --stop
```

### Remove Scheduled Task
```bash
python jarvis_voice_service.py --remove-task
```

### Remove Files
```bash
del jarvis_voice_activation.py
del jarvis_lights.py
del jarvis_voice_service.py
del jarvis_config.json
del start_voice_service.bat
del setup_auto_startup.bat
```

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure light hardware
3. ✅ Run `start_voice_service.bat`
4. ✅ Say "Hey Jarvis" near your microphone
5. ✅ Watch your lights turn on! 💡

---

## Support & Customization

For custom wake words, light effects, or hardware:
- Edit `jarvis_config.json` for quick changes
- Modify `jarvis_voice_activation.py` for wake word logic
- Customize `jarvis_lights.py` for light effects

Enjoy your AI assistant! 🤖✨
