import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aiohttp
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.fastapi.models import Base

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
    """Base client for connecting to the Swarm Squad Dialouge server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client with server URL."""
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.heartbeat_interval = 25  # seconds (less than server's 30s)
        self.ws_timeout = 60  # seconds

        # Setup database connection
        self.SessionLocal = SessionLocal

    def get_db(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    async def connect(self):
        """Create aiohttp session with retries."""
        if not self.session:
            retries = 0
            while retries < self.max_retries:
                try:
                    self.session = aiohttp.ClientSession()
                    # Test the connection
                    async with self.session.get(self.base_url) as response:
                        if response.status == 200:
                            return
                    print("Failed to connect to server, retrying...")
                except Exception as e:
                    print(f"Connection error: {e}")
                    if self.session:
                        await self.session.close()
                        self.session = None
                retries += 1
                await asyncio.sleep(self.retry_delay)
            raise ConnectionError("Failed to connect to server after maximum retries")

    async def disconnect(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def send_heartbeat(self, ws: aiohttp.ClientWebSocketResponse):
        """Send periodic heartbeat to keep the connection alive."""
        try:
            await ws.send_str("ping")
            msg = await ws.receive()  # Use receive() instead of receive_text()
            if msg.type == aiohttp.WSMsgType.TEXT and msg.data == "pong":
                return True
            print("Invalid heartbeat response")
            return False
        except Exception as e:
            print(f"Heartbeat error: {e}")
            return False

    async def send_message(
        self,
        room_id: str,
        entity_id: str,
        content: str,
        message_type: str,
        state: Dict[str, Any] = None,
    ):
        """Send a message to a room with retries."""
        if not self.session:
            await self.connect()

        message_data = {
            "room_id": room_id,
            "entity_id": entity_id,
            "content": content,
            "message_type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state if state is not None else {},
        }

        retries = 0
        while retries < self.max_retries:
            try:
                print(f"Sending message to {room_id}: {content}")
                async with self.session.post(
                    f"{self.base_url}/messages/", json=message_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"Response from server: {result}")
                        return result
                    else:
                        print(f"Server error: {response.status}")
            except Exception as e:
                print(f"Error sending message: {e}")
                await asyncio.sleep(self.retry_delay)
            retries += 1
            if retries < self.max_retries:
                print(f"Retrying... ({retries}/{self.max_retries})")
                # Reconnect the session
                await self.disconnect()
                await self.connect()

        raise ConnectionError("Failed to send message after maximum retries")

    async def subscribe_to_room(self, room_id: str, callback):
        """Subscribe to WebSocket updates from a room with automatic reconnection."""
        while True:  # Keep trying to reconnect
            try:
                if not self.session:
                    await self.connect()

                async with self.session.ws_connect(
                    f"{self.ws_url}/ws?rooms={room_id}",
                    heartbeat=self.heartbeat_interval,
                    timeout=self.ws_timeout,
                    receive_timeout=self.ws_timeout,
                ) as ws:
                    print(f"Connected to room: {room_id}")

                    # Create a lock for receive operations
                    receive_lock = asyncio.Lock()

                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(
                        self._heartbeat_loop(ws, receive_lock)
                    )

                    try:
                        while True:  # Keep receiving messages
                            try:
                                async with receive_lock:
                                    msg = await ws.receive()

                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    if (
                                        msg.data == "pong"
                                    ):  # Skip processing pong responses
                                        continue
                                    try:
                                        data = json.loads(msg.data)
                                        await callback(data)
                                    except json.JSONDecodeError:
                                        continue  # Skip non-JSON messages
                                    except Exception as e:
                                        print(
                                            f"Error processing message in {room_id}: {e}"
                                        )
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    print(
                                        f"WebSocket error in room {room_id}: {ws.exception()}"
                                    )
                                    break
                                elif msg.type == aiohttp.WSMsgType.CLOSED:
                                    print(f"WebSocket closed for room {room_id}")
                                    break
                            except asyncio.CancelledError:
                                raise
                            except Exception as e:
                                print(f"Error receiving message in {room_id}: {e}")
                                if "Connection reset by peer" in str(e):
                                    break
                                await asyncio.sleep(0.1)  # Brief pause before retry
                    finally:
                        # Cancel heartbeat task
                        heartbeat_task.cancel()
                        try:
                            await heartbeat_task
                        except asyncio.CancelledError:
                            pass

            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"Connection error for {room_id}: {e}")
                await asyncio.sleep(self.retry_delay)
                continue  # Try to reconnect

    async def _heartbeat_loop(
        self, ws: aiohttp.ClientWebSocketResponse, receive_lock: asyncio.Lock
    ):
        """Maintain heartbeat for WebSocket connection."""
        try:
            while True:
                try:
                    await asyncio.sleep(self.heartbeat_interval)
                    await ws.send_str("ping")
                    async with receive_lock:
                        msg = await ws.receive()
                        if msg.type != aiohttp.WSMsgType.TEXT or msg.data != "pong":
                            print("Invalid heartbeat response")
                            await ws.close()
                            break
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                    try:
                        await ws.close()
                    except Exception:  # Catch any errors during close
                        pass
                    break
        except asyncio.CancelledError:
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
