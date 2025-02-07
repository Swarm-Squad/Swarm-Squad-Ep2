from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection URL
MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "swarm_squad"

# MongoDB client
client: Optional[AsyncIOMotorClient] = None

# Collections
db = None
vehicles_collection = None
llms_collection = None
veh2llm_collection = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global client, db, vehicles_collection, llms_collection, veh2llm_collection
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DB_NAME]
        vehicles_collection = db.vehicles
        llms_collection = db.llms
        veh2llm_collection = db.veh2llm


async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client is not None:
        client.close()
        client = None


def get_database():
    """Get database instance"""
    return db


def get_collection(name: str):
    """Get collection by name"""
    return db[name]
