from fastapi import APIRouter, HTTPException, Body, Query, Path, status
from fastapi.encoders import jsonable_encoder
from db import study_plans_collection, topics_collection
from models.models import (
    StudyPlan,
    StudyPlanCreate,
    StudySession,
    ResponseModel,
)
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import random
import os
import requests
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pydantic import BaseModel

router = APIRouter()


# Helper function to verify ObjectId
def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail=f"Invalid id format: {id}")


# Helper to recursively convert ObjectId to str
def convert_objectid_to_str(obj):
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj


async def generate_mistral_study_plan(topic_data, total_minutes):
    """Generate a personalized study plan using Mistral AI."""
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

    if not mistral_api_key:
        return None

    try:
        url = "https://api.mistral.ai/v1/chat/completions"

        # Create a detailed prompt for the study plan
        topic_info = {
            "title": topic_data.get("title", "Unknown Topic"),
            "description": topic_data.get("description", ""),
            "current_progress": topic_data.get("progress", 0),
            "time_spent": topic_data.get("time_spent_minutes", 0),
            "resources": [r.get("title") for r in topic_data.get("resources", [])],
        }

        prompt = f"""
        Create a comprehensive study plan for: {topic_info['title']}
        Topic Description: {topic_info['description']}
        Current Progress: {topic_info['current_progress']}%
        Time Already Spent: {topic_info['time_spent']} minutes
        Available Resources: {', '.join(topic_info['resources']) if topic_info['resources'] else 'None'}
        Total Time Available: {total_minutes} minutes

        Create a detailed study plan that includes actual learning content. For each focus area and activity:
        1. Provide comprehensive explanations and summaries
        2. Include practical code examples where relevant
        3. Add learning tips and best practices
        4. Include revision notes and key points to remember
        5. Provide specific examples and use cases
        6. Include troubleshooting guides where applicable

        Format the response as a JSON object with this structure:
        {{
            "focus_areas": [
                {{
                    "title": "Area Title",
                    "summary": "Detailed explanation of this area",
                    "key_concepts": ["concept1", "concept2"],
                    "best_practices": ["practice1", "practice2"]
                }}
            ],
            "learning_objectives": [
                {{
                    "objective": "What you'll learn",
                    "importance": "Why this matters",
                    "practical_application": "How you'll use this"
                }}
            ],
            "activities": [
                {{
                    "title": "Activity name",
                    "type": "reading|practice|exercise|quiz|review",
                    "content": {{
                        "introduction": "Brief intro to the topic",
                        "main_content": "Detailed explanation with examples",
                        "code_examples": [
                            {{
                                "title": "Example title",
                                "language": "programming language",
                                "code": "actual code here",
                                "explanation": "What the code does"
                            }}
                        ],
                        "key_points": ["point1", "point2"],
                        "common_pitfalls": ["pitfall1", "pitfall2"],
                        "best_practices": ["practice1", "practice2"]
                    }},
                    "duration_minutes": 30,
                    "learning_tips": ["tip1", "tip2"],
                    "revision_notes": "Key points to review later",
                    "practice_exercises": [
                        {{
                            "description": "What to do",
                            "difficulty": "beginner|intermediate|advanced",
                            "steps": ["step1", "step2"]
                        }}
                    ]
                }}
            ],
            "review_strategy": {{
                "approach": "How to review the material",
                "key_review_points": ["point1", "point2"],
                "spaced_repetition_schedule": "When to review"
            }},
            "success_criteria": [
                {{
                    "criterion": "What to achieve",
                    "verification": "How to verify you've learned it"
                }}
            ],
            "recommended_breaks": [
                {{
                    "after_activity": 1,
                    "duration_minutes": 5,
                    "break_activity": "What to do during break"
                }}
            ]
        }}

        Make sure to:
        1. Include actual educational content, not just placeholders
        2. Provide real code examples when relevant
        3. Include specific, actionable learning tips
        4. Make content easy to understand and remember
        5. Focus on practical applications
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {mistral_api_key}",
        }

        payload = {
            "model": "mistral-medium",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert learning advisor who creates detailed, content-rich study plans based on cognitive science and learning research. You provide actual educational content, not just structure.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        # Extract JSON from response
        try:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                plan_data = json.loads(content[start_idx:end_idx])
            else:
                plan_data = json.loads(content)

            return plan_data

        except json.JSONDecodeError as e:
            print(f"Error parsing Mistral response: {e}")
            return None

    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return None


@router.post("/generate", response_model=ResponseModel)
async def generate_study_plan(
    user_id: str = Body(...),
    date: Optional[datetime] = Body(None),
    total_minutes: int = Body(..., gt=0),
    topic_ids: Optional[List[str]] = Body(None),
    prioritize_low_progress: bool = Body(True),
):
    """Generate a personalized study plan based on available topics."""
    if date is None:
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Validate topic IDs
    valid_topic_ids = []
    if topic_ids:
        for topic_id in topic_ids:
            valid_topic_ids.append(validate_object_id(topic_id))

    # Query topics
    query = {}
    if valid_topic_ids:
        query["_id"] = {"$in": valid_topic_ids}

    available_topics = await topics_collection().find(query).to_list(length=100)

    if not available_topics:
        raise HTTPException(
            status_code=404, detail="No topics available for study plan"
        )

    # Sort topics by priority and progress
    if prioritize_low_progress:
        available_topics.sort(
            key=lambda x: (x.get("progress", 0), -x.get("priority", 1))
        )
    else:
        available_topics.sort(
            key=lambda x: (-x.get("priority", 1), x.get("progress", 0))
        )

    # Generate AI study plan for each topic
    study_plan_data = {
        "user_id": user_id,
        "date": date,
        "total_duration_minutes": total_minutes,
        "focus_areas": [],
        "learning_objectives": [],
        "activities": [],
        "sessions": [],
        "review_strategy": "",
        "success_criteria": [],
        "recommended_breaks": [],
        "completed": False,
    }

    remaining_minutes = total_minutes

    for topic in available_topics:
        if remaining_minutes <= 0:
            break

        # Allocate time for this topic
        topic_minutes = min(
            int(remaining_minutes * 0.4),  # Max 40% of remaining time per topic
            max(30, remaining_minutes),  # At least 30 minutes if available
        )

        # Generate AI plan for this topic
        topic_plan = await generate_mistral_study_plan(topic, topic_minutes)

        if topic_plan:
            # Add topic-specific activities
            for activity in topic_plan.get("activities", []):
                if remaining_minutes <= 0:
                    break

                duration = min(activity["duration_minutes"], remaining_minutes)
                activity["topic_id"] = str(topic["_id"])
                activity["topic_title"] = topic["title"]
                study_plan_data["activities"].append(activity)
                remaining_minutes -= duration

            # Add focus areas and objectives
            study_plan_data["focus_areas"].extend(topic_plan.get("focus_areas", []))
            study_plan_data["learning_objectives"].extend(
                topic_plan.get("learning_objectives", [])
            )

            # Add review strategy if not set
            if not study_plan_data["review_strategy"] and topic_plan.get(
                "review_strategy"
            ):
                study_plan_data["review_strategy"] = topic_plan["review_strategy"]

            # Add success criteria
            study_plan_data["success_criteria"].extend(
                topic_plan.get("success_criteria", [])
            )

            # Add recommended breaks
            study_plan_data["recommended_breaks"].extend(
                topic_plan.get("recommended_breaks", [])
            )

            # Create a study session for this topic
            study_plan_data["sessions"].append(
                {
                    "topic_id": str(topic["_id"]),
                    "duration_minutes": topic_minutes,
                    "completed": False,
                }
            )

    # Remove duplicates from lists
    study_plan_data["focus_areas"] = list(set(study_plan_data["focus_areas"]))
    study_plan_data["learning_objectives"] = list(
        set(study_plan_data["learning_objectives"])
    )
    study_plan_data["success_criteria"] = list(set(study_plan_data["success_criteria"]))

    # Save to database
    new_plan = await study_plans_collection().insert_one(study_plan_data)

    # Retrieve created plan
    created_plan = await study_plans_collection().find_one(
        {"_id": new_plan.inserted_id}
    )
    if created_plan:
        created_plan["_id"] = str(created_plan["_id"])

        # Convert any nested ObjectIds to strings
        for session in created_plan.get("sessions", []):
            if "topic_id" in session and isinstance(session["topic_id"], ObjectId):
                session["topic_id"] = str(session["topic_id"])

        for activity in created_plan.get("activities", []):
            if "topic_id" in activity and isinstance(activity["topic_id"], ObjectId):
                activity["topic_id"] = str(activity["topic_id"])

    return ResponseModel(
        data=created_plan, message="AI-powered study plan generated successfully"
    )


@router.get("/today", response_model=ResponseModel)
async def get_today_plan(user_id: str = Query(...)):
    """Get the study plan for today."""
    # Get today's date with time set to midnight
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    # Find plan for today
    plan = await study_plans_collection().find_one(
        {"user_id": user_id, "date": {"$gte": today, "$lt": tomorrow}}
    )

    if not plan:
        # No plan exists for today
        return ResponseModel(data=None, message="No study plan found for today")

    # Enrich plan with topic details
    enriched_sessions = []
    for session in plan.get("sessions", []):
        topic_id = session.get("topic_id")
        if topic_id:
            try:
                topic = await topics_collection().find_one({"_id": ObjectId(topic_id)})
                if topic:
                    session["topic_title"] = topic.get("title")
                    session["topic_progress"] = topic.get("progress", 0)
            except Exception:
                # If topic not found, just continue
                pass
        enriched_sessions.append(session)

    plan["sessions"] = enriched_sessions

    return ResponseModel(data=plan, message="Today's study plan retrieved successfully")


@router.put("/mark-complete", response_model=ResponseModel)
async def mark_session_complete(
    plan_id: str = Body(...),
    session_index: int = Body(..., ge=0),
    completed: bool = Body(...),
    actual_minutes: Optional[int] = Body(None),
):
    """Mark a study session as completed."""
    plan_obj_id = validate_object_id(plan_id)

    # Check if plan exists
    plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    if not plan:
        raise HTTPException(
            status_code=404, detail=f"Study plan with ID {plan_id} not found"
        )

    # Check if session index is valid
    sessions = plan.get("sessions", [])
    if session_index >= len(sessions):
        raise HTTPException(
            status_code=404, detail=f"Session at index {session_index} not found"
        )

    # Get the session to update
    session = sessions[session_index]

    # Update the session's completion status
    update_data = {f"sessions.{session_index}.completed": completed}

    if completed:
        update_data[f"sessions.{session_index}.completed_date"] = datetime.now()

    # If actual time spent is provided, update it
    if actual_minutes is not None and actual_minutes >= 0:
        update_data[f"sessions.{session_index}.duration_minutes"] = actual_minutes

    # Update the plan in the database
    result = await study_plans_collection().update_one(
        {"_id": plan_obj_id}, {"$set": update_data}
    )

    # If completed, also update the topic's progress and time spent
    if completed and "topic_id" in session:
        topic_id = session["topic_id"]
        try:
            topic_obj_id = ObjectId(topic_id)

            # Get the topic
            topic = await topics_collection().find_one({"_id": topic_obj_id})
            if topic:
                # Calculate new progress - this is a simple linear increment
                current_progress = topic.get("progress", 0)
                # Increment by approximately 5-10% for each completed session
                new_progress = min(100, current_progress + random.uniform(5, 10))

                # Update the topic with new progress and time spent
                duration = session.get("duration_minutes", 0)
                if actual_minutes is not None:
                    duration = actual_minutes

                await topics_collection().update_one(
                    {"_id": topic_obj_id},
                    {
                        "$set": {
                            "progress": new_progress,
                            "last_studied": datetime.now(),
                        },
                        "$inc": {"time_spent_minutes": duration},
                    },
                )
        except Exception as e:
            # If updating the topic fails, just log and continue
            print(f"Error updating topic: {e}")

    # Check if all sessions are completed
    updated_plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    all_completed = all(
        s.get("completed", False) for s in updated_plan.get("sessions", [])
    )

    if all_completed:
        # Mark the entire plan as completed
        await study_plans_collection().update_one(
            {"_id": plan_obj_id}, {"$set": {"completed": True}}
        )

    # Get the updated plan
    final_plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    final_plan = convert_objectid_to_str(final_plan)

    return ResponseModel(
        data=final_plan,
        message=f"Session {'marked as completed' if completed else 'marked as incomplete'}",
    )


@router.get("/{plan_id}", response_model=ResponseModel)
async def get_plan(plan_id: str):
    """Get a specific study plan."""
    plan_obj_id = validate_object_id(plan_id)

    # Find the plan
    plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    if not plan:
        raise HTTPException(
            status_code=404, detail=f"Study plan with ID {plan_id} not found"
        )

    # Enrich with topic details
    enriched_sessions = []
    for session in plan.get("sessions", []):
        topic_id = session.get("topic_id")
        if topic_id:
            try:
                topic = await topics_collection().find_one({"_id": ObjectId(topic_id)})
                if topic:
                    session["topic_title"] = topic.get("title")
                    session["topic_progress"] = topic.get("progress", 0)
            except Exception:
                # If topic not found, just continue
                pass
        enriched_sessions.append(session)

    plan["sessions"] = enriched_sessions

    return ResponseModel(data=plan, message="Study plan retrieved successfully")


@router.get("/", response_model=ResponseModel)
async def get_plans(
    user_id: str = Query("default"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """Get all study plans with pagination."""
    try:
        # Build query
        query = {"user_id": user_id}

        # Execute query with pagination
        cursor = (
            study_plans_collection()
            .find(query)
            .sort("date", -1)
            .skip(skip)
            .limit(limit)
        )

        # Convert to list and handle ObjectId serialization
        plans = []
        async for doc in cursor:
            # Convert ObjectIds to strings
            doc["_id"] = str(doc["_id"])

            # Convert topic IDs in sessions and activities
            if "sessions" in doc:
                for session in doc["sessions"]:
                    if "topic_id" in session:
                        session["topic_id"] = str(session["topic_id"])

            if "activities" in doc:
                for activity in doc["activities"]:
                    if "topic_id" in activity:
                        activity["topic_id"] = str(activity["topic_id"])

            # Get topic details for each session/activity
            if "sessions" in doc:
                for session in doc["sessions"]:
                    if "topic_id" in session:
                        topic = await topics_collection().find_one(
                            {"_id": ObjectId(session["topic_id"])}
                        )
                        if topic:
                            session["topic_title"] = topic.get("title")
                            session["topic_progress"] = topic.get("progress", 0)

            plans.append(doc)

        # Get total count for pagination
        total_count = await study_plans_collection().count_documents(query)

        return ResponseModel(
            data={"plans": plans, "total": total_count, "skip": skip, "limit": limit},
            message="Study plans retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving study plans: {str(e)}"
        )


@router.put("/mark-activity-complete", response_model=ResponseModel)
async def mark_activity_complete(
    plan_id: str = Body(...),
    activity_index: int = Body(..., ge=0),
    completed: bool = Body(...),
):
    """Mark a study activity as completed."""
    plan_obj_id = validate_object_id(plan_id)

    # Check if plan exists
    plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    if not plan:
        raise HTTPException(
            status_code=404, detail=f"Study plan with ID {plan_id} not found"
        )

    # Check if activity index is valid
    activities = plan.get("activities", [])
    if activity_index >= len(activities):
        raise HTTPException(
            status_code=404, detail=f"Activity at index {activity_index} not found"
        )

    # Update the activity's completion status
    update_data = {f"activities.{activity_index}.completed": completed}

    if completed:
        update_data[f"activities.{activity_index}.completed_date"] = datetime.now()

    # Update the plan in the database
    result = await study_plans_collection().update_one(
        {"_id": plan_obj_id}, {"$set": update_data}
    )

    # Check if all activities are completed
    updated_plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    all_completed = all(
        activity.get("completed", False)
        for activity in updated_plan.get("activities", [])
    )

    if all_completed:
        # Mark the entire plan as completed
        await study_plans_collection().update_one(
            {"_id": plan_obj_id}, {"$set": {"completed": True}}
        )

    # Get the updated plan
    final_plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    final_plan = convert_objectid_to_str(final_plan)

    return ResponseModel(
        data=final_plan,
        message=f"Activity {'marked as completed' if completed else 'marked as incomplete'}",
    )


class EmailRequest(BaseModel):
    email: str


@router.post("/{plan_id}/calendar", response_model=ResponseModel)
async def add_to_google_calendar(plan_id: str, req: EmailRequest):
    email = req.email
    plan_obj_id = validate_object_id(plan_id)
    plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    if not plan:
        raise HTTPException(
            status_code=404, detail=f"Study plan with ID {plan_id} not found"
        )
    try:
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
        service = build("calendar", "v3", credentials=creds)
        events = []
        start_time = datetime.fromisoformat(plan["date"].isoformat())
        for activity in plan.get("activities", []):
            event = {
                "summary": f"Study: {activity['title']}",
                "description": activity.get("content", {}).get("main_content", ""),
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": (
                        start_time + timedelta(minutes=activity["duration_minutes"])
                    ).isoformat(),
                    "timeZone": "UTC",
                },
                "attendees": [{"email": email}],
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},
                        {"method": "popup", "minutes": 30},
                    ],
                },
            }
            created_event = (
                service.events()
                .insert(calendarId="primary", body=event, sendUpdates="all")
                .execute()
            )
            events.append(created_event)
            start_time = start_time + timedelta(minutes=activity["duration_minutes"])
            if plan.get("recommended_breaks"):
                for break_ in plan["recommended_breaks"]:
                    if break_["after_activity"] == len(events):
                        start_time = start_time + timedelta(
                            minutes=break_["duration_minutes"]
                        )
        return ResponseModel(
            data={"events": events},
            message="Study plan added to Google Calendar and invitation sent",
        )
    except Exception as e:
        print(f"Error adding to Google Calendar: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to add study plan to Google Calendar"
        )


@router.delete("/{plan_id}", response_model=ResponseModel)
async def delete_plan(plan_id: str):
    """Delete a study plan."""
    plan_obj_id = validate_object_id(plan_id)

    # Check if plan exists
    plan = await study_plans_collection().find_one({"_id": plan_obj_id})
    if not plan:
        raise HTTPException(
            status_code=404, detail=f"Study plan with ID {plan_id} not found"
        )

    # Delete the plan
    result = await study_plans_collection().delete_one({"_id": plan_obj_id})

    if result.deleted_count == 1:
        return ResponseModel(
            data={"id": plan_id}, message="Study plan deleted successfully"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to delete study plan")
