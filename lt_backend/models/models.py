from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId
import re

def serialize_object_id(obj_id: ObjectId) -> str:
    return str(obj_id)

# Custom ObjectId field for proper MongoDB ID handling
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# Resource model
class Resource(BaseModel):
    title: str
    url: str
    type: str  # video, article, book, course, etc.
    notes: Optional[str] = None
    completed: bool = False
    completed_date: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "FastAPI Tutorial",
                "url": "https://fastapi.tiangolo.com/",
                "type": "documentation",
                "notes": "Official FastAPI documentation",
                "completed": False
            }
        }
    }


# Topic model
class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    resources: List[Resource] = []
    tags: List[str] = []
    priority: int = Field(default=1, ge=1, le=5)  # 1-5 priority scale
    created_date: datetime = Field(default_factory=datetime.now)
    last_studied: Optional[datetime] = None
    time_spent_minutes: int = 0
    
    @validator('tags')
    def lowercase_tags(cls, v):
        return [tag.lower() for tag in v]

    model_config = {
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    tags: Optional[List[str]] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    time_spent_minutes: Optional[int] = None
    
    @validator('tags')
    def lowercase_tags(cls, v):
        if v is not None:
            return [tag.lower() for tag in v]
        return v

    model_config = {
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


class Topic(TopicBase):
    id: Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


# StudyPlan models
class StudySession(BaseModel):
    topic_id: str
    duration_minutes: int
    completed: bool = False
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


class StudyActivity(BaseModel):
    title: str
    type: str  # reading, practice, exercise, quiz, review
    description: str
    duration_minutes: int
    objective: str
    method: str
    resources_needed: List[str] = []
    checkpoint: str
    topic_id: Optional[str] = None
    topic_title: Optional[str] = None
    completed: bool = False
    completed_date: Optional[datetime] = None

    model_config = {
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


class StudyBreak(BaseModel):
    after_activity: int
    duration_minutes: int


class StudyPlanBase(BaseModel):
    user_id: str
    date: datetime
    sessions: List[StudySession]
    activities: List[StudyActivity] = []
    total_duration_minutes: int
    completed: bool = False
    focus_areas: List[str] = []
    learning_objectives: List[str] = []
    review_strategy: Optional[str] = None
    success_criteria: List[str] = []
    recommended_breaks: List[StudyBreak] = []

    model_config = {
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


class StudyPlanCreate(StudyPlanBase):
    pass


class StudyPlan(StudyPlanBase):
    id: Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


# Quiz models
class QuizQuestion(BaseModel):
    question: str
    options: List[str]  # Always require options for MCQs
    correct_answer: str  # Store the correct option (A, B, C, or D)
    explanation: str
    points: int = 1  # Points for this question
    difficulty: Optional[str] = None  # Add this field

    @validator('correct_answer')
    def validate_correct_answer(cls, v):
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('Correct answer must be A, B, C, or D')
        return v

    @validator('options')
    def validate_options(cls, v):
        if len(v) != 4:
            raise ValueError('Must provide exactly 4 options')
        return v

    model_config = {
        "json_encoders": {
            ObjectId: str
        }
    }


class QuizSubmission(BaseModel):
    question_id: int  # Index of the question in the quiz
    selected_answer: str  # The selected option (A, B, C, or D)

    @validator('selected_answer')
    def validate_selected_answer(cls, v):
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError('Selected answer must be A, B, C, or D')
        return v


class QuizResult(BaseModel):
    total_questions: int
    correct_answers: int
    score: float
    answers: List[Dict[str, Any]]  # Detailed results for each question
    completed_date: datetime = Field(default_factory=datetime.now)


class QuizBase(BaseModel):
    topic_id: str
    title: str
    questions: List[QuizQuestion]
    created_date: datetime = Field(default_factory=datetime.now)
    last_taken: Optional[datetime] = None
    times_taken: int = 0
    total_points: int = 0  # Total possible points for the quiz

    @validator('questions')
    def set_total_points(cls, v):
        total = sum(q.points for q in v)
        cls.total_points = total
        return v

    model_config = {
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


class QuizCreate(QuizBase):
    pass


class Quiz(QuizBase):
    id: Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id")]
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }


# User models (for future multi-user support)
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: Annotated[PyObjectId, Field(default_factory=PyObjectId, alias="_id", serialization_alias="_id")]
    created_date: datetime = Field(default_factory=datetime.now)
    active: bool = True
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


# Response models for API endpoints
class ResponseModel(BaseModel):
    data: Any
    message: str = "Success"

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    }


# Analytics models
class ProgressSummary(BaseModel):
    total_topics: int
    completed_topics: int
    completion_percentage: float
    total_time_spent_minutes: int
    avg_progress: float
    
    
class StudyStreak(BaseModel):
    current_streak: int
    longest_streak: int
    last_study_date: Optional[datetime] = None