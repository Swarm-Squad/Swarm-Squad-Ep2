from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class RoomType(str, Enum):
    VEHICLE = "vehicle"  # For vehicle-to-vehicle communication
    VL = "vl"  # For vehicle-to-LLM communication
    LLM = "llm"  # For LLM-to-LLM communication


class EntityType(str, Enum):
    VEHICLE = "vehicle"  # For vehicles
    LLM = "llm"  # For LLM agents


class MessageType(str, Enum):
    VEHICLE_UPDATE = "vehicle_update"
    LLM_RESPONSE = "llm_response"
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
    room_id: str
    entity_id: str
    content: str
    message_type: str
    state: Dict[str, Any] = {}


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class VehicleState(BaseModel):
    latitude: float
    longitude: float
    speed: float
    battery: float
    status: str


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    timestamp: str
    type: str
    message: str
    entity_id: str
    room_id: str
    highlight_fields: Optional[List[str]] = None
    state: Dict[str, Any] = {}
