import asyncio
import random
from datetime import datetime
from decimal import Decimal
from typing import Dict

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.fastapi.models import Entity, Message, MessageType
from backend.fastapi.routers.websocket import ws_manager

from .utils.message_templates import MessageTemplate


def generate_random_coordinates():
    """Generate random latitude and longitude."""
    return (
        random.uniform(-90, 90),  # latitude
        random.uniform(-180, 180),  # longitude
    )


class Vehicle:
    """Simulates a vehicle with real-time state updates."""

    def __init__(self, vehicle_id: str):
        """Initialize vehicle with random starting values."""
        self.id = vehicle_id
        self.location = generate_random_coordinates()
        self.speed = random.uniform(0, 120)
        self.battery = random.uniform(20, 100)
        self.status = random.choice(["moving", "idle", "charging"])
        self.room_id = vehicle_id  # Each vehicle has its own room

    def update(self) -> None:
        """Update vehicle state with random changes."""
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
            "timestamp": datetime.now().isoformat(),
            "entity_id": self.id,
            "room_id": self.room_id,
            "message": template.generate_message(),
            "type": MessageType.VEHICLE_UPDATE.value,
            "highlight_fields": template.get_highlight_fields(),
            "state": {
                "latitude": self.location[0],
                "longitude": self.location[1],
                "speed": self.speed,
                "battery": self.battery,
                "status": self.status,
            },
        }


async def broadcast_to_room(message: dict, db: Session, room_id: str) -> None:
    """Broadcast message to specific room and store in database."""
    try:
        # Update entity status
        entity = db.query(Entity).filter(Entity.id == message["entity_id"]).first()
        if entity:
            entity.status = "online"
            entity.last_seen = datetime.utcnow()

        # Store message in database
        db_message = Message(
            entity_id=message["entity_id"],
            room_id=room_id,
            content=message["message"],
            timestamp=datetime.fromisoformat(message["timestamp"]),
            message_type=MessageType.VEHICLE_UPDATE,
            latitude=message["state"]["latitude"],
            longitude=message["state"]["longitude"],
            speed=message["state"]["speed"],
            battery=message["state"]["battery"],
            status=message["state"]["status"],
        )
        db.add(db_message)
        db.commit()

        # Convert message for JSON serialization and broadcast
        json_message = jsonable_encoder(message, custom_encoder={Decimal: float})
        await ws_manager.broadcast_message(json_message, room_id)
    except Exception as e:
        print(f"Error in broadcast_to_room: {e}")
        db.rollback()
        raise


async def vehicle_simulation(db: Session) -> None:
    """Main simulation loop for updating and broadcasting vehicle states."""
    while True:
        for vehicle in vehicles.values():
            vehicle.update()
            message = vehicle.to_message()
            await broadcast_to_room(message, db, vehicle.room_id)
        await asyncio.sleep(2)


# Initialize global variables
vehicles: Dict[str, Vehicle] = {}
