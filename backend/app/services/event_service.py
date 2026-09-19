"""Event service — records learning events with metadata."""

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import LearningEvent, EventType


async def record_event(
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID,
    event_type: EventType,
    metadata: dict = None,
):
    """Record a learning event. Non-blocking — caller commits."""
    event = LearningEvent(
        user_id=user_id,
        project_id=project_id,
        event_type=event_type,
        metadata_=metadata or {},
    )
    db.add(event)
    return event
