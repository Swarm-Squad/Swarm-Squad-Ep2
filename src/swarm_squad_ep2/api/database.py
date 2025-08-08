import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = Path(__file__).parent / "vehicle_sim.db"

# Global database connection
_connection: Optional[sqlite3.Connection] = None


def get_db_connection() -> sqlite3.Connection:
    """Get or create database connection."""
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _connection.row_factory = sqlite3.Row  # Enable dict-like access
        _connection.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
        logger.info(f"Connected to SQLite database: {DB_PATH}")
    return _connection


async def connect_to_db() -> bool:
    """
    Initialize SQLite database with required tables.

    Returns:
        bool: True if connection was successful, False otherwise
    """
    try:
        conn = get_db_connection()
        
        # Create tables if they don't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY,
                messages TEXT DEFAULT '[]',
                status TEXT DEFAULT 'unknown',
                last_seen TEXT DEFAULT '',
                state TEXT DEFAULT '{}'
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS llms (
                id TEXT PRIMARY KEY,
                messages TEXT DEFAULT '[]',
                status TEXT DEFAULT 'unknown',
                last_seen TEXT DEFAULT '',
                vehicle_id TEXT DEFAULT NULL
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS veh2llm (
                vehicle_id TEXT PRIMARY KEY,
                llm_id TEXT NOT NULL
            )
        """)
        
        conn.commit()
        logger.info("SQLite database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {str(e)}")
        return False


async def close_db_connection() -> None:
    """Close SQLite database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
        logger.info("Closed SQLite database connection")


def is_db_connected() -> bool:
    """
    Check if database connection is available.

    Returns:
        bool: True if connected, False otherwise
    """
    return _connection is not None


# Vehicle operations
async def get_all_vehicles() -> List[Dict[str, Any]]:
    """Get all vehicles from database."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM vehicles")
        vehicles = []
        for row in cursor.fetchall():
            vehicle = {
                "_id": row["id"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "status": row["status"],
                "last_seen": row["last_seen"],
                "state": json.loads(row["state"]) if row["state"] else {}
            }
            vehicles.append(vehicle)
        return vehicles
    except Exception as e:
        logger.error(f"Error getting vehicles: {e}")
        return []


async def find_vehicle(vehicle_id: str) -> Optional[Dict[str, Any]]:
    """Find a specific vehicle by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        row = cursor.fetchone()
        if row:
            return {
                "_id": row["id"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "status": row["status"],
                "last_seen": row["last_seen"],
                "state": json.loads(row["state"]) if row["state"] else {}
            }
        return None
    except Exception as e:
        logger.error(f"Error finding vehicle {vehicle_id}: {e}")
        return None


async def upsert_vehicle_message(vehicle_id: str, message: Dict[str, Any]) -> bool:
    """Add a message to a vehicle, creating the vehicle if it doesn't exist."""
    try:
        conn = get_db_connection()
        
        # Get existing vehicle or create new one
        cursor = conn.execute("SELECT messages FROM vehicles WHERE id = ?", (vehicle_id,))
        row = cursor.fetchone()
        
        if row:
            # Update existing vehicle
            messages = json.loads(row["messages"]) if row["messages"] else []
            messages.append(message)
            conn.execute(
                "UPDATE vehicles SET messages = ? WHERE id = ?",
                (json.dumps(messages), vehicle_id)
            )
        else:
            # Create new vehicle
            messages = [message]
            conn.execute(
                "INSERT INTO vehicles (id, messages) VALUES (?, ?)",
                (vehicle_id, json.dumps(messages))
            )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error upserting vehicle message for {vehicle_id}: {e}")
        return False


async def update_vehicle_status(vehicle_id: str, status: str) -> bool:
    """Update vehicle status."""
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE vehicles SET status = ? WHERE id = ?",
            (status, vehicle_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating vehicle status for {vehicle_id}: {e}")
        return False


# LLM operations
async def get_all_llms() -> List[Dict[str, Any]]:
    """Get all LLMs from database."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM llms")
        llms = []
        for row in cursor.fetchall():
            llm = {
                "_id": row["id"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "status": row["status"],
                "last_seen": row["last_seen"],
                "vehicle_id": row["vehicle_id"]
            }
            llms.append(llm)
        return llms
    except Exception as e:
        logger.error(f"Error getting LLMs: {e}")
        return []


async def find_llm(llm_id: str) -> Optional[Dict[str, Any]]:
    """Find a specific LLM by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM llms WHERE id = ?", (llm_id,))
        row = cursor.fetchone()
        if row:
            return {
                "_id": row["id"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "status": row["status"],
                "last_seen": row["last_seen"],
                "vehicle_id": row["vehicle_id"]
            }
        return None
    except Exception as e:
        logger.error(f"Error finding LLM {llm_id}: {e}")
        return None


async def upsert_llm_message(llm_id: str, message: Dict[str, Any]) -> bool:
    """Add a message to an LLM, creating the LLM if it doesn't exist."""
    try:
        conn = get_db_connection()
        
        # Get existing LLM or create new one
        cursor = conn.execute("SELECT messages FROM llms WHERE id = ?", (llm_id,))
        row = cursor.fetchone()
        
        if row:
            # Update existing LLM
            messages = json.loads(row["messages"]) if row["messages"] else []
            messages.append(message)
            conn.execute(
                "UPDATE llms SET messages = ? WHERE id = ?",
                (json.dumps(messages), llm_id)
            )
        else:
            # Create new LLM
            messages = [message]
            conn.execute(
                "INSERT INTO llms (id, messages) VALUES (?, ?)",
                (llm_id, json.dumps(messages))
            )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error upserting LLM message for {llm_id}: {e}")
        return False


async def update_llm_status(llm_id: str, status: str) -> bool:
    """Update LLM status."""
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE llms SET status = ? WHERE id = ?",
            (status, llm_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating LLM status for {llm_id}: {e}")
        return False


# Clear database operations
async def clear_all_data() -> bool:
    """Clear all data from the database."""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM vehicles")
        conn.execute("DELETE FROM llms")
        conn.execute("DELETE FROM veh2llm")
        conn.commit()
        logger.info("All database data cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return False


# Legacy compatibility functions (for existing code that expects MongoDB-style operations)
def get_collection(name: str):
    """Legacy compatibility function - returns a mock collection object."""
    return MockCollection(name)


class MockCollection:
    """Mock collection object to maintain compatibility with existing MongoDB code."""
    
    def __init__(self, name: str):
        self.name = name
    
    def find(self, filter_dict: Dict = None):
        """Mock find operation - returns MockCursor that can be async iterated."""
        return MockAsyncCursor(self.name, filter_dict)
    
    async def find_one(self, filter_dict: Dict):
        """Mock find_one operation."""
        entity_id = filter_dict.get("_id")
        if self.name == "vehicles":
            return await find_vehicle(entity_id)
        elif self.name == "llms":
            return await find_llm(entity_id)
        return None
    
    async def update_one(self, filter_dict: Dict, update_dict: Dict, upsert: bool = False):
        """Mock update_one operation."""
        entity_id = filter_dict.get("_id")
        
        if "$push" in update_dict and "messages" in update_dict["$push"]:
            # Adding a message
            message = update_dict["$push"]["messages"]
            if self.name == "vehicles":
                success = await upsert_vehicle_message(entity_id, message)
            elif self.name == "llms":
                success = await upsert_llm_message(entity_id, message)
            return MockResult(success)
        
        if "$set" in update_dict and "status" in update_dict["$set"]:
            # Updating status
            status = update_dict["$set"]["status"]
            if self.name == "vehicles":
                success = await update_vehicle_status(entity_id, status)
            elif self.name == "llms":
                success = await update_llm_status(entity_id, status)
            return MockResult(success)
        
        return MockResult(True)
    
    async def count_documents(self, filter_dict: Dict = None):
        """Mock count_documents operation."""
        if self.name == "vehicles":
            vehicles = await get_all_vehicles()
            return len(vehicles)
        elif self.name == "llms":
            llms = await get_all_llms()
            return len(llms)
        return 0


class MockAsyncCursor:
    """Mock async cursor for iterating over results."""
    
    def __init__(self, collection_name: str, filter_dict: Dict = None):
        self.collection_name = collection_name
        self.filter_dict = filter_dict or {}
        self.data = None
        self.index = 0
    
    async def _load_data(self):
        """Load data from SQLite on first access."""
        if self.data is None:
            if self.collection_name == "vehicles":
                self.data = await get_all_vehicles()
            elif self.collection_name == "llms":
                self.data = await get_all_llms()
            else:
                self.data = []
            
            # Apply filtering if needed
            if "_id" in self.filter_dict and "$in" in str(self.filter_dict.get("_id", {})):
                # Handle $in filter for batch operations
                allowed_ids = self.filter_dict["_id"]["$in"]
                self.data = [item for item in self.data if item["_id"] in allowed_ids]
            elif "_id" in self.filter_dict and "$ne" in str(self.filter_dict.get("_id", {})):
                # Handle $ne filter (not equal)
                excluded_id = self.filter_dict["_id"]["$ne"]
                self.data = [item for item in self.data if item["_id"] != excluded_id]
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        await self._load_data()
        if self.index >= len(self.data):
            raise StopAsyncIteration
        item = self.data[self.index]
        self.index += 1
        return item
    
    async def to_list(self, length: int = None):
        """Convert cursor to list (MongoDB compatibility)."""
        await self._load_data()
        if length is None:
            return self.data
        return self.data[:length]


class MockCursor:
    """Mock cursor for iterating over results (legacy compatibility)."""
    
    def __init__(self, data: List[Dict]):
        self.data = data
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.data):
            raise StopAsyncIteration
        item = self.data[self.index]
        self.index += 1
        return item


class MockResult:
    """Mock result object for update operations."""
    
    def __init__(self, success: bool):
        self.matched_count = 1 if success else 0
        self.modified_count = 1 if success else 0
        self.upserted_id = None if success else None