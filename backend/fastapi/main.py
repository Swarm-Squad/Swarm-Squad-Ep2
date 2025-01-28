import os
import sys
from contextlib import asynccontextmanager

# Add the parent directory to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import uvicorn
from sqlalchemy.orm import Session

from backend.fastapi.database import Base, SessionLocal, engine, get_db
from backend.fastapi.models import Entity, Message, Room
from backend.fastapi.routers import entities, messages, rooms, websocket
from backend.fastapi.utils import create_simulation_resources
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
    description="API for managing rooms, messages, and agents",
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
