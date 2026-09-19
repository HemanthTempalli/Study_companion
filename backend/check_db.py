import asyncio
import asyncpg
from app.core.config import settings

async def main():
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    rows = await conn.fetch('SELECT id, project_id, content FROM document_chunks')
    for r in rows:
        print(f'Chunk {r["id"]} project: {r["project_id"]} content: {r["content"][:50]}...')
    await conn.close()

asyncio.run(main())
