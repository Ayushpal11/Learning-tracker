from fastapi import APIRouter, HTTPException, Query
from lt_backend.db import topics_collection, study_plans_collection
from lt_backend.models.models import ResponseModel, ProgressSummary, StudyStreak
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter()


@router.get("/progress", response_model=ResponseModel)
async def get_progress_summary(user_id: str = Query(...)):
    """Get progress summary for all topics."""
    # Get all topics
    topics = await topics_collection().find({}).to_list(length=1000)

    if not topics:
        raise HTTPException(status_code=404, detail="No topics found")

    # Calculate progress stats
    total_topics = len(topics)
    completed_topics = sum(1 for topic in topics if topic.get("progress", 0) >= 100)
    total_progress = sum(topic.get("progress", 0) for topic in topics)
    avg_progress = total_progress / total_topics if total_topics > 0 else 0
    total_time_spent = sum(topic.get("time_spent_minutes", 0) for topic in topics)
    completion_percentage = (
        (completed_topics / total_topics) * 100 if total_topics > 0 else 0
    )

    # Create summary object
    summary = ProgressSummary(
        total_topics=total_topics,
        completed_topics=completed_topics,
        completion_percentage=completion_percentage,
        total_time_spent_minutes=total_time_spent,
        avg_progress=avg_progress,
    )

    return ResponseModel(
        data=summary, message="Progress summary retrieved successfully"
    )


@router.get("/topic-stats", response_model=ResponseModel)
async def get_topic_stats():
    """Get detailed statistics for each topic."""
    # Get all topics
    topics = await topics_collection().find({}).to_list(length=1000)

    if not topics:
        raise HTTPException(status_code=404, detail="No topics found")

    # Process each topic to extract key stats
    topic_stats = []
    for topic in topics:
        # Calculate resource completion
        resources = topic.get("resources", [])
        completed_resources = sum(1 for r in resources if r.get("completed", False))
        resource_completion = (
            (completed_resources / len(resources)) * 100 if resources else 0
        )

        # Format last studied date
        last_studied = topic.get("last_studied")
        last_studied_formatted = last_studied.isoformat() if last_studied else None

        # Add to stats list
        topic_stats.append(
            {
                "id": str(topic["_id"]),
                "title": topic.get("title"),
                "progress": topic.get("progress", 0),
                "time_spent_minutes": topic.get("time_spent_minutes", 0),
                "resource_count": len(resources),
                "completed_resources": completed_resources,
                "resource_completion": resource_completion,
                "last_studied": last_studied_formatted,
                "priority": topic.get("priority", 1),
                "tags": topic.get("tags", []),
            }
        )

    # Sort by progress (descending)
    topic_stats.sort(key=lambda x: x["progress"], reverse=True)

    return ResponseModel(
        data=topic_stats, message="Topic statistics retrieved successfully"
    )


@router.get("/streak", response_model=ResponseModel)
async def get_study_streak(user_id: str = Query(...)):
    """Get current and longest study streaks."""
    # Get all completed study plans
    plans = (
        await study_plans_collection()
        .find({"user_id": user_id, "completed": True})
        .sort("date", 1)
        .to_list(length=1000)
    )

    if not plans:
        return ResponseModel(
            data=StudyStreak(current_streak=0, longest_streak=0),
            message="No study history found",
        )

    # Calculate streaks
    study_dates = [plan.get("date").date() for plan in plans if plan.get("date")]
    study_dates.sort()

    # Remove duplicates (in case of multiple plans on same day)
    unique_dates = []
    for date in study_dates:
        if not unique_dates or date != unique_dates[-1]:
            unique_dates.append(date)

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    current_count = 0
    last_date = None

    for date in unique_dates:
        if last_date is None:
            current_count = 1
        elif (date - last_date).days == 1:
            current_count += 1
        else:
            current_count = 1

        longest_streak = max(longest_streak, current_count)
        last_date = date

    # Check if current streak is still active
    today = datetime.now().date()
    if last_date and (today - last_date).days <= 1:
        current_streak = current_count
    else:
        current_streak = 0

    # Create streak object
    streak = StudyStreak(
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_study_date=(
            datetime.combine(last_date, datetime.min.time()) if last_date else None
        ),
    )

    return ResponseModel(data=streak, message="Study streak retrieved successfully")


