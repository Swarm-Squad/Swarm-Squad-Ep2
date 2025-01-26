import asyncio
import random
from datetime import datetime
from typing import Dict
from decimal import Decimal
import os

import uvicorn
from faker import Faker
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager

from message_templates import MessageTemplate
from database import get_db, engine, Base, SessionLocal
from models import Message
from websocket_server import WebSocketManager


def initialize_database() -> None:
    """Initialize the database if it doesn't exist."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_sim.db")
    db_exists = os.path.exists(db_path)

    if not db_exists:
        print("Database does not exist. Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    else:
        print("Database already exists, skipping table creation")


class Vehicle:
    """Simulates a vehicle with real-time state updates."""

    def __init__(self, vehicle_id: str):
        """Initialize vehicle with random starting values."""
        self.id = vehicle_id
        self.location = (fake.latitude(), fake.longitude())
        self.speed = random.uniform(0, 120)
        self.battery = random.uniform(20, 100)
        self.status = random.choice(["moving", "idle", "charging"])

    def update(self) -> None:
        """Update vehicle state with random changes."""
        # Update speed within bounds
        self.speed = max(0, min(120, self.speed + random.uniform(-5, 5)))

        # Decrease battery level
        self.battery = max(0, self.battery - random.uniform(0, 0.5))

        # Occasionally change status
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


async def broadcast_to_clients(message: dict, db: Session) -> None:
    """Broadcast message to all connected clients and store in database."""
    try:
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
    except Exception as e:
        print(f"Error in broadcast_to_clients: {e}")
        db.rollback()
        raise


async def vehicle_simulation(db: Session) -> None:
    """Main simulation loop for updating and broadcasting vehicle states."""
    while True:
        for vehicle in vehicles.values():
            vehicle.update()
            message = vehicle.to_message()
            await broadcast_to_clients(message, db)
        await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Initialize database only if needed
    initialize_database()

    # Create database session
    db = SessionLocal()

    try:
        # Initialize vehicles
        global vehicles
        vehicles = {f"V{i}": Vehicle(f"V{i}") for i in range(1, 4)}

        # Set up simulation to start on first client connection
        async def start_simulation():
            asyncio.create_task(vehicle_simulation(db))

        ws_manager.on_first_client_connect = start_simulation

        yield
    finally:
        # Cleanup
        db.close()
        vehicles.clear()


# Initialize global variables
fake = Faker()
ws_manager = WebSocketManager()
vehicles: Dict[str, Vehicle] = {}

# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/messages")
async def get_messages(
    limit: int = 50, vehicle_id: str = None, db: Session = Depends(get_db)
) -> list:
    """Fetch historical messages with optional filtering."""
    query = db.query(Message).order_by(Message.timestamp.desc())

    if vehicle_id:
        query = query.filter(Message.vehicle_id == vehicle_id)

    messages = query.limit(limit).all()
    return jsonable_encoder(
        [message.to_dict() for message in messages], custom_encoder={Decimal: float}
    )


# Mount the WebSocket app
app.mount("", ws_manager.app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
