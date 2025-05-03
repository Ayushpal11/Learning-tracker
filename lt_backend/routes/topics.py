from fastapi import APIRouter, HTTPException, Body, Query, status
from fastapi.encoders import jsonable_encoder
from ..db import topics_collection
from ..models.models import TopicCreate, Topic, TopicUpdate, ResponseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter()

# Helper function to verify ObjectId
def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail=f"Invalid id format: {id}")

@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_topic(topic: TopicCreate = Body(...)):
    """Create a new learning topic."""
    try:
        topic_data = jsonable_encoder(topic)
        
        # Add creation timestamp
        topic_data["created_date"] = datetime.utcnow()
        
        # Insert the topic into the database
        new_topic = await topics_collection().insert_one(topic_data)
        
        # Retrieve the created topic
        created_topic = await topics_collection().find_one({"_id": new_topic.inserted_id})
        
        if not created_topic:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created topic"
            )
        
        # Convert ObjectId to string
        created_topic["_id"] = str(created_topic["_id"])
        
        # Convert any nested ObjectIds to strings
        if "resources" in created_topic:
            for resource in created_topic["resources"]:
                if "_id" in resource and isinstance(resource["_id"], ObjectId):
                    resource["_id"] = str(resource["_id"])
        
        return ResponseModel(
            data=created_topic,
            message="Topic created successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create topic: {str(e)}"
        )

@router.get("/", response_model=ResponseModel)
async def get_topics(
    skip: int = 0, 
    limit: int = 10,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    min_progress: Optional[float] = None,
    max_progress: Optional[float] = None,
    sort_by: Optional[str] = "created_date",
    sort_order: int = -1  # -1 for descending, 1 for ascending
):
    """Get all topics with optional filtering and pagination."""
    # Build query based on filters
    query = {}
    
    if search:
        # Search in title and description
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if tag:
        query["tags"] = {"$in": [tag.lower()]}
    
    progress_query = {}
    if min_progress is not None:
        progress_query["$gte"] = min_progress
    if max_progress is not None:
        progress_query["$lte"] = max_progress
    
    if progress_query:
        query["progress"] = progress_query
    
    # Execute query with pagination
    cursor = topics_collection().find(query)
    
    # Apply sorting
    valid_sort_fields = ["title", "progress", "created_date", "last_studied", "priority"]
    sort_field = sort_by if sort_by in valid_sort_fields else "created_date"
    cursor = cursor.sort(sort_field, sort_order)
    
    # Apply pagination
    cursor = cursor.skip(skip).limit(limit)
    
    # Convert to list and convert ObjectId to string
    topics = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        topics.append(doc)
    
    # Get total count for pagination
    total_count = await topics_collection().count_documents(query)
    
    return ResponseModel(
        data={
            "topics": topics,
            "total": total_count,
            "skip": skip,
            "limit": limit
        },
        message="Topics retrieved successfully"
    )

@router.get("/{topic_id}", response_model=ResponseModel)
async def get_topic(topic_id: str):
    """Get details of a specific topic."""
    topic_obj_id = validate_object_id(topic_id)
    
    topic = await topics_collection().find_one({"_id": topic_obj_id})
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
    
    return ResponseModel(
        data=topic,
        message="Topic retrieved successfully"
    )

@router.put("/{topic_id}", response_model=ResponseModel)
async def update_topic(topic_id: str, topic_update: TopicUpdate = Body(...)):
    """Update a topic's details."""
    topic_obj_id = validate_object_id(topic_id)
    
    # Remove None values from update data
    update_data = {k: v for k, v in topic_update.dict().items() if v is not None}
    
    # If update data is empty, return the existing topic
    if not update_data:
        topic = await topics_collection().find_one({"_id": topic_obj_id})
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
        return ResponseModel(
            data=topic,
            message="No updates provided"
        )
    
    # Add last modified timestamp
    update_data["last_modified"] = datetime.now()
    
    # Perform update
    result = await topics_collection().update_one(
        {"_id": topic_obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
    
    # Get updated topic
    updated_topic = await topics_collection().find_one({"_id": topic_obj_id})
    
    return ResponseModel(
        data=updated_topic,
        message="Topic updated successfully"
    )

@router.delete("/{topic_id}", response_model=ResponseModel)
async def delete_topic(topic_id: str):
    """Delete a topic."""
    topic_obj_id = validate_object_id(topic_id)
    
    # Find and delete topic
    result = await topics_collection().delete_one({"_id": topic_obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
    
    return ResponseModel(
        data={"id": topic_id},
        message="Topic deleted successfully"
    )

@router.put("/{topic_id}/progress", response_model=ResponseModel)
async def update_topic_progress(
    topic_id: str, 
    progress: float = Body(..., embed=True),
    time_spent_minutes: Optional[int] = Body(0, embed=True)
):
    """Update a topic's progress and time spent."""
    topic_obj_id = validate_object_id(topic_id)
    
    # Validate progress value
    if progress < 0 or progress > 100:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
    
    # Update topic progress
    update_data = {
        "progress": progress,
        "last_studied": datetime.now()
    }
    
    # Add time spent if provided
    if time_spent_minutes > 0:
        update_data["$inc"] = {"time_spent_minutes": time_spent_minutes}
    
    result = await topics_collection().update_one(
        {"_id": topic_obj_id},
        {"$set": {k: v for k, v in update_data.items() if k != "$inc"}},
        upsert=False
    )
    
    # Handle time increment separately if needed
    if time_spent_minutes > 0:
        await topics_collection().update_one(
            {"_id": topic_obj_id},
            {"$inc": {"time_spent_minutes": time_spent_minutes}}
        )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
    
    # Get updated topic
    updated_topic = await topics_collection().find_one({"_id": topic_obj_id})
    
    return ResponseModel(
        data=updated_topic,
        message=f"Progress updated to {progress}%"
    )