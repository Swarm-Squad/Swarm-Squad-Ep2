from typing import List

from fastapi import APIRouter, HTTPException

from ..database import vehicles_collection
from ..models import Position, VehicleAgent, VehicleMessage, VehicleState
from ..utils import calculate_distance

router = APIRouter(
    prefix="/vehicles",
    tags=["vehicles"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[VehicleAgent])
async def get_vehicles():
    """Get all vehicles"""
    vehicles = await vehicles_collection.find().to_list(None)
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleAgent)
async def get_vehicle(vehicle_id: str):
    """Get a specific vehicle and its messages"""
    vehicle = await vehicles_collection.find_one({"_id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/{vehicle_id}/state")
async def update_vehicle_state(vehicle_id: str, state: VehicleState):
    """Update complete vehicle state and get nearby vehicles"""
    vehicle = await vehicles_collection.find_one_and_update(
        {"_id": vehicle_id},
        {"$set": {"state": state.model_dump()}},
        return_document=True,
    )
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Find nearby vehicles based on position
    nearby_vehicles = []
    async for other_vehicle in vehicles_collection.find({"_id": {"$ne": vehicle_id}}):
        if other_vehicle.get("state", {}).get("position"):
            other_pos = Position(**other_vehicle["state"]["position"])
            distance = calculate_distance(
                state.position.coordinates[:2], other_pos.coordinates[:2]
            )
            if distance <= state.position.radius:
                nearby_vehicles.append(other_vehicle["_id"])

    # Create a vehicle message with the state update
    message = VehicleMessage(
        message="State updated",
        timestamp=state.timestamp,
        nearby_vehicles=nearby_vehicles,
        state=state,
    )

    # Add message to vehicle's messages
    await vehicles_collection.update_one(
        {"_id": vehicle_id}, {"$push": {"messages": message.model_dump()}}
    )

    return {"vehicle": vehicle, "nearby_vehicles": nearby_vehicles}


@router.get("/{vehicle_id}/state")
async def get_vehicle_state(vehicle_id: str):
    """Get current state of a specific vehicle"""
    vehicle = await vehicles_collection.find_one({"_id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle.get("state", {})
