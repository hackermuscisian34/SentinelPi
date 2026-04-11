import sys
print(sys.path)
import supabase
print(f"Supabase file: {supabase.__file__}")
print(f"Dir: {dir(supabase)}")
try:
    from supabase import create_client
    print("create_client imported successfully")
except ImportError as e:
    print(f"Failed to import create_client: {e}")
