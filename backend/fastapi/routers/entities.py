from datetime import datetime
from typing import List

from database import get_db
from models import Entity
from schemas import EntityCreate, EntityResponse, EntityUpdate
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/", response_model=EntityResponse)
def create_entity(entity: EntityCreate, db: Session = Depends(get_db)):
    # Check if entity already exists
    db_entity = db.query(Entity).filter(Entity.id == entity.id).first()
    if db_entity:
        raise HTTPException(status_code=400, detail="Entity already exists")

    # Check if room exists
    db_room = db.query(Entity).filter(Entity.id == entity.room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    db_entity = Entity(
        id=entity.id,
        name=entity.name,
        type=entity.type,
        room_id=entity.room_id,
        status="offline",
        last_seen=datetime.utcnow(),
    )
    db.add(db_entity)
    db.commit()
    db.refresh(db_entity)
    return db_entity


@router.get("/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: str, db: Session = Depends(get_db)):
    db_entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db_entity


@router.get("/", response_model=List[EntityResponse])
def list_entities(db: Session = Depends(get_db)):
    return db.query(Entity).all()


@router.patch("/{entity_id}", response_model=EntityResponse)
def update_entity(
    entity_id: str, entity_update: EntityUpdate, db: Session = Depends(get_db)
):
    db_entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if entity_update.status is not None:
        db_entity.status = entity_update.status
    if entity_update.last_seen is not None:
        db_entity.last_seen = entity_update.last_seen

    db.commit()
    db.refresh(db_entity)
    return db_entity


@router.delete("/{entity_id}")
def delete_entity(entity_id: str, db: Session = Depends(get_db)):
    db_entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    db.delete(db_entity)
    db.commit()
    return {"message": "Entity deleted successfully"}
