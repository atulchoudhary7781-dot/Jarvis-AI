#!/usr/bin/env python
"""
Jarvis Launcher Script - Handles environment setup and execution
"""
import sys
import os

# Add python_deps to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python_deps'))

# Set environment variables
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Navigate to Jarvis directory
jarvis_dir = os.path.join(os.path.dirname(__file__), 'content', 'drive', 'MyDrive', 'Jarvis')
os.chdir(jarvis_dir)
sys.path.insert(0, jarvis_dir)

print("=" * 80)
print("JARVIS - Advanced AI Personal Assistant")
print("=" * 80)
print(f"Working Directory: {os.getcwd()}")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"Installed Dependencies in python_deps: {len([p for p in sys.path if 'python_deps' in p]) > 0}")
print()

# Try to run the main jarvis_interface
try:
    import runpy
    print("Launching Jarvis Interface...")
    print("-" * 80)
    runpy.run_path('jarvis_interface.py', run_name='__main__')
except KeyboardInterrupt:
    print("\n[!] Jarvis interrupted by user")
    sys.exit(0)
except Exception as e:
    print(f"\n[ERROR] Failed to run Jarvis: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
