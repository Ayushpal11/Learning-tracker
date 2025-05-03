from fastapi import APIRouter, HTTPException, Body, Query, Path
from fastapi.encoders import jsonable_encoder
from lt_backend.db import topics_collection, quiz_collection, study_plans_collection
from lt_backend.models.models import (
    QuizCreate,
    Quiz,
    QuizQuestion,
    ResponseModel,
    QuizSubmission,
    QuizResult,
)
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import random
import os
import requests
import json

router = APIRouter()


# Helper function to verify ObjectId
def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail=f"Invalid id format: {id}")


# Simple mock question generator (replace with AI-based generation in production)
def generate_mock_questions_for_topic(topic_title, topic_description, num_questions=5):
    """Generate mock quiz questions for a topic."""
    # Sample question templates
    question_templates = [
        "What is the main concept of {topic}?",
        "Which of the following is NOT related to {topic}?",
        "Which statement about {topic} is correct?",
        "Which tool is commonly used in {topic}?",
        "What's a key principle in {topic}?",
        "Which approach is best for {topic}?",
        "What's the primary purpose of {topic}?",
        "Which feature is essential in {topic}?",
        "What's the most important aspect of {topic}?",
        "Which method is commonly used in {topic}?",
    ]

    questions = []
    for i in range(min(num_questions, len(question_templates))):
        # Create a question using the template
        question_text = question_templates[i].format(topic=topic_title)

        # Create 4 options (A, B, C, D)
        options = [
            f"Option A: {topic_title} concept {i+1}",
            f"Option B: Alternative approach to {topic_title}",
            f"Option C: Related concept in {topic_title}",
            f"Option D: Common misconception about {topic_title}",
        ]

        # First option is correct in this mock
        correct_answer = "A"

        questions.append(
            QuizQuestion(
                question=question_text,
                options=options,
                correct_answer=correct_answer,
                explanation=f"Option A is correct because it directly relates to the core concept of {topic_title}.",
                points=1,
            )
        )

    return questions


# Function to generate questions using Mistral API
async def generate_mistral_questions(topic, num_questions=5, difficulty="medium"):
    """Generate quiz questions using Mistral API."""
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        return generate_mock_questions_for_topic(
            topic, f"Description of {topic}", num_questions
        )
    try:
        url = "https://api.mistral.ai/v1/chat/completions"
        prompt = f"""
        Generate {num_questions} multiple choice quiz questions about {topic} at {difficulty} difficulty.
        For each question:
        1. Write a clear, concise question
        2. Provide exactly 4 options labeled A, B, C, D
        3. Indicate the correct answer (A, B, C, or D)
        4. Give a brief explanation of why the answer is correct
        Format each question in this exact JSON structure:
        {{
            "question": "What is...",
            "options": [
                "A) First option",
                "B) Second option",
                "C) Third option",
                "D) Fourth option"
            ],
            "correct_answer": "A",
            "explanation": "This is correct because..."
        }}
        Return an array of these question objects. Make sure:
        - Each question tests understanding, not just memorization
        - Options are plausible but only one is clearly correct
        - Explanations are helpful for learning
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
                    "content": "You are an expert quiz creator who generates clear, educational multiple choice questions.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        try:
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                questions_data = json.loads(json_str)
            else:
                questions_data = json.loads(content)
            questions = []
            for q_data in questions_data:
                options = q_data.get("options", [])
                options = [
                    opt.split(") ", 1)[-1] if ") " in opt else opt for opt in options
                ]
                questions.append(
                    QuizQuestion(
                        question=q_data.get("question", ""),
                        options=options,
                        correct_answer=q_data.get("correct_answer", ""),
                        explanation=q_data.get("explanation", ""),
                        points=1,
                        difficulty=difficulty,
                    )
                )
            return questions
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from Mistral API response: {e}")
            return generate_mock_questions_for_topic(
                topic, f"Description of {topic}", num_questions
            )
    except Exception as e:
        print(f"Error generating questions with Mistral API: {e}")
        return generate_mock_questions_for_topic(
            topic, f"Description of {topic}", num_questions
        )


@router.post("/generate", response_model=ResponseModel)
async def generate_quiz(
    topic_id: str = Body(...),
    num_questions: int = Body(5, ge=3, le=20),
    title: Optional[str] = Body(None),
    difficulty: Optional[str] = Body("medium"),
):
    """Generate a quiz for a specific topic."""
    topic_obj_id = validate_object_id(topic_id)

    # Check if topic exists
    topic = await topics_collection().find_one({"_id": topic_obj_id})
    if not topic:
        raise HTTPException(
            status_code=404, detail=f"Topic with ID {topic_id} not found"
        )

    # Generate default title if not provided
    if not title:
        title = f"Quiz on {topic.get('title', 'Topic')}"

    # Generate questions
    try:
        questions = await generate_mistral_questions(
            topic.get("title", "Topic"), num_questions, difficulty
        )
    except Exception as e:
        print(f"Error generating questions: {e}")
        questions = generate_mock_questions_for_topic(
            topic.get("title", ""), topic.get("description", ""), num_questions
        )

    # Add difficulty to each question
    for q in questions:
        q.difficulty = difficulty

    # Create quiz object
    quiz = QuizCreate(
        topic_id=str(topic_obj_id),
        title=title,
        questions=questions,
        created_date=datetime.now(),
        last_taken=None,
        times_taken=0,
    )

    # Save to database
    quiz_data = jsonable_encoder(quiz)
    new_quiz = await quiz_collection().insert_one(quiz_data)

    # Get created quiz and handle ObjectId serialization
    created_quiz = await quiz_collection().find_one({"_id": new_quiz.inserted_id})
    if created_quiz:
        # Convert _id to string
        created_quiz["_id"] = str(created_quiz["_id"])
        # Convert topic_id to string
        if "topic_id" in created_quiz:
            created_quiz["topic_id"] = str(created_quiz["topic_id"])
        # Convert any ObjectIds in questions
        if "questions" in created_quiz:
            for question in created_quiz["questions"]:
                if "_id" in question:
                    question["_id"] = str(question["_id"])

    return ResponseModel(data=created_quiz, message="Quiz generated successfully")


@router.post("/quiz/generate-custom", response_model=ResponseModel)
async def generate_custom_quiz(
    topic: str = Body(...),
    num_questions: int = Body(5, ge=3, le=20),
    title: Optional[str] = Body(None),
):
    """Generate a quiz for a custom topic provided by the user."""
    # Generate default title if not provided
    if not title:
        title = f"Quiz on {topic}"

    # Generate questions using Mistral API
    try:
        questions = await generate_mistral_questions(topic, num_questions)
    except Exception as e:
        print(f"Error generating questions: {e}")
        questions = generate_mock_questions_for_topic(
            topic, f"Description of {topic}", num_questions
        )

    # Create quiz object
    quiz = QuizCreate(
        topic_id=None,  # No associated topic ID for custom quizzes
        title=title,
        questions=questions,
        created_date=datetime.now(),
        last_taken=None,
        times_taken=0,
    )

    # Save to database
    quiz_data = jsonable_encoder(quiz)
    new_quiz = await quiz_collection().insert_one(quiz_data)

    # Retrieve created quiz
    created_quiz = await quiz_collection().find_one({"_id": new_quiz.inserted_id})

    return ResponseModel(
        data=created_quiz, message="Custom quiz generated successfully"
    )


@router.get("/{quiz_id}", response_model=ResponseModel)
async def get_quiz(quiz_id: str):
    """Get a specific quiz."""
    quiz_obj_id = validate_object_id(quiz_id)

    # Find the quiz
    quiz = await quiz_collection().find_one({"_id": quiz_obj_id})
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

    # Handle ObjectId serialization
    quiz["_id"] = str(quiz["_id"])
    if "topic_id" in quiz and isinstance(quiz["topic_id"], ObjectId):
        quiz["topic_id"] = str(quiz["topic_id"])

    return ResponseModel(data=quiz, message="Quiz retrieved successfully")


@router.get("/topic/{topic_id}/quizzes", response_model=ResponseModel)
async def get_quizzes_by_topic(topic_id: str):
    """Get all quizzes for a specific topic."""
    # Validate topic ID format
    validate_object_id(topic_id)

    # Find quizzes for the topic
    quizzes = await quiz_collection().find({"topic_id": topic_id}).to_list(length=100)

    return ResponseModel(
        data=quizzes, message=f"Found {len(quizzes)} quizzes for the topic"
    )


@router.post("/{quiz_id}/take", response_model=ResponseModel)
async def take_quiz(quiz_id: str, answers: List[QuizSubmission] = Body(...)):
    """Submit answers for a quiz and get results."""
    quiz_obj_id = validate_object_id(quiz_id)

    # Find the quiz
    quiz = await quiz_collection().find_one({"_id": quiz_obj_id})
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

    # Validate answers
    if len(answers) != len(quiz.get("questions", [])):
        raise HTTPException(
            status_code=400,
            detail=f"Number of answers ({len(answers)}) does not match number of questions ({len(quiz['questions'])})",
        )

    # Grade the quiz
    correct_count = 0
    total_points = 0
    max_points = 0
    results = []

    for answer in answers:
        question = quiz["questions"][answer.question_id]
        max_points += question.get("points", 1)

        is_correct = answer.selected_answer == question["correct_answer"]
        if is_correct:
            correct_count += 1
            total_points += question.get("points", 1)

        results.append(
            {
                "question_id": answer.question_id,
                "question": question["question"],
                "your_answer": answer.selected_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": is_correct,
                "points_earned": question.get("points", 1) if is_correct else 0,
                "max_points": question.get("points", 1),
                "explanation": question.get("explanation", ""),
            }
        )

    # Calculate score as percentage
    score = (total_points / max_points * 100) if max_points > 0 else 0

    # Create quiz result
    quiz_result = QuizResult(
        total_questions=len(quiz["questions"]),
        correct_answers=correct_count,
        score=score,
        answers=results,
        completed_date=datetime.now(),
    )

    # If score is 100%, update topic progress and delete the quiz
    if score == 100 and quiz.get("topic_id"):
        topic_obj_id = ObjectId(quiz["topic_id"])
        topic = await topics_collection().find_one({"_id": topic_obj_id})

        if topic:
            # Calculate time spent (assume average of 2 minutes per question)
            time_spent = len(quiz["questions"]) * 2

            # Update topic progress
            current_progress = topic.get("progress", 0)
            # Increase progress by 10-20% for mastering a quiz
            progress_increase = min(100 - current_progress, random.uniform(10, 20))
            new_progress = current_progress + progress_increase

            # Update topic
            await topics_collection().update_one(
                {"_id": topic_obj_id},
                {
                    "$set": {"progress": new_progress, "last_studied": datetime.now()},
                    "$inc": {"time_spent_minutes": time_spent},
                },
            )

            # Delete the mastered quiz
            await quiz_collection().delete_one({"_id": quiz_obj_id})

            # Generate a new study plan based on updated progress
            try:
                await generate_adaptive_study_plan(str(topic_obj_id))
            except Exception as e:
                print(f"Error generating adaptive study plan: {e}")
    else:
        # Just update quiz metadata for non-perfect scores
        await quiz_collection().update_one(
            {"_id": quiz_obj_id},
            {"$set": {"last_taken": datetime.now()}, "$inc": {"times_taken": 1}},
        )

    return ResponseModel(
        data={
            "result": quiz_result.dict(),
            "perfect_score": score == 100,
            "topic_updated": score == 100 and quiz.get("topic_id") is not None,
        },
        message="Quiz completed successfully",
    )


async def generate_adaptive_study_plan(topic_id: str):
    """Generate an AI-powered adaptive study plan based on topic progress."""
    topic = await topics_collection().find_one({"_id": ObjectId(topic_id)})
    if not topic:
        return

    # Get Mistral API key
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if not mistral_api_key:
        return

    try:
        # Create a prompt for study plan generation
        prompt = f"""
        Create a personalized study plan for the topic: {topic.get('title')}
        
        Current progress: {topic.get('progress')}%
        Time spent so far: {topic.get('time_spent_minutes')} minutes
        
        Based on this information, create a structured study plan that:
        1. Identifies areas that need more focus
        2. Suggests specific learning activities
        3. Estimates time needed for each activity
        4. Sets measurable learning objectives
        
        Format the response as a JSON object with this structure:
        {{
            "focus_areas": ["area1", "area2"],
            "activities": [
                {{
                    "title": "Activity name",
                    "type": "reading|practice|quiz|exercise",
                    "duration_minutes": 30,
                    "objective": "What you'll learn"
                }}
            ],
            "total_duration_minutes": 120,
            "learning_objectives": ["objective1", "objective2"]
        }}
        """

        # Call Mistral API
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {mistral_api_key}",
            },
            json={
                "model": "mistral-medium",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert learning advisor who creates personalized study plans.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            },
        )

        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Parse the study plan
        try:
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                plan_data = json.loads(content[start_idx:end_idx])
            else:
                plan_data = json.loads(content)

            # Create study plan
            study_plan = {
                "user_id": "default",  # Replace with actual user ID when available
                "topic_id": topic_id,
                "date": datetime.now(),
                "focus_areas": plan_data.get("focus_areas", []),
                "activities": plan_data.get("activities", []),
                "total_duration_minutes": plan_data.get("total_duration_minutes", 0),
                "learning_objectives": plan_data.get("learning_objectives", []),
                "completed": False,
            }

            # Save the study plan
            await study_plans_collection().insert_one(study_plan)

        except json.JSONDecodeError as e:
            print(f"Error parsing study plan JSON: {e}")

    except Exception as e:
        print(f"Error generating adaptive study plan: {e}")


@router.get("/", response_model=ResponseModel)
async def get_all_quizzes(
    skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)
):
    """Get all quizzes with pagination."""
    # Find quizzes with pagination
    cursor = quiz_collection().find().sort("created_date", -1).skip(skip).limit(limit)

    # Convert to list and handle ObjectId serialization
    quizzes = []
    async for doc in cursor:
        # Convert _id to string
        doc["_id"] = str(doc["_id"])
        # Convert topic_id to string if it exists
        if "topic_id" in doc:
            doc["topic_id"] = str(doc["topic_id"])
        # Convert any ObjectIds in questions
        if "questions" in doc:
            for question in doc["questions"]:
                if "_id" in question:
                    question["_id"] = str(question["_id"])
        quizzes.append(doc)

    # Get total count for pagination
    total_count = await quiz_collection().count_documents({})

    return ResponseModel(
        data={"quizzes": quizzes, "total": total_count, "skip": skip, "limit": limit},
        message="Quizzes retrieved successfully",
    )


@router.delete("/{quiz_id}", response_model=ResponseModel)
async def delete_quiz(quiz_id: str):
    """Delete a specific quiz."""
    quiz_obj_id = validate_object_id(quiz_id)

    # Check if quiz exists
    quiz = await quiz_collection().find_one({"_id": quiz_obj_id})
    if not quiz:
        raise HTTPException(status_code=404, detail=f"Quiz with ID {quiz_id} not found")

    # Delete the quiz
    result = await quiz_collection().delete_one({"_id": quiz_obj_id})

    if result.deleted_count == 1:
        return ResponseModel(data={"id": quiz_id}, message="Quiz deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete quiz")


@router.get("/topics", response_model=ResponseModel)
async def get_quiz_topics():
    """Get all available topics for quiz generation."""
    cursor = topics_collection().find({}, {"title": 1, "description": 1})

    topics = []
    async for doc in cursor:
        topics.append(
            {
                "id": str(doc["_id"]),
                "title": doc.get("title", ""),
                "description": doc.get("description", ""),
            }
        )

    return ResponseModel(data=topics, message="Topics retrieved successfully")
