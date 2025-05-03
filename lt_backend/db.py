from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection details
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://GG:<db_password>@learning.zieolhs.mongodb.net/?retryWrites=true&w=majority&appName=Learning")
DB_NAME = os.getenv("DB_NAME", "learning_tracker")

# Global database client and database instances
client = None
db = None

async def connect_to_mongo():
    """Connect to MongoDB database."""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Verify connection is successful
        await client.admin.command('ping')
        db = client[DB_NAME]
        logger.info(f"Connected to MongoDB at {MONGO_URI}")
        logger.info(f"Using database: {DB_NAME}")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection")

# Helper functions to access collections
def get_collection(collection_name):
    """Get a reference to a collection."""
    if db is None:
        raise ConnectionError("Database not connected")
    return db[collection_name]

# Collection references
def topics_collection():
    return get_collection("topics")

def study_plans_collection():
    return get_collection("study_plans")

def quiz_collection():
    return get_collection("quizzes")
