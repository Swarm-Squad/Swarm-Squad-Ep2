import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

# Database connection settings
MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "swarm_squad"
CONNECTION_TIMEOUT_MS = 5000

# MongoDB client and collections
client: Optional[AsyncIOMotorClient] = None
db = None
vehicles_collection = None
llms_collection = None
veh2llm_collection = None

# Configure logging
logger = logging.getLogger(__name__)


async def connect_to_mongo() -> bool:
    """
    Establish connection to MongoDB server.

    Returns:
        bool: True if connection was successful, False otherwise
    """
    global client, db, vehicles_collection, llms_collection, veh2llm_collection
    try:
        if client is None:
            logger.info(f"Connecting to MongoDB at {MONGODB_URL}")
            client = AsyncIOMotorClient(
                MONGODB_URL, serverSelectionTimeoutMS=CONNECTION_TIMEOUT_MS
            )
            # Test the connection
            await client.server_info()

            # Setup database and collections
            db = client[DB_NAME]
            vehicles_collection = db.vehicles
            llms_collection = db.llms
            veh2llm_collection = db.veh2llm

            logger.info("Successfully connected to MongoDB")
            return True
        return True  # Already connected
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        if client:
            client.close()
            client = None
        return False


async def close_mongo_connection() -> None:
    """Close MongoDB connection and reset global variables."""
    global client, db, vehicles_collection, llms_collection, veh2llm_collection

    if client is not None:
        logger.info("Closing MongoDB connection")
        client.close()

        # Reset globals
        client = None
        db = None
        vehicles_collection = None
        llms_collection = None
        veh2llm_collection = None


def get_database():
    """
    Get the current database instance.

    Returns:
        Database object or None if not connected
    """
    if not is_db_connected():
        logger.warning(
            "Attempting to access database but connection is not established"
        )
    return db


def get_collection(name: str) -> Optional[AsyncIOMotorCollection]:
    """
    Get a MongoDB collection by name.

    Args:
        name: Name of the collection to retrieve

    Returns:
        AsyncIOMotorCollection or None if database is not connected
    """
    if db is None:
        logger.warning(
            f"Attempting to access collection '{name}' but database connection is not established"
        )
        return None
    return db[name]


def is_db_connected() -> bool:
    """
    Check if database connection is available.

    Returns:
        bool: True if connected, False otherwise
    """
    return client is not None
