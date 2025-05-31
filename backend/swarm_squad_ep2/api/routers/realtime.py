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

from swarm_squad_ep2.api.database import get_collection
from swarm_squad_ep2.api.utils import ConnectionManager

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


@router.get("/messages")
async def get_messages(
    room_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get messages from the database.

    If room_id is provided, get messages for that specific room.
    Otherwise, get recent messages from all entities.
    """
    try:
        vehicles_collection = get_collection("vehicles")
        llms_collection = get_collection("llms")

        if vehicles_collection is None or llms_collection is None:
            raise HTTPException(
                status_code=500, detail="Database collections not available"
            )

        all_messages = []

        if room_id:
            # Get messages for specific room/entity
            if room_id.startswith("v"):
                # Vehicle room
                entity_id = room_id.replace(
                    "vl", "v"
                )  # Handle both 'v1' and 'vl1' formats
                collection = vehicles_collection
            elif room_id.startswith("l"):
                # LLM room
                entity_id = room_id
                collection = llms_collection
            else:
                raise HTTPException(status_code=400, detail="Invalid room_id format")

            entity = await collection.find_one({"_id": entity_id})
            if entity and entity.get("messages"):
                for msg in entity["messages"][-limit:]:
                    all_messages.append(
                        {
                            "id": f"{entity_id}-{msg.get('timestamp', '')}",
                            "room_id": room_id,
                            "entity_id": entity_id,
                            "content": msg.get("message", ""),
                            "timestamp": msg.get("timestamp", ""),
                            "message_type": msg.get("message_type", "update"),
                            "state": msg.get("state", {}),
                        }
                    )
        else:
            # Get recent messages from all entities
            async for vehicle in vehicles_collection.find():
                if vehicle.get("messages"):
                    for msg in vehicle["messages"][-5:]:  # Last 5 from each vehicle
                        all_messages.append(
                            {
                                "id": f"{vehicle['_id']}-{msg.get('timestamp', '')}",
                                "room_id": vehicle["_id"],
                                "entity_id": vehicle["_id"],
                                "content": msg.get("message", ""),
                                "timestamp": msg.get("timestamp", ""),
                                "message_type": msg.get(
                                    "message_type", "vehicle_update"
                                ),
                                "state": msg.get("state", {}),
                            }
                        )

            async for llm in llms_collection.find():
                if llm.get("messages"):
                    for msg in llm["messages"][-5:]:  # Last 5 from each LLM
                        all_messages.append(
                            {
                                "id": f"{llm['_id']}-{msg.get('timestamp', '')}",
                                "room_id": llm["_id"],
                                "entity_id": llm["_id"],
                                "content": msg.get("message", ""),
                                "timestamp": msg.get("timestamp", ""),
                                "message_type": msg.get("message_type", "llm_response"),
                                "state": msg.get("state", {}),
                            }
                        )

        # Sort by timestamp and limit results
        all_messages.sort(key=lambda x: x["timestamp"] or "", reverse=True)
        return all_messages[:limit]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching messages: {str(e)}"
        )


@router.get("/rooms")
async def get_rooms():
    """Get available rooms/entities."""
    try:
        vehicles_collection = get_collection("vehicles")
        llms_collection = get_collection("llms")

        if vehicles_collection is None or llms_collection is None:
            raise HTTPException(
                status_code=500, detail="Database collections not available"
            )

        rooms = []

        # Add vehicle rooms
        async for vehicle in vehicles_collection.find():
            rooms.append(
                {
                    "id": vehicle["_id"],
                    "name": f"Vehicle {vehicle['_id']}",
                    "type": "vehicle",
                    "messages": [],
                }
            )

        # Add LLM rooms
        async for llm in llms_collection.find():
            rooms.append(
                {
                    "id": llm["_id"],
                    "name": f"LLM {llm['_id']}",
                    "type": "llm",
                    "messages": [],
                }
            )

        return rooms

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rooms: {str(e)}")


@router.get("/entities")
async def get_entities(room_id: Optional[str] = Query(None)):
    """Get entities, optionally filtered by room."""
    try:
        vehicles_collection = get_collection("vehicles")
        llms_collection = get_collection("llms")

        if vehicles_collection is None or llms_collection is None:
            raise HTTPException(
                status_code=500, detail="Database collections not available"
            )

        entities = []

        # Add vehicles
        async for vehicle in vehicles_collection.find():
            if not room_id or vehicle["_id"] == room_id:
                entities.append(
                    {
                        "id": vehicle["_id"],
                        "name": f"Vehicle {vehicle['_id']}",
                        "type": "vehicle",
                        "room_id": vehicle["_id"],
                        "status": vehicle.get("status", "unknown"),
                        "last_seen": vehicle.get("last_seen", ""),
                    }
                )

        # Add LLMs
        async for llm in llms_collection.find():
            if not room_id or llm["_id"] == room_id:
                entities.append(
                    {
                        "id": llm["_id"],
                        "name": f"LLM {llm['_id']}",
                        "type": "llm",
                        "room_id": llm["_id"],
                        "status": llm.get("status", "unknown"),
                        "last_seen": llm.get("last_seen", ""),
                    }
                )

        return entities

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching entities: {str(e)}"
        )


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
