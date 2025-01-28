import os
import sys
from contextlib import asynccontextmanager

# Add the parent directory to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uvicorn

from backend.fastapi.database import Base, SessionLocal, engine
from backend.fastapi.models import Entity
from backend.fastapi.routers import entities, messages, rooms, websocket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def initialize_database() -> None:
    """Initialize the database by creating tables."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_sim.db")

    # Always recreate tables
    if os.path.exists(db_path):
        os.remove(db_path)

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


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
