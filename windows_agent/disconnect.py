
import os
import sys
import subprocess

# Add the parent directory to sys.path so we can import from the package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from windows_agent.app.services.credentials import CredentialStore
    
    print("Initializing Credential Store...")
    creds = CredentialStore()
    
    print("Clearing credentials...")
    creds.clear("device_id")
    creds.clear("api_key")
    creds.clear("pi_ip")
    print("Credentials cleared successfully.")
    
except ImportError as e:
    print(f"Error importing CredentialStore: {e}")
except Exception as e:
    print(f"Error clearing credentials: {e}")

print("Stopping any running agent processes...")
try:
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], check=False)
    print("Agent processes terminated.")
except Exception as e:
    print(f"Error stopping processes: {e}")

print("\nDISCONNECTION COMPLETE.")
print("The agent is now disconnected and stopped.")
