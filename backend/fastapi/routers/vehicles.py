import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..database import get_collection, is_db_connected

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    responses={
        404: {"description": "Not found"},
        503: {"description": "Database unavailable"},
        500: {"description": "Internal server error"},
    },
)


def normalize_vehicle_id(vehicle_id: str) -> str:
    """
    Normalize vehicle ID by ensuring it has the 'v' prefix.
    If it's a numeric ID, prefix it with 'v'.
    """
    if vehicle_id.isdigit():
        return f"v{vehicle_id}"
    return vehicle_id


@router.get("/")
async def get_vehicles():
    """Get all vehicles with only their latest message/state"""
    if not is_db_connected():
        raise HTTPException(
            status_code=503, detail="Database connection is not available"
        )

    vehicles_collection = get_collection("vehicles")
    if vehicles_collection is None:
        raise HTTPException(
            status_code=503, detail="Vehicles collection is not available"
        )

    try:
        # Get all vehicles
        vehicles = await vehicles_collection.find().to_list(None)

        # Process each vehicle to only include the latest message
        for vehicle in vehicles:
            if "messages" in vehicle and vehicle["messages"]:
                # Keep only the latest message
                vehicle["messages"] = [vehicle["messages"][-1]]

        return vehicles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vehicles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Get a specific vehicle with only its latest message"""
    if not is_db_connected():
        raise HTTPException(
            status_code=503, detail="Database connection is not available"
        )

    vehicles_collection = get_collection("vehicles")
    if vehicles_collection is None:
        raise HTTPException(
            status_code=503, detail="Vehicles collection is not available"
        )

    # Normalize the vehicle ID
    normalized_id = normalize_vehicle_id(vehicle_id)

    try:
        vehicle = await vehicles_collection.find_one({"_id": normalized_id})
        if vehicle is None:
            raise HTTPException(
                status_code=404, detail=f"Vehicle {vehicle_id} not found"
            )

        # Keep only the latest message
        if "messages" in vehicle and vehicle["messages"]:
            vehicle["messages"] = [vehicle["messages"][-1]]

        return vehicle
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vehicle {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{vehicle_id}/state")
async def update_vehicle_state(vehicle_id: str, state: Dict[str, Any]):
    """Update vehicle state and return only the updated state"""
    if not is_db_connected():
        raise HTTPException(
            status_code=503, detail="Database connection is not available"
        )

    vehicles_collection = get_collection("vehicles")
    if vehicles_collection is None:
        raise HTTPException(
            status_code=503, detail="Vehicles collection is not available"
        )

    # Normalize the vehicle ID
    normalized_id = normalize_vehicle_id(vehicle_id)

    try:
        # First check if the vehicle exists
        vehicle = await vehicles_collection.find_one({"_id": normalized_id})
        if vehicle is None:
            raise HTTPException(
                status_code=404, detail=f"Vehicle {vehicle_id} not found"
            )

        # Update the vehicle state
        await vehicles_collection.update_one(
            {"_id": normalized_id}, {"$set": {"state": state}}
        )

        # Create a message for the update
        message = {
            "message": "State updated",
            "timestamp": state.get("timestamp", datetime.utcnow().timestamp()),
            "state": state,
        }

        # Add message to vehicle's messages
        await vehicles_collection.update_one(
            {"_id": normalized_id}, {"$push": {"messages": message}}
        )

        # Return only the updated state and minimal metadata
        return {
            "vehicle_id": normalized_id,
            "state": state,
            "timestamp": message["timestamp"],
            "status": "updated",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vehicle state for {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{vehicle_id}/state")
async def get_vehicle_state(vehicle_id: str):
    """Get the latest state of a specific vehicle"""
    if not is_db_connected():
        raise HTTPException(
            status_code=503, detail="Database connection is not available"
        )

    vehicles_collection = get_collection("vehicles")
    if vehicles_collection is None:
        raise HTTPException(
            status_code=503, detail="Vehicles collection is not available"
        )

    # Normalize the vehicle ID
    normalized_id = normalize_vehicle_id(vehicle_id)

    try:
        vehicle = await vehicles_collection.find_one({"_id": normalized_id})
        if vehicle is None:
            raise HTTPException(
                status_code=404, detail=f"Vehicle {vehicle_id} not found"
            )

        # Get the latest state either from state field or from the last message
        state = vehicle.get("state", {})

        # If state is empty and we have messages, try to get state from the last message
        if not state and "messages" in vehicle and vehicle["messages"]:
            last_message = vehicle["messages"][-1]
            if "state" in last_message:
                state = last_message["state"]

        return state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vehicle state for {vehicle_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
