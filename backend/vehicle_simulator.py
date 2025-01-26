import asyncio
import random
from datetime import datetime
from typing import Dict
from decimal import Decimal

import uvicorn
from faker import Faker
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager

from message_templates import MessageTemplate
from database import get_db
from models import Message
from websocket_server import WebSocketManager


# Simulate vehicle data
class Vehicle:
    def __init__(self, vehicle_id: str):
        self.id = vehicle_id
        self.location = (fake.latitude(), fake.longitude())
        self.speed = random.uniform(0, 120)
        self.battery = random.uniform(20, 100)
        self.status = random.choice(["moving", "idle", "charging"])

    def update(self):
        """Update vehicle state"""
        self.speed += random.uniform(-5, 5)
        self.speed = max(0, min(120, self.speed))
        self.battery -= random.uniform(0, 0.5)
        self.battery = max(0, self.battery)
        self.status = (
            random.choice(["moving", "idle", "charging"])
            if random.random() < 0.1
            else self.status
        )

    def get_status_description(self) -> str:
        return {
            "moving": "is currently in motion",
            "idle": "is stationary",
            "charging": "is at a charging station",
        }[self.status]

    def to_message(self) -> dict:
        """Convert vehicle state to a structured message using MessageTemplate"""
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
            "vehicle_id": self.id,
            "message": template.generate_message(),
            "type": "vehicle_update",
            "highlight_fields": template.get_highlight_fields(),
            "state": {
                "latitude": self.location[0],
                "longitude": self.location[1],
                "speed": self.speed,
                "battery": self.battery,
                "status": self.status,
            },
        }


# Initialize global variables
ws_manager = WebSocketManager()
fake = Faker()
vehicles: Dict[str, Vehicle] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize vehicles and setup simulation
    global vehicles
    vehicles = {f"V{i}": Vehicle(f"V{i}") for i in range(1, 4)}
    db = next(get_db())

    async def start_simulation():
        asyncio.create_task(vehicle_simulation(db))

    ws_manager.on_first_client_connect = start_simulation

    yield

    # Cleanup (if needed)
    vehicles.clear()


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


async def broadcast_to_clients(message: dict, db: Session):
    """Broadcast message to all connected clients and store in database"""
    # Store message in database
    db_message = Message(
        vehicle_id=message["vehicle_id"],
        content=message["message"],
        timestamp=datetime.fromisoformat(message["timestamp"]),
        message_type=message["type"],
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
    await ws_manager.broadcast_message(json_message)


async def vehicle_simulation(db: Session):
    """Main simulation loop"""
    while True:
        for vehicle in vehicles.values():
            vehicle.update()
            message = vehicle.to_message()
            await broadcast_to_clients(message, db)
        await asyncio.sleep(2)


@app.get("/messages")
async def get_messages(
    limit: int = 50, vehicle_id: str = None, db: Session = Depends(get_db)
):
    """Fetch historical messages with optional filtering"""
    query = db.query(Message).order_by(Message.timestamp.desc())

    if vehicle_id:
        query = query.filter(Message.vehicle_id == vehicle_id)

    messages = query.limit(limit).all()
    return jsonable_encoder(
        [message.to_dict() for message in messages], custom_encoder={Decimal: float}
    )


# Mount the WebSocket app at the root level
app.mount("", ws_manager.app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
