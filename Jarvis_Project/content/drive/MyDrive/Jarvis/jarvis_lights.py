# jarvis_lights.py - RGB Light Control for Iron Man-style Activation
# Supports multiple light types and effects

import threading
import time
import logging
from typing import Tuple, Optional
from enum import Enum
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightColor(Enum):
    """Predefined colors for JARVIS effects"""
    BLUE = (0, 100, 255)           # Classic JARVIS blue
    CYAN = (0, 255, 255)            # Cyan blue
    IRON_GOLD = (255, 200, 0)       # Iron Man gold
    IRON_RED = (255, 30, 30)        # Iron Man red
    PURPLE = (200, 0, 255)          # Purple
    GREEN = (0, 255, 0)             # Green
    WHITE = (255, 255, 255)         # White
    ORANGE = (255, 165, 0)          # Orange


class LightEffect(Enum):
    """Predefined light effects"""
    PULSE = "pulse"                 # Pulsing effect
    GLOW = "glow"                   # Fade in/out
    STROBE = "strobe"               # Fast flashing
    BREATHING = "breathing"         # Smooth breathing
    RAINBOW = "rainbow"             # Color cycling
    ACTIVATION = "activation"       # Quick burst


class LightController:
    """Main light control class with support for multiple light types"""
    
    def __init__(self, light_type: str = "generic", config: dict = None):
        """
        Initialize light controller
        
        Args:
            light_type: Type of lights ("generic", "philips_hue", "lifx", "serial")
            config: Configuration dictionary
        """
        self.light_type = light_type
        self.config = config or {}
        self.is_active = False
        self.current_color = LightColor.BLUE.value
        self.current_brightness = 255
        self.effect_thread = None
        self.stop_effect = threading.Event()
        
        self._setup_light_type()
    
    def _setup_light_type(self):
        """Setup specific light controller based on type"""
        if self.light_type == "philips_hue":
            self._setup_philips_hue()
        elif self.light_type == "lifx":
            self._setup_lifx()
        elif self.light_type == "serial":
            self._setup_serial()
        else:
            logger.info("Using generic/simulated light mode")
    
    def _setup_philips_hue(self):
        """Setup Philips Hue lights"""
        try:
            from phue import Bridge
            self.bridge = Bridge(self.config.get("hue_ip", "192.168.1.100"))
            self.lights = self.bridge.get_light_objects()
            logger.info(f"Connected to {len(self.lights)} Hue lights")
        except ImportError:
            logger.warning("phue not installed. Install with: pip install phue")
            self.bridge = None
        except Exception as e:
            logger.warning(f"Could not connect to Philips Hue: {e}")
            self.bridge = None
    
    def _setup_lifx(self):
        """Setup LIFX lights"""
        try:
            import lifxlan
            self.lifx = lifxlan.LifxLAN()
            self.lifx_devices = self.lifx.get_lights()
            logger.info(f"Connected to {len(self.lifx_devices)} LIFX devices")
        except ImportError:
            logger.warning("lifxlan not installed. Install with: pip install lifxlan")
            self.lifx = None
        except Exception as e:
            logger.warning(f"Could not connect to LIFX: {e}")
            self.lifx = None
    
    def _setup_serial(self):
        """Setup serial-based RGB controller (Arduino, etc.)"""
        try:
            import serial
            port = self.config.get("serial_port", "COM3")
            self.serial = serial.Serial(port, 9600, timeout=1)
            logger.info(f"Connected to serial device on {port}")
        except ImportError:
            logger.warning("pyserial not installed. Install with: pip install pyserial")
            self.serial = None
        except Exception as e:
            logger.warning(f"Could not connect to serial device: {e}")
            self.serial = None
    
    def set_color(self, color: Tuple[int, int, int], brightness: int = 255):
        """
        Set light color (R, G, B)
        
        Args:
            color: RGB tuple (0-255, 0-255, 0-255)
            brightness: Brightness level (0-255)
        """
        self.current_color = color
        self.current_brightness = brightness
        
        if self.light_type == "philips_hue" and self.bridge:
            self._set_hue_color(color, brightness)
        elif self.light_type == "lifx" and self.lifx:
            self._set_lifx_color(color, brightness)
        elif self.light_type == "serial" and self.serial:
            self._set_serial_color(color, brightness)
        else:
            self._simulate_color(color, brightness)
    
    def _set_hue_color(self, color: Tuple[int, int, int], brightness: int):
        """Set Philips Hue color"""
        try:
            r, g, b = color
            # Convert RGB to Hue XY color space
            xy = self._rgb_to_xy(r, g, b)
            for light in self.lights:
                light.xy = xy
                light.brightness = brightness
            logger.debug(f"Hue: Set color to RGB{color}")
        except Exception as e:
            logger.error(f"Hue color error: {e}")
    
    def _set_lifx_color(self, color: Tuple[int, int, int], brightness: int):
        """Set LIFX color"""
        try:
            r, g, b = color
            h, s, v = self._rgb_to_hsv(r, g, b)
            brightness_lifx = int((brightness / 255) * 65535)
            
            for device in self.lifx_devices:
                device.set_color([h, s, v, 3500], duration=500, rapid=True)
                device.set_brightness(brightness_lifx, rapid=True)
            logger.debug(f"LIFX: Set color to RGB{color}")
        except Exception as e:
            logger.error(f"LIFX color error: {e}")
    
    def _set_serial_color(self, color: Tuple[int, int, int], brightness: int):
        """Set serial RGB controller color"""
        try:
            r, g, b = color
            # Scale to brightness
            r = int(r * brightness / 255)
            g = int(g * brightness / 255)
            b = int(b * brightness / 255)
            
            command = f"RGB:{r},{g},{b}\n".encode()
            self.serial.write(command)
            logger.debug(f"Serial: Set color to RGB({r},{g},{b})")
        except Exception as e:
            logger.error(f"Serial color error: {e}")
    
    def _simulate_color(self, color: Tuple[int, int, int], brightness: int):
        """Simulate color setting (for testing)"""
        r, g, b = color
        r = int(r * brightness / 255)
        g = int(g * brightness / 255)
        b = int(b * brightness / 255)
        logger.info(f"🎨 Light Color: RGB({r}, {g}, {b})")
    
    def activate_response_lights(self):
        """Activate lights for JARVIS activation - Iron Man style"""
        logger.info("⚡ JARVIS Activation Light Effect")
        self.play_effect(LightEffect.ACTIVATION, LightColor.BLUE)
    
    def play_effect(self, effect: LightEffect, color: LightColor, duration: float = 3.0):
        """
        Play a light effect
        
        Args:
            effect: Effect type
            color: Color to use
            duration: Duration in seconds
        """
        # Stop any existing effect
        self.stop_effect.set()
        if self.effect_thread:
            self.effect_thread.join(timeout=2)
        
        self.stop_effect.clear()
        
        if effect == LightEffect.PULSE:
            self.effect_thread = threading.Thread(
                target=self._pulse_effect,
                args=(color, duration),
                daemon=True
            )
        elif effect == LightEffect.BREATHING:
            self.effect_thread = threading.Thread(
                target=self._breathing_effect,
                args=(color, duration),
                daemon=True
            )
        elif effect == LightEffect.ACTIVATION:
            self.effect_thread = threading.Thread(
                target=self._activation_effect,
                args=(color, duration),
                daemon=True
            )
        elif effect == LightEffect.STROBE:
            self.effect_thread = threading.Thread(
                target=self._strobe_effect,
                args=(color, duration),
                daemon=True
            )
        elif effect == LightEffect.RAINBOW:
            self.effect_thread = threading.Thread(
                target=self._rainbow_effect,
                args=(duration,),
                daemon=True
            )
        
        if self.effect_thread:
            self.effect_thread.start()
    
    def _pulse_effect(self, color: LightColor, duration: float):
        """Pulsing light effect"""
        start_time = time.time()
        while time.time() - start_time < duration and not self.stop_effect.is_set():
            progress = (time.time() - start_time) / duration
            brightness = int(128 + 127 * (0.5 * (1 + __import__('math').sin(2 * __import__('math').pi * progress * 3))))
            self.set_color(color.value, brightness)
            time.sleep(0.05)
        self.set_color(color.value, 255)
    
    def _breathing_effect(self, color: LightColor, duration: float):
        """Smooth breathing effect"""
        start_time = time.time()
        while time.time() - start_time < duration and not self.stop_effect.is_set():
            elapsed = time.time() - start_time
            brightness = int(100 + 155 * (0.5 * (1 + __import__('math').sin(2 * __import__('math').pi * elapsed / 2))))
            self.set_color(color.value, brightness)
            time.sleep(0.05)
        self.set_color(color.value, 255)
    
    def _activation_effect(self, color: LightColor, duration: float):
        """Quick burst effect for activation"""
        # Quick ramp up
        for brightness in range(0, 256, 15):
            if self.stop_effect.is_set():
                return
            self.set_color(color.value, brightness)
            time.sleep(0.02)
        
        # Hold bright for a moment
        time.sleep(0.3)
        
        # Settle to normal
        for brightness in range(255, 100, -15):
            if self.stop_effect.is_set():
                return
            self.set_color(color.value, brightness)
            time.sleep(0.03)
    
    def _strobe_effect(self, color: LightColor, duration: float):
        """Fast strobe effect"""
        start_time = time.time()
        while time.time() - start_time < duration and not self.stop_effect.is_set():
            self.set_color(color.value, 255)
            time.sleep(0.1)
            self.set_color(color.value, 0)
            time.sleep(0.1)
    
    def _rainbow_effect(self, duration: float):
        """Color cycling rainbow effect"""
        colors = [
            LightColor.BLUE.value,
            LightColor.CYAN.value,
            LightColor.PURPLE.value,
            LightColor.IRON_RED.value,
            LightColor.IRON_GOLD.value,
            LightColor.GREEN.value,
        ]
        
        start_time = time.time()
        color_index = 0
        
        while time.time() - start_time < duration and not self.stop_effect.is_set():
            self.set_color(colors[color_index], 255)
            color_index = (color_index + 1) % len(colors)
            time.sleep(0.5)
    
    def turn_off(self):
        """Turn off lights"""
        self.stop_effect.set()
        self.set_color((0, 0, 0), 0)
        logger.info("Lights turned off")
    
    def turn_on(self, color: LightColor = LightColor.BLUE):
        """Turn on lights with specific color"""
        self.set_color(color.value, 255)
        logger.info(f"Lights turned on - {color.name}")
    
    @staticmethod
    def _rgb_to_xy(r: int, g: int, b: int) -> Tuple[float, float]:
        """Convert RGB to Hue XY color space"""
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        
        # Apply gamma correction
        if r > 0.04045:
            r = ((r + 0.055) / 1.055) ** 2.4
        else:
            r = r / 12.92
        
        if g > 0.04045:
            g = ((g + 0.055) / 1.055) ** 2.4
        else:
            g = g / 12.92
        
        if b > 0.04045:
            b = ((b + 0.055) / 1.055) ** 2.4
        else:
            b = b / 12.92
        
        # Calculate XYZ
        x = r * 0.664511 + g * 0.154324 + b * 0.162028
        y = r * 0.283881 + g * 0.668433 + b * 0.047685
        z = r * 0.000088 + g * 0.072750 + b * 0.986039
        
        # Calculate XY
        xyz_sum = x + y + z
        if xyz_sum == 0:
            return (0.0, 0.0)
        
        x_final = x / xyz_sum
        y_final = y / xyz_sum
        
        return (round(x_final, 4), round(y_final, 4))
    
    @staticmethod
    def _rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSV color space"""
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c
        
        # Hue
        if delta == 0:
            h = 0
        elif max_c == r:
            h = (60 * ((g - b) / delta) + 360) % 360
        elif max_c == g:
            h = (60 * ((b - r) / delta) + 120) % 360
        else:
            h = (60 * ((r - g) / delta) + 240) % 360
        
        # Saturation
        s = 0 if max_c == 0 else delta / max_c
        
        # Value
        v = max_c
        
        return (int(h / 360 * 65535), int(s * 65535), int(v * 65535))


# Example usage
if __name__ == "__main__":
    # Create light controller (using generic mode for testing)
    lights = LightController("generic")
    
    # Test different effects
    print("Testing light effects...")
    
    lights.play_effect(LightEffect.ACTIVATION, LightColor.BLUE, duration=2)
    time.sleep(3)
    
    lights.play_effect(LightEffect.BREATHING, LightColor.CYAN, duration=3)
    time.sleep(4)
    
    lights.play_effect(LightEffect.PULSE, LightColor.IRON_GOLD, duration=2)
    time.sleep(3)
    
    lights.play_effect(LightEffect.RAINBOW, LightColor.BLUE, duration=3)
    time.sleep(4)
    
    lights.turn_off()
    print("Done!")
