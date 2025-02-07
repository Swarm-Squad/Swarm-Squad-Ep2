from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from ..database import llms_collection
from ..models import LLMAgent, LLMMessage

router = APIRouter(
    prefix="/llms",
    tags=["llms"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[LLMAgent])
async def get_llms():
    """Get all LLM agents"""
    llms = await llms_collection.find().to_list(None)
    return llms


@router.get("/{agent_id}", response_model=LLMAgent)
async def get_llm(agent_id: str):
    """Get messages for a specific LLM"""
    llm = await llms_collection.find_one({"_id": agent_id})
    if not llm:
        raise HTTPException(status_code=404, detail="LLM agent not found")
    return llm


@router.post("/{agent_id}/messages")
async def add_llm_message(agent_id: str, message: LLMMessage):
    """Add a new message for an LLM agent"""
    llm = await llms_collection.find_one({"_id": agent_id})
    if not llm:
        raise HTTPException(status_code=404, detail="LLM agent not found")

    # Add timestamp if not provided
    if not message.timestamp:
        message.timestamp = datetime.utcnow().timestamp()

    # Add message to LLM's messages
    await llms_collection.update_one(
        {"_id": agent_id}, {"$push": {"messages": message.model_dump()}}
    )
    return {"status": "success", "message": "Message added successfully"}
