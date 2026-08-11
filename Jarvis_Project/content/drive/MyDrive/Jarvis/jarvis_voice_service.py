# jarvis_voice_service.py - Background Service for Always-Listening JARVIS
# Run this as a background process to keep JARVIS listening even when UI is closed

import os
import sys
import logging
import json
from pathlib import Path
from jarvis_voice_activation import VoiceActivationService
from jarvis_lights import LightController, LightEffect, LightColor
from jarvis_core import speak

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "jarvis_voice_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JarvisBackgroundService:
    """Background service that runs JARVIS voice activation 24/7"""
    
    def __init__(self, config_file: str = "jarvis_config.json"):
        """Initialize background service"""
        self.config_file = config_file
        self.config = self.load_config()
        self.voice_service = None
        self.light_controller = None
        self.is_running = False
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        default_config = {
            "light_type": "generic",
            "wake_words": ["hey jarvis", "jarvis activate", "activate jarvis"],
            "mic_sensitivity": 4000,
            "speak_activation": True,
            "light_on_activation": True,
            "hue_ip": "192.168.1.100",
            "serial_port": "COM3"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def setup_lights(self):
        """Initialize light controller"""
        try:
            self.light_controller = LightController(
                light_type=self.config.get("light_type", "generic"),
                config={
                    "hue_ip": self.config.get("hue_ip"),
                    "serial_port": self.config.get("serial_port")
                }
            )
            logger.info("Light controller initialized")
        except Exception as e:
            logger.error(f"Failed to initialize light controller: {e}")
            self.light_controller = None
    
    def on_jarvis_activated(self):
        """Callback when JARVIS is activated"""
        logger.info("🎯 JARVIS ACTIVATED in background service")
        
        # Speak activation message
        if self.config.get("speak_activation", True):
            try:
                speak("I am online and ready.")
            except Exception as e:
                logger.error(f"Speech error: {e}")
        
        # Activate light effect
        if self.light_controller and self.config.get("light_on_activation", True):
            try:
                self.light_controller.play_effect(
                    LightEffect.ACTIVATION,
                    LightColor.BLUE,
                    duration=3
                )
            except Exception as e:
                logger.error(f"Light activation error: {e}")
        
        # Save activation log
        self.log_activation()
    
    def log_activation(self):
        """Log activation event"""
        import datetime
        activation_log = log_dir / "activations.log"
        with open(activation_log, "a") as f:
            f.write(f"{datetime.datetime.now()}: JARVIS activated\n")
    
    def start_service(self):
        """Start the background voice activation service"""
        if self.is_running:
            logger.warning("Service is already running")
            return
        
        logger.info("🚀 Starting JARVIS Background Service...")
        
        # Setup lights
        self.setup_lights()
        
        # Create voice activation service
        self.voice_service = VoiceActivationService(
            activation_callback=self.on_jarvis_activated,
            light_controller=self.light_controller,
            wake_words=self.config.get("wake_words", ["hey jarvis"])
        )
        
        # Start listening
        self.voice_service.start_listening()
        self.is_running = True
        
        logger.info("✅ JARVIS Background Service is now running")
        logger.info("🎤 Listening for 'Hey Jarvis'...")
        
        # Keep service alive
        try:
            while self.is_running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping service...")
            self.stop_service()
    
    def stop_service(self):
        """Stop the background service"""
        logger.info("Stopping JARVIS Background Service...")
        
        if self.voice_service:
            self.voice_service.stop_listening()
        
        if self.light_controller:
            self.light_controller.turn_off()
        
        self.is_running = False
        logger.info("Service stopped")


def create_scheduled_task():
    """Create Windows scheduled task to run at startup (Windows only)"""
    import platform
    
    if platform.system() != "Windows":
        logger.warning("Scheduled task creation is Windows-only")
        return False
    
    try:
        import subprocess
        
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable
        
        # Create task
        cmd = f'''schtasks /create /tn "JARVIS Background Service" /tr "{python_exe} {script_path}" /sc onstart /rl highest /f'''
        
        subprocess.run(cmd, shell=True, check=True)
        logger.info("✅ Windows scheduled task created successfully")
        logger.info("JARVIS will now start automatically on system startup")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create scheduled task: {e}")
        return False


def remove_scheduled_task():
    """Remove Windows scheduled task"""
    try:
        import subprocess
        cmd = 'schtasks /delete /tn "JARVIS Background Service" /f'
        subprocess.run(cmd, shell=True, check=True)
        logger.info("Scheduled task removed")
        return True
    except Exception as e:
        logger.error(f"Failed to remove scheduled task: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="JARVIS Background Voice Service")
    parser.add_argument("--start", action="store_true", help="Start the service")
    parser.add_argument("--stop", action="store_true", help="Stop the service")
    parser.add_argument("--task", action="store_true", help="Create Windows scheduled task")
    parser.add_argument("--remove-task", action="store_true", help="Remove scheduled task")
    parser.add_argument("--config", type=str, help="Config file path")
    
    args = parser.parse_args()
    
    if args.config:
        service = JarvisBackgroundService(config_file=args.config)
    else:
        service = JarvisBackgroundService()
    
    if args.task:
        create_scheduled_task()
    elif args.remove_task:
        remove_scheduled_task()
    elif args.stop:
        service.stop_service()
    else:
        # Default: start service
        service.start_service()
