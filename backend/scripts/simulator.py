import asyncio
import math
import os
import random
import sys
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.fastapi.models import Entity, EntityType, MessageType, Room, RoomType
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
            f"va{vehicle_id[1]}"  # Room for vehicle-agent communication
        )
        self.llm2llm_room_id = (
            f"a{vehicle_id[1]}"  # Room for agent-to-agent communication
        )

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
            lat + random.uniform(-0.01, 0.01),  # Small random movement
            lon + random.uniform(-0.01, 0.01),
        )

        self.speed = max(0, min(120, self.speed + random.uniform(-5, 5)))
        self.battery = max(0, self.battery - random.uniform(0, 0.5))
        if random.random() < 0.1:
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

        # First create all required rooms and entities
        self._initialize_rooms_and_entities(num_vehicles)

        # Create vehicles
        for i in range(1, num_vehicles + 1):
            self.vehicles[f"v{i}"] = Vehicle(f"v{i}", simulator=self)

    def _initialize_rooms_and_entities(self, num_vehicles: int):
        """Initialize rooms and entities for the simulation."""
        db = self.client.get_db()
        try:
            # Create rooms for each vehicle
            rooms = []

            # V2V rooms (one for each vehicle)
            for i in range(1, num_vehicles + 1):
                rooms.append(
                    Room(id=f"v{i}", name=f"Vehicle {i} Room", type=RoomType.VEHICLE)
                )

            # Vehicle-to-LLM rooms (one for each vehicle)
            for i in range(1, num_vehicles + 1):
                rooms.append(
                    Room(
                        id=f"va{i}",
                        name=f"Vehicle {i} to Agent Room",
                        type=RoomType.VEH2LLM,
                    )
                )

            # LLM-to-LLM rooms (one for each vehicle's agent)
            for i in range(1, num_vehicles + 1):
                rooms.append(
                    Room(id=f"a{i}", name=f"Agent {i} Room", type=RoomType.AGENT)
                )

            db.add_all(rooms)

            # Create entities
            entities = []
            # Create vehicle entities
            for i in range(1, num_vehicles + 1):
                entities.append(
                    Entity(
                        id=f"v{i}",
                        name=f"Vehicle {i}",
                        type=EntityType.VEHICLE,
                        room_id=f"v{i}",  # Each vehicle is associated with its V2V room
                        status="online",
                    )
                )

            # Create agent entities
            for i in range(1, num_vehicles + 1):
                entities.append(
                    Entity(
                        id=f"a{i}",
                        name=f"Agent {i}",
                        type=EntityType.AGENT,
                        room_id=f"a{i}",  # Each agent is associated with its LLM2LLM room
                        status="online",
                    )
                )

            db.add_all(entities)
            db.commit()
            print("Rooms and entities created successfully")

        except Exception as e:
            print(f"Error creating rooms and entities: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    async def run(self):
        """Run the simulation."""
        print("Starting vehicle simulation...")
        print(f"Simulating {len(self.vehicles)} vehicles")
        print("Press Ctrl+C to stop")

        async with self.client:
            while True:
                for vehicle in self.vehicles.values():
                    # Update vehicle state
                    vehicle.update()
                    message = vehicle.to_message()

                    # Get list of rooms to broadcast to
                    broadcast_rooms = [
                        vehicle.v2v_room_id,  # Vehicle's own V2V room
                        vehicle.veh2llm_room_id,  # Vehicle-to-LLM communication room
                    ] + vehicle.get_neighbor_rooms()  # Rooms of nearby vehicles

                    # Broadcast to each relevant room
                    for room_id in set(broadcast_rooms):
                        try:
                            await self.client.send_message(
                                room_id=room_id,
                                entity_id=vehicle.id,
                                content=message["message"],
                                message_type=message["message_type"],
                                state=message["state"],
                            )
                        except Exception as e:
                            print(f"Error sending message to room {room_id}: {e}")

                await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(VehicleSimulator(num_vehicles=3).run())
    except KeyboardInterrupt:
        print("\nStopping simulation...")
