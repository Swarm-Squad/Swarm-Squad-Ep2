import asyncio
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
from backend.scripts.simulator import Vehicle, vehicle_simulation, vehicles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def initialize_database() -> None:
    """Initialize the database and create initial rooms and entities."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_sim.db")
    db_exists = os.path.exists(db_path)

    if not db_exists:
        print("Database does not exist. Creating tables...")
        Base.metadata.create_all(bind=engine)

        # Create initial rooms and entities
        db = SessionLocal()
        try:
            # Create rooms
            rooms = [
                Room(id=f"v{i}", name=f"vehicle-{i}", type=RoomType.VEHICLE)
                for i in range(1, 4)
            ]
            rooms.extend(
                [
                    Room(id=f"a{i}", name=f"agent-{i}", type=RoomType.AGENT)
                    for i in range(1, 4)
                ]
            )
            rooms.extend(
                [
                    Room(id=f"va{i}", name=f"veh{i}-agent{i}", type=RoomType.VEH2LLM)
                    for i in range(1, 4)
                ]
            )
            db.add_all(rooms)

            # Create entities (vehicles and agents)
            entities = [
                Entity(
                    id=f"v{i}",
                    name=f"Vehicle {i}",
                    type=EntityType.VEHICLE,
                    room_id=f"v{i}",
                )
                for i in range(1, 4)
            ]
            entities.extend(
                [
                    Entity(
                        id=f"a{i}",
                        name=f"Agent {i}",
                        type=EntityType.AGENT,
                        room_id=f"a{i}",
                    )
                    for i in range(1, 4)
                ]
            )
            db.add_all(entities)

            db.commit()
            print("Initial rooms and entities created successfully")
        except Exception as e:
            print(f"Error creating initial data: {e}")
            db.rollback()
        finally:
            db.close()
    else:
        print("Database already exists, skipping initialization")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    initialize_database()
    db = SessionLocal()

    try:
        # Initialize vehicles
        for i in range(1, 4):
            vehicles[f"v{i}"] = Vehicle(f"v{i}")

        # Set up simulation to start on first client connection
        async def start_simulation():
            asyncio.create_task(vehicle_simulation(db))

        websocket.ws_manager.on_first_client_connect = start_simulation

        yield
    finally:
        # Update all entities to offline status
        for entity in db.query(Entity).all():
            entity.status = "offline"
        db.commit()
        db.close()
        vehicles.clear()


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
