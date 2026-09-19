"""Mastery service — evidence-based concept mastery tracking."""

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import MasteryRecord, EventType
from app.services.event_service import record_event


async def update_mastery_from_answer(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    concept_name: str,
    score: float,
    source_type: str = "quiz",
) -> dict:
    """Update mastery for a concept based on assessment evidence.

    Uses weighted moving average: new_mastery = old * 0.7 + score * 0.3
    This gives more weight to accumulated evidence while still being responsive.
    """
    result = await db.execute(
        select(MasteryRecord).where(
            MasteryRecord.project_id == project_id,
            MasteryRecord.concept_name == concept_name,
        )
    )
    record = result.scalar_one_or_none()

    if record:
        old_level = record.mastery_level
        # Weighted moving average
        weight = 0.7 if record.evidence_count > 3 else 0.5
        new_level = round(record.mastery_level * weight + score * (1 - weight), 1)
        new_level = max(0, min(100, new_level))

        record.mastery_level = new_level
        record.evidence_count += 1
        record.last_assessed = datetime.now(timezone.utc)

        # Append to history
        history = record.history or []
        history.append({
            "date": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "source": source_type,
            "mastery_after": new_level,
        })
        record.history = history[-50]  if len(history) > 50 else history  # Keep last 50
        record.history = history
    else:
        old_level = 0
        new_level = round(score * 0.5, 1)  # First evidence: conservative estimate
        record = MasteryRecord(
            project_id=project_id,
            user_id=user_id,
            concept_name=concept_name,
            mastery_level=new_level,
            evidence_count=1,
            history=[{
                "date": datetime.now(timezone.utc).isoformat(),
                "score": score,
                "source": source_type,
                "mastery_after": new_level,
            }],
        )
        db.add(record)

    await record_event(db, user_id, project_id, EventType.MASTERY_UPDATED, {
        "concept": concept_name,
        "old_level": old_level,
        "new_level": new_level,
        "evidence": source_type,
    })

    return {
        "concept": concept_name,
        "old_mastery": old_level,
        "new_mastery": new_level,
        "direction": "up" if new_level > old_level else ("down" if new_level < old_level else "stable"),
    }


async def get_project_mastery(db: AsyncSession, project_id: UUID) -> list[dict]:
    """Get all mastery records for a project."""
    result = await db.execute(
        select(MasteryRecord)
        .where(MasteryRecord.project_id == project_id)
        .order_by(MasteryRecord.mastery_level.asc())
    )
    records = result.scalars().all()
    return [{
        "concept_name": r.concept_name,
        "mastery_level": r.mastery_level,
        "evidence_count": r.evidence_count,
        "last_assessed": r.last_assessed.isoformat() if r.last_assessed else None,
        "history": r.history or [],
    } for r in records]
