from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from backend.fastapi.database import get_db
from backend.fastapi.models import Entity, Message, Room
from backend.fastapi.routers.websocket import ws_manager
from backend.fastapi.schemas import MessageCreate, MessageResponse
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
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
        timestamp=datetime.now(timezone.utc),
    )

    # If it's a vehicle update, add vehicle state
    if hasattr(message, "state"):
        db_message.latitude = message.state.get("latitude")
        db_message.longitude = message.state.get("longitude")
        db_message.speed = message.state.get("speed")
        db_message.battery = message.state.get("battery")
        db_message.status = message.state.get("status")

    # Add to database
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Broadcast the message to WebSocket clients in the room as a background task
    broadcast_data = {
        "timestamp": db_message.timestamp.isoformat(),
        "entity_id": message.entity_id,
        "message": message.content,
        "message_type": message.message_type,
        "state": message.state if hasattr(message, "state") else None,
    }

    # Schedule WebSocket broadcast as a background task
    background_tasks.add_task(
        ws_manager.broadcast_message, broadcast_data, message.room_id
    )

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
