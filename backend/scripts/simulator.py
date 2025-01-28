import asyncio
import json
import math
import os
import random
import sys
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.fastapi.main import create_simulation_resources
from backend.fastapi.models import MessageType
from backend.scripts.utils.client import SwarmClient
from backend.scripts.utils.message_templates import MessageTemplate


def generate_random_coordinates():
    """Generate random latitude and longitude."""
    return (
        random.uniform(-90, 90),  # latitude
        random.uniform(-180, 180),  # longitude
    )


class Vehicle:
    """Simulates a vehicle with real-time state updates and neighbor detection."""

    def __init__(self, vehicle_id: str, simulator: "VehicleSimulator" = None):
        """Initialize vehicle with random starting values."""
        self.id = vehicle_id
        self.simulator = simulator
        self.location = generate_random_coordinates()
        self.speed = random.uniform(0, 120)
        self.battery = random.uniform(20, 100)
        self.status = random.choice(["moving", "idle", "charging"])

        # Room IDs for different communication channels
        self.v2v_room_id = vehicle_id  # Vehicle's own room for V2V communication
        self.veh2llm_room_id = (
            f"vl{vehicle_id[1]}"  # Room for vehicle-LLM communication
        )
        self.llm2llm_room_id = f"l{vehicle_id[1]}"  # Room for LLM-to-LLM communication

        self.neighbor_range = (
            50.0  # Maximum distance to consider vehicles as neighbors (in km)
        )

    def distance_to(self, other_vehicle: "Vehicle") -> float:
        """Calculate distance to another vehicle in kilometers using Haversine formula."""
        lat1, lon1 = map(math.radians, self.location)
        lat2, lon2 = map(math.radians, other_vehicle.location)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return 6371 * c  # Earth's radius in km

    def get_neighbor_rooms(self) -> list[str]:
        """Get rooms of neighboring vehicles based on distance."""
        if not self.simulator:
            return []

        neighbor_rooms = []
        for other_vehicle in self.simulator.vehicles.values():
            if (
                other_vehicle.id != self.id
                and self.distance_to(other_vehicle) <= self.neighbor_range
            ):
                neighbor_rooms.append(other_vehicle.v2v_room_id)
        return neighbor_rooms

    def update(self) -> None:
        """Update vehicle state with random changes."""
        # Update location with random movement
        lat, lon = self.location
        self.location = (
            lat + random.uniform(-2.0, 2.0),  # Increased movement range (4x faster)
            lon + random.uniform(-2.0, 2.0),  # Increased movement range (4x faster)
        )

        # More noticeable speed changes
        self.speed = max(0, min(120, self.speed + random.uniform(-10, 10)))
        self.battery = max(
            0, self.battery - random.uniform(0.1, 1.0)
        )  # Faster battery drain
        if random.random() < 0.1:  # 10% chance to change status
            self.status = random.choice(["moving", "idle", "charging"])

    def get_status_description(self) -> str:
        """Get human-readable status description."""
        return {
            "moving": "is currently in motion",
            "idle": "is stationary",
            "charging": "is at a charging station",
        }[self.status]

    def to_message(self) -> dict:
        """Convert vehicle state to a structured message."""
        template = MessageTemplate(
            template="Vehicle {id} {status_desc} at coordinates ({lat:.2f}, {lon:.2f}). "
            "It's traveling at {speed:.1f} km/h with {battery:.1f}% battery remaining.",
            variables={
                "id": self.id,
                "status_desc": self.get_status_description(),
                "lat": self.location[0],
                "lon": self.location[1],
                "speed": self.speed,
                "battery": self.battery,
            },
            highlight_fields=["speed", "battery"],
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity_id": self.id,
            "room_id": self.v2v_room_id,
            "message": template.generate_message(),
            "message_type": MessageType.VEHICLE_UPDATE.value,
            "highlight_fields": template.get_highlight_fields(),
            "state": {
                "latitude": self.location[0],
                "longitude": self.location[1],
                "speed": self.speed,
                "battery": self.battery,
                "status": self.status,
            },
        }


class VehicleSimulator:
    """Manages multiple vehicles and their communication."""

    def __init__(self, num_vehicles: int = 3):
        """Initialize simulator with specified number of vehicles."""
        self.client = SwarmClient()
        self.vehicles = {}

        # Initialize rooms and entities using shared function
        db = self.client.get_db()
        try:
            # Don't force recreate - use existing resources if they exist
            create_simulation_resources(db, num_vehicles, force_recreate=False)
        finally:
            db.close()

        # Create vehicles
        for i in range(1, num_vehicles + 1):
            self.vehicles[f"v{i}"] = Vehicle(f"v{i}", simulator=self)

    async def run(self):
        """Run the simulation."""
        print("Starting vehicle simulation...")
        print(f"Simulating {len(self.vehicles)} vehicles")
        print("Press Ctrl+C to stop")

        while True:  # Outer loop for reconnection
            try:
                async with self.client:
                    while True:  # Inner loop for simulation
                        try:
                            for vehicle in self.vehicles.values():
                                try:
                                    # Update vehicle state
                                    vehicle.update()
                                    message = vehicle.to_message()

                                    # Get list of rooms to broadcast to
                                    broadcast_rooms = (
                                        [
                                            vehicle.v2v_room_id,  # Vehicle's own V2V room
                                            vehicle.veh2llm_room_id,  # Vehicle-to-LLM communication room
                                        ]
                                        + vehicle.get_neighbor_rooms()
                                    )  # Rooms of nearby vehicles

                                    # Broadcast to each relevant room
                                    for room_id in set(broadcast_rooms):
                                        await self.client.send_message(
                                            room_id=room_id,
                                            entity_id=vehicle.id,
                                            content=message["message"],
                                            message_type=message["message_type"],
                                            state=message["state"],
                                        )
                                        print(f"\n[{room_id}] {message['message']}")
                                        print(
                                            "State:",
                                            json.dumps(message["state"], indent=2),
                                        )
                                except Exception as e:
                                    print(f"Error updating vehicle {vehicle.id}: {e}")
                                    continue

                            # Wait before next update
                            await asyncio.sleep(1)

                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            if "Cannot connect to host" in str(e):
                                print(f"Connection lost: {e}")
                                raise  # Re-raise to trigger reconnection
                            else:
                                print(f"Error in simulation loop: {e}")
                                await asyncio.sleep(1)  # Brief pause before continuing

            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"Connection error: {e}")
                print("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)  # Wait before reconnecting
                continue  # Retry the connection


if __name__ == "__main__":
    try:
        asyncio.run(VehicleSimulator(num_vehicles=3).run())
    except KeyboardInterrupt:
        print("\nStopping simulation...")
