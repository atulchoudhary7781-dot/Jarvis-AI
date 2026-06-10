# jarvis_scheduling.py - Smart Scheduling & Reminders
# Manages time-based tasks, reminders, and notifications

import threading
import time
from typing import Optional, Callable, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import calendar
import logging

try:
    import pyttsx3
    TTSAVAILABLE = True
except ImportError:
    TTSAVAILABLE = False

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class ReminderTask:
    """Represents a single reminder task."""
    
    def __init__(
        self,
        task_id: str,
        title: str,
        scheduled_time: datetime,
        message: str = "",
        notification_type: str = "popup",  # popup, sound, voice
        repeat: Optional[str] = None  # daily, weekly, monthly
    ):
        self.task_id = task_id
        self.title = title
        self.scheduled_time = scheduled_time
        self.message = message
        self.notification_type = notification_type
        self.repeat = repeat
        self.completed = False
        self.timer_thread = None
    
    def __repr__(self):
        return f"ReminderTask(id={self.task_id}, title={self.title}, time={self.scheduled_time})"


class SchedulingHandler:
    """
    Manages reminders and scheduled tasks using threading.
    Supports one-time and recurring reminders with various notification types.
    """
    
    def __init__(self):
        self.reminders: Dict[str, ReminderTask] = {}
        self.reminder_lock = threading.Lock()
        self.tts_engine = None
        self.enable_voice = False
        
        # Initialize text-to-speech if available
        if TTSAVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.enable_voice = True
            except Exception as e:
                logging.warning(f"Could not initialize TTS: {e}")
                self.enable_voice = False
        
        # Callback for UI notifications
        self.notification_callback = None
    
    def set_notification_callback(self, callback: Callable):
        """Set callback function for UI notifications."""
        self.notification_callback = callback
    
    def _trigger_notification(self, reminder: ReminderTask):
        """Trigger notification based on type."""
        if reminder.notification_type == "voice" and self.enable_voice:
            self._voice_notification(reminder)
        elif reminder.notification_type == "sound":
            self._sound_notification(reminder)
        else:
            self._popup_notification(reminder)
    
    def _popup_notification(self, reminder: ReminderTask):
        """Create a popup notification (UI callback)."""
        message = f"🔔 {reminder.title}\n\n{reminder.message}"
        
        if self.notification_callback:
            self.notification_callback({
                "type": "reminder",
                "title": reminder.title,
                "message": reminder.message,
                "task_id": reminder.task_id
            })
        else:
            logging.info(f"REMINDER: {reminder.title} - {reminder.message}")
    
    def _sound_notification(self, reminder: ReminderTask):
        """Play sound notification."""
        try:
            if WINSOUND_AVAILABLE:
                # Play system beep
                for _ in range(3):
                    winsound.Beep(1000, 500)  # frequency, duration
                    time.sleep(0.5)
            self._popup_notification(reminder)
        except Exception as e:
            logging.error(f"Could not play sound: {e}")
            self._popup_notification(reminder)
    
    def _voice_notification(self, reminder: ReminderTask):
        """Play voice notification."""
        try:
            if self.tts_engine:
                text = f"Reminder: {reminder.title}. {reminder.message}"
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            self._popup_notification(reminder)
        except Exception as e:
            logging.error(f"Could not play voice: {e}")
            self._sound_notification(reminder)
    
    def _calculate_next_time(self, repeat: str, current_time: datetime) -> datetime:
        """Calculate next occurrence time for recurring reminders."""
        if repeat == "daily":
            return current_time + timedelta(days=1)
        elif repeat == "weekly":
            return current_time + timedelta(weeks=1)
        elif repeat == "monthly":
            # Robust month-based recurrence
            month = current_time.month + 1
            year = current_time.year
            if month > 12:
                month = 1
                year += 1
            
            # Get the number of days in the target month
            last_day_of_month = calendar.monthrange(year, month)[1]
            day = min(current_time.day, last_day_of_month)
            return current_time.replace(year=year, month=month, day=day)
        else:
            return None
    
    def _reminder_worker(self, reminder: ReminderTask):
        """Thread worker that waits for reminder time and triggers it."""
        while not reminder.completed:
            now = datetime.now()
            wait_seconds = (reminder.scheduled_time - now).total_seconds()
            
            if wait_seconds <= 0:
                # Time to trigger
                self._trigger_notification(reminder)
                
                # Schedule next occurrence if repeating
                if reminder.repeat:
                    next_time = self._calculate_next_time(reminder.repeat, datetime.now())
                    if next_time:
                        reminder.scheduled_time = next_time
                        # Continue waiting for next occurrence
                        continue
                else:
                    reminder.completed = True
                    break
            else:
                # Sleep for min(wait_seconds, 60) to avoid busy waiting
                time.sleep(min(wait_seconds, 60))
    
    def add_reminder(
        self,
        title: str,
        delay_minutes: int = 0,
        specific_time: Optional[datetime] = None,
        message: str = "",
        notification_type: str = "popup",
        repeat: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new reminder.
        
        Args:
            title: Reminder title
            delay_minutes: Minutes from now (if specific_time not provided)
            specific_time: Explicit datetime for reminder
            message: Reminder message/details
            notification_type: "popup", "sound", or "voice"
            repeat: None, "daily", "weekly", "monthly"
            task_id: Custom ID (default: auto-generated)
            
        Returns:
            Status dict with task_id
        """
        if specific_time is None:
            scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        else:
            scheduled_time = specific_time
        
        if task_id is None:
            task_id = f"reminder_{int(time.time())}"
        
        with self.reminder_lock:
            reminder = ReminderTask(
                task_id=task_id,
                title=title,
                scheduled_time=scheduled_time,
                message=message,
                notification_type=notification_type,
                repeat=repeat
            )
            
            self.reminders[task_id] = reminder
            
            # Start worker thread
            thread = threading.Thread(
                target=self._reminder_worker,
                args=(reminder,),
                daemon=True,
                name=f"ReminderWorker-{task_id}"
            )
            thread.start()
            reminder.timer_thread = thread
        
        return {
            "success": True,
            "task_id": task_id,
            "title": title,
            "scheduled_time": scheduled_time.isoformat(),
            "notification_type": notification_type,
            "repeat": repeat
        }
    
    def cancel_reminder(self, task_id: str) -> Dict[str, Any]:
        """Cancel a scheduled reminder."""
        with self.reminder_lock:
            if task_id in self.reminders:
                self.reminders[task_id].completed = True
                del self.reminders[task_id]
                return {"success": True, "message": f"Reminder {task_id} cancelled"}
        
        return {"success": False, "error": f"Reminder {task_id} not found"}
    
    def list_reminders(self) -> List[Dict[str, Any]]:
        """Get list of all active reminders."""
        with self.reminder_lock:
            return [
                {
                    "task_id": r.task_id,
                    "title": r.title,
                    "scheduled_time": r.scheduled_time.isoformat(),
                    "message": r.message,
                    "notification_type": r.notification_type,
                    "repeat": r.repeat,
                    "time_until": (r.scheduled_time - datetime.now()).total_seconds()
                }
                for r in self.reminders.values()
            ]
    
    def get_reminder(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific reminder."""
        with self.reminder_lock:
            if task_id in self.reminders:
                r = self.reminders[task_id]
                return {
                    "task_id": r.task_id,
                    "title": r.title,
                    "scheduled_time": r.scheduled_time.isoformat(),
                    "message": r.message,
                    "notification_type": r.notification_type,
                    "repeat": r.repeat,
                    "completed": r.completed
                }
        return None
    
    def snooze_reminder(self, task_id: str, minutes: int = 10) -> Dict[str, Any]:
        """Snooze a reminder for specified minutes."""
        with self.reminder_lock:
            if task_id in self.reminders:
                reminder = self.reminders[task_id]
                reminder.scheduled_time = datetime.now() + timedelta(minutes=minutes)
                return {
                    "success": True,
                    "task_id": task_id,
                    "new_time": reminder.scheduled_time.isoformat()
                }
        
        return {"success": False, "error": f"Reminder {task_id} not found"}
    
    def schedule_meeting(
        self,
        title: str,
        meeting_time: datetime,
        duration_minutes: int = 30,
        reminders_before: List[int] = None  # minutes before meeting
    ) -> Dict[str, Any]:
        """
        Schedule a meeting with automatic reminders before it.
        
        Args:
            title: Meeting title
            meeting_time: When the meeting is
            duration_minutes: Meeting duration
            reminders_before: List of minutes to remind before (e.g., [15, 5])
            
        Returns:
            Status dict
        """
        if reminders_before is None:
            reminders_before = [15, 5]  # Default: 15 and 5 minutes before
        
        task_ids = []
        results = []
        
        for minutes_before in reminders_before:
            reminder_time = meeting_time - timedelta(minutes=minutes_before)
            if reminder_time > datetime.now():
                result = self.add_reminder(
                    title=f"Meeting Reminder: {title}",
                    specific_time=reminder_time,
                    message=f"Your meeting '{title}' starts in {minutes_before} minutes",
                    notification_type="voice" if self.enable_voice else "sound"
                )
                task_ids.append(result.get("task_id"))
                results.append(result)
        
        return {
            "success": len(results) > 0,
            "title": title,
            "meeting_time": meeting_time.isoformat(),
            "reminders_set": len(results),
            "reminder_task_ids": task_ids
        }


# Example usage
if __name__ == "__main__":
    handler = SchedulingHandler()
    
    # Set a test reminder for 5 seconds from now
    result = handler.add_reminder(
        title="Test Reminder",
        delay_minutes=0.083,  # ~5 seconds
        message="This is a test reminder"
    )
    logging.info(f"Added reminder: {result}")
    
    # List all reminders
    logging.info(f"Active reminders: {handler.list_reminders()}")
    
    # Keep the script running to see the reminder trigger
    logging.info("Waiting for reminder...")
    time.sleep(10)
