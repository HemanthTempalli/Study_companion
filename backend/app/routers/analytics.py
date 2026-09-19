"""Analytics router — project and global analytics from real database aggregations."""

from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import (
    User, Material, Conversation, QuizAttempt, Question, Answer,
    MasteryRecord, LearningEvent, AIUsageLog, EventType, Project, Space,
)
from app.schemas.schemas import ProjectAnalytics, GlobalAnalytics
from app.security.auth import get_student_user, get_admin_user, verify_project_ownership

router = APIRouter(prefix="/api", tags=["Analytics"])


@router.get("/projects/{project_id}/analytics", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)

    # Total counts
    mat_count = (await db.execute(select(func.count(Material.id)).where(Material.project_id == project_id))).scalar() or 0
    conv_count = (await db.execute(select(func.count(Conversation.id)).where(Conversation.project_id == project_id))).scalar() or 0
    quiz_count = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.project_id == project_id))).scalar() or 0
    q_answered = (await db.execute(select(func.count(Answer.id)).join(Question).where(Question.project_id == project_id))).scalar() or 0

    # Learning activity (last 30 days, grouped by day)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    events_result = await db.execute(
        select(
            func.date_trunc('day', LearningEvent.created_at).label('day'),
            func.count(LearningEvent.id).label('count'),
        )
        .where(LearningEvent.project_id == project_id, LearningEvent.created_at >= thirty_days_ago)
        .group_by('day')
        .order_by('day')
    )
    learning_activity = [{"date": str(r.day), "count": r.count} for r in events_result.fetchall()]

    # Assessment performance (quiz scores over time)
    quiz_result = await db.execute(
        select(QuizAttempt)
        .where(QuizAttempt.project_id == project_id, QuizAttempt.completed == True)
        .order_by(QuizAttempt.completed_at)
    )
    assessment_performance = [
        {"date": q.completed_at.isoformat() if q.completed_at else q.created_at.isoformat(), "score": q.score, "questions": q.total_questions}
        for q in quiz_result.scalars().all()
    ]

    # Mastery distribution
    mastery_result = await db.execute(
        select(MasteryRecord).where(MasteryRecord.project_id == project_id)
    )
    mastery_records = mastery_result.scalars().all()
    mastery_distribution = [
        {"concept": m.concept_name, "mastery": m.mastery_level, "evidence_count": m.evidence_count}
        for m in mastery_records
    ]

    # Concept trends (from mastery history)
    concept_trends = []
    for m in mastery_records:
        if m.history:
            concept_trends.append({
                "concept": m.concept_name,
                "data": [{"date": h["date"], "mastery": h["mastery_after"]} for h in (m.history or [])[-10:]],
            })

    # AI activity
    ai_result = await db.execute(
        select(
            AIUsageLog.feature,
            func.count(AIUsageLog.id).label('count'),
            func.avg(AIUsageLog.latency_ms).label('avg_latency'),
        )
        .where(AIUsageLog.project_id == project_id)
        .group_by(AIUsageLog.feature)
    )
    ai_activity = {r.feature: {"count": r.count, "avg_latency_ms": round(float(r.avg_latency or 0))} for r in ai_result.fetchall()}

    return ProjectAnalytics(
        learning_activity=learning_activity,
        assessment_performance=assessment_performance,
        mastery_distribution=mastery_distribution,
        concept_trends=concept_trends,
        ai_activity=ai_activity,
        total_materials=mat_count,
        total_conversations=conv_count,
        total_quizzes=quiz_count,
        total_questions_answered=q_answered,
    )


@router.get("/admin/analytics", response_model=GlobalAnalytics)
async def get_global_analytics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    total_materials = (await db.execute(select(func.count(Material.id)))).scalar() or 0
    total_quizzes = (await db.execute(select(func.count(QuizAttempt.id)))).scalar() or 0
    total_convos = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    ai_requests = (await db.execute(select(func.count(AIUsageLog.id)))).scalar() or 0

    # Global learning activity (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    events_result = await db.execute(
        select(
            func.date_trunc('day', LearningEvent.created_at).label('day'),
            func.count(LearningEvent.id).label('count'),
        )
        .where(LearningEvent.created_at >= thirty_days_ago)
        .group_by('day')
        .order_by('day')
    )
    learning_activity = [{"date": str(r.day), "count": r.count} for r in events_result.fetchall()]

    # Global mastery trends
    mastery_result = await db.execute(
        select(
            func.avg(MasteryRecord.mastery_level).label('avg_mastery'),
            func.count(MasteryRecord.id).label('count'),
        )
    )
    mastery_row = mastery_result.one()
    mastery_trends = [{"average_mastery": round(float(mastery_row.avg_mastery or 0), 1), "total_records": mastery_row.count or 0}]

    return GlobalAnalytics(
        total_users=total_users,
        total_projects=total_projects,
        total_materials=total_materials,
        total_quizzes=total_quizzes,
        total_conversations=total_convos,
        ai_requests=ai_requests,
        learning_activity=learning_activity,
        mastery_trends=mastery_trends,
    )
