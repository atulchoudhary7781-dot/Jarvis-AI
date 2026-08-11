"""
Enhanced Session Management Module for JARVIS
Provides persistent login with secure session handling
"""
import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

class SessionManager:
    """
    Manages user sessions with persistent storage.
    Handles login persistence across app restarts.
    """
    
    def __init__(self, session_dir: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            session_dir: Directory to store session files. Defaults to app directory.
        """
        if session_dir is None:
            self.session_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.session_dir = session_dir
        
        self.session_file = os.path.join(self.session_dir, "jarvis_session.json")
        self.legacy_session_file = os.path.join(self.session_dir, "login_session.txt")
        self.logger = logging.getLogger(__name__)
        
        # Ensure session directory exists
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Migrate legacy session file if it exists
        self._migrate_legacy_session()
    
    def _migrate_legacy_session(self):
        """Migrate from old text-based session to new JSON format."""
        if os.path.exists(self.legacy_session_file):
            try:
                with open(self.legacy_session_file, "r") as f:
                    user_id = f.read().strip()
                if user_id:
                    # Create a new session from the legacy file
                    self.create_session(int(user_id))
                # Remove legacy file
                os.remove(self.legacy_session_file)
                self.logger.info("Migrated legacy session to new format")
            except Exception as e:
                self.logger.error(f"Error migrating legacy session: {e}")
    
    def create_session(self, user_id: int, duration_days: int = 30) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: The user ID to create session for
            duration_days: Number of days the session should remain valid
            
        Returns:
            Session token
        """
        try:
            # Generate a secure session token
            session_token = self._generate_session_token()
            
            session_data = {
                "user_id": user_id,
                "session_token": session_token,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat(),
                "last_accessed": datetime.now().isoformat()
            }
            
            # Write session to file
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.info(f"Session created for user {user_id}")
            return session_token
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            return ""
    
    def get_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the current session if it exists and is valid.
        
        Returns:
            Session data dict if valid, None otherwise
        """
        if not os.path.exists(self.session_file):
            return None
        
        try:
            with open(self.session_file, "r") as f:
                session_data = json.load(f)
            
            # Validate session
            if not self._is_session_valid(session_data):
                self.logger.info("Session expired, removing")
                self.clear_session()
                return None
            
            # Update last accessed time
            session_data["last_accessed"] = datetime.now().isoformat()
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Error reading session: {e}")
            return None
    
    def get_user_id(self) -> Optional[int]:
        """
        Get the user ID from the current session.
        
        Returns:
            User ID if session exists and is valid, None otherwise
        """
        session = self.get_session()
        if session:
            return session.get("user_id")
        return None
    
    def is_logged_in(self) -> bool:
        """
        Check if there's a valid session.
        
        Returns:
            True if user is logged in, False otherwise
        """
        return self.get_session() is not None
    
    def clear_session(self) -> bool:
        """
        Clear the current session (logout).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            # Also remove legacy file if it exists
            if os.path.exists(self.legacy_session_file):
                os.remove(self.legacy_session_file)
            self.logger.info("Session cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")
            return False
    
    def validate_session(self, user_id: int) -> bool:
        """
        Validate if the saved session belongs to a specific user.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            True if session is valid for the user, False otherwise
        """
        session = self.get_session()
        if session and session.get("user_id") == user_id:
            return True
        return False
    
    def _is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """
        Check if a session is still valid based on expiration time.
        
        Args:
            session_data: Session data to validate
            
        Returns:
            True if session is valid, False if expired
        """
        try:
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            if datetime.now() > expires_at:
                self.logger.info("Session has expired")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return False
    
    def _generate_session_token(self) -> str:
        """
        Generate a secure session token.
        
        Returns:
            A secure random token
        """
        token = secrets.token_urlsafe(32)
        return token
    
    def get_session_info(self) -> Optional[Dict[str, str]]:
        """
        Get readable session information.
        
        Returns:
            Dictionary with session info, or None if no session
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            return {
                "user_id": str(session.get("user_id", "")),
                "created_at": session.get("created_at", ""),
                "expires_at": session.get("expires_at", ""),
                "last_accessed": session.get("last_accessed", "")
            }
        except Exception as e:
            self.logger.error(f"Error getting session info: {e}")
            return None


# Legacy compatibility functions
def save_session(user_id: int) -> None:
    """
    Legacy function for backward compatibility.
    Creates a new session for the user.
    """
    manager = SessionManager()
    manager.create_session(user_id)


def get_session() -> Optional[str]:
    """
    Legacy function for backward compatibility.
    Returns the user ID from the current session if valid as a string.
    """
    manager = SessionManager()
    user_id = manager.get_user_id()
    if user_id is not None:
        return str(user_id)
    return None


def clear_session() -> None:
    """
    Legacy function for backward compatibility.
    Clears the current session.
    """
    manager = SessionManager()
    manager.clear_session()
