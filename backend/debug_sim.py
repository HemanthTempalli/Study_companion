import asyncio
import asyncpg
from app.core.config import settings
from app.retrieval.embeddings import generate_embedding

async def main():
    embedding = generate_embedding('what is machine learning')
    conn = await asyncpg.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
    rows = await conn.fetch('SELECT id, 1 - (embedding <=> $1::vector) as similarity FROM document_chunks', embedding_str)
    for r in rows:
        print(f'Chunk similarity: {r["similarity"]}')
    await conn.close()

asyncio.run(main())
