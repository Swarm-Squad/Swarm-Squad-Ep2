from datetime import datetime
from typing import List

from database import get_db
from models import Entity, Message, Room
from schemas import MessageCreate, MessageResponse, MessageType
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse)
def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    # Validate room exists
    room = db.query(Room).filter(Room.id == message.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Validate entity exists
    entity = db.query(Entity).filter(Entity.id == message.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    db_message = Message(
        room_id=message.room_id,
        entity_id=message.entity_id,
        content=message.content,
        message_type=message.message_type,
        timestamp=datetime.utcnow(),
    )

    # If it's a vehicle update, add vehicle state
    if message.message_type == MessageType.VEHICLE_UPDATE and hasattr(message, "state"):
        db_message.latitude = message.state.location[0]
        db_message.longitude = message.state.location[1]
        db_message.speed = message.state.speed
        db_message.battery = message.state.battery
        db_message.status = message.state.status

    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


@router.get("/", response_model=List[MessageResponse])
def list_messages(
    room_id: str = None,
    entity_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Message).order_by(Message.timestamp.desc())

    if room_id:
        query = query.filter(Message.room_id == room_id)
    if entity_id:
        query = query.filter(Message.entity_id == entity_id)

    return query.limit(limit).all()


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.delete("/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
    return {"message": "Message deleted successfully"}
