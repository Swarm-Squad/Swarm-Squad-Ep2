from collections import defaultdict
from typing import Dict, Set

from database import get_db
from models import Room
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class WebSocketManager:
    def __init__(self):
        self.room_clients: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.client_rooms: Dict[WebSocket, Set[str]] = defaultdict(set)
        self.on_first_client_connect = None

    async def connect(self, websocket: WebSocket, room_ids: list[str]):
        await websocket.accept()

        # Add client to specified rooms
        for room_id in room_ids:
            self.room_clients[room_id].add(websocket)
            self.client_rooms[websocket].add(room_id)

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

        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            print(f"Received message from client: {data}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        ws_manager.disconnect(websocket)
