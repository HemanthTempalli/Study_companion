"""Pydantic schemas for all API request/response models."""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ──────────────────── Auth ─────────────────────

class UserRegister(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────── Spaces ───────────────────

class SpaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    color: str = Field(default="#6366f1", max_length=7)
    icon: str = Field(default="book", max_length=50)


class SpaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)


class SpaceOut(BaseModel):
    id: UUID
    name: str
    description: str
    color: str
    icon: str
    created_at: datetime
    updated_at: datetime
    project_count: int = 0

    model_config = {"from_attributes": True}


# ──────────────────── Projects ─────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    learning_goal: str = Field(default="", max_length=5000)
    space_id: UUID


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    learning_goal: Optional[str] = Field(None, max_length=5000)


class ProjectOut(BaseModel):
    id: UUID
    space_id: UUID
    name: str
    description: str
    learning_goal: str
    created_at: datetime
    updated_at: datetime
    material_count: int = 0
    concept_count: int = 0

    model_config = {"from_attributes": True}


class ProjectDashboard(BaseModel):
    project: ProjectOut
    recent_activity: List[dict] = []
    mastery_summary: dict = {}
    recommendation: Optional[str] = None
    quiz_stats: dict = {}


# ──────────────────── Materials ────────────────

class MaterialOut(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    file_size: int
    page_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────── Tutor ────────────────────

class TutorMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[UUID] = None


class Citation(BaseModel):
    material_name: str
    page_number: int
    content_snippet: str = ""


class TutorResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    has_sufficient_evidence: bool = True
    conversation_id: UUID


class ConversationOut(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    created_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    citations: List[dict] = []
    has_sufficient_evidence: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────── Quiz ─────────────────────

class QuizGenerateRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Optional[str] = None  # EASY, MEDIUM, HARD or None for adaptive
    focus_concepts: List[str] = []


class QuestionOut(BaseModel):
    id: UUID
    question_type: str
    concept_name: Optional[str] = None
    difficulty: str
    question_text: str
    options: Optional[List[str]] = None
    source_page: Optional[str] = None

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: UUID
    user_answer: str = Field(..., min_length=1, max_length=5000)


class AnswerFeedback(BaseModel):
    question_id: UUID
    is_correct: Optional[bool]
    score: float
    correct_answer: str
    explanation: str
    feedback: dict = {}


class QuizResult(BaseModel):
    quiz_id: UUID
    total_questions: int
    correct_answers: int
    score: float
    question_results: List[AnswerFeedback]
    mastery_updates: List[dict] = []
    weak_concepts: List[str] = []


class QuizAttemptOut(BaseModel):
    id: UUID
    total_questions: int
    correct_answers: int
    score: float
    completed: bool
    difficulty_level: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[QuestionOut] = []

    model_config = {"from_attributes": True}


# ──────────────────── Mastery ──────────────────

class MasteryOut(BaseModel):
    concept_name: str
    mastery_level: float
    evidence_count: int
    last_assessed: Optional[datetime] = None
    trend: str = "stable"  # improving, stable, declining

    model_config = {"from_attributes": True}


# ──────────────────── Growth ───────────────────

class GrowthAnalysis(BaseModel):
    improving: List[dict] = []
    stable: List[dict] = []
    needs_attention: List[dict] = []
    overall_trend: str = "stable"
    mastery_over_time: List[dict] = []
    summary: str = ""


# ──────────────────── Recommendations ──────────

class RecommendationOut(BaseModel):
    id: UUID
    recommendation_text: str
    reasoning: str
    action_type: str
    target_concepts: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────── Analytics ────────────────

class ProjectAnalytics(BaseModel):
    learning_activity: List[dict] = []
    assessment_performance: List[dict] = []
    mastery_distribution: List[dict] = []
    concept_trends: List[dict] = []
    ai_activity: dict = {}
    total_materials: int = 0
    total_conversations: int = 0
    total_quizzes: int = 0
    total_questions_answered: int = 0


class GlobalAnalytics(BaseModel):
    total_users: int = 0
    total_projects: int = 0
    total_materials: int = 0
    total_quizzes: int = 0
    total_conversations: int = 0
    ai_requests: int = 0
    learning_activity: List[dict] = []
    mastery_trends: List[dict] = []


# ──────────────────── Admin ────────────────────

class AdminUserView(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    project_count: int = 0
    quiz_count: int = 0
    last_activity: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SystemHealth(BaseModel):
    database: str = "unknown"
    background_jobs: dict = {}
    ai_service: str = "unknown"
    storage: str = "unknown"


class AIUsageLogOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    project_id: Optional[UUID]
    feature: str
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class BackgroundJobOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class AdminProjectView(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str
    space_name: str
    name: str
    created_at: datetime
    material_count: int = 0
    quiz_count: int = 0

    model_config = {"from_attributes": True}


class AIEvaluationOut(BaseModel):
    id: UUID
    feature: str
    test_case_name: str
    score: Optional[float]
    passed: Optional[bool]
    created_at: datetime

    model_config = {"from_attributes": True}
