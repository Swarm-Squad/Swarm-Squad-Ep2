import asyncio
import json
import math
import random
from datetime import datetime, timezone

from swarm_squad_ep2.api.models import MessageType
from swarm_squad_ep2.scripts.utils.client import SwarmClient
from swarm_squad_ep2.scripts.utils.message_templates import MessageTemplate


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
        # Update location with smoother, smaller movements
        lat, lon = self.location
        self.location = (
            lat + random.uniform(-1.0, 1.0),  # Smaller, smoother movements
            lon + random.uniform(-1.0, 1.0),  # Smaller, smoother movements
        )

        # Smoother speed changes
        self.speed = max(
            0, min(120, self.speed + random.uniform(-5, 5))
        )  # Smaller speed changes
        self.battery = max(
            0, self.battery - random.uniform(0.05, 0.5)
        )  # Slower battery drain
        if random.random() < 0.05:  # 5% chance to change status (less frequent changes)
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

        # Create vehicles
        for i in range(1, num_vehicles + 1):
            self.vehicles[f"v{i}"] = Vehicle(f"v{i}", simulator=self)

    async def _update_vehicle(self, vehicle: Vehicle):
        """Update a single vehicle and send its messages concurrently."""
        try:
            # Update vehicle state
            vehicle.update()
            message = vehicle.to_message()

            # Get list of rooms to broadcast to
            broadcast_rooms = (
                [
                    vehicle.v2v_room_id,  # Vehicle's own V2V room
                    vehicle.veh2llm_room_id,  # Vehicle-to-LLM communication room
                    "master-vehicles",  # Master vehicle room for aggregation
                ]
                + vehicle.get_neighbor_rooms()
            )  # Rooms of nearby vehicles

            # Send messages to all rooms concurrently
            send_tasks = []
            for room_id in set(broadcast_rooms):
                task = self.client.send_message(
                    room_id=room_id,
                    entity_id=vehicle.id,
                    content=message["message"],
                    message_type=message["message_type"],
                    state=message["state"],
                )
                send_tasks.append(task)
            
            # Wait for all sends to complete
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                room_id = list(set(broadcast_rooms))[i]
                if isinstance(result, Exception):
                    print(f"Failed to send message for vehicle {vehicle.id} to room {room_id}: {result}")
                elif result:
                    print(f"\n[{room_id}] {message['message']}")
                    print("State:", json.dumps(message["state"], indent=2))
                else:
                    print(f"Failed to send message for vehicle {vehicle.id} to room {room_id}")
                    
        except Exception as e:
            print(f"Error updating vehicle {vehicle.id}: {e}")

    async def run(self):
        """Run the simulation."""
        print("Starting vehicle simulation...")
        print(f"Simulating {len(self.vehicles)} vehicles")
        print("Press Ctrl+C to stop")
        
        # Wait for the API to be ready before starting simulation
        import aiohttp
        max_wait = 30  # Wait up to 30 seconds
        wait_time = 0
        while wait_time < max_wait:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/") as response:
                        if response.status == 200:
                            print("✓ FastAPI server is ready")
                            break
            except Exception:
                print(f"Waiting for FastAPI server... ({wait_time}s)")
                await asyncio.sleep(2)
                wait_time += 2
        
        if wait_time >= max_wait:
            print("⚠ Warning: FastAPI server may not be ready, continuing anyway...")

        while True:  # Outer loop for reconnection
            try:
                async with self.client:
                    # Create initial LLM entities for each vehicle
                    print("Creating LLM entities...")
                    for vehicle_id in self.vehicles.keys():
                        llm_id = f"l{vehicle_id[1:]}"  # Convert v1 -> l1
                        await self.client.send_message(
                            room_id=llm_id,
                            entity_id=llm_id,
                            content=f"LLM {llm_id} initialized and ready for vehicle {vehicle_id}",
                            message_type="llm_response",
                            state={"status": "active", "vehicle_id": vehicle_id}
                        )
                        print(f"Created LLM entity: {llm_id}")
                    
                    while True:  # Inner loop for simulation
                        try:
                            # Process all vehicles concurrently
                            tasks = []
                            for vehicle in self.vehicles.values():
                                task = self._update_vehicle(vehicle)
                                tasks.append(task)
                            
                            # Execute all vehicle updates concurrently
                            await asyncio.gather(*tasks, return_exceptions=True)

                            # Wait before next update
                            await asyncio.sleep(0.25)  # Update 4x more frequently

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
        asyncio.run(VehicleSimulator(num_vehicles=10).run())
    except KeyboardInterrupt:
        print("\nStopping simulation...")
