import os
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

# Add the parent directory to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uvicorn
from sqlalchemy.orm import Session

from backend.fastapi.database import Base, SessionLocal, engine, get_db
from backend.fastapi.models import Entity, EntityType, Message, Room, RoomType
from backend.fastapi.routers import entities, messages, rooms, websocket
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)

# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

# Create templates instance
templates = Jinja2Templates(directory=templates_dir)


def create_simulation_resources(
    db: Session,
    num_vehicles: int,
    room_types: Optional[List[RoomType]] = None,
    entity_types: Optional[List[EntityType]] = None,
    force_recreate: bool = False,
) -> None:
    """Create rooms and entities for simulation."""
    try:
        # Check if resources already exist
        existing_rooms = db.query(Room).count()
        existing_entities = db.query(Entity).count()

        if existing_rooms > 0 or existing_entities > 0:
            if force_recreate:
                # Delete existing resources
                db.query(Entity).delete()
                db.query(Room).delete()
                db.commit()
                print("Deleted existing resources")
            else:
                print("Resources already exist, skipping creation")
                return

        # Use all room types if none specified
        if room_types is None:
            room_types = [RoomType.VEHICLE, RoomType.VL, RoomType.LLM]

        # Use all entity types if none specified
        if entity_types is None:
            entity_types = [EntityType.VEHICLE, EntityType.LLM]

        rooms = []
        entities = []

        # Create rooms based on specified types
        for i in range(1, num_vehicles + 1):
            if RoomType.VEHICLE in room_types:
                rooms.append(
                    Room(id=f"v{i}", name=f"Vehicle {i} Room", type=RoomType.VEHICLE)
                )
            if RoomType.VL in room_types:
                rooms.append(
                    Room(
                        id=f"vl{i}",
                        name=f"Vehicle {i} to Agent Room",
                        type=RoomType.VL,
                    )
                )
            if RoomType.LLM in room_types:
                rooms.append(
                    Room(
                        id=f"l{i}",
                        name=f"Agent {i} Room",
                        type=RoomType.LLM,
                    )
                )

        # Create entities based on specified types
        for i in range(1, num_vehicles + 1):
            if EntityType.VEHICLE in entity_types:
                entities.append(
                    Entity(
                        id=f"v{i}",
                        name=f"Vehicle {i}",
                        type=EntityType.VEHICLE,
                        room_id=f"v{i}",
                        status="online",
                    )
                )
            if EntityType.LLM in entity_types:
                entities.append(
                    Entity(
                        id=f"l{i}",
                        name=f"Agent {i}",
                        type=EntityType.LLM,
                        room_id=f"l{i}",
                        status="online",
                    )
                )

        if rooms:
            db.add_all(rooms)
        if entities:
            db.add_all(entities)

        db.commit()
        print(f"Created {len(rooms)} rooms and {len(entities)} entities")

    except Exception as e:
        print(f"Error creating simulation resources: {e}")
        db.rollback()
        raise


def initialize_database(num_vehicles: int = 3) -> None:
    """Initialize the database by creating tables and basic resources."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_sim.db")

    # Always recreate tables
    if os.path.exists(db_path):
        os.remove(db_path)

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Create initial resources with force_recreate=True since we just created the tables
    db = SessionLocal()
    try:
        create_simulation_resources(db, num_vehicles, force_recreate=True)
        print("Database initialized successfully")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    initialize_database()
    db = SessionLocal()

    try:
        yield
    finally:
        # Update all entities to offline status
        for entity in db.query(Entity).all():
            entity.status = "offline"
        db.commit()
        db.close()


# Create FastAPI app
app = FastAPI(
    title="Swarm Squad: The Digital Dialogue",
    description="API for managing rooms, messages, vehicles, and agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon.ico from static directory."""
    return StaticFiles(directory=static_dir).get_response("favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Root endpoint displaying simulation overview."""
    rooms = db.query(Room).all()
    entities = db.query(Entity).all()
    messages = db.query(Message).order_by(Message.timestamp.desc()).limit(10).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rooms": rooms,
            "entities": entities,
            "messages": messages,
        },
    )


# Include routers
app.include_router(rooms.router)
app.include_router(entities.router)
app.include_router(messages.router)
app.include_router(websocket.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["."])
