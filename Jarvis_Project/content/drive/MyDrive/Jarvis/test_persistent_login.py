"""
Test script for JARVIS Persistent Login Feature
Verify that session management is working correctly
"""
import os
import sys
import json
import time
from pathlib import Path

# Add the Jarvis directory to the path
JARVIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, JARVIS_DIR)

try:
    from jarvis_session_manager import SessionManager, save_session, get_session, clear_session
except ImportError:
    print("❌ Error: jarvis_session_manager not found!")
    sys.exit(1)

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def test_session_creation():
    """Test creating a new session."""
    print_header("TEST 1: Session Creation")
    
    manager = SessionManager()
    user_id = 123
    
    print(f"Creating session for user {user_id}...")
    token = manager.create_session(user_id)
    
    if token:
        print(f"✅ Session created successfully!")
        print(f"   Token: {token[:20]}...")
        return True
    else:
        print("❌ Failed to create session!")
        return False

def test_session_retrieval():
    """Test retrieving a session."""
    print_header("TEST 2: Session Retrieval")
    
    manager = SessionManager()
    
    print("Retrieving active session...")
    session = manager.get_session()
    
    if session:
        print(f"✅ Session retrieved successfully!")
        print(f"   User ID: {session.get('user_id')}")
        print(f"   Created: {session.get('created_at')}")
        print(f"   Expires: {session.get('expires_at')}")
        return True
    else:
        print("⚠️  No active session found")
        return False

def test_get_user_id():
    """Test getting user ID from session."""
    print_header("TEST 3: Get User ID from Session")
    
    manager = SessionManager()
    
    print("Fetching user ID from session...")
    user_id = manager.get_user_id()
    
    if user_id:
        print(f"✅ User ID retrieved: {user_id}")
        return True
    else:
        print("⚠️  No user ID in session")
        return False

def test_is_logged_in():
    """Test checking login status."""
    print_header("TEST 4: Login Status Check")
    
    manager = SessionManager()
    
    print("Checking login status...")
    if manager.is_logged_in():
        print("✅ User is logged in!")
        return True
    else:
        print("⚠️  User is not logged in")
        return False

def test_session_info():
    """Test getting session info."""
    print_header("TEST 5: Session Information")
    
    manager = SessionManager()
    
    print("Retrieving session info...")
    info = manager.get_session_info()
    
    if info:
        print("✅ Session info retrieved:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        return True
    else:
        print("⚠️  No session info available")
        return False

def test_session_file_exists():
    """Test if session file exists."""
    print_header("TEST 6: Session File Check")
    
    manager = SessionManager()
    session_file = manager.session_file
    
    print(f"Checking for session file: {session_file}")
    
    if os.path.exists(session_file):
        file_size = os.path.getsize(session_file)
        print(f"✅ Session file exists!")
        print(f"   Size: {file_size} bytes")
        
        # Try to read and parse
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            print(f"✅ Session file is valid JSON")
            return True
        except json.JSONDecodeError:
            print("❌ Session file is not valid JSON!")
            return False
    else:
        print("⚠️  Session file does not exist")
        return False

def test_legacy_migration():
    """Test legacy session migration."""
    print_header("TEST 7: Legacy Session Migration")
    
    legacy_file = os.path.join(JARVIS_DIR, "login_session.txt")
    
    if os.path.exists(legacy_file):
        print("⚠️  Legacy session file found (will be migrated automatically)")
        print(f"   File: {legacy_file}")
        
        # Try to read legacy file
        try:
            with open(legacy_file, 'r') as f:
                user_id = f.read().strip()
            print(f"   Legacy user_id: {user_id}")
            print("✅ Legacy file can be read and migrated")
            return True
        except Exception as e:
            print(f"❌ Error reading legacy file: {e}")
            return False
    else:
        print("ℹ️  No legacy session file (first time setup)")
        return True

def test_session_clear():
    """Test clearing/logout."""
    print_header("TEST 8: Session Clear (Logout)")
    
    manager = SessionManager()
    
    print("Clearing session (simulating logout)...")
    success = manager.clear_session()
    
    if success:
        print("✅ Session cleared successfully!")
        
        # Verify it's really cleared
        if not manager.is_logged_in():
            print("✅ Verified: User is now logged out")
            return True
        else:
            print("❌ Session still exists after clear!")
            return False
    else:
        print("❌ Failed to clear session!")
        return False

def test_legacy_backward_compatibility():
    """Test backward compatible functions."""
    print_header("TEST 9: Backward Compatible Functions")
    
    print("Testing legacy function: save_session()...")
    try:
        save_session(456)
        print("✅ save_session() works")
        
        print("Testing legacy function: get_session()...")
        user_id = get_session()
        if user_id == "456":
            print("✅ get_session() works")
            
            print("Testing legacy function: clear_session()...")
            clear_session()
            if get_session() is None:
                print("✅ clear_session() works")
                return True
            else:
                print("❌ clear_session() didn't clear session")
                return False
        else:
            print(f"❌ get_session() returned wrong value: {user_id}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  JARVIS PERSISTENT LOGIN - TEST SUITE".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Run all tests
    results.append(("Session Creation", test_session_creation()))
    results.append(("Session Retrieval", test_session_retrieval()))
    results.append(("Get User ID", test_get_user_id()))
    results.append(("Login Status Check", test_is_logged_in()))
    results.append(("Session Information", test_session_info()))
    results.append(("Session File Check", test_session_file_exists()))
    results.append(("Legacy Migration", test_legacy_migration()))
    
    # Create a new session for remaining tests
    print("\n[Setting up new session for remaining tests...]")
    manager = SessionManager()
    manager.create_session(999)
    
    results.append(("Session Clear", test_session_clear()))
    results.append(("Backward Compatibility", test_legacy_backward_compatibility()))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    # Overall status
    if passed == total:
        print(f"\n{'='*60}")
        print("  ✅ ALL TESTS PASSED - Persistent login is working!")
        print(f"{'='*60}\n")
        return 0
    else:
        print(f"\n{'='*60}")
        print(f"  ⚠️  {total - passed} test(s) failed - Check the output above")
        print(f"{'='*60}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
