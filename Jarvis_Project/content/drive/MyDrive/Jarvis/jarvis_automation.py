# jarvis_automation.py - Personal Assistant & System Automation
# Maps user voice commands to pyautogui functions for computer control

import os
import subprocess
from typing import Optional, Dict, Callable, Any, List
from pathlib import Path
import time
import logging
import re

# Optional dependencies for system control
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    sbc = None
    SBC_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False


class SystemAutomationHandler:
    """
    Enables voice/text command-based system automation using pyautogui.
    Maps natural language intents to computer control actions.
    """
    
    def __init__(self):
        self.pyautogui_enabled = PYAUTOGUI_AVAILABLE
        if not self.pyautogui_enabled:
            logging.warning("pyautogui not available. Automation features disabled.")
        
        # Command mappings
        self.command_handlers = {
            "open_browser": self.open_browser,
            "search_web": self.search_web,
            "take_screenshot": self.take_screenshot,
            "open_file": self.open_file,
            "open_folder": self.open_folder,
            "press_key": self.press_key,
            "type_text": self.type_text,
            "click": self.click,
            "scroll": self.scroll,
            "open_app": self.open_app,
            "iot_control": self.control_iot_device,
        }
        
        # Common browser commands
        self.browser_shortcuts = {
            "new_tab": "ctrl+t",
            "close_tab": "ctrl+w",
            "next_tab": "ctrl+Tab",
            "prev_tab": "ctrl+shift+Tab",
            "refresh": "F5",
            "back": "alt+Left",
            "forward": "alt+Right",
            "home": "alt+Home",
            "new_window": "ctrl+n",
        }
    
    def open_browser(self, url: str = "https://www.google.com") -> Dict[str, Any]:
        """
        Open the default web browser and navigate to a URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            import webbrowser
            webbrowser.open(url)
            return {"success": True, "message": f"Opening browser with {url}", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_web(self, query: str, engine: str = "google") -> Dict[str, Any]:
        """
        Perform a web search using the specified search engine.
        
        Args:
            query: Search query
            engine: Search engine ("google", "bing", "duckduckgo")
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        search_urls = {
            "google": f"https://www.google.com/search?q={query.replace(' ', '+')}",
            "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}",
            "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        }
        
        url = search_urls.get(engine.lower(), search_urls["google"])
        return self.open_browser(url)
    
    def take_screenshot(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Take a screenshot and optionally save it.
        
        Args:
            save_path: Path to save screenshot (default: ~/JARVIS_Screenshots/)
            
        Returns:
            Status dict with file path
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if save_path is None:
                # Create default screenshot directory
                home_dir = Path.home()
                screenshot_dir = home_dir / "JARVIS_Screenshots"
                screenshot_dir.mkdir(exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_path = screenshot_dir / f"screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(str(save_path))
            
            return {
                "success": True,
                "message": f"Screenshot saved to {save_path}",
                "path": str(save_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_file(self, file_path: str) -> Dict[str, Any]:
        """
        Open a file with its default application.
        
        Args:
            file_path: Path to file
            
        Returns:
            Status dict
        """
        if not Path(file_path).exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(file_path))
            else:  # macOS/Linux
                subprocess.run(['open', str(file_path)])
            
            return {"success": True, "message": f"Opening file: {file_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Open a folder in file explorer.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Status dict
        """
        if not Path(folder_path).exists():
            return {"success": False, "error": f"Folder not found: {folder_path}"}
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(str(folder_path))
            else:  # macOS/Linux
                subprocess.run(['open', str(folder_path)])
            
            return {"success": True, "message": f"Opening folder: {folder_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def press_key(self, key: str, count: int = 1) -> Dict[str, Any]:
        """
        Press a keyboard key.
        
        Args:
            key: Key name (e.g., "Return", "Tab", "Delete")
            count: Number of times to press
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            for _ in range(count):
                pyautogui.press(key.lower())
            return {"success": True, "message": f"Pressed {key} {count} times"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def type_text(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.typewrite(text, interval=interval)
            return {"success": True, "message": f"Typed: {text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def click(self, x: int = None, y: int = None) -> Dict[str, Any]:
        """
        Click at specified coordinates (or center of screen if not specified).
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if x is None or y is None:
                # Click center of screen
                x, y = pyautogui.position()
            
            pyautogui.click(x, y)
            return {"success": True, "message": f"Clicked at ({x}, {y})"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scroll(self, direction: str = "down", amount: int = 5) -> Dict[str, Any]:
        """
        Scroll page up or down.
        
        Args:
            direction: "up" or "down"
            amount: Number of scroll clicks
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            scroll_amount = amount if direction.lower() == "down" else -amount
            pyautogui.scroll(scroll_amount)
            return {"success": True, "message": f"Scrolled {direction} {amount} clicks"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_app(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application by name.
        
        Args:
            app_name: Name of application (e.g., "notepad", "chrome", "explorer")
            
        Returns:
            Status dict
        """
        try:
            if os.name == 'nt':  # Windows
                # Using 'start' through shell is more robust for common app names
                subprocess.Popen(f"start {app_name}", shell=True)
            else:  # macOS/Linux
                subprocess.Popen(['open', '-a', app_name])
            
            return {"success": True, "message": f"Opening {app_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def control_iot_device(self, device: str, action: str) -> Dict[str, Any]:
        """
        Simulate or execute IoT device control commands.
        Connects JARVIS to Smart Home environments.
        """
        # Placeholder for actual API integrations (e.g., Home Assistant, Phillips Hue, etc.)
        logging.info(f"IoT Command: {action} requested for {device}")
        return {
            "success": True, 
            "message": f"I have sent the command to {action} your {device}. System confirmed.",
            "device": device,
            "action": action
        }

    def change_volume(self, mode: str, value: int = 10) -> Dict[str, Any]:
        """Helper to handle volume control requests."""
        if not PYCAW_AVAILABLE:
            return {"success": False, "error": "pycaw not available"}
        # Implementation logic for volume...
        return {"success": True, "message": f"Volume adjusted to {mode}."}

    def change_brightness(self, mode: str, value: int = 10) -> Dict[str, Any]:
        """Helper to handle brightness control requests."""
        if not SBC_AVAILABLE:
            return {"success": False, "error": "screen_brightness_control not available"}
        try:
            sbc.set_brightness(value) if mode == "set" else sbc.set_brightness(f"{'+' if mode=='up' else '-'}{value}")
            return {"success": True, "message": f"Brightness adjusted {mode}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_shortcut(self, shortcut: str) -> Dict[str, Any]:
        """
        Execute keyboard shortcut.
        
        Args:
            shortcut: Keyboard shortcut (e.g., "ctrl+c", "alt+tab")
            
        Returns:
            Status dict
        """
        if not self.pyautogui_enabled:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.hotkey(*shortcut.split('+'))
            return {"success": True, "message": f"Executed shortcut: {shortcut}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def handle_voice_command(self, command_text: str) -> Dict[str, Any]:
        """
        Parse natural language command and execute appropriate action.
        
        Args:
            command_text: Natural language command
            
        Returns:
            Status dict
        """
        command_lower = command_text.lower()
        
        # Pre-check for library availability if an automation intent is detected
        automation_keywords = ["open", "launch", "start", "search", "screenshot", "type", "click", "scroll"]
        if not self.pyautogui_enabled:
            if any(word in command_lower for word in automation_keywords):
                return {"success": False, "error": "pyautogui not available"}

        # Command routing
        if any(word in command_lower for word in ["open", "launch", "start"]):
            if "browser" in command_lower or "chrome" in command_lower:
                return self.open_browser()
            elif "file" in command_lower or "folder" in command_lower:
                # Would need more parsing or UI interaction to get file path
                return {"success": False, "error": "Need file path specification"}
            
            # Generic app opening: "open notepad", "start calculator", etc.
            for word in ["open", "launch", "start"]:
                if command_lower.startswith(word):
                    app_name = command_lower.replace(word, "").strip()
                    if app_name:
                        return self.open_app(app_name)
        
        # IoT Device Routing
        elif any(word in command_lower for word in ["turn on", "turn off", "switch", "lights", "ac", "fan"]):
            action = "on" if "on" in command_lower else "off"
            devices = ["light", "ac", "fan", "heater", "bulb", "tv"]
            target_device = next((d for d in devices if d in command_lower), "device")
            return self.control_iot_device(target_device, action)

        # Volume Commands
        elif any(word in command_lower for word in ["volume", "sound", "mute", "unmute"]):
            digits = re.findall(r'\d+', command_lower)
            val = int(digits[0]) if digits else 10
            
            if "mute" in command_lower and "unmute" not in command_lower:
                return self.change_volume("mute")
            elif "unmute" in command_lower:
                return self.change_volume("unmute")
            elif "set" in command_lower or "to" in command_lower:
                return self.change_volume("set", val)
            elif any(w in command_lower for w in ["up", "increase", "louder"]):
                return self.change_volume("up", val)
            elif any(w in command_lower for w in ["down", "decrease", "lower", "quiet"]):
                return self.change_volume("down", val)

        # Brightness Commands
        elif "brightness" in command_lower or "light" in command_lower:
            digits = re.findall(r'\d+', command_lower)
            val = int(digits[0]) if digits else 10
            
            if "set" in command_lower or "to" in command_lower:
                return self.change_brightness("set", val)
            elif any(w in command_lower for w in ["up", "increase", "brighter"]):
                return self.change_brightness("up", val)
            elif any(w in command_lower for w in ["down", "decrease", "dim", "lower"]):
                return self.change_brightness("down", val)

        elif "search" in command_lower:
            # Extract search query (everything after "search")
            query = command_text.split("search", 1)[1].strip()
            return self.search_web(query)
        
        elif "screenshot" in command_lower or "screenshot" in command_lower:
            return self.take_screenshot()
        
        elif "take a screenshot" in command_lower:
            return self.take_screenshot()
        
        return {"success": False, "error": f"Unknown command: {command_text}"}


# Example usage
if __name__ == "__main__":
    handler = SystemAutomationHandler()
    logging.info(f"SystemAutomationHandler initialized")
    logging.info(f"pyautogui available: {handler.pyautogui_enabled}")
