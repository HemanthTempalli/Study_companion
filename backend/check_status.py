import asyncio
import sys
sys.path.insert(0, ".")

from app.database.session import async_session_factory
from app.retrieval.embeddings import generate_embedding
from app.retrieval.vector_search import search_project_chunks
from sqlalchemy import text

PROJECT_ID = "5d5f1157-d5db-439d-a5c9-33bd266808c2"  # AI Study Companion
TEST_QUERY = "what is this document about"

async def check():
    async with async_session_factory() as db:
        print(f"Generating embedding for: '{TEST_QUERY}'")
        embedding = generate_embedding(TEST_QUERY)
        print(f"Embedding dim: {len(embedding)}, sample values: {[round(x,4) for x in embedding[:3]]}")

        # Check chunks - use string interpolation to avoid asyncpg bind param issue
        r = await db.execute(text(f"""
            SELECT COUNT(*) as total,
                   COUNT(embedding) as with_embedding
            FROM document_chunks
            WHERE project_id = '{PROJECT_ID}'
        """))
        row = r.fetchone()
        print(f"\nChunks in project: {row.total} total, {row.with_embedding} with embeddings")

        # Try with threshold = 0.0 to get ALL results
        print("\nSearching with threshold=0.0 (return everything)...")
        results = await search_project_chunks(db, PROJECT_ID, embedding, top_k=5, similarity_threshold=0.0)
        if results:
            print(f"Found {len(results)} results!")
            for r in results:
                print(f"  Similarity: {r.similarity:.4f} | File: {r.material_name} | Page: {r.page_number}")
                print(f"  Content: {r.content[:120]}...")
        else:
            print("  ZERO results even at threshold=0.0")
            # Check if embeddings are actually stored
            r2 = await db.execute(text(f"""
                SELECT id::text,
                       embedding IS NOT NULL as has_emb,
                       left(content, 60) as snippet
                FROM document_chunks
                WHERE project_id = '{PROJECT_ID}'
                LIMIT 5
            """))
            print("\n  Raw chunk data:")
            for row in r2.fetchall():
                print(f"    ID: {row.id[:8]}... | Has embedding: {row.has_emb} | Content: {row.snippet}")

asyncio.run(check())
