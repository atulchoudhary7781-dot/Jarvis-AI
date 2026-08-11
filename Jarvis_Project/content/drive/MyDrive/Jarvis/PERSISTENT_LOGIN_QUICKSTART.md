# Persistent Login - Quick Reference

## One-Time Setup
1. Open JARVIS
2. Log in with your credentials once
3. Done! ✅

## After That
- Next time you open JARVIS → Automatically logged in
- No need to enter credentials again
- Session lasts 30 days

## To Log Out
Click Profile → Logout

## Files Involved
- `jarvis_session.json` - Contains your session (created on login)
- `jarvis_accounts.db` - User database (already exists)

## Troubleshooting
| Issue | Solution |
|-------|----------|
| Not auto-logging in | Delete `jarvis_session.json` and log in again |
| Logged out after 30 days | Log in again (normal expiration) |
| Getting logged out randomly | Check if your account is active |
| Session file errors | Close app and restart |

---

**Key Benefit**: Log in once, stay logged in! 🚀
