from fastapi import APIRouter, HTTPException, Body, Path, status
from fastapi.encoders import jsonable_encoder
from lt_backend.db import topics_collection
from lt_backend.models.models import Resource, ResponseModel
from typing import List
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/topics")


# Helper function to verify ObjectId
def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail=f"Invalid id format: {id}")


@router.post("/{topic_id}/resources", response_model=ResponseModel)
async def add_resource(
    topic_id: str = Path(..., description="The ID of the topic to add a resource to"),
    resource: Resource = Body(...),
):
    """Add a new resource to a topic."""
    topic_obj_id = validate_object_id(topic_id)

    # First check if topic exists
    topic = await topics_collection().find_one({"_id": topic_obj_id})
    if not topic:
        raise HTTPException(
            status_code=404, detail=f"Topic with ID {topic_id} not found"
        )

    resource_data = jsonable_encoder(resource)

    # Add the resource to the topic
    result = await topics_collection().update_one(
        {"_id": topic_obj_id}, {"$push": {"resources": resource_data}}
    )

    # Get updated topic with new resource
    updated_topic = await topics_collection().find_one({"_id": topic_obj_id})

    return ResponseModel(data=updated_topic, message="Resource added successfully")


@router.get("/{topic_id}/resources", response_model=ResponseModel)
async def get_resources(
    topic_id: str = Path(..., description="The ID of the topic to get resources from")
):
    """Get all resources for a specific topic."""
    topic_obj_id = validate_object_id(topic_id)

    # Check if topic exists
    topic = await topics_collection().find_one(
        {"_id": topic_obj_id}, {"resources": 1, "title": 1}
    )

    if not topic:
        raise HTTPException(
            status_code=404, detail=f"Topic with ID {topic_id} not found"
        )

    resources = topic.get("resources", [])

    return ResponseModel(
        data={
            "topic_id": topic_id,
            "topic_title": topic.get("title"),
            "resources": resources,
            "count": len(resources),
        },
        message="Resources retrieved successfully",
    )


@router.put("/{topic_id}/resources/{resource_index}", response_model=ResponseModel)
async def update_resource(
    topic_id: str = Path(..., description="The ID of the topic"),
    resource_index: int = Path(
        ..., description="The index of the resource to update", ge=0
    ),
    resource: Resource = Body(...),
):
    """Update a specific resource in a topic."""
    topic_obj_id = validate_object_id(topic_id)

    # Check if topic exists
    topic = await topics_collection().find_one({"_id": topic_obj_id})
    if not topic:
        raise HTTPException(
            status_code=404, detail=f"Topic with ID {topic_id} not found"
        )

    # Check if resource index is valid
    resources = topic.get("resources", [])
    if resource_index >= len(resources):
        raise HTTPException(
            status_code=404, detail=f"Resource at index {resource_index} not found"
        )

    resource_data = jsonable_encoder(resource)

    # Update the resource at the specified index
    result = await topics_collection().update_one(
        {"_id": topic_obj_id}, {"$set": {f"resources.{resource_index}": resource_data}}
    )

    # Get updated topic
    updated_topic = await topics_collection().find_one({"_id": topic_obj_id})

    return ResponseModel(data=updated_topic, message="Resource updated successfully")


@router.delete("/{topic_id}/resources/{resource_index}", response_model=ResponseModel)
async def delete_resource(
    topic_id: str = Path(..., description="The ID of the topic"),
    resource_index: int = Path(
        ..., description="The index of the resource to delete", ge=0
    ),
):
    """Delete a specific resource from a topic."""
    topic_obj_id = validate_object_id(topic_id)

    # Check if topic exists
    topic = await topics_collection().find_one({"_id": topic_obj_id})
    if not topic:
        raise HTTPException(
            status_code=404, detail=f"Topic with ID {topic_id} not found"
        )

    # Check if resource index is valid
    resources = topic.get("resources", [])
    if resource_index >= len(resources):
        raise HTTPException(
            status_code=404, detail=f"Resource at index {resource_index} not found"
        )

    # Get the resource to be deleted for the response
    resource_to_delete = resources[resource_index]

    # Remove the resource at the specified index
    resources.pop(resource_index)

    # Update the topic with the modified resources list
    result = await topics_collection().update_one(
        {"_id": topic_obj_id}, {"$set": {"resources": resources}}
    )

    return ResponseModel(
        data={"deleted_resource": resource_to_delete},
        message="Resource deleted successfully",
    )


@router.put(
    "/{topic_id}/resources/{resource_index}/complete", response_model=ResponseModel
)
async def mark_resource_complete(
    topic_id: str = Path(..., description="The ID of the topic"),
    resource_index: int = Path(
        ..., description="The index of the resource to mark as complete", ge=0
    ),
    completed: bool = Body(..., embed=True),
):
    """Mark a resource as completed or not completed."""
    topic_obj_id = validate_object_id(topic_id)

    # Check if topic exists
    topic = await topics_collection().find_one({"_id": topic_obj_id})
    if not topic:
        raise HTTPException(
            status_code=404, detail=f"Topic with ID {topic_id} not found"
        )

    # Check if resource index is valid
    resources = topic.get("resources", [])
    if resource_index >= len(resources):
        raise HTTPException(
            status_code=404, detail=f"Resource at index {resource_index} not found"
        )

    # Update the completion status and date
    update_data = {f"resources.{resource_index}.completed": completed}

    if completed:
        update_data[f"resources.{resource_index}.completed_date"] = datetime.now()

    # Update the resource
    result = await topics_collection().update_one(
        {"_id": topic_obj_id}, {"$set": update_data}
    )

    # Get updated topic
    updated_topic = await topics_collection().find_one({"_id": topic_obj_id})

    return ResponseModel(
        data=updated_topic,
        message=f"Resource marked as {'completed' if completed else 'not completed'}",
    )
