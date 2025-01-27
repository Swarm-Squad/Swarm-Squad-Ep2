from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class RoomType(str, Enum):
    VEHICLE = "vehicle"
    AGENT = "agent"
    VEH2LLM = "veh2llm"


class EntityType(str, Enum):
    VEHICLE = "vehicle"
    AGENT = "agent"


class MessageType(str, Enum):
    VEHICLE_UPDATE = "vehicle_update"
    AGENT_RESPONSE = "agent_response"
    AGENT_COORDINATION = "agent_coordination"


# Room Schemas
class RoomBase(BaseModel):
    name: str
    type: RoomType


class RoomCreate(RoomBase):
    id: str  # We want to specify room IDs


class RoomResponse(RoomBase):
    id: str
    messages: List = []

    model_config = ConfigDict(from_attributes=True)


# Entity Schemas
class EntityBase(BaseModel):
    name: str
    type: EntityType
    room_id: str


class EntityCreate(EntityBase):
    id: str


class EntityUpdate(BaseModel):
    status: Optional[str] = None
    last_seen: Optional[datetime] = None


class EntityResponse(EntityBase):
    id: str
    status: str
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


# Message Schemas
class MessageBase(BaseModel):
    content: str
    room_id: str
    entity_id: str
    message_type: MessageType


class MessageCreate(MessageBase):
    pass


class VehicleState(BaseModel):
    location: List[float]
    speed: float
    battery: float
    status: str


class MessageResponse(MessageBase):
    id: int
    timestamp: datetime
    state: Optional[VehicleState] = None

    model_config = ConfigDict(from_attributes=True)


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    timestamp: str
    type: str
    message: str
    entity_id: str
    room_id: str
    highlight_fields: Optional[List[str]] = None
    state: Optional[Dict[str, Any]] = None
