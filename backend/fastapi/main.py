import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.fastapi.database import (
    close_mongo_connection,
    connect_to_mongo,
    get_collection,
)
from backend.fastapi.routers import batch, llms, realtime, veh2llm, vehicles

# Configure logging
logger = logging.getLogger(__name__)

# Configure paths
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    await connect_to_mongo()
    yield
    # Shutdown: Close MongoDB connection
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="Swarm Squad: The Digital Dialogue",
    description="API for managing vehicles, LLM agents, and their communication",
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

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# Add datetime filter for Jinja2
def datetime_filter(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return ""


templates.env.filters["datetime"] = datetime_filter

# Include routers
app.include_router(vehicles.router)
app.include_router(llms.router)
app.include_router(veh2llm.router)
app.include_router(realtime.router)
app.include_router(batch.router)


@app.get("/")
async def root(request: Request):
    """Serve the index page with live data"""
    try:
        # Get collections
        vehicles_collection = get_collection("vehicles")
        llms_collection = get_collection("llms")

        # Get all vehicles
        vehicles = await vehicles_collection.find().to_list(None)

        # Get all LLM agents
        llms = await llms_collection.find().to_list(None)

        # Get recent messages from both vehicles and LLMs
        recent_messages = []

        # Get vehicle messages
        async for vehicle in vehicles_collection.find():
            if vehicle.get("messages"):
                for msg in vehicle["messages"][
                    -5:
                ]:  # Last 5 messages from each vehicle
                    recent_messages.append(
                        {
                            "timestamp": msg.get("timestamp"),
                            "source": f"Vehicle {vehicle['_id']}",
                            "message": msg.get("message"),
                        }
                    )

        # Get LLM messages
        async for llm in llms_collection.find():
            if llm.get("messages"):
                for msg in llm["messages"][-5:]:  # Last 5 messages from each LLM
                    recent_messages.append(
                        {
                            "timestamp": msg.get("timestamp"),
                            "source": f"LLM {llm['_id']}",
                            "message": msg.get("message"),
                        }
                    )

        # Sort messages by timestamp and get the 10 most recent
        recent_messages.sort(
            key=lambda x: x["timestamp"] if x["timestamp"] else 0, reverse=True
        )
        recent_messages = recent_messages[:10]

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "vehicles": vehicles,
                "llms": llms,
                "recent_messages": recent_messages,
            },
        )
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading data from database")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
