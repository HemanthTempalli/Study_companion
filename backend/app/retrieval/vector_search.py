"""Vector search — project-scoped RAG retrieval using pgvector."""

import logging
from uuid import UUID
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DocumentChunk, Material
from app.core.config import settings

logger = logging.getLogger(__name__)


class RetrievalResult:
    def __init__(self, content: str, material_name: str, page_number: int, similarity: float, chunk_id: str):
        self.content = content
        self.material_name = material_name
        self.page_number = page_number
        self.similarity = similarity
        self.chunk_id = chunk_id

    def to_dict(self):
        return {
            "content": self.content,
            "material_name": self.material_name,
            "page_number": self.page_number,
            "similarity": round(self.similarity, 3),
        }


async def search_project_chunks(
    db: AsyncSession,
    project_id: UUID,
    query_embedding: list[float],
    top_k: int = None,
    similarity_threshold: float = None,
) -> List[RetrievalResult]:
    """Search for relevant chunks within a specific project using pgvector cosine similarity."""
    top_k = top_k or settings.RAG_TOP_K
    threshold = similarity_threshold or settings.RAG_SIMILARITY_THRESHOLD

    # asyncpg doesn't support mixing :named params with ::type casts.
    # Interpolate safe values directly and use CAST() for the vector type.
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    project_id_str = str(project_id)

    query = text(f"""
        SELECT
            dc.id,
            dc.content,
            dc.page_number,
            m.filename as material_name,
            1 - (dc.embedding <=> CAST('{embedding_str}' AS vector)) as similarity
        FROM document_chunks dc
        JOIN materials m ON dc.material_id = m.id
        WHERE dc.project_id = '{project_id_str}'
          AND dc.embedding IS NOT NULL
          AND 1 - (dc.embedding <=> CAST('{embedding_str}' AS vector)) >= :threshold
        ORDER BY dc.embedding <=> CAST('{embedding_str}' AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(query, {
        "threshold": threshold,
        "top_k": top_k,
    })

    rows = result.fetchall()
    results = []
    for row in rows:
        results.append(RetrievalResult(
            content=row.content,
            material_name=row.material_name,
            page_number=row.page_number,
            similarity=float(row.similarity),
            chunk_id=str(row.id),
        ))

    logger.info(f"Retrieved {len(results)} chunks for project {project_id} (threshold={threshold})")
    return results


async def build_context(
    db: AsyncSession,
    project_id: UUID,
    query_embedding: list[float],
    max_context_length: int = 4000,
) -> tuple[str, list[dict]]:
    """Build context string and citations from retrieved chunks."""
    results = await search_project_chunks(db, project_id, query_embedding)

    if not results:
        return "", []

    context_parts = []
    citations = []
    total_len = 0

    for r in results:
        chunk_text = f"[Source: {r.material_name} — Page {r.page_number}]\n{r.content}\n"
        if total_len + len(chunk_text) > max_context_length:
            break
        context_parts.append(chunk_text)
        citations.append({
            "material_name": r.material_name,
            "page_number": r.page_number,
            "content_snippet": r.content[:200],
            "similarity": r.similarity,
        })
        total_len += len(chunk_text)

    context = "\n---\n".join(context_parts)
    return context, citations
