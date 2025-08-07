from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# Message type enum for categorizing messages
class MessageType(str, Enum):
    VEHICLE_UPDATE = "vehicle_update"
    LLM_RESPONSE = "llm_response"
    SYSTEM_NOTIFICATION = "system_notification"
    VEHICLE_ALERT = "vehicle_alert"
    NETWORK_STATUS = "network_status"


class Position(BaseModel):
    coordinates: Tuple[float, float, float]  # (latitude, longitude, altitude)
    radius: float = 100.0  # radius in meters to determine nearby entities


class VehicleState(BaseModel):
    """Comprehensive vehicle state data"""

    position: Position
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (vx, vy, vz) in m/s
    acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (ax, ay, az) in m/s²
    battery_status: float = Field(ge=0, le=100)  # battery percentage
    communication_quality: float = Field(ge=0, le=100)  # signal strength percentage
    status: str = "idle"  # vehicle operational status
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    custom_data: Dict[str, Any] = {}  # for any additional sensor/state data


class VehicleMessage(BaseModel):
    message: str
    timestamp: Optional[float] = None
    nearby_vehicles: List[str] = []
    state: Optional[VehicleState] = None  # Include vehicle state with messages


class LLMMessage(BaseModel):
    message: str
    timestamp: Optional[float] = None
    nearby_llms: List[str] = []


class VehicleAgent(BaseModel):
    _id: str
    state: Optional[VehicleState] = None  # Current vehicle state
    llm_id: Optional[str] = None
    messages: List[VehicleMessage] = []


class LLMAgent(BaseModel):
    _id: str
    vehicle_id: Optional[str] = None
    messages: List[LLMMessage] = []


class VehicleLLMMapping(BaseModel):
    vehicle_id: str
    llm_id: str


# Response Models for Batch Operations
class NearbyVehicle(BaseModel):
    vehicle_id: str
    distance: float
    state: Optional[VehicleState] = None


class BatchStateResponse(BaseModel):
    states: Dict[str, VehicleState]
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())


class BatchMessageResponse(BaseModel):
    messages: Dict[str, List[VehicleMessage]]
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
