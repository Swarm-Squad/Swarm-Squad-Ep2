from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String, index=True)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_type = Column(String)  # 'vehicle_update' or future types

    # Additional vehicle state data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    battery = Column(Float, nullable=True)
    status = Column(String, nullable=True)  # 'moving', 'idle', 'charging'

    def to_dict(self):
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
