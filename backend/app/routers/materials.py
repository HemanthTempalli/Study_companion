"""Materials router — PDF upload, listing, deletion with background processing trigger."""

import os
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.models import Material, MaterialStatus, User, BackgroundJob, JobType, JobStatus, EventType
from app.schemas.schemas import MaterialOut
from app.security.auth import get_student_user, verify_project_ownership
from app.core.config import settings
from app.services.event_service import record_event

router = APIRouter(prefix="/api/projects/{project_id}/materials", tags=["Materials"])

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/", response_model=MaterialOut, status_code=201)
async def upload_material(
    project_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    project = await verify_project_ownership(project_id, user, db)

    # Validate file type
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. Got: {ext}")

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 50MB.")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    # Store locally
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(project_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    storage_path = os.path.join(upload_dir, f"{file_id}{ext}")
    with open(storage_path, "wb") as f:
        f.write(content)

    # Create material record
    material = Material(
        project_id=project_id,
        user_id=user.id,
        filename=file.filename or "document.pdf",
        storage_path=storage_path,
        file_size=len(content),
        status=MaterialStatus.QUEUED,
    )
    db.add(material)
    await db.flush()

    # Create background job (duplicate protection via idempotency key)
    idempotency_key = f"process_material_{material.id}"
    existing_job = await db.execute(
        select(BackgroundJob).where(BackgroundJob.idempotency_key == idempotency_key)
    )
    if not existing_job.scalar_one_or_none():
        job = BackgroundJob(
            job_type=JobType.PROCESS_MATERIAL,
            payload={"material_id": str(material.id), "project_id": str(project_id), "user_id": str(user.id)},
            idempotency_key=idempotency_key,
        )
        db.add(job)

    await record_event(db, user.id, project_id, EventType.MATERIAL_UPLOADED, {
        "filename": file.filename, "size": len(content),
    })

    return MaterialOut.model_validate(material)


@router.get("/", response_model=list[MaterialOut])
async def list_materials(
    project_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(Material)
        .where(Material.project_id == project_id)
        .order_by(Material.created_at.desc())
    )
    return [MaterialOut.model_validate(m) for m in result.scalars().all()]


@router.get("/{material_id}", response_model=MaterialOut)
async def get_material(
    project_id: UUID,
    material_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(Material).where(Material.id == material_id, Material.project_id == project_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return MaterialOut.model_validate(material)


@router.delete("/{material_id}", status_code=204)
async def delete_material(
    project_id: UUID,
    material_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(Material).where(Material.id == material_id, Material.project_id == project_id, Material.user_id == user.id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Clean up file
    if os.path.exists(material.storage_path):
        os.remove(material.storage_path)

    await db.delete(material)


@router.post("/{material_id}/retry", response_model=MaterialOut)
async def retry_processing(
    project_id: UUID,
    material_id: UUID,
    user: User = Depends(get_student_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_project_ownership(project_id, user, db)
    result = await db.execute(
        select(Material).where(Material.id == material_id, Material.project_id == project_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if material.status != MaterialStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed materials can be retried")

    material.status = MaterialStatus.QUEUED
    material.error_message = None

    job = BackgroundJob(
        job_type=JobType.PROCESS_MATERIAL,
        payload={"material_id": str(material.id), "project_id": str(project_id), "user_id": str(user.id)},
        idempotency_key=f"retry_material_{material.id}_{uuid.uuid4().hex[:8]}",
    )
    db.add(job)
    await db.flush()

    return MaterialOut.model_validate(material)
