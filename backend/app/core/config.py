"""Core configuration — loads and validates all environment variables at startup."""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/studycompanion"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24h

    # Groq
    GROQ_API_KEY: str = ""

    # Supabase (optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Storage
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "./uploads"

    # Worker
    WORKER_POLL_INTERVAL: int = 5
    WORKER_MAX_RETRIES: int = 3

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.3

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Admin
    ADMIN_EMAIL: str = "admin@studycompanion.ai"

    model_config = {"env_file": (".env", "../.env"), "env_file_encoding": "utf-8", "extra": "ignore"}

settings = Settings()


def validate_settings():
    """Validate critical settings at startup."""
    issues = []
    if not settings.GROQ_API_KEY:
        issues.append("GROQ_API_KEY is not set — AI features will be disabled")
    if settings.JWT_SECRET == "change-me-in-production":
        issues.append("JWT_SECRET is using default value — change for production")
    return issues

