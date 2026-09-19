"""Spaces router — full CRUD with ownership."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import Space, Project, User
from app.schemas.schemas import SpaceCreate, SpaceUpdate, SpaceOut
from app.security.auth import get_student_user, verify_space_ownership

router = APIRouter(prefix="/api/spaces", tags=["Spaces"])


@router.post("/", response_model=SpaceOut, status_code=201)
async def create_space(data: SpaceCreate, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    space = Space(user_id=user.id, **data.model_dump())
    db.add(space)
    await db.flush()
    return SpaceOut(**{**SpaceOut.model_validate(space).model_dump(), "project_count": 0})


@router.get("/", response_model=list[SpaceOut])
async def list_spaces(user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Space).where(Space.user_id == user.id).order_by(Space.created_at.desc()))
    spaces = result.scalars().all()
    out = []
    for s in spaces:
        cnt = await db.execute(select(func.count(Project.id)).where(Project.space_id == s.id))
        out.append(SpaceOut(**{**SpaceOut.model_validate(s).model_dump(), "project_count": cnt.scalar() or 0}))
    return out


@router.get("/{space_id}", response_model=SpaceOut)
async def get_space(space_id: UUID, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    space = await verify_space_ownership(space_id, user, db)
    cnt = await db.execute(select(func.count(Project.id)).where(Project.space_id == space.id))
    return SpaceOut(**{**SpaceOut.model_validate(space).model_dump(), "project_count": cnt.scalar() or 0})


@router.put("/{space_id}", response_model=SpaceOut)
async def update_space(space_id: UUID, data: SpaceUpdate, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    space = await verify_space_ownership(space_id, user, db)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(space, k, v)
    await db.flush()
    cnt = await db.execute(select(func.count(Project.id)).where(Project.space_id == space.id))
    return SpaceOut(**{**SpaceOut.model_validate(space).model_dump(), "project_count": cnt.scalar() or 0})


@router.delete("/{space_id}", status_code=204)
async def delete_space(space_id: UUID, user: User = Depends(get_student_user), db: AsyncSession = Depends(get_db)):
    space = await verify_space_ownership(space_id, user, db)
    await db.delete(space)
