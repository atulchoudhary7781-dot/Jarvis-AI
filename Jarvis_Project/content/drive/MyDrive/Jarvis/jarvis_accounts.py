"""
JARVIS Account Management Module
Provides user authentication, registration, and profile management
"""
import logging

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    ctk = None
    CTK_AVAILABLE = False

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None

import sqlite3
import hashlib
import os
import re
import smtplib
import random
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import urllib.request
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False

# Try importing bcrypt for secure password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    bcrypt = None
    BCRYPT_AVAILABLE = False


class AccountDatabase:
    """Handles all database operations for user accounts"""
    
    def __init__(self, db_path: str = "jarvis_accounts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the accounts database with necessary tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone_number TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                subscription_tier TEXT DEFAULT 'free'
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                pref_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                theme TEXT DEFAULT 'dark',
                voice_enabled INTEGER DEFAULT 1,
                api_key TEXT,
                voice_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Chat Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Chat Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                sender TEXT,
                text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            )
        ''')
        
        # Password Resets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Add Message Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                feedback_type TEXT NOT NULL, -- e.g., 'like', 'dislike', 'correction'
                feedback_text TEXT,          -- Optional: for corrections or comments
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES chat_messages(message_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        conn.commit()
        conn.close()
        self._migrate_db()

    def _migrate_db(self):
        """Ensure new columns exist in old databases"""
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("ALTER TABLE users ADD COLUMN phone_number TEXT UNIQUE")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Column likely exists
            
            try:
                conn.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free'")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN voice_id TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass

            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to migrate database: {e}", exc_info=True)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt (secure) or SHA-256 (fallback)"""
        if BCRYPT_AVAILABLE:
            # gensalt() generates a random salt each time
            return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a stored hash"""
        if BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            except ValueError:
                # Handle legacy SHA-256 hashes if migration occurs
                pass
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash

    def check_user_exists(self, username: str, email: str) -> Tuple[bool, str]:
        """Check if username or email already exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return True, "Username already exists"
            
            cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return True, "Email already registered"
            return False, ""
        except Exception as e:
            return True, f"Error: {str(e)}"
        finally:
            conn.close()

    def check_phone_exists(self, phone: str) -> Tuple[bool, str]:
        """Check if phone number already exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE phone_number = ?', (phone,))
            result = cursor.fetchone()
            conn.close()
            return (True, "Phone number already registered") if result else (False, "")
        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_user(self, username: str, email: str, password: str, full_name: str = "", phone_number: str = None) -> Tuple[bool, str]:
        """
        Create a new user account
        Returns: (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, phone_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, phone_number))
            
            user_id = cursor.lastrowid
            
            # Create default preferences
            cursor.execute('''
                INSERT INTO user_preferences (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True, "Account created successfully!"
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.username" in str(e):
                return False, "Username already exists"
            elif "UNIQUE constraint failed: users.email" in str(e):
                return False, "Email already registered"
            elif "UNIQUE constraint failed: users.phone_number" in str(e):
                return False, "Phone number already registered"
            return False, "Account creation failed"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[int], str]:
        """
        Authenticate a user
        Returns: (success: bool, user_id: Optional[int], message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, password_hash, is_active FROM users
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            
            if result is None:
                conn.close()
                return False, None, "Invalid username or password"
            
            user_id, stored_hash, is_active = result
            
            if not self.verify_password(password, stored_hash):
                conn.close()
                return False, None, "Invalid username or password"
            
            if not is_active:
                conn.close()
                return False, None, "Account is disabled"
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            # Create session record
            cursor.execute('''
                INSERT INTO user_sessions (user_id)
                VALUES (?)
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True, user_id, "Login successful"
        except Exception as e:
            return False, None, f"Error: {str(e)}"
    
    def get_user_id_by_email(self, email: str) -> Optional[int]:
        """Get user ID associated with an email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception:
            return None

    def get_user_id_by_phone(self, phone: str) -> Optional[int]:
        """Get user ID associated with a phone number"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE phone_number = ?', (phone,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception:
            return None

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, email, full_name, created_at, last_login, subscription_tier
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'username': result[0],
                    'email': result[1],
                    'full_name': result[2],
                    'created_at': result[3],
                    'last_login': result[4],
                    'subscription_tier': result[5]
                }
            return None
        except Exception:
            return None
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict]:
        """Get all preferences for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT theme, voice_enabled, api_key, voice_id FROM user_preferences WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return {
                    'theme': result[0],
                    'voice_enabled': result[1],
                    'api_key': result[2],
                    'voice_id': result[3]
                }
            return None
        except Exception:
            return None

    def update_user_preference(self, user_id: int, key: str, value: Any) -> Tuple[bool, str]:
        """Update a specific user preference."""
        if key not in ('theme', 'voice_enabled', 'api_key', 'voice_id'):
            return False, "Invalid preference key"
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"UPDATE user_preferences SET {key} = ? WHERE user_id = ?", (value, user_id))
            conn.commit()
            conn.close()
            return True, "Preference updated"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def update_user_info(self, user_id: int, full_name: str = None, email: str = None) -> Tuple[bool, str]:
        """Update user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            
            if not updates:
                return True, "No changes made"
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True, "Profile updated successfully"
        except sqlite3.IntegrityError:
            return False, "Email already in use"
        except Exception as e:
            return False, f"Error: {str(e)}"
            
    def update_user_subscription(self, user_id: int, tier: str) -> Tuple[bool, str]:
        """Update user subscription tier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET subscription_tier = ? WHERE user_id = ?", (tier, user_id))
            conn.commit()
            conn.close()
            return True, "Subscription updated successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT password_hash FROM users
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row is None or not self.verify_password(old_password, row[0]):
                conn.close()
                return False, "Current password is incorrect"
            
            new_hash = self.hash_password(new_password)
            cursor.execute('''
                UPDATE users SET password_hash = ?
                WHERE user_id = ?
            ''', (new_hash, user_id))
            
            conn.commit()
            conn.close()
            return True, "Password changed successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_chat_session(self, user_id: int, title: str) -> int:
        """Create a new chat session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)', (user_id, title))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id

    def add_chat_message(self, session_id: int, sender: str, text: str):
        """Add a message to a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chat_messages (session_id, sender, text) VALUES (?, ?, ?)', (session_id, sender, text))
        cursor.execute('UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?', (session_id,))
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return msg_id

    def get_user_chat_sessions(self, user_id: int) -> list:
        """Get all sessions for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT session_id, title FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC', (user_id,))
        sessions = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
        conn.close()
        return sessions

    def get_chat_history(self, session_id: int) -> list:
        """Get messages for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT message_id, sender, text FROM chat_messages WHERE session_id = ? ORDER BY message_id ASC', (session_id,))
        messages = [{'id': row[0], 'sender': row[1], 'text': row[2]} for row in cursor.fetchall()]
        conn.close()
        return messages

    def update_chat_session_title(self, session_id: int, title: str):
        """Update the title of a chat session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?', (title, session_id))
        conn.commit()
        conn.close()

    def delete_chat_message(self, message_id: int):
        """Delete a specific message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chat_messages WHERE message_id = ?', (message_id,))
        conn.commit()
        conn.close()

    def delete_chat_session(self, session_id: int):
        """Delete a chat session and all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Delete all messages in the session first
        cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
        # Delete the session
        cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()

    def create_password_reset_token(self, email: str) -> Tuple[bool, Optional[str], str]:
        """Generate a secure password reset token for the given email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False, None, "Email not found"
            
            user_id = result[0]
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            
            # Remove old tokens for this user
            cursor.execute('DELETE FROM password_resets WHERE user_id = ?', (user_id,))
            
            cursor.execute('INSERT INTO password_resets (token, user_id, expires_at) VALUES (?, ?, ?)',
                           (token, user_id, expires_at))
            
            conn.commit()
            conn.close()
            return True, token, "Reset token generated"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def reset_password_with_token(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset password using a valid token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id, expires_at FROM password_resets WHERE token = ?', (token,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "Invalid or expired token"
            
            user_id, expires_at_str = result
            # Parse timestamp (sqlite stores as string usually)
            if isinstance(expires_at_str, str):
                expires_at = datetime.fromisoformat(expires_at_str)
            else:
                expires_at = expires_at_str
                
            if datetime.now() > expires_at:
                cursor.execute('DELETE FROM password_resets WHERE token = ?', (token,))
                conn.commit()
                conn.close()
                return False, "Token has expired"
            
            new_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE user_id = ?', (new_hash, user_id))
            cursor.execute('DELETE FROM password_resets WHERE token = ?', (token,))
            
            conn.commit()
            conn.close()
            return True, "Password reset successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def record_message_feedback(self, message_id: int, user_id: int, feedback_type: str, feedback_text: Optional[str] = None) -> Tuple[bool, str]:
        """
        Records user feedback for a specific message.
        Returns: (success: bool, message: str)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_feedback (message_id, user_id, feedback_type, feedback_text)
                VALUES (?, ?, ?, ?)
            ''', (message_id, user_id, feedback_type, feedback_text))
            conn.commit()
            conn.close()
            return True, "Feedback recorded successfully."
        except Exception as e:
            return False, f"Error recording feedback: {str(e)}"


class AccountPage:
    """GUI for account management using CustomTkinter"""
    
    def __init__(self, on_login_success=None, on_logout=None, master=None, start_mode="login", current_user_id=None, db_path="jarvis_accounts.db"):
        """
        Initialize the account page
        Args:
            on_login_success: Callback function(user_id) called when login succeeds
            on_logout: Callback function() called when logout occurs
            master: Parent window if running as a submodule
            start_mode: "login", "register", or "profile"
            current_user_id: ID of currently logged in user (for profile mode)
            db_path: Path to the account database file
        """
        if not CTK_AVAILABLE:
            raise RuntimeError("customtkinter is required for AccountPage")
        
        self.db = AccountDatabase(db_path=db_path)
        self.on_login_success = on_login_success
        self.on_logout = on_logout
        self.current_user_id = current_user_id
        self.master = master
        
        self.generated_otp = None
        self.otp_generation_time = None
        self.otp_attempts = 0
        self.pending_user_data = {}
        
        # Create main window
        if self.master:
            self.root = ctk.CTkToplevel(self.master)
        else:
            self.root = ctk.CTk()
        self.root.title("JARVIS - Account")
        
        # Open in full screen/maximized
        try:
            self.root.after(0, lambda: self.root.state("zoomed"))
        except Exception:
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Background setup (Star Animation)
        self.root.configure(fg_color="#000000")
        self.stars = []
        self.shooting_star = None
        if tk:
            self.star_canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
            self.star_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.init_stars()
            self.animate_stars()
            
        self.content_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
        
        # Show login page initially
        if start_mode == "register":
            self.show_register_page()
        elif start_mode == "profile" and self.current_user_id:
            self.show_profile_page()
        else:
            self.show_login_page()
    
    def init_stars(self):
        if not tk: return
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        for _ in range(100):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.random() * 2
            speed = random.random() * 0.5 + 0.1
            star = self.star_canvas.create_oval(x, y, x+size, y+size, fill="white", outline="")
            self.stars.append({"id": star, "speed": speed})
        self.shooting_star = None

    def animate_stars(self):
        if not tk: return
        width = self.root.winfo_width()
        if width < 100: width = self.root.winfo_screenwidth()
        height = self.root.winfo_height()
        if height < 100: height = self.root.winfo_screenheight()
        
        for star in self.stars:
            self.star_canvas.move(star["id"], 0, star["speed"])
            coords = self.star_canvas.coords(star["id"])
            if coords[1] > height:
                new_x = random.randint(0, width)
                self.star_canvas.coords(star["id"], new_x, 0, new_x+2, 2)
        
        if self.shooting_star:
            self.star_canvas.move(self.shooting_star["id"], self.shooting_star["vx"], self.shooting_star["vy"])
            coords = self.star_canvas.coords(self.shooting_star["id"])
            if not coords or (coords[0] > width and coords[2] > width) or (coords[1] > height and coords[3] > height):
                self.star_canvas.delete(self.shooting_star["id"])
                self.shooting_star = None
        elif random.random() < 0.01:
            if random.choice([True, False]):
                sx = random.randint(0, width)
                sy = -50
            else:
                sx = -50
                sy = random.randint(0, height // 2)
            length = random.randint(40, 100)
            speed = random.randint(20, 40)
            star_id = self.star_canvas.create_line(sx, sy, sx + length, sy + length, fill="#aaddff", width=2)
            self.shooting_star = {"id": star_id, "vx": speed, "vy": speed}
                
        self.root.after(50, self.animate_stars)

    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def get_provider_logo(self, provider: str) -> str:
        """
        Get logo emoji/symbol for a provider.
        Returns emoji string that works universally.
        """
        logos = {
            "Google": "🔍",      # magnifying glass
            "Apple": "🍎",        # apple
            "Microsoft": "🟦",    # blue square / window
            "Phone": "📱",       # mobile phone
        }
        return logos.get(provider, "●")
    
    def show_login_page(self):
        """Modern Login UI (ChatGPT style)"""
        self.clear_window()

        # Center card
        card = ctk.CTkFrame(
            self.content_frame,
            width=360,
            height=540,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        card.pack(pady=50, padx=20, anchor="center")

        # Title
        title = ctk.CTkLabel(
            card,
            text="Log in or sign up",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=(30, 8))

        subtitle = ctk.CTkLabel(
            card,
            text="You'll get smarter responses and can\nupload files, images, and more.",
            font=ctk.CTkFont(size=12),
            text_color="#CCCCCC",
            justify="center"
        )
        subtitle.pack(pady=(0, 20))

        # Social Buttons with logos
        def social_btn_with_logo(text, provider, logo):
            """Create a social button with logo on the right side"""
            # Provider-specific colors
            colors = {
                "Google": ("#1a1a1a", "#4285F4"),    # Google blue
                "Apple": ("#1a1a1a", "#FFFFFF"),     # White
                "Microsoft": ("#1a1a1a", "#00A4EF"), # Microsoft blue
                "Phone": ("#1a1a1a", "#4a5fe8"),     # Default blue
            }
            bg_color, logo_color = colors.get(provider, ("#1a1a1a", "#ffffff"))
            
            btn_frame = ctk.CTkFrame(card, fg_color=bg_color, corner_radius=20, border_width=1, border_color="#444444", height=40)
            btn_frame.pack(pady=6, fill="x", padx=30)
            btn_frame.pack_propagate(False)
            
            # Left side: text
            text_label = ctk.CTkLabel(
                btn_frame,
                text=text,
                font=ctk.CTkFont(size=13),
                text_color="#ffffff"
            )
            text_label.pack(side="left", padx=20, pady=10)
            
            # Right side: logo with provider color
            logo_frame = ctk.CTkFrame(btn_frame, fg_color="transparent", width=30, height=30)
            logo_frame.pack(side="right", padx=20, pady=10)
            logo_frame.pack_propagate(False)
            
            logo_label = ctk.CTkLabel(
                logo_frame,
                text=logo,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=logo_color
            )
            logo_label.pack(expand=True)
            
            # Bind click to the entire frame
            def on_click(event=None):
                self.handle_social_login(provider)
            btn_frame.bind("<Button-1>", on_click)
            text_label.bind("<Button-1>", on_click)
            logo_label.bind("<Button-1>", on_click)
            logo_frame.bind("<Button-1>", on_click)
            
            return btn_frame

        social_btn_with_logo("Continue with Google", "Google", "G")
        social_btn_with_logo("Continue with Apple", "Apple", "A")
        social_btn_with_logo("Continue with Microsoft", "Microsoft", "M")
        social_btn_with_logo("Continue with Phone", "Phone", "☎")

        # OR Divider
        divider_frame = ctk.CTkFrame(card, fg_color="transparent")
        divider_frame.pack(pady=15)

        ctk.CTkLabel(divider_frame, text="──────── OR ────────", text_color="#AAAAAA").pack()

        # Email Field
        self.login_username = ctk.CTkEntry(
            card,
            placeholder_text="Email address or Username",
            width=300,
            height=40,
            corner_radius=20
        )
        self.login_username.pack(pady=(10, 12))

        # Password Field
        self.login_password = ctk.CTkEntry(
            card,
            placeholder_text="Password",
            show="*",
            width=300,
            height=40,
            corner_radius=20
        )
        self.login_password.pack(pady=(0, 5))

        # Forgot Password Link
        forgot_btn = ctk.CTkButton(
            card,
            text="Forgot password?",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="#CCCCCC",
            hover_color="#333333",
            height=20,
            command=self.show_forgot_password_page
        )
        forgot_btn.pack(pady=(0, 15))

        # Continue Button
        login_btn = ctk.CTkButton(
            card,
            text="Continue",
            width=300,
            height=42,
            corner_radius=22,
            fg_color="#4a5fe8",
            text_color="#ffffff",
            hover_color="#3a4fd8",
            command=self.handle_login
        )
        login_btn.pack(pady=(5, 10))

        # Message label
        self.login_message = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.login_message.pack(pady=5)

        # Create account link
        signup_btn = ctk.CTkButton(
            card,
            text="Create new account",
            fg_color="transparent",
            hover_color="#333333",
            text_color="#4da6ff",
            command=self.show_register_page
        )
        signup_btn.pack(pady=(10, 15))
        
        # Bind Enter key
        self.login_password.bind("<Return>", lambda e: self.handle_login())
    
    def show_register_page(self):
        """Display the registration page"""
        self.clear_window()
        
        # Main frame
        main_frame = ctk.CTkFrame(
            self.content_frame,
            width=400,
            height=600,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        main_frame.pack(pady=50, padx=20, anchor="center")
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Create Account",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            main_frame,
            text="Join JARVIS AI today",
            font=ctk.CTkFont(size=14)
        )
        subtitle.pack(pady=(0, 30))
        
        # Registration form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Full Name
        ctk.CTkLabel(form_frame, text="Full Name", font=ctk.CTkFont(size=12)).pack(pady=(20, 5))
        self.reg_fullname = ctk.CTkEntry(form_frame, placeholder_text="Enter your full name", width=300)
        self.reg_fullname.pack(pady=(0, 10))
        
        # Username
        ctk.CTkLabel(form_frame, text="Username", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.reg_username = ctk.CTkEntry(form_frame, placeholder_text="Choose a username", width=300)
        self.reg_username.pack(pady=(0, 10))
        
        # Email
        ctk.CTkLabel(form_frame, text="Email", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.reg_email = ctk.CTkEntry(form_frame, placeholder_text="Enter your email", width=300)
        self.reg_email.pack(pady=(0, 10))
        
        # Password
        ctk.CTkLabel(form_frame, text="Password", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.reg_password = ctk.CTkEntry(form_frame, placeholder_text="Choose a password", show="*", width=300)
        self.reg_password.pack(pady=(0, 10))
        
        # Confirm Password
        ctk.CTkLabel(form_frame, text="Confirm Password", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.reg_confirm = ctk.CTkEntry(form_frame, placeholder_text="Re-enter password", show="*", width=300)
        self.reg_confirm.pack(pady=(0, 20))
        
        # Terms of Service Checkbox
        self.terms_check = ctk.CTkCheckBox(
            form_frame,
            text="I agree to the Terms of Service and Privacy Policy",
            font=ctk.CTkFont(size=12),
            command=self.toggle_register_button
        )
        self.terms_check.pack(pady=10)
        
        # Register button
        self.register_btn = ctk.CTkButton(
            form_frame,
            text="Create Account",
            command=self.handle_register,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4a5fe8",
            hover_color="#3a4fd8",
            state="disabled"  # Initially disabled
        )
        self.register_btn.pack(pady=10)
        
        # Message label
        self.reg_message = ctk.CTkLabel(form_frame, text="", text_color="red")
        self.reg_message.pack(pady=5)
        
        # Back to login
        back_btn = ctk.CTkButton(
            form_frame,
            text="← Back to Sign In",
            command=self.show_login_page,
            width=300,
            fg_color="transparent",
            border_width=0
        )
        back_btn.pack(pady=10)

    def toggle_register_button(self):
        """Enable/disable register button based on terms checkbox"""
        if self.terms_check.get() == 1:
            self.register_btn.configure(state="normal")
        else:
            self.register_btn.configure(state="disabled")
    
    def show_create_password_page(self, email_value="user@email.com"):
        """JARVIS Create Password Page"""

        self.pending_email = email_value
        self.is_phone_flow = "@" not in email_value
        self.clear_window()

        # Card Container
        card = ctk.CTkFrame(
            self.content_frame,
            width=380,
            height=560,
            fg_color="#000000",
            corner_radius=20,
            border_width=1,
            border_color="#333333"
        )
        card.pack(pady=50, padx=20, anchor="center")

        # Title
        title = ctk.CTkLabel(
            card,
            text="Create a password",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            card,
            text="You’ll use this password to log in to\nJARVIS and other JARVIS products",
            font=ctk.CTkFont(size=13),
            text_color="#555555",
            justify="center"
        )
        subtitle.pack(pady=(0, 25))

        # Email Display Box
        email_frame = ctk.CTkFrame(
            card,
            width=320,
            height=45,
            fg_color="#12121a",
            border_width=1,
            border_color="#333333",
            corner_radius=22
        )
        email_frame.pack(pady=(0, 18))

        email_frame.pack_propagate(False)

        email_label = ctk.CTkLabel(
            email_frame,
            text=email_value,
            font=ctk.CTkFont(size=12),
            text_color="#dddddd"
        )
        email_label.pack(side="left", padx=15)

        edit_btn = ctk.CTkButton(
            email_frame,
            text="Edit",
            fg_color="transparent",
            hover_color="#eeeeee",
            text_color="#2563eb",
            width=50
        )
        edit_btn.pack(side="right", padx=10)

        # If phone flow, we need an email address
        if self.is_phone_flow:
            self.create_email_entry = ctk.CTkEntry(
                card,
                placeholder_text="Email Address",
                width=320,
                height=45,
                corner_radius=22,
                border_width=1,
                border_color="#444444"
            )
            self.create_email_entry.pack(pady=(0, 15))

        # Password Entry
        self.create_password_entry = ctk.CTkEntry(
            card,
            placeholder_text="Password",
            width=320,
            height=45,
            show="*",
            corner_radius=22,
            border_width=1,
            border_color="#dddddd"
        )
        self.create_password_entry.pack(pady=(0, 25))

        # Continue Button
        continue_btn = ctk.CTkButton(
            card,
            text="Continue",
            width=320,
            height=48,
            corner_radius=24,
            fg_color="#4a5fe8",
            hover_color="#3a4fd8",
            text_color="#ffffff",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.handle_create_password
        )
        continue_btn.pack(pady=(5, 30))
        
        # Message label
        self.create_pass_message = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.create_pass_message.pack(pady=(0, 5))

        # Footer
        footer = ctk.CTkLabel(
            card,
            text="Terms of Use   |   Privacy Policy",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        footer.pack(side="bottom", pady=15)

    def handle_create_password(self):
        """Handle password creation logic"""
        password = self.create_password_entry.get()
        
        if getattr(self, 'is_phone_flow', False):
            email = self.create_email_entry.get().strip()
            phone = self.pending_email
            if not self.validate_email(email):
                self.create_pass_message.configure(text="Invalid email address", text_color="red")
                return
        else:
            email = getattr(self, 'pending_email', None)
            phone = None
            if not email:
                self.show_login_page()
                return

        if not password:
            self.create_pass_message.configure(text="Password cannot be empty", text_color="red")
            return
            
        valid, msg = self.validate_password(password)
        if not valid:
            self.create_pass_message.configure(text=msg, text_color="red")
            return
            
        # Generate username from email
        username = email.split('@')[0]
        # Sanitize username
        username = "".join(c for c in username if c.isalnum() or c in "._-")
        if len(username) < 3:
            username = f"user_{random.randint(1000, 9999)}"
            
        # Try to create user
        success, msg = self.db.create_user(username, email, password, full_name=username, phone_number=phone)
        
        # Handle username collision by appending numbers
        if not success and "Username already exists" in msg:
            username = f"{username}{random.randint(100, 999)}"
            success, msg = self.db.create_user(username, email, password, full_name=username, phone_number=phone)
            
        if success:
            # Auto login
            auth_success, user_id, auth_msg = self.db.authenticate_user(username, password)
            if auth_success:
                self.current_user_id = user_id
                self.show_success_animation()
            else:
                self.show_login_page()
        else:
            self.create_pass_message.configure(text=msg, text_color="red")

    def show_forgot_password_page(self):
        """Display the forgot password page"""
        self.clear_window()
        
        # Main frame (reuse style from login)
        card = ctk.CTkFrame(
            self.content_frame,
            width=360,
            height=450,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        card.pack(pady=50, padx=20, anchor="center")
        
        # Title
        title = ctk.CTkLabel(
            card,
            text="Reset Password",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            card,
            text="Enter your email address and we'll send you\na code to reset your password.",
            font=ctk.CTkFont(size=12),
            text_color="#CCCCCC",
            justify="center"
        )
        subtitle.pack(pady=(0, 30))
        
        # Email Field
        self.reset_email = ctk.CTkEntry(
            card,
            placeholder_text="Email address",
            width=300,
            height=40,
            corner_radius=20
        )
        self.reset_email.pack(pady=(0, 20))
        
        # Send Button
        send_btn = ctk.CTkButton(
            card,
            text="Send Reset Code",
            width=300,
            height=42,
            corner_radius=22,
            fg_color="#4a5fe8",
            text_color="#ffffff",
            hover_color="#3a4fd8",
            command=self.handle_forgot_password
        )
        send_btn.pack(pady=(0, 10))
        
        # Message label
        self.reset_message = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.reset_message.pack(pady=5)
        
        # Back to login
        back_btn = ctk.CTkButton(
            card,
            text="Back to Login",
            fg_color="transparent",
            hover_color="#333333",
            text_color="#CCCCCC",
            command=self.show_login_page
        )
        back_btn.pack(pady=10)

    def handle_forgot_password(self):
        email = self.reset_email.get().strip()
        if not email:
            self.reset_message.configure(text="Please enter your email", text_color="red")
            return
            
        if not self.validate_email(email):
            self.reset_message.configure(text="Invalid email address", text_color="red")
            return
            
        self.reset_message.configure(text="Sending...", text_color="yellow")
        self.root.update()
        
        success, msg = self.send_password_reset_email(email)
        
        if success:
            self.show_reset_password_page(email)
        else:
            self.reset_message.configure(text=msg, text_color="red")

    def show_reset_password_page(self, email=""):
        """Display the page to enter token and new password"""
        self.clear_window()
        
        card = ctk.CTkFrame(
            self.content_frame,
            width=360,
            height=550,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        card.pack(pady=50, padx=20, anchor="center")
        
        title = ctk.CTkLabel(
            card,
            text="Set New Password",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            card,
            text=f"Enter the code sent to {email}",
            font=ctk.CTkFont(size=12),
            text_color="#CCCCCC",
            justify="center"
        )
        subtitle.pack(pady=(0, 20))
        
        # Token Field
        self.reset_token = ctk.CTkEntry(
            card,
            placeholder_text="Reset Token / Code",
            width=300,
            height=40,
            corner_radius=20
        )
        self.reset_token.pack(pady=(0, 15))
        
        # New Password
        self.reset_new_pass = ctk.CTkEntry(
            card,
            placeholder_text="New Password",
            show="*",
            width=300,
            height=40,
            corner_radius=20
        )
        self.reset_new_pass.pack(pady=(0, 15))
        
        # Confirm Password
        self.reset_confirm_pass = ctk.CTkEntry(
            card,
            placeholder_text="Confirm Password",
            show="*",
            width=300,
            height=40,
            corner_radius=20
        )
        self.reset_confirm_pass.pack(pady=(0, 20))
        
        # Reset Button
        reset_btn = ctk.CTkButton(
            card,
            text="Reset Password",
            width=300,
            height=42,
            corner_radius=22,
            fg_color="#4a5fe8",
            text_color="#ffffff",
            hover_color="#3a4fd8",
            command=self.handle_reset_password
        )
        reset_btn.pack(pady=(0, 10))
        
        # Message label
        self.reset_final_message = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.reset_final_message.pack(pady=5)
        
        back_btn = ctk.CTkButton(
            card,
            text="Back to Login",
            fg_color="transparent",
            hover_color="#333333",
            text_color="#CCCCCC",
            command=self.show_login_page
        )
        back_btn.pack(pady=10)

    def handle_reset_password(self):
        token = self.reset_token.get().strip()
        new_pass = self.reset_new_pass.get()
        confirm_pass = self.reset_confirm_pass.get()
        
        if not token or not new_pass:
            self.reset_final_message.configure(text="Please fill all fields", text_color="red")
            return
            
        if new_pass != confirm_pass:
            self.reset_final_message.configure(text="Passwords do not match", text_color="red")
            return
            
        valid, msg = self.validate_password(new_pass)
        if not valid:
            self.reset_final_message.configure(text=msg, text_color="red")
            return
            
        success, msg = self.db.reset_password_with_token(token, new_pass)
        
        if success:
            self.reset_final_message.configure(text="Password reset successful!", text_color="green")
            self.root.after(1500, self.show_login_page)
        else:
            self.reset_final_message.configure(text=msg, text_color="red")

    def show_otp_verification_page(self):
        """Display the OTP verification page"""
        self.clear_window()
        
        # Main frame
        main_frame = ctk.CTkFrame(
            self.content_frame,
            width=400,
            height=500,
            corner_radius=20,
            fg_color="#0a0a12",
            border_width=1,
            border_color="#2a2a35"
        )
        main_frame.pack(pady=50, padx=20, anchor="center")
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Verify Account",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(30, 10))
        
        subtitle = ctk.CTkLabel(
            main_frame,
            text=f"Enter the code sent to\n{self.pending_user_data.get('email', '')}",
            font=ctk.CTkFont(size=14)
        )
        subtitle.pack(pady=(0, 30))
        
        # Form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # OTP Entry
        ctk.CTkLabel(form_frame, text="Verification Code", font=ctk.CTkFont(size=12)).pack(pady=(20, 5))
        self.otp_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter 6-digit code", width=300, justify="center", font=ctk.CTkFont(size=18, weight="bold"))
        self.otp_entry.pack(pady=(0, 20))
        
        # Verify button
        verify_btn = ctk.CTkButton(
            form_frame,
            text="Verify & Create Account",
            command=self.handle_otp_verification,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4a5fe8",
            hover_color="#3a4fd8"
        )
        verify_btn.pack(pady=10)
        
        # Resend button
        self.resend_btn = ctk.CTkButton(
            form_frame,
            text="Resend Code",
            command=self.resend_otp,
            width=300,
            fg_color="transparent",
            border_width=0,
            text_color="#aaaaaa"
        )
        self.resend_btn.pack(pady=5)
        
        # Message label
        self.otp_message = ctk.CTkLabel(form_frame, text="", text_color="red")
        self.otp_message.pack(pady=5)
        
        # Back button
        back_btn = ctk.CTkButton(
            form_frame,
            text="← Back",
            command=self.show_register_page,
            width=300,
            fg_color="transparent",
            border_width=0
        )
        back_btn.pack(pady=10)

    def show_profile_page(self):
        """Display the user profile page"""
        self.clear_window()
        
        user_info = self.db.get_user_info(self.current_user_id)
        if not user_info:
            self.show_login_page()
            return
        
        # Main frame
        main_frame = ctk.CTkFrame(
            self.content_frame,
            width=500,
            height=600,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        main_frame.pack(pady=50, padx=20, anchor="center")
        
        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(20, 30))
        
        title = ctk.CTkLabel(
            header_frame,
            text="👤 Profile",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(side="left", padx=20)
        
        # Profile info
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Display user info
        self._add_info_row(info_frame, "Username:", user_info['username'])
        self._add_info_row(info_frame, "Email:", user_info['email'])
        self._add_info_row(info_frame, "Full Name:", user_info['full_name'] or "Not set")
        self._add_info_row(info_frame, "Member Since:", user_info['created_at'].split()[0] if user_info['created_at'] else "Unknown")
        
        # Edit profile button
        edit_btn = ctk.CTkButton(
            info_frame,
            text="Edit Profile",
            command=self.show_edit_profile_page,
            width=250
        )
        edit_btn.pack(pady=20)
        
        # Change password button
        password_btn = ctk.CTkButton(
            info_frame,
            text="Change Password",
            command=self.show_change_password_page,
            width=250,
            fg_color="transparent",
            border_width=2
        )
        password_btn.pack(pady=10)
        
        # Logout button
        logout_btn = ctk.CTkButton(
            info_frame,
            text="Logout",
            command=self.handle_logout,
            width=250,
            fg_color="#be3535", hover_color="#8b3a3a"
        )
        logout_btn.pack(pady=10)
        
        # Continue to JARVIS button
        if self.on_login_success:
            def on_continue():
                self.on_login_success(self.current_user_id)
                self.root.destroy()

            continue_btn = ctk.CTkButton(
                main_frame,
                text="Continue to JARVIS →",
                command=on_continue,
                width=300,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#4a5fe8",
                hover_color="#3a4fd8"
            )
            continue_btn.pack(pady=20)
    
    def _add_info_row(self, parent, label, value):
        """Helper to add a row of information"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=120,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(side="left", padx=(10, 0))
    
    def show_edit_profile_page(self):
        """Display the edit profile page"""
        self.clear_window()
        
        user_info = self.db.get_user_info(self.current_user_id)
        user_prefs = self.db.get_user_preferences(self.current_user_id)
        
        # Main frame
        main_frame = ctk.CTkFrame(
            self.content_frame,
            width=400,
            height=600,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        main_frame.pack(pady=50, padx=20, anchor="center")
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Edit Profile & Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 30))
        
        # Form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Full Name
        ctk.CTkLabel(form_frame, text="Full Name", font=ctk.CTkFont(size=12)).pack(pady=(10, 5))
        self.edit_fullname = ctk.CTkEntry(form_frame, width=300)
        self.edit_fullname.insert(0, user_info['full_name'] or "")
        self.edit_fullname.pack(pady=(0, 15))
        
        # Email
        ctk.CTkLabel(form_frame, text="Email", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.edit_email = ctk.CTkEntry(form_frame, width=300)
        self.edit_email.insert(0, user_info['email'])
        self.edit_email.pack(pady=(0, 20))
        
        # API Key
        ctk.CTkLabel(form_frame, text="AI API Key (Groq or OpenAI)", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.edit_api_key = ctk.CTkEntry(form_frame, width=300, show="*")
        if user_prefs and user_prefs.get('api_key'):
            self.edit_api_key.insert(0, user_prefs['api_key'])
        self.edit_api_key.pack(pady=(0, 20))
        
        # Upload Avatar Button
        avatar_btn = ctk.CTkButton(
            form_frame,
            text="Upload Profile Picture",
            command=self.handle_avatar_upload,
            width=300,
            fg_color="#333333", hover_color="#444444"
        )
        avatar_btn.pack(pady=(0, 20))
        
        # Save button
        save_btn = ctk.CTkButton(
            form_frame,
            text="Save Changes",
            command=self.handle_edit_profile,
            width=300,
            height=40,
            fg_color="#4a5fe8",
            hover_color="#3a4fd8"
        )
        save_btn.pack(pady=10)
        
        # Message label
        self.edit_message = ctk.CTkLabel(form_frame, text="")
        self.edit_message.pack(pady=5)
        
        # Back button
        back_btn = ctk.CTkButton(
            form_frame,
            text="← Back to Profile",
            command=self.show_profile_page,
            width=300,
            fg_color="transparent",
            border_width=0
        )
        back_btn.pack(pady=10)
    
    def show_change_password_page(self):
        """Display the change password page"""
        self.clear_window()
        
        # Main frame
        main_frame = ctk.CTkFrame(
            self.content_frame,
            width=400,
            height=500,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        main_frame.pack(pady=50, padx=20, anchor="center")
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Change Password",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 30))
        
        # Form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Current Password
        ctk.CTkLabel(form_frame, text="Current Password", font=ctk.CTkFont(size=12)).pack(pady=(20, 5))
        self.old_password = ctk.CTkEntry(form_frame, placeholder_text="Enter current password", show="*", width=300)
        self.old_password.pack(pady=(0, 15))
        
        # New Password
        ctk.CTkLabel(form_frame, text="New Password", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.new_password = ctk.CTkEntry(form_frame, placeholder_text="Enter new password", show="*", width=300)
        self.new_password.pack(pady=(0, 15))
        
        # Confirm New Password
        ctk.CTkLabel(form_frame, text="Confirm New Password", font=ctk.CTkFont(size=12)).pack(pady=(0, 5))
        self.confirm_new_password = ctk.CTkEntry(form_frame, placeholder_text="Re-enter new password", show="*", width=300)
        self.confirm_new_password.pack(pady=(0, 20))
        
        # Change button
        change_btn = ctk.CTkButton(
            form_frame,
            text="Change Password",
            command=self.handle_change_password,
            width=300,
            height=40,
            fg_color="#4a5fe8",
            hover_color="#3a4fd8"
        )
        change_btn.pack(pady=10)
        
        # Message label
        self.password_message = ctk.CTkLabel(form_frame, text="")
        self.password_message.pack(pady=5)
        
        # Back button
        back_btn = ctk.CTkButton(
            form_frame,
            text="← Back to Profile",
            command=self.show_profile_page,
            width=300,
            fg_color="transparent",
            border_width=0
        )
        back_btn.pack(pady=10)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        return True, ""
        
    def send_otp_email(self, to_email, otp):
        """Send OTP via email"""
        # In a real app, use environment variables
        sender_email = os.getenv("JARVIS_SMTP_EMAIL")
        sender_password = os.getenv("JARVIS_SMTP_PASSWORD")
        
        if not sender_email or not sender_password:
            logging.info(f"Simulating OTP email to {to_email}: {otp}")
            return True, "OTP sent (simulation check console)"

        try:
            msg = EmailMessage()
            msg.set_content(f"Your verification code is: {otp}\n\nPlease enter this code to verify your account.")
            msg['Subject'] = "JARVIS Account Verification Code"
            msg['From'] = sender_email
            msg['To'] = to_email
            # Connect to Gmail's SMTP server using SSL
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                # server.set_debuglevel(1) # a lot of noise
                server.login(sender_email, sender_password)
                server.send_message(msg)
                
            return True, "OTP sent successfully"
        except Exception as e:
            logging.error(f"SMTP Error: {e}", exc_info=True)
            return False, f"Failed to send email: {e}"
            
    def send_password_reset_email(self, email):
        """Initiate password reset flow"""
        success, token, msg = self.db.create_password_reset_token(email)
        if not success:
            return False, msg
            
        # In a real app, this would be a link like https://app.com/reset?token=...
        # For this desktop app, we might just send the token code
        reset_link = f"jarvis://reset-password?token={token}"
        
        try:
            msg = EmailMessage()
            msg.set_content(f"You requested a password reset.\n\nYour reset token is:\n{token}\n\nIf you did not request this, please ignore this email.")
            msg['Subject'] = "JARVIS Password Reset"
            msg['From'] = os.getenv("JARVIS_SMTP_EMAIL", "noreply@jarvis.ai")
            msg['To'] = email
            
            # Using the same SMTP logic as OTP
            # Note: This requires the SMTP env vars to be set
            # For simulation, we just print it
            logging.info(f"--- SIMULATED EMAIL TO {email} ---\nSubject: Password Reset\nToken: {token}\n----------------------------------")
            return True, "Reset instructions sent to email"
        except Exception as e:
            return False, f"Failed to send email: {e}"

    def show_success_animation(self):
        """Display login success animation"""
        self.clear_window()
        
        # Center frame
        self.success_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.success_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Success Icon
        icon = ctk.CTkLabel(
            self.success_frame,
            text="✓",
            font=ctk.CTkFont(size=80, weight="bold"),
            text_color="#2cc985"
        )
        icon.pack(pady=20)
        
        # Success Text
        text = ctk.CTkLabel(
            self.success_frame,
            text="Login Successful",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        text.pack(pady=10)
        
        # Loading bar
        progress = ctk.CTkProgressBar(self.success_frame, width=200, height=10, progress_color="#2cc985")
        progress.pack(pady=20)
        progress.set(0)
        
        def update_progress(val=0):
            if val <= 1.0:
                progress.set(val)
                self.root.after(15, lambda: update_progress(val + 0.02))
            else:
                self.root.after(200, self.finish_login)
                
        update_progress()

    def finish_login(self):
        """Complete login process and transition"""
        if hasattr(self, 'success_frame') and self.success_frame:
            self.success_frame.destroy()
            
        if self.on_login_success:
            self.on_login_success(self.current_user_id)
            
        if self.master or self.on_login_success:
            # Close window to return to main interface
            self.root.destroy()
        else:
            # Standalone mode: show profile
            self.show_profile_page()
    
    def handle_login(self):
        """Handle login button click"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            self.login_message.configure(text="Please fill in all fields", text_color="red")
            return
        
        success, user_id, message = self.db.authenticate_user(username, password)
        
        if success:
            self.current_user_id = user_id
            self.login_message.configure(text=message, text_color="green")
            self.root.after(500, self.show_success_animation)
        else:
            self.login_message.configure(text=message, text_color="red")
    
    def handle_social_login(self, provider):
        """Handle social login simulation"""
        if provider == "Phone":
            self.show_phone_login_page()
            return

        # Simulate getting email from provider
        dialog = ctk.CTkInputDialog(
            text=f"Enter your email to continue with {provider}:", 
            title=f"{provider} Login"
        )
        
        # Center dialog if possible
        try:
            dialog.geometry(f"+{self.root.winfo_rootx()+50}+{self.root.winfo_rooty()+50}")
        except:
            pass
            
        email = dialog.get_input()
        
        if not email:
            return
            
        email = email.strip()
        if not self.validate_email(email):
            self.login_message.configure(text="Invalid email format", text_color="red")
            return
            
        # Check if user exists (using a dummy username to check only email)
        dummy_user = f"__check__{random.randint(10000,99999)}"
        exists, msg = self.db.check_user_exists(dummy_user, email)
        
        if exists and "Email already registered" in msg:
            # Login existing user
            user_id = self.db.get_user_id_by_email(email)
            if user_id:
                self.current_user_id = user_id
                self.show_success_animation()
            else:
                self.login_message.configure(text="Account error. Please try password login.", text_color="red")
        else:
            # New user -> Create Password flow
            self.show_create_password_page(email)

    def show_phone_login_page(self):
        """Display phone number entry page"""
        self.clear_window()
        
        card = ctk.CTkFrame(
            self.content_frame,
            width=360,
            height=450,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        card.pack(pady=50, padx=20, anchor="center")
        
        ctk.CTkLabel(card, text="Enter your phone number", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="We'll send you a code to verify your number.", font=ctk.CTkFont(size=12), text_color="#CCCCCC").pack(pady=(0, 30))
        
        self.phone_entry = ctk.CTkEntry(card, placeholder_text="+1 555 000 0000", width=300, height=40, corner_radius=20)
        self.phone_entry.pack(pady=(0, 20))
        
        ctk.CTkButton(card, text="Send Code", width=300, height=42, corner_radius=22, fg_color="#4a5fe8", hover_color="#3a4fd8", command=self.handle_send_phone_otp).pack(pady=(0, 10))
        
        self.phone_message = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.phone_message.pack(pady=5)
        
        ctk.CTkButton(card, text="Back to Login", fg_color="transparent", hover_color="#333333", text_color="#CCCCCC", command=self.show_login_page).pack(pady=10)

    def handle_send_phone_otp(self):
        """Simulate sending OTP to phone"""
        phone = self.phone_entry.get().strip()
        if not phone:
            self.phone_message.configure(text="Please enter a phone number", text_color="red")
            return
        
        # Basic validation
        if not re.match(r'^\+?[\d\s-]{7,}$', phone):
             self.phone_message.configure(text="Invalid phone number format", text_color="red")
             return
             
        # Generate OTP
        self.generated_otp = str(random.randint(100000, 999999))
        self.otp_generation_time = datetime.now()
        self.otp_attempts = 0
        self.pending_phone = phone
        
        # Simulate sending
        logging.info(f"--- SIMULATED SMS TO {phone} ---\nCode: {self.generated_otp}\n----------------------------------")
        
        self.show_phone_otp_page(phone)

    def show_phone_otp_page(self, phone):
        """Display OTP entry for phone verification"""
        self.clear_window()
        
        card = ctk.CTkFrame(
            self.content_frame,
            width=360,
            height=500,
            corner_radius=20,
            fg_color="#000000",
            border_width=1,
            border_color="#333333"
        )
        card.pack(pady=50, padx=20, anchor="center")
        
        ctk.CTkLabel(card, text="Verify Phone", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(30, 10))
        ctk.CTkLabel(card, text=f"Enter the code sent to {phone}", font=ctk.CTkFont(size=12), text_color="#CCCCCC").pack(pady=(0, 30))
        
        self.phone_otp_entry = ctk.CTkEntry(card, placeholder_text="000000", width=300, height=40, corner_radius=20, justify="center", font=ctk.CTkFont(size=18, weight="bold"))
        self.phone_otp_entry.pack(pady=(0, 20))
        
        ctk.CTkButton(card, text="Verify", width=300, height=42, corner_radius=22, fg_color="#4a5fe8", hover_color="#3a4fd8", command=self.handle_verify_phone_otp).pack(pady=(0, 10))
        
        # Resend button
        ctk.CTkButton(
            card,
            text="Resend Code",
            command=self.resend_phone_otp,
            width=300,
            fg_color="transparent",
            border_width=0,
            text_color="#CCCCCC"
        ).pack(pady=5)
        
        self.phone_otp_message = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11))
        self.phone_otp_message.pack(pady=5)
        
        ctk.CTkButton(card, text="Back", fg_color="transparent", hover_color="#333333", text_color="#CCCCCC", command=self.show_phone_login_page).pack(pady=10)

    def handle_verify_phone_otp(self):
        """Verify phone OTP"""
        otp = self.phone_otp_entry.get().strip()
        if otp != self.generated_otp:
            self.phone_otp_message.configure(text="Invalid code", text_color="red")
            return
            
        # Success
        phone = self.pending_phone
        user_id = self.db.get_user_id_by_phone(phone)
        
        if user_id:
            # Login existing user
            self.current_user_id = user_id
            self.show_success_animation()
        else:
            # New user -> Create Password (and ask for email)
            # We pass the phone number as the identifier
            self.show_create_password_page(email_value=phone)

    def resend_phone_otp(self):
        """Resend OTP to phone"""
        if not hasattr(self, 'pending_phone') or not self.pending_phone:
            return

        self.generated_otp = str(random.randint(100000, 999999))
        self.otp_generation_time = datetime.now()
        self.otp_attempts = 0
        
        # Simulate sending
        logging.info(f"--- SIMULATED SMS TO {self.pending_phone} ---\nCode: {self.generated_otp}\n----------------------------------")
        
        self.phone_otp_message.configure(text="New code sent!", text_color="green")

    def handle_register(self):
        """Handle registration button click"""
        full_name = self.reg_fullname.get().strip()
        username = self.reg_username.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        
        # Terms of service validation
        if self.terms_check.get() == 0:
            self.reg_message.configure(text="You must agree to the Terms of Service", text_color="red")
            return
            
        # Validation
        if not username or not email or not password:
            self.reg_message.configure(text="Please fill in all required fields", text_color="red")
            return
        
        if len(username) < 3:
            self.reg_message.configure(text="Username must be at least 3 characters", text_color="red")
            return
        
        if not self.validate_email(email):
            self.reg_message.configure(text="Please enter a valid email address", text_color="red")
            return
        
        valid_pwd, pwd_msg = self.validate_password(password)
        if not valid_pwd:
            self.reg_message.configure(text=pwd_msg, text_color="red")
            return
        
        if password != confirm:
            self.reg_message.configure(text="Passwords do not match", text_color="red")
            return
        
        # Check if user exists before sending OTP
        exists, msg = self.db.check_user_exists(username, email)
        if exists:
            self.reg_message.configure(text=msg, text_color="red")
            return
            
        # Generate and send OTP
        self.generated_otp = str(random.randint(100000, 999999))
        self.otp_generation_time = datetime.now()
        self.otp_attempts = 0
        self.pending_user_data = {
            'username': username,
            'email': email,
            'password': password,
            'full_name': full_name
        }
        
        self.reg_message.configure(text="Sending verification code...", text_color="yellow")
        self.root.update()
        
        success, msg = self.send_otp_email(email, self.generated_otp)
        
        if success:
            self.show_otp_verification_page()
            self.otp_message.configure(text=msg, text_color="green")
        else:
            self.reg_message.configure(text=msg, text_color="red")

    def handle_otp_verification(self):
        """Verify OTP and create account"""
        # Check for too many attempts
        if self.otp_attempts >= 3:
            self.otp_message.configure(text="Too many failed attempts. Please request a new code.", text_color="red")
            return

        # Check OTP expiry (5 minutes)
        if self.otp_generation_time:
            elapsed = (datetime.now() - self.otp_generation_time).total_seconds()
            if elapsed > 300:
                self.otp_message.configure(text="OTP has expired. Please request a new one.", text_color="red")
                return

        entered_otp = self.otp_entry.get().strip()
        
        if entered_otp != self.generated_otp:
            self.otp_attempts += 1
            remaining = 3 - self.otp_attempts
            if remaining > 0:
                self.otp_message.configure(text=f"Invalid code. You have {remaining} attempt(s) left.", text_color="orange")
            else:
                self.otp_message.configure(text="Invalid code. Too many failed attempts.", text_color="red")
            return
            
        # Create account
        data = self.pending_user_data
        success, message = self.db.create_user(
            data['username'], 
            data['email'], 
            data['password'], 
            data['full_name']
        )
        
        if success:
            self.otp_message.configure(text="Account verified and created!", text_color="green")
            self.root.after(1500, self.show_login_page)
        else:
            self.otp_message.configure(text=message, text_color="red")
    
    def resend_otp(self):
        """Resend the OTP"""
        if not self.pending_user_data:
            return
            
        self.generated_otp = str(random.randint(100000, 999999))
        self.otp_generation_time = datetime.now()
        self.otp_attempts = 0
        success, msg = self.send_otp_email(self.pending_user_data['email'], self.generated_otp)
        
        if success:
            self.otp_message.configure(text="New code sent!", text_color="green")
        else:
            self.otp_message.configure(text=msg, text_color="red")

    def handle_edit_profile(self):
        """Handle profile edit submission"""
        full_name = self.edit_fullname.get().strip()
        email = self.edit_email.get().strip()
        api_key = self.edit_api_key.get().strip()
        
        if not email:
            self.edit_message.configure(text="Email cannot be empty", text_color="red")
            return
        
        if not self.validate_email(email):
            self.edit_message.configure(text="Please enter a valid email address", text_color="red")
            return
        
        success, message = self.db.update_user_info(self.current_user_id, full_name, email)
        
        if not success:
            self.edit_message.configure(text=message, text_color="red")
            return

        # Update API key preference
        if api_key:
            # Basic validation for an API key format
            if (api_key.startswith("sk-") or api_key.startswith("gsk_")) and len(api_key) >= 40:
                 pref_success, pref_msg = self.db.update_user_preference(self.current_user_id, 'api_key', api_key)
                 if not pref_success:
                     self.edit_message.configure(text=f"Profile updated, but API key save failed: {pref_msg}", text_color="orange")
                     return
        
        self.edit_message.configure(text="Profile updated successfully", text_color="green")

    def handle_avatar_upload(self):
        """Handle profile picture upload"""
        file_path = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                filename = f"user_avatar_{self.current_user_id}.png" if self.current_user_id else "user_avatar.png"
                img.save(filename)
                self.edit_message.configure(text="Profile picture updated successfully", text_color="green")
            except Exception as e:
                self.edit_message.configure(text=f"Error saving image: {str(e)}", text_color="red")

    def handle_change_password(self):
        """Handle password change submission"""
        old_pwd = self.old_password.get()
        new_pwd = self.new_password.get()
        confirm_pwd = self.confirm_new_password.get()
        
        if not old_pwd or not new_pwd or not confirm_pwd:
            self.password_message.configure(text="Please fill in all fields", text_color="red")
            return
        
        valid_pwd, pwd_msg = self.validate_password(new_pwd)
        if not valid_pwd:
            self.password_message.configure(text=pwd_msg, text_color="red")
            return
        
        if new_pwd != confirm_pwd:
            self.password_message.configure(text="New passwords do not match", text_color="red")
            return
        
        success, message = self.db.change_password(self.current_user_id, old_pwd, new_pwd)
        
        if success:
            self.password_message.configure(text=message, text_color="green")
            self.root.after(1500, self.show_profile_page)
        else:
            self.password_message.configure(text=message, text_color="red")
    
    def handle_logout(self):
        """Handle logout"""
        # Create confirmation dialog
        win = ctk.CTkToplevel(self.root)
        win.title("Logout")
        win.geometry("300x150")
        win.resizable(False, False)
        
        # Center window
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (150)
        y = (win.winfo_screenheight() // 2) - (75)
        win.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(win, text="Are you sure you want to logout?", font=ctk.CTkFont(size=14)).pack(pady=(30, 20))
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def yes():
            win.destroy()
            self.current_user_id = None
            
            if self.on_logout:
                self.on_logout()
            
            if self.master:
                self.root.destroy()
            else:
                self.show_login_page()
            
        def no():
            win.destroy()
            
        ctk.CTkButton(btn_frame, text="Logout", command=yes, width=100, fg_color="#be3535", hover_color="#8b3a3a").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=no, width=100, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="left", padx=10)
        
        win.transient(self.root)
        win.grab_set()
    
    def run(self):
        """Start the account page GUI"""
        if self.master:
            self.root.transient(self.master)
            self.root.grab_set()
            self.root.lift()
            self.root.focus_force()
        else:
            self.root.mainloop()


if __name__ == "__main__":
    # Demo: standalone account page
    def on_login(user_id):
        logging.info(f"User {user_id} logged in successfully!")
        # Here you would typically launch the main JARVIS interface
    
    try:
        app = AccountPage(on_login_success=on_login)
        app.run()
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        logging.error("Make sure customtkinter is installed: pip install customtkinter")