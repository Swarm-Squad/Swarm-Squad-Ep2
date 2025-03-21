from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from ..database import get_collection
from ..utils import ConnectionManager

router = APIRouter(tags=["realtime"])

# Create a connection manager instance
manager = ConnectionManager()


class RoomConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, rooms: List[str]):
        """Accept and store a new WebSocket connection with room subscriptions"""
        await websocket.accept()

        # Add connection to each room
        for room in rooms:
            if room not in self.active_connections:
                self.active_connections[room] = set()
            self.active_connections[room].add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection from all rooms"""
        for room in list(self.active_connections.keys()):
            if websocket in self.active_connections[room]:
                self.active_connections[room].remove(websocket)
                # Clean up empty rooms
                if not self.active_connections[room]:
                    del self.active_connections[room]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        await websocket.send_json(message)

    async def broadcast_to_room(self, message: dict, room: str):
        """Broadcast a message to all clients in a room"""
        if room in self.active_connections:
            disconnected_clients = set()
            for connection in self.active_connections[room]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Mark for removal if sending fails
                    disconnected_clients.add(connection)

            # Remove any disconnected clients
            for client in disconnected_clients:
                self.disconnect(client)


# Create a room connection manager instance
room_manager = RoomConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, rooms: str = Query(None)):
    """WebSocket endpoint for real-time updates with room support"""
    # Parse room list
    room_list = rooms.split(",") if rooms else []

    # Connect to all requested rooms
    await room_manager.connect(websocket, room_list)

    try:
        while True:
            data = await websocket.receive_json()

            # Check if message has a target room
            target_room = data.get("room_id")

            if target_room:
                # Broadcast to specific room
                await room_manager.broadcast_to_room(data, target_room)
            else:
                # Broadcast to all rooms this client is connected to
                for room in room_list:
                    await room_manager.broadcast_to_room(data, room)
    except WebSocketDisconnect:
        room_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        room_manager.disconnect(websocket)


@router.post("/messages/")
async def send_message(
    room_id: str = Body(...),
    entity_id: str = Body(...),
    content: str = Body(...),
    message_type: str = Body(...),
    timestamp: Optional[str] = Body(None),
    state: Optional[Dict] = Body(None),
):
    """
    Send a message to a room and store it in the database

    This endpoint:
    1. Adds the message to the appropriate collection
    2. Broadcasts the message to all clients in the specified room
    """
    try:
        message_data = {
            "timestamp": timestamp or datetime.now().isoformat(),
            "entity_id": entity_id,
            "room_id": room_id,
            "message": content,
            "message_type": message_type,
            "state": state or {},
        }

        # Determine which collection to update based on the entity_id prefix
        # v* for vehicles, l* for LLMs
        if entity_id.startswith("v"):
            collection = get_collection("vehicles")
        elif entity_id.startswith("l"):
            collection = get_collection("llms")
        else:
            raise HTTPException(status_code=400, detail="Invalid entity_id")

        # Store the message in the database
        await collection.update_one(
            {"_id": entity_id},
            {
                "$push": {
                    "messages": {
                        "timestamp": message_data["timestamp"],
                        "message": content,
                        "message_type": message_type,
                        "state": state or {},
                    }
                }
            },
            upsert=True,
        )

        # Also update the entity's status if it's in the state
        if state and "status" in state:
            await collection.update_one(
                {"_id": entity_id}, {"$set": {"status": state["status"]}}, upsert=True
            )

        # Broadcast to WebSocket clients
        await room_manager.broadcast_to_room(message_data, room_id)

        return {"status": "success", "message": "Message sent"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")
