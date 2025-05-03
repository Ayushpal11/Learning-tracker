from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection details
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_tracker")

async def init_database():
    """Initialize the database with proper configurations."""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Create collections with custom configurations
        # Topics collection
        await db.create_collection(
            "topics",
            collation={
                "locale": "en",
                "strength": 2,  # Case-insensitive
                "caseLevel": False,
                "caseFirst": "off",
                "numericOrdering": False,
                "alternate": "non-ignorable",
                "maxVariable": "punct",
                "normalization": True,
                "backwards": False
            }
        )
        
        # Study Plans collection (Time-series)
        await db.create_collection(
            "study_plans",
            timeseries={
                "timeField": "date",
                "metaField": "user_id",
                "granularity": "hours"
            },
            clusteredIndex={
                "key": {"_id": 1},
                "unique": True
            }
        )
        
        # Quizzes collection
        await db.create_collection(
            "quizzes",
            collation={
                "locale": "en",
                "strength": 2,
                "caseLevel": False,
                "caseFirst": "off",
                "numericOrdering": False,
                "alternate": "non-ignorable",
                "maxVariable": "punct",
                "normalization": True,
                "backwards": False
            }
        )
        
        # Create indexes
        await db.topics.create_index([("title", ASCENDING)], unique=True)
        await db.topics.create_index([("tags", ASCENDING)])
        await db.study_plans.create_index([("user_id", ASCENDING), ("date", ASCENDING)])
        await db.quizzes.create_index([("topic_id", ASCENDING)])
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_database()) 