"""Admin router — user management, system health, AI observability, job monitoring."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import (
    User, Project, Space, QuizAttempt, LearningEvent, BackgroundJob,
    AIUsageLog, Material, Conversation, MasteryRecord, UserRole,
    AIEvaluation
)
from app.schemas.schemas import AdminUserView, SystemHealth, AIUsageLogOut, BackgroundJobOut, AdminProjectView, AIEvaluationOut
from app.security.auth import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users", response_model=list[AdminUserView])
async def list_users(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    out = []
    for u in users:
        pc = (await db.execute(select(func.count(Project.id)).where(Project.user_id == u.id))).scalar() or 0
        qc = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == u.id))).scalar() or 0
        last_ev = await db.execute(
            select(LearningEvent.created_at)
            .where(LearningEvent.user_id == u.id)
            .order_by(LearningEvent.created_at.desc())
            .limit(1)
        )
        last = last_ev.scalar_one_or_none()
        out.append(AdminUserView(
            id=u.id, email=u.email, full_name=u.full_name, role=u.role.value,
            is_active=u.is_active, created_at=u.created_at,
            project_count=pc, quiz_count=qc, last_activity=last,
        ))
    return out


@router.get("/users/{user_id}/journey")
async def get_user_journey(user_id: UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    """Inspect a specific user's learning journey."""
    target = await db.execute(select(User).where(User.id == user_id))
    target_user = target.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Projects
    projects = await db.execute(select(Project).where(Project.user_id == user_id))
    project_list = []
    for p in projects.scalars().all():
        mastery = await db.execute(
            select(func.avg(MasteryRecord.mastery_level)).where(MasteryRecord.project_id == p.id)
        )
        avg_mastery = mastery.scalar() or 0
        project_list.append({
            "id": str(p.id), "name": p.name, "learning_goal": p.learning_goal,
            "average_mastery": round(float(avg_mastery), 1), "created_at": p.created_at.isoformat(),
        })

    # Recent events
    events = await db.execute(
        select(LearningEvent)
        .where(LearningEvent.user_id == user_id)
        .order_by(LearningEvent.created_at.desc())
        .limit(50)
    )
    event_list = [
        {"type": e.event_type.value, "project_id": str(e.project_id),
         "metadata": e.metadata_, "created_at": e.created_at.isoformat()}
        for e in events.scalars().all()
    ]

    return {
        "user": {"id": str(target_user.id), "email": target_user.email, "full_name": target_user.full_name},
        "projects": project_list,
        "recent_events": event_list,
    }


@router.get("/projects", response_model=list[AdminProjectView])
async def list_projects(
    user_id: UUID = None,
    admin: User = Depends(get_admin_user), 
    db: AsyncSession = Depends(get_db)
):
    query = select(Project, User, Space).join(User, Project.user_id == User.id).join(Space, Project.space_id == Space.id)
    if user_id:
        query = query.where(Project.user_id == user_id)
    
    query = query.order_by(Project.created_at.desc())
    result = await db.execute(query)
    
    out = []
    for project, user, space in result.all():
        mc = (await db.execute(select(func.count(Material.id)).where(Material.project_id == project.id))).scalar() or 0
        qc = (await db.execute(select(func.count(QuizAttempt.id)).where(QuizAttempt.project_id == project.id))).scalar() or 0
        
        out.append(AdminProjectView(
            id=project.id,
            user_id=project.user_id,
            user_email=user.email,
            space_name=space.name,
            name=project.name,
            created_at=project.created_at,
            material_count=mc,
            quiz_count=qc
        ))
    return out


@router.get("/health", response_model=SystemHealth)
async def get_system_health(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    # DB check
    try:
        await db.execute(select(func.count(User.id)))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # Job queue status
    from app.models.models import JobStatus
    queued = (await db.execute(select(func.count(BackgroundJob.id)).where(BackgroundJob.status == JobStatus.QUEUED))).scalar() or 0
    processing = (await db.execute(select(func.count(BackgroundJob.id)).where(BackgroundJob.status == JobStatus.PROCESSING))).scalar() or 0
    failed = (await db.execute(select(func.count(BackgroundJob.id)).where(BackgroundJob.status == JobStatus.FAILED))).scalar() or 0
    completed = (await db.execute(select(func.count(BackgroundJob.id)).where(BackgroundJob.status == JobStatus.COMPLETED))).scalar() or 0

    # AI status
    from app.core.config import settings
    ai_status = "configured" if settings.GROQ_API_KEY else "not_configured"

    return SystemHealth(
        database=db_status,
        background_jobs={"queued": queued, "processing": processing, "failed": failed, "completed": completed},
        ai_service=ai_status,
        storage="local",
    )


@router.get("/ai-logs", response_model=list[AIUsageLogOut])
async def get_ai_logs(
    limit: int = 50,
    feature: str = None,
    model: str = None,
    status: str = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AIUsageLog).order_by(AIUsageLog.created_at.desc()).limit(limit)
    if feature:
        query = query.where(AIUsageLog.feature == feature)
    if model:
        query = query.where(AIUsageLog.model == model)
    if status:
        query = query.where(AIUsageLog.status == status)
    result = await db.execute(query)
    return [AIUsageLogOut.model_validate(log) for log in result.scalars().all()]


@router.get("/evaluations", response_model=list[AIEvaluationOut])
async def get_evaluations(
    limit: int = 50,
    feature: str = None,
    passed: bool = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AIEvaluation).order_by(AIEvaluation.created_at.desc()).limit(limit)
    if feature:
        query = query.where(AIEvaluation.feature == feature)
    if passed is not None:
        query = query.where(AIEvaluation.passed == passed)
    result = await db.execute(query)
    return [AIEvaluationOut.model_validate(ev) for ev in result.scalars().all()]


@router.get("/jobs", response_model=list[BackgroundJobOut])
async def get_jobs(
    status: str = None,
    job_type: str = None,
    limit: int = 50,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(BackgroundJob).order_by(BackgroundJob.created_at.desc()).limit(limit)
    if status:
        query = query.where(BackgroundJob.status == status)
    if job_type:
        query = query.where(BackgroundJob.job_type == job_type)
    result = await db.execute(query)
    return [BackgroundJobOut.model_validate(j) for j in result.scalars().all()]


@router.post("/make-admin/{user_id}")
async def make_admin(user_id: UUID, admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = UserRole.ADMIN
    return {"message": f"User {user.email} is now an admin"}
