from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class Message(Base):
    """Database model for vehicle messages."""

    __tablename__ = "messages"

    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String)  # 'vehicle_update' or future types

    # Vehicle state data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    battery = Column(Float, nullable=True)
    status = Column(String, nullable=True)  # 'moving', 'idle', 'charging'

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format for API responses."""
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "type": self.message_type,
            "state": {
                "location": [self.latitude, self.longitude],
                "speed": self.speed,
                "battery": self.battery,
                "status": self.status,
            },
        }
