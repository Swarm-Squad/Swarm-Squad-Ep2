import math
from typing import List, Set, Tuple, Type, TypeVar

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastapi import WebSocket

T = TypeVar("T")


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections"""
        for connection in self.active_connections:
            await connection.send_json(message)


async def get_nearby_entities(
    session: AsyncSession,
    model: Type[T],
    x: float,
    y: float,
    radius: float = 100.0,  # Default radius in meters
    exclude_id: str = None,
) -> List[T]:
    """
    Get nearby entities based on their last known position within a radius.
    Uses Euclidean distance for simplicity, but could be updated to use
    proper geographic distance calculations if needed.

    Args:
        session: Database session
        model: SQLModel class to query
        x: X coordinate
        y: Y coordinate
        radius: Search radius in meters
        exclude_id: ID to exclude from results

    Returns:
        List of nearby entities
    """
    if not hasattr(model, "messages"):
        return []

    # Get all entities except the excluded one
    stmt = select(model).where(model.id != exclude_id if exclude_id else True)
    result = await session.execute(stmt)
    entities = result.scalars().all()

    # Filter entities by distance
    nearby = []
    for entity in entities:
        if entity.messages:
            last_msg = entity.messages[-1]
            distance = math.sqrt(
                (last_msg.position_x - x) ** 2 + (last_msg.position_y - y) ** 2
            )
            if distance <= radius:
                nearby.append(entity)

    return nearby


def format_vehicle_message(vehicle_id: str, message: str, position: dict) -> str:
    """Format vehicle message for natural language display"""
    return (
        f"Vehicle {vehicle_id} at position "
        f"({position.get('x', 0)}, {position.get('y', 0)}): {message}"
    )


def format_llm_message(llm_id: str, message: str, response: str) -> str:
    """Format LLM message for natural language display"""
    return f"Agent {llm_id} received: {message}\nResponse: {response}"


def calculate_distance(
    coord1: Tuple[float, float], coord2: Tuple[float, float]
) -> float:
    """
    Calculate the distance between two coordinates using the Haversine formula.
    Coordinates should be in (latitude, longitude) format.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance
