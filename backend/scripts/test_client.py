import asyncio
import json
import os
import sys

# Add the project root to Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.scripts.utils.client import SwarmClient


async def monitor_room(client: SwarmClient, room_id: str):
    """Monitor messages in a specific room."""

    async def message_handler(data):
        print(f"\n[{room_id}] {data['message']}")
        if "state" in data and data["state"]:
            print(f"State: {json.dumps(data['state'], indent=2)}")

    try:
        await client.subscribe_to_room(room_id, message_handler)
    except Exception as e:
        print(f"Error monitoring room {room_id}: {e}")


async def main():
    """Monitor multiple rooms simultaneously."""
    client = SwarmClient()

    # Example: Monitor Vehicle 1's rooms
    v2v_room = "v1"  # Vehicle 1's V2V room
    v2l_room = "vl1"  # Vehicle 1's Vehicle-to-LLM room
    l2l_room = "l1"  # Vehicle 1's LLM room

    print("Starting WebSocket clients...")
    print("This will connect to Vehicle 1's rooms:")
    print("- V2V Room (v1): Vehicle-to-Vehicle communication")
    print("- V2L Room (vl1): Vehicle-to-LLM communication")
    print("- L2L Room (l1): LLM-to-LLM communication")
    print("\nPress Ctrl+C to stop")

    async with client:
        try:
            # Connect to all rooms concurrently
            await asyncio.gather(
                monitor_room(client, v2v_room),
                monitor_room(client, v2l_room),
                monitor_room(client, l2l_room),
            )
        except KeyboardInterrupt:
            print("\nStopping clients...")
        except Exception as e:
            print(f"Error in main loop: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping clients...")
