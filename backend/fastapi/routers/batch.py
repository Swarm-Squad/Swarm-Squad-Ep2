from math import sqrt
from typing import List

from fastapi import APIRouter, Query

from ..database import llms_collection, veh2llm_collection, vehicles_collection
from ..models import BatchMessageResponse, BatchStateResponse

router = APIRouter(
    prefix="/batch",
    tags=["batch"],
)


def calculate_distance(coord1: List[float], coord2: List[float]) -> float:
    """Calculate Euclidean distance between two 2D coordinates"""
    return sqrt((coord2[0] - coord1[0]) ** 2 + (coord2[1] - coord1[1]) ** 2)


@router.get("/vehicles/states", response_model=BatchStateResponse)
async def get_vehicles_states(
    vehicle_ids: List[str] = Query(
        ..., description="List of vehicle IDs to fetch states for"
    ),
):
    """Batch fetch states for multiple vehicles"""
    states = {}
    async for vehicle in vehicles_collection.find({"_id": {"$in": vehicle_ids}}):
        if vehicle.get("state"):
            states[vehicle["_id"]] = vehicle["state"]

    return BatchStateResponse(states=states)


@router.get("/vehicles/messages", response_model=BatchMessageResponse)
async def get_vehicles_messages(
    vehicle_ids: List[str] = Query(...), limit: int = Query(50, ge=1, le=100)
):
    """Batch fetch messages for multiple vehicles"""
    messages = {}
    async for vehicle in vehicles_collection.find({"_id": {"$in": vehicle_ids}}):
        if vehicle.get("messages"):
            messages[vehicle["_id"]] = vehicle["messages"][-limit:]

    return BatchMessageResponse(messages=messages)


@router.get("/llms/messages")
async def get_llms_messages(
    llm_ids: List[str] = Query(...), limit: int = Query(50, ge=1, le=100)
):
    """Batch fetch messages for multiple LLM agents"""
    messages = {}
    async for llm in llms_collection.find({"_id": {"$in": llm_ids}}):
        if llm.get("messages"):
            messages[llm["_id"]] = llm["messages"][-limit:]

    return {"messages": messages}


@router.get("/llms/nearby/messages")
async def get_nearby_llms_messages(llm_id: str, limit: int = Query(50, ge=1, le=100)):
    """Batch fetch messages from all nearby LLM agents"""
    # First get the vehicle associated with this LLM
    mapping = await veh2llm_collection.find_one({"llm_id": llm_id})
    if not mapping:
        return {"messages": {}}

    # Get the vehicle and find nearby vehicles
    vehicle = await vehicles_collection.find_one({"_id": mapping["vehicle_id"]})
    if not vehicle or not vehicle.get("state", {}).get("position"):
        return {"messages": {}}

    # Get nearby vehicles
    position = vehicle["state"]["position"]
    nearby_vehicles = []
    async for other_vehicle in vehicles_collection.find(
        {"_id": {"$ne": mapping["vehicle_id"]}},
        projection={"_id": 1, "state.position": 1},
    ):
        if other_vehicle.get("state", {}).get("position"):
            distance = calculate_distance(
                position["coordinates"][:2],
                other_vehicle["state"]["position"]["coordinates"][:2],
            )
            if distance <= position.get("radius", 100.0):
                nearby_vehicles.append(other_vehicle["_id"])

    # Get LLMs associated with nearby vehicles
    nearby_llm_ids = []
    async for nearby_mapping in veh2llm_collection.find(
        {"vehicle_id": {"$in": nearby_vehicles}}
    ):
        nearby_llm_ids.append(nearby_mapping["llm_id"])

    # Fetch messages for all nearby LLMs
    messages = {}
    async for llm in llms_collection.find({"_id": {"$in": nearby_llm_ids}}):
        if llm.get("messages"):
            messages[llm["_id"]] = llm["messages"][-limit:]

    return {"messages": messages}
