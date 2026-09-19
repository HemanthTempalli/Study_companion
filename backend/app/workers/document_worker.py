"""Document processing worker — extracts text, chunks, generates embeddings, extracts concepts."""

import logging
import json
from uuid import UUID

import fitz  # PyMuPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Material, MaterialStatus, DocumentChunk, Concept, ProjectConcept, EventType,
)
from app.retrieval.embeddings import generate_embedding, generate_embeddings_batch
from app.core.config import settings

logger = logging.getLogger(__name__)

# Chunking config
CHUNK_SIZE = 500  # tokens (approx chars / 4)
CHUNK_OVERLAP = 50


async def process_material(db: AsyncSession, material_id: str, project_id: str, user_id: str):
    """Full material processing pipeline: extract → chunk → embed → concepts."""
    from app.services.event_service import record_event

    result = await db.execute(select(Material).where(Material.id == UUID(material_id)))
    material = result.scalar_one_or_none()
    if not material:
        logger.error(f"Material {material_id} not found")
        return

    material.status = MaterialStatus.PROCESSING
    await db.commit()

    try:
        # Step 1: Extract text from PDF
        logger.info(f"Extracting text from {material.filename}")
        pages = extract_pdf_text(material.storage_path)
        material.page_count = len(pages)

        if not pages:
            raise ValueError("No text could be extracted from the PDF")

        # Step 2: Chunk text (page-aware)
        logger.info(f"Chunking {len(pages)} pages")
        chunks = chunk_pages(pages)

        if not chunks:
            raise ValueError("No meaningful text chunks were created")

        # Step 3: Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        texts = [c["content"] for c in chunks]
        embeddings = generate_embeddings_batch(texts)

        # Step 4: Store chunks with embeddings
        logger.info("Storing chunks in database")
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                material_id=material.id,
                project_id=UUID(project_id),
                page_number=chunk["page_number"],
                chunk_index=i,
                content=chunk["content"],
                embedding=embedding,
                metadata_={"char_count": len(chunk["content"])},
            )
            db.add(db_chunk)

        # Step 5: Extract concepts via Groq
        logger.info("Extracting concepts")
        await extract_concepts(db, material, UUID(project_id), pages)

        material.status = MaterialStatus.READY
        material.error_message = None
        await db.commit()

        await record_event(db, UUID(user_id), UUID(project_id), EventType.MATERIAL_READY, {
            "filename": material.filename, "pages": len(pages), "chunks": len(chunks),
        })
        await db.commit()
        logger.info(f"Material {material.filename} processed successfully: {len(pages)} pages, {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Failed to process material {material_id}: {e}")
        material.status = MaterialStatus.FAILED
        material.error_message = str(e)[:500]
        await db.commit()

        await record_event(db, UUID(user_id), UUID(project_id), EventType.MATERIAL_FAILED, {
            "filename": material.filename, "error": str(e)[:200],
        })
        await db.commit()
        raise


def extract_pdf_text(file_path: str) -> list[dict]:
    """Extract text from PDF using PyMuPDF, page by page."""
    pages = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                pages.append({
                    "page_number": page_num + 1,
                    "content": text.strip(),
                })
        doc.close()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    return pages


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Create page-aware chunks with overlap for better context."""
    chunks = []
    for page in pages:
        text = page["content"]
        page_num = page["page_number"]

        # Split into sentences/paragraphs
        words = text.split()
        if not words:
            continue

        current_chunk = []
        current_len = 0

        for word in words:
            current_chunk.append(word)
            current_len += 1

            if current_len >= chunk_size:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.strip()) > 20:  # Minimum meaningful content
                    chunks.append({
                        "page_number": page_num,
                        "content": chunk_text.strip(),
                    })
                # Keep overlap
                current_chunk = current_chunk[-overlap:]
                current_len = len(current_chunk)

        # Remaining text
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.strip()) > 20:
                chunks.append({
                    "page_number": page_num,
                    "content": chunk_text.strip(),
                })

    return chunks


async def extract_concepts(db: AsyncSession, material: Material, project_id: UUID, pages: list[dict]):
    """Extract key concepts from material using Groq."""
    try:
        from app.ai.groq_provider import get_ai_provider

        # Sample text from pages
        sample_text = "\n\n".join([
            f"Page {p['page_number']}: {p['content'][:500]}"
            for p in pages[:10]
        ])

        provider = get_ai_provider()
        result, stats = await provider.generate_structured(
            system_prompt="""Extract the key learning concepts from this educational material.
Return a JSON object with a "concepts" array. Each concept should have:
- "name": the concept name (short, specific)
- "description": brief description (1-2 sentences)

Extract 5-15 key concepts. Focus on the main topics and important ideas.""",
            user_prompt=f"Material: {material.filename}\n\n{sample_text}",
            feature="concept_extraction",
        )

        from app.ai.groq_provider import log_ai_usage
        await log_ai_usage(db, stats, project_id=project_id)

        concepts_data = result.get("concepts", [])
        for cd in concepts_data[:15]:
            name = cd.get("name", "").strip()
            if not name:
                continue

            # Find or create concept
            existing = await db.execute(select(Concept).where(Concept.name == name))
            concept = existing.scalar_one_or_none()
            if not concept:
                concept = Concept(name=name, description=cd.get("description", ""))
                db.add(concept)
                await db.flush()

            # Link to project
            existing_link = await db.execute(
                select(ProjectConcept).where(
                    ProjectConcept.project_id == project_id,
                    ProjectConcept.concept_id == concept.id,
                )
            )
            if not existing_link.scalar_one_or_none():
                link = ProjectConcept(
                    project_id=project_id,
                    concept_id=concept.id,
                    material_id=material.id,
                )
                db.add(link)

    except Exception as e:
        logger.warning(f"Concept extraction failed (non-critical): {e}")
        # Don't fail the whole pipeline for concept extraction
