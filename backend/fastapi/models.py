from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import relationship

from backend.fastapi.database import Base


class RoomType(str, Enum):
    VEHICLE = "vehicle"
    AGENT = "agent"
    VEH2LLM = "veh2llm"


class EntityType(str, Enum):
    VEHICLE = "vehicle"
    AGENT = "agent"


class MessageType(Enum):
    VEHICLE_UPDATE = "vehicle_update"
    AGENT_RESPONSE = "agent_response"
    AGENT_COORDINATION = "agent_coordination"


class Room(Base):
    """Database model for rooms."""

    __tablename__ = "rooms"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(SQLAEnum(RoomType), nullable=False)
    messages = relationship("Message", back_populates="room")


class Entity(Base):
    """Database model for vehicles and agents."""

    __tablename__ = "entities"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(SQLAEnum(EntityType), nullable=False)
    room_id = Column(String, ForeignKey("rooms.id"))
    status = Column(String, default="offline")  # online/offline
    last_seen = Column(DateTime, default=datetime.utcnow)
    messages = relationship("Message", back_populates="entity")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "room_id": self.room_id,
            "status": self.status,
            "last_seen": self.last_seen.isoformat(),
        }


class Message(Base):
    """Database model for all types of messages."""

    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)  # Primary key is automatically indexed
    room_id = Column(String, ForeignKey("rooms.id"))
    entity_id = Column(String, ForeignKey("entities.id"))
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_type = Column(SQLAEnum(MessageType))

    # Vehicle state data (for vehicle updates)
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
        base_dict = {
            "id": self.id,
            "room_id": self.room_id,
            "entity_id": self.entity_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "type": self.message_type.value,
        }

        # Include vehicle state data if this is a vehicle update
        if self.message_type == MessageType.VEHICLE_UPDATE:
            base_dict["state"] = {
                "location": [self.latitude, self.longitude],
                "speed": self.speed,
                "battery": self.battery,
                "status": self.status,
            }

        return base_dict
