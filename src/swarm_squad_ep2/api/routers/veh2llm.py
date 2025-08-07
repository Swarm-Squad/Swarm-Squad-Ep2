from fastapi import APIRouter, HTTPException

from swarm_squad_ep2.api.database import get_collection

router = APIRouter(
    prefix="/veh2llm",
    tags=["vehicle-llm-mapping"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{vehicle_id}")
async def get_vehicle_llm(vehicle_id: str):
    """Get corresponding LLM agent for a vehicle"""
    veh2llm_collection = get_collection("veh2llm")
    mapping = await veh2llm_collection.find_one({"vehicle_id": vehicle_id})
    if not mapping:
        raise HTTPException(
            status_code=404, detail="No LLM agent assigned to this vehicle"
        )
    return mapping


@router.post("/{vehicle_id}")
async def assign_llm_to_vehicle(vehicle_id: str, llm_id: str):
    """Assign an LLM agent to a vehicle"""
    vehicles_collection = get_collection("vehicles")
    llms_collection = get_collection("llms")
    veh2llm_collection = get_collection("veh2llm")
    
    # Check if vehicle exists
    vehicle = await vehicles_collection.find_one({"_id": vehicle_id})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Check if LLM exists
    llm = await llms_collection.find_one({"_id": llm_id})
    if not llm:
        raise HTTPException(status_code=404, detail="LLM agent not found")

    # Update or create the mapping
    await veh2llm_collection.update_one(
        {"vehicle_id": vehicle_id}, {"$set": {"llm_id": llm_id}}, upsert=True
    )

    # Update vehicle and LLM with cross-references
    await vehicles_collection.update_one(
        {"_id": vehicle_id}, {"$set": {"llm_id": llm_id}}
    )
    await llms_collection.update_one(
        {"_id": llm_id}, {"$set": {"vehicle_id": vehicle_id}}
    )

    return {
        "status": "success",
        "message": f"Assigned LLM {llm_id} to vehicle {vehicle_id}",
    }
