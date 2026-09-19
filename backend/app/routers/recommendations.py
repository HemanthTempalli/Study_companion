"""Recommendation router — AI-powered actionable learning recommendations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import (
    User, Recommendation, MasteryRecord, QuizAttempt,
    Material, LearningContext, DocumentChunk, EventType, Project,
)
from app.schemas.schemas import RecommendationOut
from app.security.auth import get_student_user, verify_project_ownership
from app.ai.groq_provider import get_ai_provider, log_ai_usage, AIProviderError
from app.services.event_service import record_event

router = APIRouter(prefix="/api/projects/{project_id}/recommendations", tags=["Recommendations"])


@router.post("/generate", response_model=RecommendationOut)
async def generate_recommendation(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_project_ownership(project_id, user, db)

    # Gather inputs
    mastery_result = await db.execute(
        select(MasteryRecord).where(MasteryRecord.project_id == project_id)
    )
    mastery_records = mastery_result.scalars().all()
    weak_concepts = [{"name": m.concept_name, "level": m.mastery_level}
                     for m in mastery_records if m.mastery_level < 60]
    strong_concepts = [{"name": m.concept_name, "level": m.mastery_level}
                       for m in mastery_records if m.mastery_level >= 80]

    # Recent quiz performance
    quiz_result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.project_id == project_id, QuizAttempt.completed == True)
        .order_by(QuizAttempt.created_at.desc())
        .limit(3)
    )
    recent_quizzes = quiz_result.scalars().all()

    # Available materials
    material_result = await db.execute(
        select(Material).where(Material.project_id == project_id)
    )
    materials = [{"name": m.filename, "pages": m.page_count} for m in material_result.scalars().all()]

    # Previous recommendations
    prev_rec = await db.execute(
        select(Recommendation)
        .where(Recommendation.project_id == project_id)
        .order_by(Recommendation.created_at.desc())
        .limit(3)
    )
    prev_recs = [r.recommendation_text for r in prev_rec.scalars().all()]

    # Learning goal
    learning_goal = project.learning_goal or "General understanding of the material"

    import json
    prompt = f"""Generate a specific, actionable learning recommendation for this student.

Learning Goal: {learning_goal}
Weak Concepts: {json.dumps(weak_concepts)}
Strong Concepts: {json.dumps([c['name'] for c in strong_concepts])}
Recent Quiz Scores: {[f"{q.score:.0f}%" for q in recent_quizzes]}
Available Materials: {json.dumps(materials)}
Previous Recommendations (avoid repeating): {json.dumps(prev_recs)}

Generate ONE specific recommendation. Be concrete:
- Reference specific materials and page ranges when possible
- Suggest specific study actions (review, quiz, explore)
- Consider the student's current level

Respond as JSON:
{{
  "recommendation": "Your specific recommendation text...",
  "reasoning": "Why this recommendation...",
  "action_type": "review" or "quiz" or "explore" or "revisit",
  "target_concepts": ["concept1", "concept2"]
}}"""

    try:
        provider = get_ai_provider()
        result, stats = await provider.generate_structured(
            system_prompt="You are a learning advisor. Give specific, actionable study recommendations.",
            user_prompt=prompt,
            feature="recommendation",
        )
        await log_ai_usage(db, stats, user_id=user.id, project_id=project_id)
    except AIProviderError as e:
        raise HTTPException(status_code=503, detail=str(e.message))

    rec = Recommendation(
        project_id=project_id,
        user_id=user.id,
        recommendation_text=result.get("recommendation", "Continue studying your materials."),
        reasoning=result.get("reasoning", ""),
        action_type=result.get("action_type", "review"),
        target_concepts=result.get("target_concepts", []),
    )
    db.add(rec)
    await db.flush()

    await record_event(db, user.id, project_id, EventType.RECOMMENDATION_GENERATED, {
        "action_type": rec.action_type,
        "target_concepts": rec.target_concepts,
    })

    return RecommendationOut.model_validate(rec)


@router.get("/", response_model=list[RecommendationOut])
async def list_recommendations(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.project_id == project_id, Recommendation.user_id == user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(10)
    )
    return [RecommendationOut.model_validate(r) for r in result.scalars().all()]


@router.post("/{rec_id}/dismiss", status_code=204)
async def dismiss_recommendation(
    project_id: UUID,
    rec_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == rec_id, Recommendation.user_id == user.id)
    )
    rec = result.scalar_one_or_none()
    if rec:
        rec.is_dismissed = True
