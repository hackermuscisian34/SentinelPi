"""
SentinelPi Windows Agent — PyInstaller Build Script

Usage:
    pip install pyinstaller
    python build_exe.py

This will create:
    dist/SentinelPiAgent.exe
"""
import subprocess
import sys
import os

def build():
    """Build the Windows Agent EXE using PyInstaller."""
    
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "run_agent.py")
    
    if not os.path.exists(main_script):
        print(f"ERROR: {main_script} not found!")
        sys.exit(1)
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SentinelPiAgent",
        "--onefile",
        "--windowed",  # No console window (Qt tray app)
        "--noconfirm",
        
        # Hidden imports that PyInstaller may miss
        "--hidden-import", "paho.mqtt.client",
        "--hidden-import", "paho.mqtt",
        "--hidden-import", "keyring.backends.Windows",
        "--hidden-import", "keyring.backends",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "psutil",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "watchdog.observers",
        "--hidden-import", "watchdog.events",
        "--hidden-import", "supabase",
        "--hidden-import", "httpx",
        "--hidden-import", "dotenv",
        
        # Collect all data for supabase/gotrue/storage
        "--collect-all", "supabase",
        "--collect-all", "gotrue",
        "--collect-all", "storage3",
        "--collect-all", "postgrest",
        "--collect-all", "realtime",
        
        # Add the app package as source
        "--add-data", f"{os.path.join(script_dir, 'app')};app",
        
        # Set working directory
        "--distpath", os.path.join(script_dir, "dist"),
        "--workpath", os.path.join(script_dir, "build"),
        "--specpath", script_dir,
        
        main_script
    ]
    
    print("=" * 60)
    print("  SentinelPi Agent — Building EXE")
    print("=" * 60)
    print(f"\nCommand: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode == 0:
        exe_path = os.path.join(script_dir, "dist", "SentinelPiAgent.exe")
        print("\n" + "=" * 60)
        print("  BUILD SUCCESSFUL!")
        print(f"  EXE: {exe_path}")
        print("=" * 60)
        print("\nDEPLOYMENT NOTES:")
        print("  1. Copy SentinelPiAgent.exe to the target machine")
        print("  2. Create a .env file in the same directory with:")
        print("     PI_SERVER_IP=<your-pi-ip>")
        print("     SUPABASE_URL=<your-supabase-url>")
        print("     SUPABASE_KEY=<your-supabase-key>")
        print("  3. Run as Administrator for full functionality")
        print("  4. ClamAV and YARA must be installed separately")
    else:
        print("\n  BUILD FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    build()
