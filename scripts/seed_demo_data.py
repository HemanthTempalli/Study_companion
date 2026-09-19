"""Seed demo data — creates admin user and optional demo content."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import async_session_factory, engine, Base
from app.models.models import User, UserRole
from app.security.auth import hash_password
from app.core.config import settings


async def seed():
    """Create tables and seed demo data."""
    # Create tables
    async with engine.begin() as conn:
        await conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")

    async with async_session_factory() as db:
        # Create admin user
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        if not existing.scalar_one_or_none():
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password("admin123456"),
                full_name="Admin User",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print(f"✅ Admin user created: {settings.ADMIN_EMAIL} / admin123456")
        else:
            print(f"ℹ️  Admin user already exists: {settings.ADMIN_EMAIL}")

        # Create demo user
        demo_email = "demo@studycompanion.ai"
        existing = await db.execute(select(User).where(User.email == demo_email))
        if not existing.scalar_one_or_none():
            demo = User(
                email=demo_email,
                hashed_password=hash_password("demo123456"),
                full_name="Demo Student",
                role=UserRole.USER,
            )
            db.add(demo)
            print(f"✅ Demo user created: {demo_email} / demo123456")
        else:
            print(f"ℹ️  Demo user already exists: {demo_email}")

        await db.commit()
    print("🎉 Seed complete!")


from sqlalchemy import text as sa_text

if __name__ == "__main__":
    asyncio.run(seed())