@router.get("/time-distribution", response_model=ResponseModel)
async def get_time_distribution():
    """Get time spent distribution across topics."""
    # Get all topics
    topics = (
        await topics_collection()
        .find({}, {"title": 1, "time_spent_minutes": 1, "tags": 1})
        .to_list(length=1000)
    )

    if not topics:
        raise HTTPException(status_code=404, detail="No topics found")

    # Calculate time distribution by topic
    topic_distribution = [
        {
            "topic_id": str(topic["_id"]),
            "title": topic.get("title", "Unknown"),
            "time_spent_minutes": topic.get("time_spent_minutes", 0),
        }
        for topic in topics
    ]

    # Sort by time spent (descending)
    topic_distribution.sort(key=lambda x: x["time_spent_minutes"], reverse=True)

    # Calculate time distribution by tag
    tag_distribution = {}
    for topic in topics:
        time_spent = topic.get("time_spent_minutes", 0)
        tags = topic.get("tags", [])

        for tag in tags:
            if tag in tag_distribution:
                tag_distribution[tag] += time_spent
            else:
                tag_distribution[tag] = time_spent

    # Convert to list for the response
    tag_list = [
        {"tag": tag, "time_spent_minutes": minutes}
        for tag, minutes in tag_distribution.items()
    ]

    # Sort by time spent (descending)
    tag_list.sort(key=lambda x: x["time_spent_minutes"], reverse=True)

    # Calculate total time spent
    total_time = sum(topic.get("time_spent_minutes", 0) for topic in topics)

    return ResponseModel(
        data={
            "total_time_spent_minutes": total_time,
            "by_topic": topic_distribution,
            "by_tag": tag_list,
        },
        message="Time distribution retrieved successfully",
    )


@router.get("/recommendations", response_model=ResponseModel)
async def get_recommendations():
    """Get learning recommendations based on progress, activity, and gaps."""
    # Get all topics with their resources
    topics = await topics_collection().find({}).to_list(length=1000)

    if not topics:
        raise HTTPException(status_code=404, detail="No topics found")

    recommendations = {
        "neglected_topics": [],
        "almost_complete": [],
        "uncompleted_resources": [],
        "suggested_next": None,
    }

    # Current date for comparison
    now = datetime.now()
    two_weeks_ago = now - timedelta(days=14)

    # Find neglected topics (not studied in last 2 weeks but not completed)
    for topic in topics:
        last_studied = topic.get("last_studied")
        progress = topic.get("progress", 0)

        # Topic is neglected if:
        # 1. It's not been studied in the last 2 weeks
        # 2. It's not complete (progress < 95%)
        # 3. It has at least started (progress > 0)
        if (last_studied is None or last_studied < two_weeks_ago) and 0 < progress < 95:
            recommendations["neglected_topics"].append(
                {
                    "id": str(topic["_id"]),
                    "title": topic.get("title"),
                    "progress": progress,
                    "last_studied": last_studied.isoformat() if last_studied else None,
                    "days_since_studied": (
                        (now - last_studied).days if last_studied else None
                    ),
                }
            )

    # Sort neglected topics by progress (descending)
    recommendations["neglected_topics"].sort(key=lambda x: x["progress"], reverse=True)

    # Find almost complete topics (progress > 75% but < 100%)
    for topic in topics:
        progress = topic.get("progress", 0)

        if 75 <= progress < 100:
            recommendations["almost_complete"].append(
                {
                    "id": str(topic["_id"]),
                    "title": topic.get("title"),
                    "progress": progress,
                    "remaining": 100 - progress,
                }
            )

    # Sort almost complete topics by remaining progress (ascending)
    recommendations["almost_complete"].sort(key=lambda x: x["remaining"])

    # Find topics with uncompleted resources
    for topic in topics:
        resources = topic.get("resources", [])
        uncompleted = [
            {"title": r.get("title"), "type": r.get("type"), "url": r.get("url")}
            for r in resources
            if not r.get("completed", False)
        ]

        if uncompleted:
            recommendations["uncompleted_resources"].append(
                {
                    "id": str(topic["_id"]),
                    "title": topic.get("title"),
                    "uncompleted_count": len(uncompleted),
                    "resources": uncompleted[:3],  # Limit to 3 resources
                }
            )

    # Sort by uncompleted count (descending)
    recommendations["uncompleted_resources"].sort(
        key=lambda x: x["uncompleted_count"], reverse=True
    )

    # Find suggested next topic based on:
    # 1. Has some progress but not complete
    # 2. Recently studied
    # 3. High priority
    active_topics = [
        {
            "id": str(topic["_id"]),
            "title": topic.get("title"),
            "progress": topic.get("progress", 0),
            "priority": topic.get("priority", 1),
            "last_studied": topic.get("last_studied"),
        }
        for topic in topics
        if 0 < topic.get("progress", 0) < 100
    ]

    if active_topics:
        # Sort by priority (descending), then by last studied (most recent first)
        active_topics.sort(
            key=lambda x: (
                -x["priority"],
                -x["progress"],  # More progress is better
                now - x["last_studied"] if x["last_studied"] else timedelta(days=9999),
            )
        )

        recommendations["suggested_next"] = active_topics[0]

    return ResponseModel(
        data=recommendations, message="Recommendations retrieved successfully"
    )
