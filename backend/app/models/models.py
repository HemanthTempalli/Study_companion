"""All SQLAlchemy models for the AI Study Companion.

20+ tables covering users, spaces, projects, materials, knowledge,
conversations, assessments, mastery, events, recommendations, jobs, and AI logs.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Index, Enum as SQLEnum, JSON, BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.database.session import Base
import enum


# ──────────────────────────── Enums ────────────────────────────

class MaterialStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, enum.Enum):
    PROCESS_MATERIAL = "PROCESS_MATERIAL"
    EXTRACT_CONCEPTS = "EXTRACT_CONCEPTS"
    GENERATE_EMBEDDINGS = "GENERATE_EMBEDDINGS"
    UPDATE_MASTERY = "UPDATE_MASTERY"
    GENERATE_RECOMMENDATION = "GENERATE_RECOMMENDATION"


class QuestionType(str, enum.Enum):
    MCQ = "MCQ"
    OPEN_ENDED = "OPEN_ENDED"


class Difficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class EventType(str, enum.Enum):
    PROJECT_CREATED = "PROJECT_CREATED"
    MATERIAL_UPLOADED = "MATERIAL_UPLOADED"
    MATERIAL_READY = "MATERIAL_READY"
    MATERIAL_FAILED = "MATERIAL_FAILED"
    TUTOR_INTERACTION = "TUTOR_INTERACTION"
    QUIZ_STARTED = "QUIZ_STARTED"
    QUESTION_ANSWERED = "QUESTION_ANSWERED"
    ASSESSMENT_COMPLETED = "ASSESSMENT_COMPLETED"
    MASTERY_UPDATED = "MASTERY_UPDATED"
    RECOMMENDATION_GENERATED = "RECOMMENDATION_GENERATED"


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


# ──────────────────────── Helper mixin ─────────────────────────

def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return uuid.uuid4()


# ──────────────────────────── Users ────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole, native_enum=False), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    spaces = relationship("Space", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


# ──────────────────────────── Spaces ───────────────────────────

class Space(Base):
    __tablename__ = "spaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    color = Column(String(7), default="#6366f1")  # Visual customization
    icon = Column(String(50), default="book")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="spaces")
    projects = relationship("Project", back_populates="space", cascade="all, delete-orphan")


# ──────────────────────────── Projects ─────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    learning_goal = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="projects")
    space = relationship("Space", back_populates="projects")
    materials = relationship("Material", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    concepts = relationship("ProjectConcept", back_populates="project", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="project", cascade="all, delete-orphan")
    learning_context = relationship("LearningContext", back_populates="project", uselist=False, cascade="all, delete-orphan")
    mastery_records = relationship("MasteryRecord", back_populates="project", cascade="all, delete-orphan")
    learning_events = relationship("LearningEvent", back_populates="project", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="project", cascade="all, delete-orphan")


# ──────────────────────────── Materials ────────────────────────

class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, default=0)
    page_count = Column(Integer, default=0)
    status = Column(SQLEnum(MaterialStatus, native_enum=False), default=MaterialStatus.QUEUED, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    project = relationship("Project", back_populates="materials")
    chunks = relationship("DocumentChunk", back_populates="material", cascade="all, delete-orphan")


# ──────────────────────── Document Chunks ──────────────────────

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # all-MiniLM-L6-v2 = 384 dims
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    material = relationship("Material", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_project_embedding", "project_id"),
    )


# ──────────────────────────── Concepts ─────────────────────────

class Concept(Base):
    __tablename__ = "concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class ProjectConcept(Base):
    __tablename__ = "project_concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="SET NULL"), nullable=True)
    relevance_score = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    project = relationship("Project", back_populates="concepts")
    concept = relationship("Concept")


# ──────────────────────── Conversations ────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), default="New conversation")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=list)  # [{material_name, page_number, chunk_content}]
    has_sufficient_evidence = Column(Boolean, default=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


# ──────────────────── Learning Context ─────────────────────────

class LearningContext(Base):
    __tablename__ = "learning_context"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    learning_goals = Column(JSON, default=list)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    important_history = Column(JSON, default=list)  # Significant interactions
    repeated_mistakes = Column(JSON, default=list)
    last_activity = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    project = relationship("Project", back_populates="learning_context")


# ──────────────────────── Quiz System ──────────────────────────

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    completed = Column(Boolean, default=False)
    difficulty_level = Column(SQLEnum(Difficulty, native_enum=False), default=Difficulty.MEDIUM)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="quiz_attempts")
    questions = relationship("Question", back_populates="quiz_attempt", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    quiz_attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type = Column(SQLEnum(QuestionType, native_enum=False), nullable=False)
    concept_name = Column(String(500), nullable=True)
    difficulty = Column(SQLEnum(Difficulty, native_enum=False), default=Difficulty.MEDIUM)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)  # For MCQ: ["A", "B", "C", "D"]
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, default="")
    source_page = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    quiz_attempt = relationship("QuizAttempt", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)  # null for open-ended until evaluated
    score = Column(Float, default=0.0)  # 0-100
    feedback = Column(JSON, default=dict)  # Structured feedback for open-ended
    evaluated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    question = relationship("Question", back_populates="answer")


# ──────────────────── Mastery Records ──────────────────────────

class MasteryRecord(Base):
    __tablename__ = "mastery_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_name = Column(String(500), nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0-100
    evidence_count = Column(Integer, default=0)
    last_assessed = Column(DateTime(timezone=True), default=utcnow)
    history = Column(JSON, default=list)  # [{date, score, source}]
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    project = relationship("Project", back_populates="mastery_records")

    __table_args__ = (
        Index("ix_mastery_project_concept", "project_id", "concept_name", unique=True),
    )


# ──────────────────── Learning Events ──────────────────────────

class LearningEvent(Base):
    __tablename__ = "learning_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(SQLEnum(EventType, native_enum=False), nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    project = relationship("Project", back_populates="learning_events")

    __table_args__ = (
        Index("ix_events_type_created", "event_type", "created_at"),
    )


# ──────────────────── Recommendations ──────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    reasoning = Column(Text, default="")
    action_type = Column(String(100), default="review")  # review, quiz, explore, revisit
    target_concepts = Column(JSON, default=list)
    target_pages = Column(JSON, default=list)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    project = relationship("Project", back_populates="recommendations")


# ──────────────────── Background Jobs ──────────────────────────

class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    job_type = Column(SQLEnum(JobType, native_enum=False), nullable=False)
    status = Column(SQLEnum(JobStatus, native_enum=False), default=JobStatus.QUEUED, nullable=False)
    payload = Column(JSON, default=dict)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    idempotency_key = Column(String(500), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_jobs_status_created", "status", "created_at"),
    )


# ──────────────────── AI Usage Logs ────────────────────────────

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    feature = Column(String(100), nullable=False)  # tutor, quiz_gen, assessment, recommendation, concept_extraction
    model = Column(String(100), nullable=False)
    latency_ms = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    status = Column(String(20), default="success")  # success, error, timeout
    error_message = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ai_logs_feature_created", "feature", "created_at"),
    )


# ──────────────────── AI Evaluations ───────────────────────────

class AIEvaluation(Base):
    __tablename__ = "ai_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    feature = Column(String(100), nullable=False)
    test_case_name = Column(String(255), nullable=False)
    input_data = Column(JSON, nullable=False)
    expected_output = Column(JSON, nullable=True)
    actual_output = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
