import os
import sys
from contextlib import asynccontextmanager

# Add the parent directory to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uvicorn

from backend.fastapi.database import Base, SessionLocal, engine
from backend.fastapi.models import Entity, EntityType, Room, RoomType
from backend.fastapi.routers import entities, messages, rooms, websocket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def initialize_database() -> None:
    """Initialize the database and create initial rooms and entities."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_sim.db")

    # Always recreate tables
    if os.path.exists(db_path):
        os.remove(db_path)

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Create initial rooms and entities
    db = SessionLocal()
    try:
        num_vehicles = 3
        # Create rooms for each vehicle
        rooms = []

        # V2V rooms (one for each vehicle)
        for i in range(1, num_vehicles + 1):
            rooms.append(
                Room(id=f"v{i}", name=f"Vehicle {i} Room", type=RoomType.VEHICLE)
            )

        # Vehicle-to-LLM rooms (one for each vehicle)
        for i in range(1, num_vehicles + 1):
            rooms.append(
                Room(
                    id=f"va{i}",
                    name=f"Vehicle {i} to Agent Room",
                    type=RoomType.VEH2LLM,
                )
            )

        # LLM-to-LLM rooms (one for each vehicle's agent)
        for i in range(1, num_vehicles + 1):
            rooms.append(Room(id=f"a{i}", name=f"Agent {i} Room", type=RoomType.AGENT))

        db.add_all(rooms)

        # Create entities
        entities = []
        # Create vehicle entities
        for i in range(1, num_vehicles + 1):
            entities.append(
                Entity(
                    id=f"v{i}",
                    name=f"Vehicle {i}",
                    type=EntityType.VEHICLE,
                    room_id=f"v{i}",  # Each vehicle is associated with its V2V room
                    status="online",
                )
            )

        # Create agent entities
        for i in range(1, num_vehicles + 1):
            entities.append(
                Entity(
                    id=f"a{i}",
                    name=f"Agent {i}",
                    type=EntityType.AGENT,
                    room_id=f"a{i}",  # Each agent is associated with its LLM2LLM room
                    status="online",
                )
            )

        db.add_all(entities)
        db.commit()
        print("Initial rooms and entities created successfully")

        # Print created rooms and entities for verification
        print("\nCreated Rooms:")
        for room in db.query(Room).all():
            print(f"- {room.id}: {room.name} ({room.type})")

        print("\nCreated Entities:")
        for entity in db.query(Entity).all():
            print(
                f"- {entity.id}: {entity.name} ({entity.type}) in room {entity.room_id}"
            )

    except Exception as e:
        print(f"Error creating initial data: {e}")
        db.rollback()
        raise
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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rooms.router)
app.include_router(entities.router)
app.include_router(messages.router)
app.include_router(websocket.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["."])
