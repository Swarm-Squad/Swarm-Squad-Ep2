from typing import List

from sqlalchemy.orm import Session

from backend.fastapi.database import get_db
from backend.fastapi.models import Room
from backend.fastapi.schemas import RoomCreate, RoomResponse
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room.id).first()
    if db_room:
        raise HTTPException(status_code=400, detail="Room already exists")

    db_room = Room(id=room.id, name=room.name, type=room.type)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, db: Session = Depends(get_db)):
    """Get a specific room by ID."""
    room = db.query(Room).filter(Room.id == room_id).first()
    return room.to_dict()


@router.get("/", response_model=List[RoomResponse])
async def get_rooms(db: Session = Depends(get_db)):
    """Get all rooms."""
    rooms = db.query(Room).all()
    return [room.to_dict() for room in rooms]


@router.delete("/{room_id}")
def delete_room(room_id: str, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    db.delete(db_room)
    db.commit()
    return {"message": "Room deleted successfully"}
