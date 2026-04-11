"""
Cleanup script to clear orphaned telemetry data from the Pi server's database.
Run this script ON THE RASPBERRY PI SERVER, not on Windows.
"""
import asyncio
import aiosqlite
import os

# Pi server database path
DB_PATH = "/var/lib/sentinelpi/telemetry.db"

async def clear_telemetry_buffer():
    """Clear all telemetry data from the buffer."""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("Make sure you're running this script on the Raspberry Pi server!")
        return
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Count telemetry entries
        cursor = await db.execute("SELECT COUNT(*) FROM telemetry")
        count = (await cursor.fetchone())[0]
        print(f"Found {count} telemetry entries in buffer")
        
        if count > 0:
            # Clear all telemetry
            await db.execute("DELETE FROM telemetry")
            await db.commit()
            print(f"✅ Cleared all {count} telemetry entries")
        else:
            print("ℹ Telemetry buffer already empty")

async def main():
    print("=" * 60)
    print("Clearing Pi Server Telemetry Buffer")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print()
    
    await clear_telemetry_buffer()
    
    print()
    print("=" * 60)
    print("✅ Cleanup complete!")
    print("=" * 60)
    print()
    print("The telemetry flush errors should stop now.")
    print("New telemetry from properly enrolled devices will work correctly.")

if __name__ == "__main__":
    asyncio.run(main())
