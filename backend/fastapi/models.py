from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import relationship

from backend.fastapi.database import Base


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


class Room(Base):
    """Room model for group communication."""

    __tablename__ = "rooms"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    name = Column(String)
    type = Column(String)

    # Relationships
    messages = relationship("Message", back_populates="room")
    entities = relationship("Entity", back_populates="room")

    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary format for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "messages": [message.to_dict() for message in self.messages],
        }


class Entity(Base):
    """Entity model for vehicles and agents."""

    __tablename__ = "entities"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    name = Column(String)
    type = Column(String)
    room_id = Column(String, ForeignKey("rooms.id"))
    status = Column(String, default="offline")
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    room = relationship("Room", back_populates="entities")
    messages = relationship("Message", back_populates="entity")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "room_id": self.room_id,
            "status": self.status,
            "last_seen": self.last_seen.isoformat(),
        }


class Message(Base):
    """Message model for communication."""

    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    room_id = Column(String, ForeignKey("rooms.id"))
    entity_id = Column(String, ForeignKey("entities.id"))
    content = Column(Text)
    message_type = Column(SQLAEnum(MessageType))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Vehicle state fields
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    battery = Column(Float, nullable=True)
    status = Column(String, nullable=True)

    # Relationships
    room = relationship("Room", back_populates="messages")
    entity = relationship("Entity", back_populates="messages")

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format for API responses."""
        # Always include state data if it exists
        state = {}
        if any(
            v is not None
            for v in [
                self.latitude,
                self.longitude,
                self.speed,
                self.battery,
                self.status,
            ]
        ):
            state = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "speed": self.speed,
                "battery": self.battery,
                "status": self.status,
            }

        return {
            "id": self.id,
            "room_id": self.room_id,
            "entity_id": self.entity_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type.value,
            "state": state,
        }
