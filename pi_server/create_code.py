import asyncio
from app.services.pairing import PairingManager
from app.supabase_client import SupabaseClient

async def main():
    manager = PairingManager()
    supabase = SupabaseClient()
    
    # Create code
    result = manager.create("ManualEnrollment")
    print(f"PAIRING_CODE:{result['pairing_code']}")
    
    # We also need to insert it into Supabase for the server to recognize it?
    # Actually pairing_manager stores it in memory?
    # Let's check PairingManager implementation.
    # The route inserts into supabase 'pairing_codes' table, but the verification might check memory or DB?
    # Let's check verify logic in PairingManager.

if __name__ == "__main__":
    asyncio.run(main())
