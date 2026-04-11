import sys
import traceback

try:
    print("Attempting to import windows_agent.app.main")
    import windows_agent.app.main
    print("Import successful")
except Exception:
    print("Caught exception:")
    traceback.print_exc()
except SystemExit as e:
    print(f"Caught SystemExit: {e}")
