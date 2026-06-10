# JARVIS Persistent Login Guide

## Overview
JARVIS now implements **persistent login** - once you log in, your session is saved and you remain logged in even after closing and reopening the application. No need to log in repeatedly!

## Features ✨

✅ **Automatic Login**: Session automatically restored when you open the app
✅ **Secure Sessions**: Session tokens with expiration dates (30 days by default)
✅ **Session Validation**: Sessions are validated on startup
✅ **Account Security**: Disabled accounts are logged out automatically
✅ **Smart Logout**: Clearing session on logout keeps you secure
✅ **Legacy Support**: Old text-based sessions automatically migrated to new format

## How It Works

### Session Files
The app stores session information in a JSON file:
- **Location**: `jarvis_session.json` (in the main Jarvis directory)
- **Format**: Secure JSON with user ID, token, and expiration date
- **Duration**: Sessions last 30 days by default

### Login Flow
1. **First Login**: When you log in via the Account page, your session is saved
2. **App Restart**: On next startup, the saved session is automatically checked
3. **Session Validation**: The app verifies the session is still valid and user account is active
4. **Auto-Login**: If valid, you're automatically logged in without seeing the login screen

### Logout Flow
When you click Logout:
1. Your session file is deleted securely
2. Session in database is marked as ended
3. You're returned to Guest mode
4. Next time you start the app, login screen will appear

## Usage

### Default Behavior (Automatic)
Simply log in once and you'll stay logged in:
```
1. Open JARVIS → See login prompt
2. Enter credentials and log in → Logged in ✅
3. Close JARVIS
4. Open JARVIS again → Auto-logged in without login prompt! ✅
```

### Manual Logout
If you want to log out:
1. Click on your profile name in the sidebar
2. Click "Logout"
3. Confirm logout
4. Session is cleared and you'll need to log in again

### Check Session Status
In Python console:
```python
from jarvis_session_manager import SessionManager

manager = SessionManager()
if manager.is_logged_in():
    info = manager.get_session_info()
    print(f"Logged in as user: {info['user_id']}")
    print(f"Session expires: {info['expires_at']}")
else:
    print("Not logged in")
```

## Session Files Location

### New Format (Enhanced)
- **File**: `jarvis_session.json`
- **Location**: `\Jarvis_Project\content\drive\MyDrive\Jarvis\`
- **Format**: 
```json
{
  "user_id": 123,
  "session_token": "secure_random_token",
  "created_at": "2026-05-23T10:30:00.000000",
  "expires_at": "2026-06-22T10:30:00.000000",
  "last_accessed": "2026-05-23T10:35:00.000000"
}
```

### Legacy Format (Migrated Automatically)
- **Old File**: `login_session.txt` (automatically migrated)
- **Contains**: Just the user ID as plain text

## Troubleshooting

### Session Not Persisting?
1. Check if `jarvis_session.json` exists in the Jarvis directory
2. Make sure the file has write permissions
3. Check the app logs for errors
4. Try logging out and logging in again

### Getting Logged Out Randomly?
1. Session may have expired (30 days)
2. Log in again - a new session will be created
3. Account may be disabled - contact administrator

### "Session Expired" Message?
Sessions expire after 30 days for security. Simply log in again to create a new session.

### Can't Remember Password?
Use the "Forgot Password?" option on the login page to reset it.

## Technical Details

### Session Manager Architecture
The new `jarvis_session_manager.py` module provides:
- `SessionManager` class for session operations
- Backward-compatible legacy functions
- Automatic migration from old to new format
- Session validation and expiration checking

### Security Features
- **Session Tokens**: Secure random 32-byte tokens
- **Expiration**: Sessions auto-expire after 30 days
- **Validation**: User account status checked on auto-login
- **Cleanup**: Invalid sessions automatically removed

### Environment Variables
No special setup needed! The session system works automatically with standard Jarvis setup.

## Frequently Asked Questions

**Q: Will my login persist across computer restarts?**
A: Yes! As long as the `jarvis_session.json` file exists and hasn't expired, you'll be auto-logged in.

**Q: Can I log in on multiple devices?**
A: Not with the same session. Each device has its own `jarvis_session.json` file. You'll need to log in separately on each device.

**Q: Is my password stored?**
A: No! Only a session token is saved, never your password. Passwords are securely hashed in the database.

**Q: What happens if I delete `jarvis_session.json`?**
A: You'll be logged out and need to log in again. A new session file will be created.

**Q: Can an admin see my session?**
A: Only if they have direct file system access to `jarvis_session.json`. The app and database don't expose session tokens.

**Q: How do I log out without closing the app?**
A: Click on your profile name in the sidebar and select "Logout". The session will be cleared immediately.

## For Developers

### Extending Session Duration
Edit `jarvis_session_manager.py`:
```python
# In create_session method, change duration_days:
self.create_session(int(user_id), duration_days=90)  # 90 days instead of 30
```

### Implementing Custom Session Behavior
```python
from jarvis_session_manager import SessionManager

# Create custom session logic
manager = SessionManager()
if not manager.is_logged_in():
    # Show login UI
    pass
else:
    user_id = manager.get_user_id()
    # Auto-load user data
```

### Testing Session Flow
```python
from jarvis_session_manager import SessionManager

manager = SessionManager()

# Create a test session
manager.create_session(user_id=1)

# Check if logged in
assert manager.is_logged_in() == True

# Get user ID
assert manager.get_user_id() == 1

# Simulate logout
manager.clear_session()
assert manager.is_logged_in() == False
```

## Files Modified

1. **jarvis_session_manager.py** (NEW)
   - Enhanced session management with JSON storage
   - Automatic legacy migration
   - Session validation and expiration

2. **jarvis_interface.py** (UPDATED)
   - Imports new SessionManager
   - Enhanced `_auto_login()` method
   - Updated `perform_logout()` to use SessionManager
   - Better error handling and logging

## Support

If you encounter any issues with persistent login:
1. Check the logs in the app directory
2. Verify `jarvis_session.json` file exists and is readable
3. Make sure your user account is active in the database
4. Try logging out and logging in again
5. Contact support if the issue persists

---

**Last Updated**: May 23, 2026
**Version**: 1.0
