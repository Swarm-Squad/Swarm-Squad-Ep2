import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aiohttp
from backend.fastapi.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Get the project root directory
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
db_path = os.path.join(project_root, "backend", "fastapi", "vehicle_sim.db")

# Create the engine with the correct database path
engine = create_engine(f"sqlite:///{db_path}", echo=False)

# Create tables and session
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SwarmClient:
    """Base client for connecting to the Swarm Squad server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client with server URL."""
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.session: Optional[aiohttp.ClientSession] = None

        # Setup database connection
        self.SessionLocal = SessionLocal

    def get_db(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    async def connect(self):
        """Create aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def disconnect(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def send_message(
        self,
        room_id: str,
        entity_id: str,
        content: str,
        message_type: str,
        state: Dict[str, Any] = None,
    ):
        """Send a message to a room."""
        if not self.session:
            await self.connect()

        message_data = {
            "room_id": room_id,
            "entity_id": entity_id,
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state
            if state is not None
            else {},  # Ensure state is always a dict
        }

        print(f"Sending message to {room_id}: {content}")
        async with self.session.post(
            f"{self.base_url}/messages/", json=message_data
        ) as response:
            result = await response.json()
            print(f"Response from server: {result}")
            return result

    async def subscribe_to_room(self, room_id: str, callback):
        """Subscribe to WebSocket updates from a room."""
        if not self.session:
            await self.connect()

        async with self.session.ws_connect(f"{self.ws_url}/ws?rooms={room_id}") as ws:
            print(f"Connected to room: {room_id}")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        print(f"Received message in {room_id}: {msg.data}")
                        await callback(data)
                    except Exception as e:
                        print(f"Error processing message in {room_id}: {e}")
                        print(f"Raw message: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"WebSocket error in room {room_id}: {ws.exception()}")
                    break

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
