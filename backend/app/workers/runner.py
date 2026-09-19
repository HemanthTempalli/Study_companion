"""DB-backed job queue runner — polls for jobs and processes them.

Replaces Redis: simpler, free, runs on the same database.
Trade-off: lower throughput, but fine for a learning companion prototype.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_factory
from app.models.models import BackgroundJob, JobStatus, JobType
from app.core.config import settings

logger = logging.getLogger(__name__)


async def claim_job(db: AsyncSession) -> BackgroundJob | None:
    """Atomically claim the next queued job."""
    result = await db.execute(
        select(BackgroundJob)
        .where(BackgroundJob.status == JobStatus.QUEUED)
        .order_by(BackgroundJob.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = result.scalar_one_or_none()
    if job:
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        await db.commit()
    return job


async def process_job(job: BackgroundJob):
    """Route job to the appropriate worker."""
    async with async_session_factory() as db:
        try:
            if job.job_type == JobType.PROCESS_MATERIAL:
                from app.workers.document_worker import process_material
                await process_material(
                    db,
                    material_id=job.payload["material_id"],
                    project_id=job.payload["project_id"],
                    user_id=job.payload["user_id"],
                )

            # Mark completed
            result = await db.execute(select(BackgroundJob).where(BackgroundJob.id == job.id))
            db_job = result.scalar_one_or_none()
            if db_job:
                db_job.status = JobStatus.COMPLETED
                db_job.completed_at = datetime.now(timezone.utc)
                await db.commit()

            logger.info(f"Job {job.id} ({job.job_type.value}) completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            result = await db.execute(select(BackgroundJob).where(BackgroundJob.id == job.id))
            db_job = result.scalar_one_or_none()
            if db_job:
                db_job.retry_count += 1
                if db_job.retry_count >= db_job.max_retries:
                    db_job.status = JobStatus.FAILED
                    db_job.error_message = str(e)[:500]
                else:
                    db_job.status = JobStatus.QUEUED  # Re-queue for retry
                    logger.info(f"Job {job.id} re-queued (attempt {db_job.retry_count}/{db_job.max_retries})")
                db_job.completed_at = datetime.now(timezone.utc)
                await db.commit()


async def run_worker():
    """Main worker loop — polls DB for queued jobs."""
    logger.info("🔧 Background worker started")
    poll_interval = settings.WORKER_POLL_INTERVAL

    while True:
        try:
            async with async_session_factory() as db:
                job = await claim_job(db)
                if job:
                    logger.info(f"Processing job {job.id} ({job.job_type.value})")
                    await process_job(job)
                else:
                    await asyncio.sleep(poll_interval)
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    asyncio.run(run_worker())
