# config/database.py
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, PyMongoError

from config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect_db(self) -> None:
        """Connect to MongoDB."""
        try:
            logger.info("Connecting to MongoDB Atlas...")
            self.client = AsyncIOMotorClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]
            # Send a ping to confirm a successful connection
            await self.ping_db()
            logger.info(f"Successfully connected to MongoDB database: {settings.DB_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while connecting to MongoDB: {e}")
            raise

    async def close_db(self) -> None:
        """Close MongoDB connection."""
        if self.client is not None:
            logger.info("Closing MongoDB connection...")
            self.client.close()
            logger.info("MongoDB connection closed.")

    def get_database(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if self.db is None:
            raise RuntimeError("Database connection has not been initialized. Call connect_db() first.")
        return self.db

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get a specific collection from the database."""
        db = self.get_database()
        return db[name]
        
    async def ping_db(self) -> bool:
        """Ping the database to check if the connection is alive."""
        if self.client is None:
            return False
        try:
            await self.client.admin.command('ping')
            return True
        except PyMongoError as e:
            logger.warning(f"Database ping failed: {e}")
            return False

# Singleton instance
db_client = DatabaseClient()

# Export functions for easier imports
async def connect_db() -> None:
    """Initialize database connection for FastAPI lifespan hook."""
    await db_client.connect_db()

async def close_db() -> None:
    """Close database connection for FastAPI lifespan hook."""
    await db_client.close_db()

def get_database() -> AsyncIOMotorDatabase:
    """Get the active database instance."""
    return db_client.get_database()

def get_collection(name: str) -> AsyncIOMotorCollection:
    """Get a specific collection from the active database."""
    return db_client.get_collection(name)

async def ping_db() -> bool:
    """Health check ping for the database."""
    return await db_client.ping_db()
