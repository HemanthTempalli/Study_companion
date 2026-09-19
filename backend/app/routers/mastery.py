"""Mastery & Growth router — mastery visualization and growth analysis."""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import User, MasteryRecord
from app.schemas.schemas import MasteryOut, GrowthAnalysis
from app.security.auth import get_student_user, verify_project_ownership
from app.services.mastery_service import get_project_mastery

router = APIRouter(prefix="/api/projects/{project_id}", tags=["Mastery & Growth"])


@router.get("/mastery", response_model=list[MasteryOut])
async def get_mastery(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    records = await get_project_mastery(db, project_id)

    out = []
    for r in records:
        # Determine trend from history
        history = r.get("history", [])
        trend = "stable"
        if len(history) >= 2:
            recent = [h["mastery_after"] for h in history[-3:]]
            if len(recent) >= 2:
                if recent[-1] > recent[0] + 5:
                    trend = "improving"
                elif recent[-1] < recent[0] - 5:
                    trend = "declining"

        out.append(MasteryOut(
            concept_name=r["concept_name"],
            mastery_level=r["mastery_level"],
            evidence_count=r["evidence_count"],
            last_assessed=r["last_assessed"],
            trend=trend,
        ))
    return out


@router.get("/growth", response_model=GrowthAnalysis)
async def get_growth_analysis(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    records = await get_project_mastery(db, project_id)

    improving = []
    stable = []
    needs_attention = []
    mastery_over_time = []

    for r in records:
        history = r.get("history", [])
        concept_data = {
            "concept": r["concept_name"],
            "mastery": r["mastery_level"],
            "evidence_count": r["evidence_count"],
        }

        # Determine trend
        if len(history) >= 2:
            recent_scores = [h["mastery_after"] for h in history[-3:]]
            if recent_scores[-1] > recent_scores[0] + 5:
                concept_data["trend"] = "improving"
                improving.append(concept_data)
            elif recent_scores[-1] < recent_scores[0] - 5:
                concept_data["trend"] = "declining"
                needs_attention.append(concept_data)
            elif r["mastery_level"] < 50:
                concept_data["trend"] = "low"
                needs_attention.append(concept_data)
            else:
                concept_data["trend"] = "stable"
                stable.append(concept_data)
        elif r["mastery_level"] < 50:
            concept_data["trend"] = "low"
            needs_attention.append(concept_data)
        else:
            concept_data["trend"] = "new"
            stable.append(concept_data)

        # Build timeline data
        for h in history:
            mastery_over_time.append({
                "concept": r["concept_name"],
                "date": h["date"],
                "mastery": h["mastery_after"],
            })

    # Overall trend
    if not records:
        overall = "no_data"
        summary = "No mastery data yet. Upload materials and take quizzes to start tracking your progress."
    else:
        avg = sum(r["mastery_level"] for r in records) / len(records)
        if len(improving) > len(needs_attention):
            overall = "improving"
            summary = f"Great progress! You're improving in {len(improving)} concepts. Average mastery: {avg:.0f}%."
        elif len(needs_attention) > len(improving):
            overall = "needs_work"
            summary = f"{len(needs_attention)} concepts need attention. Focus on your weakest areas to improve. Average mastery: {avg:.0f}%."
        else:
            overall = "stable"
            summary = f"Your knowledge is stable across {len(records)} concepts. Average mastery: {avg:.0f}%."

    return GrowthAnalysis(
        improving=improving,
        stable=stable,
        needs_attention=needs_attention,
        overall_trend=overall,
        mastery_over_time=sorted(mastery_over_time, key=lambda x: x["date"]),
        summary=summary,
    )
