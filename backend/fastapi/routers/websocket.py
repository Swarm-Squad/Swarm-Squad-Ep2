import asyncio
from collections import defaultdict
from typing import Dict, Set

from sqlalchemy.orm import Session

from backend.fastapi.database import get_db
from backend.fastapi.models import Room
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class WebSocketManager:
    def __init__(self):
        self.room_clients: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.client_rooms: Dict[WebSocket, Set[str]] = defaultdict(set)
        self.on_first_client_connect = None
        self.heartbeat_interval = 30  # seconds
        self.client_heartbeats: Dict[WebSocket, float] = {}
        self._heartbeat_task = None

    async def start_heartbeat_checker(self):
        """Start the heartbeat checker if not already running."""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self.check_heartbeats())

    async def stop_heartbeat_checker(self):
        """Stop the heartbeat checker if running."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

    async def connect(self, websocket: WebSocket, room_ids: list[str]):
        await websocket.accept()

        # Add client to specified rooms
        for room_id in room_ids:
            self.room_clients[room_id].add(websocket)
            self.client_rooms[websocket].add(room_id)

        # Initialize heartbeat timestamp
        self.client_heartbeats[websocket] = asyncio.get_event_loop().time()

        # Start heartbeat checker if needed
        await self.start_heartbeat_checker()

        # Call the callback if this is the first client overall
        total_clients = sum(len(clients) for clients in self.room_clients.values())
        if total_clients == 1 and self.on_first_client_connect:
            await self.on_first_client_connect()

    def disconnect(self, websocket: WebSocket):
        # Remove client from all rooms
        for room_id in self.client_rooms[websocket]:
            self.room_clients[room_id].discard(websocket)
            if not self.room_clients[room_id]:
                del self.room_clients[room_id]
        del self.client_rooms[websocket]
        self.client_heartbeats.pop(websocket, None)

        # Stop heartbeat checker if no more clients
        if not self.client_rooms:
            asyncio.create_task(self.stop_heartbeat_checker())

    async def broadcast_message(self, message: dict, room_id: str):
        """Broadcast a message to all clients in a specific room."""
        disconnected_clients = set()

        for client in self.room_clients[room_id]:
            try:
                await client.send_json(message)
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected_clients.add(client)

        # Clean up disconnected clients
        for client in disconnected_clients:
            self.disconnect(client)

    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle messages from clients, including pings."""
        # Update heartbeat timestamp
        self.client_heartbeats[websocket] = asyncio.get_event_loop().time()

        if message == "ping":
            try:
                await websocket.send_text("pong")
            except Exception as e:
                print(f"Error sending pong: {e}")
                self.disconnect(websocket)

    async def check_heartbeats(self):
        """Check for stale connections and disconnect them."""
        while True:
            try:
                current_time = asyncio.get_event_loop().time()
                stale_clients = set()

                # Find clients that haven't sent a heartbeat recently
                for client, last_heartbeat in self.client_heartbeats.items():
                    if current_time - last_heartbeat > self.heartbeat_interval * 2:
                        print("Client heartbeat timeout, disconnecting")
                        stale_clients.add(client)

                # Disconnect stale clients
                for client in stale_clients:
                    try:
                        await client.close()
                    except Exception:
                        pass
                    self.disconnect(client)

            except Exception as e:
                print(f"Error checking heartbeats: {e}")

            await asyncio.sleep(self.heartbeat_interval)


# Create a global WebSocket manager instance
ws_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    rooms: str = Query(..., description="Comma-separated list of room IDs to join"),
    db: Session = Depends(get_db),
):
    room_ids = [r.strip() for r in rooms.split(",") if r.strip()]

    # Validate rooms exist
    for room_id in room_ids:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await websocket.close(code=4004, reason=f"Room {room_id} not found")
            return

    try:
        await ws_manager.connect(websocket, room_ids)
        print(f"WebSocket connected to rooms: {room_ids}")

        try:
            while True:
                try:
                    # Keep connection alive and handle any client messages
                    data = await websocket.receive_text()
                    await ws_manager.handle_client_message(websocket, data)
                except WebSocketDisconnect:
                    print(f"WebSocket disconnected from rooms: {room_ids}")
                    ws_manager.disconnect(websocket)
                    break
                except Exception as e:
                    print(f"Error handling WebSocket message: {e}")
                    continue

        finally:
            ws_manager.disconnect(websocket)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected from rooms: {room_ids}")
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        ws_manager.disconnect(websocket)
