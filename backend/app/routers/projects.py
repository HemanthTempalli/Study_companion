"""Projects router — full CRUD with ownership, dashboard, and project-scoped data."""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.models import (
    Project, Material, User, ProjectConcept, QuizAttempt,
    LearningEvent, Recommendation, MasteryRecord, Conversation,
)
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectDashboard
from app.security.auth import get_student_user, verify_project_ownership, verify_space_ownership

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    await verify_space_ownership(data.space_id, user, db)
    project = Project(user_id=user.id, **data.model_dump())
    db.add(project)
    await db.flush()

    # Record event
    from app.services.event_service import record_event
    from app.models.models import EventType
    await record_event(db, user.id, project.id, EventType.PROJECT_CREATED, {"name": data.name})

    return ProjectOut(**{**ProjectOut.model_validate(project).model_dump(), "material_count": 0, "concept_count": 0})


@router.get("/", response_model=list[ProjectOut])
async def list_projects(
    space_id: UUID = None,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Project).where(Project.user_id == user.id)
    if space_id:
        query = query.where(Project.space_id == space_id)
    query = query.order_by(Project.updated_at.desc())
    result = await db.execute(query)
    projects = result.scalars().all()

    out = []
    for p in projects:
        mc = await db.execute(select(func.count(Material.id)).where(Material.project_id == p.id))
        cc = await db.execute(select(func.count(ProjectConcept.id)).where(ProjectConcept.project_id == p.id))
        out.append(ProjectOut(**{
            **ProjectOut.model_validate(p).model_dump(),
            "material_count": mc.scalar() or 0,
            "concept_count": cc.scalar() or 0,
        }))
    return out


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: UUID, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    project = await verify_project_ownership(project_id, user, db)
    mc = await db.execute(select(func.count(Material.id)).where(Material.project_id == project.id))
    cc = await db.execute(select(func.count(ProjectConcept.id)).where(ProjectConcept.project_id == project.id))
    return ProjectOut(**{
        **ProjectOut.model_validate(project).model_dump(),
        "material_count": mc.scalar() or 0,
        "concept_count": cc.scalar() or 0,
    })


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
async def get_project_dashboard(project_id: UUID, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    project = await verify_project_ownership(project_id, user, db)

    mc = await db.execute(select(func.count(Material.id)).where(Material.project_id == project.id))
    cc = await db.execute(select(func.count(ProjectConcept.id)).where(ProjectConcept.project_id == project.id))
    project_out = ProjectOut(**{
        **ProjectOut.model_validate(project).model_dump(),
        "material_count": mc.scalar() or 0,
        "concept_count": cc.scalar() or 0,
    })

    # Recent activity
    events = await db.execute(
        select(LearningEvent)
        .where(LearningEvent.project_id == project_id)
        .order_by(LearningEvent.created_at.desc())
        .limit(10)
    )
    recent_activity = [
        {"type": e.event_type.value, "metadata": e.metadata_, "created_at": e.created_at.isoformat()}
        for e in events.scalars().all()
    ]

    # Mastery summary
    mastery_result = await db.execute(
        select(MasteryRecord).where(MasteryRecord.project_id == project_id).order_by(MasteryRecord.mastery_level.asc())
    )
    mastery_records = mastery_result.scalars().all()
    mastery_summary = {
        "average": round(sum(m.mastery_level for m in mastery_records) / max(len(mastery_records), 1), 1),
        "total_concepts": len(mastery_records),
        "weak_concepts": [m.concept_name for m in mastery_records if m.mastery_level < 50][:5],
        "strong_concepts": [m.concept_name for m in mastery_records if m.mastery_level >= 80][:5],
    }

    # Latest recommendation
    rec = await db.execute(
        select(Recommendation)
        .where(Recommendation.project_id == project_id, Recommendation.is_dismissed == False)
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    )
    rec_item = rec.scalar_one_or_none()

    # Quiz stats
    qr = await db.execute(
        select(
            func.count(QuizAttempt.id),
            func.avg(QuizAttempt.score),
        ).where(QuizAttempt.project_id == project_id, QuizAttempt.completed == True)
    )
    quiz_row = qr.one()
    quiz_stats = {
        "total_quizzes": quiz_row[0] or 0,
        "average_score": round(float(quiz_row[1] or 0), 1),
    }

    return ProjectDashboard(
        project=project_out,
        recent_activity=recent_activity,
        mastery_summary=mastery_summary,
        recommendation=rec_item.recommendation_text if rec_item else None,
        quiz_stats=quiz_stats,
    )


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: UUID, data: ProjectUpdate, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    project = await verify_project_ownership(project_id, user, db)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(project, k, v)
    await db.flush()
    mc = await db.execute(select(func.count(Material.id)).where(Material.project_id == project.id))
    cc = await db.execute(select(func.count(ProjectConcept.id)).where(ProjectConcept.project_id == project.id))
    return ProjectOut(**{
        **ProjectOut.model_validate(project).model_dump(),
        "material_count": mc.scalar() or 0,
        "concept_count": cc.scalar() or 0,
    })


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    project = await verify_project_ownership(project_id, user, db)
    await db.delete(project)
