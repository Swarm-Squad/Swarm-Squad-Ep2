#!/usr/bin/env python3
"""
Script to clear the SQLite database.
This removes all vehicles, LLMs, and mappings from the database.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from swarm_squad_ep2.api.database import (
    clear_all_data,
    connect_to_db,
    get_all_llms,
    get_all_vehicles,
)


async def clear_database():
    """Clear all data from the SQLite database."""
    print("Connecting to SQLite database...")
    success = await connect_to_db()
    if not success:
        print("❌ Failed to connect to SQLite database")
        return

    print("✓ Connected to SQLite database")

    # Count existing records
    vehicles = await get_all_vehicles()
    llms = await get_all_llms()
    
    vehicle_count = len(vehicles)
    llm_count = len(llms)

    print("\nFound:")
    print(f"  - {vehicle_count} vehicles")
    print(f"  - {llm_count} LLMs")

    if vehicle_count == 0 and llm_count == 0:
        print("\n✓ Database is already clean!")
        return

    # Clear all data
    print("\nClearing database...")
    success = await clear_all_data()
    
    if success:
        print(f"  ✓ Deleted {vehicle_count} vehicles")
        print(f"  ✓ Deleted {llm_count} LLMs")
        print("\n🎉 Database cleared successfully!")
    else:
        print("❌ Failed to clear database")


if __name__ == "__main__":
    try:
        asyncio.run(clear_database())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
