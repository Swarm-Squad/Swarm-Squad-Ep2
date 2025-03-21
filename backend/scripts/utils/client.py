import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

import aiohttp
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.fastapi.models import Base

# Configure logging
logger = logging.getLogger(__name__)

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
    """Client for connecting to the Swarm Squad API and WebSocket services."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client with server URL and connection settings.

        Args:
            base_url: Base URL of the FastAPI server
        """
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.session: Optional[aiohttp.ClientSession] = None

        # Connection settings
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.heartbeat_interval = 25  # seconds (less than server's 30s)
        self.ws_timeout = 60  # seconds

        # Setup database connection
        self.SessionLocal = SessionLocal

    def get_db(self) -> Session:
        """
        Get a database session.

        Returns:
            SQLAlchemy session object
        """
        return self.SessionLocal()

    async def connect(self) -> bool:
        """
        Create aiohttp session with retries.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not self.session:
            retries = 0
            while retries < self.max_retries:
                try:
                    self.session = aiohttp.ClientSession()
                    # Test the connection
                    async with self.session.get(
                        self.base_url, timeout=self.ws_timeout
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Connected to server at {self.base_url}")
                            return True
                    logger.warning("Failed to connect to server, retrying...")
                except Exception as e:
                    logger.error(f"Connection error: {e}")
                    if self.session:
                        await self.session.close()
                        self.session = None
                retries += 1
                await asyncio.sleep(self.retry_delay)
            logger.error("Failed to connect to server after maximum retries")
            return False
        return True

    async def disconnect(self) -> None:
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Disconnected from server")

    async def send_heartbeat(self, ws: aiohttp.ClientWebSocketResponse) -> bool:
        """
        Send periodic heartbeat to keep the connection alive.

        Args:
            ws: WebSocket connection to send heartbeat on

        Returns:
            bool: True if heartbeat was successful, False otherwise
        """
        try:
            await ws.send_str("ping")
            msg = await ws.receive()
            if msg.type == aiohttp.WSMsgType.TEXT and msg.data == "pong":
                return True
            logger.warning("Invalid heartbeat response")
            return False
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False

    async def send_message(
        self,
        room_id: str,
        entity_id: str,
        content: str,
        message_type: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to a room with automatic retries.

        Args:
            room_id: Target room identifier
            entity_id: Source entity identifier
            content: Message content
            message_type: Type of message
            state: Optional state data to include

        Returns:
            Dict with server response or None if sending failed
        """
        if not self.session:
            connected = await self.connect()
            if not connected:
                logger.error("Cannot send message - not connected to server")
                return None

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
                logger.debug(f"Sending message to {room_id}: {content}")
                async with self.session.post(
                    f"{self.base_url}/messages/",
                    json=message_data,
                    timeout=self.ws_timeout,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"Response from server: {result}")
                        return result
                    else:
                        logger.warning(f"Server error: {response.status}")
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                await asyncio.sleep(self.retry_delay)

            retries += 1
            if retries < self.max_retries:
                logger.info(f"Retrying... ({retries}/{self.max_retries})")
                # Reconnect the session
                await self.disconnect()
                if not await self.connect():
                    return None

        logger.error("Failed to send message after maximum retries")
        return None

    async def subscribe_to_room(
        self, room_id: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Subscribe to WebSocket updates from a room with automatic reconnection.

        Args:
            room_id: Room identifier to subscribe to
            callback: Async function to call with received messages
        """
        while True:  # Keep trying to reconnect
            try:
                if not self.session:
                    connected = await self.connect()
                    if not connected:
                        logger.error(
                            f"Cannot subscribe to {room_id} - not connected to server"
                        )
                        await asyncio.sleep(self.retry_delay * 2)
                        continue

                logger.info(f"Connecting to room: {room_id}")
                async with self.session.ws_connect(
                    f"{self.ws_url}/ws?rooms={room_id}",
                    heartbeat=self.heartbeat_interval,
                    timeout=self.ws_timeout,
                    receive_timeout=self.ws_timeout,
                ) as ws:
                    logger.info(f"Connected to room: {room_id}")

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
                                    if msg.data == "pong":  # Skip heartbeat responses
                                        continue
                                    try:
                                        data = json.loads(msg.data)
                                        await callback(data)
                                    except json.JSONDecodeError:
                                        logger.warning(
                                            f"Received invalid JSON: {msg.data[:50]}..."
                                        )
                                        continue
                                    except Exception as e:
                                        logger.error(
                                            f"Error processing message in {room_id}: {e}"
                                        )
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    logger.error(
                                        f"WebSocket error in {room_id}: {ws.exception()}"
                                    )
                                    break
                                elif msg.type == aiohttp.WSMsgType.CLOSED:
                                    logger.info(f"WebSocket closed for {room_id}")
                                    break
                            except asyncio.CancelledError:
                                raise
                            except Exception as e:
                                logger.error(
                                    f"Error receiving message in {room_id}: {e}"
                                )
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
                logger.error(f"Connection error for {room_id}: {e}")
                await asyncio.sleep(self.retry_delay)
                continue  # Try to reconnect

    async def _heartbeat_loop(
        self, ws: aiohttp.ClientWebSocketResponse, receive_lock: asyncio.Lock
    ) -> None:
        """
        Maintain heartbeat for WebSocket connection.

        Args:
            ws: WebSocket connection to maintain
            receive_lock: Lock to prevent heartbeat and message receipt conflicts
        """
        try:
            while True:
                try:
                    await asyncio.sleep(self.heartbeat_interval)
                    await ws.send_str("ping")
                    async with receive_lock:
                        msg = await ws.receive()
                        if msg.type != aiohttp.WSMsgType.TEXT or msg.data != "pong":
                            logger.warning("Invalid heartbeat response")
                            await ws.close()
                            break
                        logger.debug("Heartbeat successful")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    try:
                        await ws.close()
                    except Exception:
                        pass
                    break
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
