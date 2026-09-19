import asyncio
import asyncpg
from app.core.config import settings

async def check():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"))
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='background_jobs'")
    print("Columns in background_jobs:")
    print([c['column_name'] for c in cols])
    await conn.close()

asyncio.run(check())
