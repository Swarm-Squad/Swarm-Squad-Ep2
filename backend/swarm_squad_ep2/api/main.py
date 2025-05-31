import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Union

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import from proper package structure
from swarm_squad_ep2.api.database import (
    close_mongo_connection,
    connect_to_mongo,
    get_collection,
    is_db_connected,
)
from swarm_squad_ep2.api.routers import batch, llms, realtime, veh2llm, vehicles

# Configure logging
logger = logging.getLogger(__name__)

# Configure paths
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup: Connect to MongoDB
    connection_success = await connect_to_mongo()
    if not connection_success:
        logger.warning("Failed to connect to MongoDB during startup")
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


# Add favicon route
@app.get("/favicon.ico")
async def get_favicon():
    """Serve the favicon"""
    return RedirectResponse(url="/static/favicon.ico")


# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# Add datetime filter for Jinja2
def datetime_filter(timestamp: Union[str, float, int, None]) -> str:
    """
    Convert various timestamp formats to a readable date string.

    Args:
        timestamp: Timestamp value to format (string, float, int)

    Returns:
        Formatted datetime string or empty string if conversion fails
    """
    if timestamp is None:
        return ""

    try:
        # Handle string timestamps
        if isinstance(timestamp, str):
            try:
                timestamp = float(timestamp)
            except ValueError:
                return timestamp

        # Convert to datetime string
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, OverflowError) as e:
        logger.debug(f"Error converting timestamp {timestamp}: {e}")
        return str(timestamp)


templates.env.filters["datetime"] = datetime_filter

# Include routers
app.include_router(vehicles.router)
app.include_router(llms.router)
app.include_router(veh2llm.router)
app.include_router(realtime.router)
app.include_router(batch.router)


@app.get("/")
async def root(request: Request):
    """
    Serve the index page with live data from the database.

    Includes:
    - List of vehicles with their latest states
    - List of LLM agents
    - Recent messages from vehicles and LLMs
    """
    try:
        if not is_db_connected():
            logger.warning("Database not connected when accessing index page")
            raise Exception("Database connection not available")

        # Get collections
        vehicles_collection = get_collection("vehicles")
        llms_collection = get_collection("llms")

        if vehicles_collection is None or llms_collection is None:
            raise Exception("Required collections not available")

        # Get all vehicles with complete state information
        vehicles = await vehicles_collection.find().to_list(None)

        # Get all LLM agents
        llms = await llms_collection.find().to_list(None)

        # Get recent messages from both vehicles and LLMs
        recent_messages = []

        # Get vehicle messages - only the 5 most recent per vehicle
        async for vehicle in vehicles_collection.find():
            if vehicle.get("messages"):
                for msg in vehicle["messages"][-5:]:
                    recent_messages.append(
                        {
                            "timestamp": msg.get("timestamp"),
                            "source": f"Vehicle {vehicle['_id']}",
                            "message": msg.get("message"),
                        }
                    )

                    # Update vehicle state from the latest message
                    if msg.get("state"):
                        for v in vehicles:
                            if v["_id"] == vehicle["_id"]:
                                v["state"] = msg.get("state")
                                break

        # Get LLM messages - only the 5 most recent per LLM
        async for llm in llms_collection.find():
            if llm.get("messages"):
                for msg in llm["messages"][-5:]:
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

        # Return the template with data
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
        # Provide fallback data when DB is not accessible
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "vehicles": [],
                "llms": [],
                "recent_messages": [],
                "error_message": "Database connection issue. The system is running but data display is temporarily unavailable.",
            },
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
