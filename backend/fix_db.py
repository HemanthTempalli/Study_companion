import asyncio
import asyncpg
from app.core.config import settings

async def fix_db():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        await conn.execute("ALTER TABLE background_jobs ADD COLUMN IF NOT EXISTS payload JSON DEFAULT '{}'")
        print("Added payload column successfully!")
    except Exception as e:
        print("Error adding payload column:", e)
        
    await conn.close()

asyncio.run(fix_db())
