# Engineering Decisions

## 1. Ownership-Based Authorization

Every entity is scoped to a user. Authorization is enforced at the API layer:

```python
async def verify_project_ownership(project_id, user, db):
    project = await db.get(Project, project_id)
    if project.user_id != user.id:
        raise HTTPException(403)
    return project
```

**Why**: Simpler than RBAC for a single-user-per-project model. Every query is automatically scoped.

## 2. Structured JSON Output from LLM

All AI responses use structured JSON schemas:

```python
result, stats = await provider.generate_structured(
    system_prompt="...",
    user_prompt="...",
    feature="quiz_generation",
)
```

**Why**: Prevents unstructured text parsing errors. If JSON parsing fails, we retry once with a stricter prompt. Fallback to `{}` if both fail.

## 3. Idempotent Job Queue

Background jobs use an `idempotency_key` to prevent duplicate processing:

```python
idempotency_key = f"process_material:{material.id}"
```

**Why**: If the user clicks "upload" twice or the worker crashes mid-process, we don't create duplicate chunks.

## 4. Event Sourcing for Learning Activity

All learning events are recorded in `learning_events`:

```python
await record_event(db, user_id, project_id, EventType.QUIZ_COMPLETED, {...})
```

**Why**: Analytics queries aggregate these events. Growth analysis uses the event trail to determine trends. No analytics data is hardcoded.

## 5. AI Usage Observability

Every AI call is logged to `ai_usage_logs` with:
- Feature name, model, latency, token counts
- Estimated cost (calculated from token pricing)
- Success/failure status
- Request ID for debugging

**Why**: The admin dashboard shows real AI usage data. Cost tracking helps monitor free-tier limits.

## 6. Page-Aware Chunking

Documents are chunked with page awareness:

```python
chunks.append({
    "page_number": page_num,
    "content": chunk_text,
})
```

**Why**: Citations reference specific pages. The tutor can say "According to page 12 of your textbook..."

## 7. Weighted Moving Average for Mastery

Mastery uses `0.7 * old + 0.3 * new` instead of simple averaging:

**Why**: Simple averaging makes mastery volatile. A student who answers 3 hard questions correctly shouldn't lose mastery on one mistake. The weighted average smooths noise while remaining responsive to genuine changes.

## 8. Concept Extraction on Upload

When a PDF is uploaded, concepts are extracted via LLM:

**Why**: The quiz system needs concept names to generate targeted questions. The mastery system tracks mastery per concept. Without extraction, we'd need manual concept tagging.

## 9. Insufficient Evidence Detection in RAG

The tutor checks if retrieved chunks have sufficient relevance:

```python
if not chunks or all(c.similarity < 0.3 for c in chunks):
    has_sufficient_evidence = False
```

**Why**: Rather than hallucinating, the system tells the user when evidence is limited. This is a critical trust feature.

## 10. No External Dependencies for Core Flows

The only external API is Groq (for LLM). Everything else runs locally:
- Embeddings: sentence-transformers (local)
- Vector search: pgvector (in database)
- Job queue: PostgreSQL (in database)
- Auth: bcrypt + JWT (in-process)

**Why**: Fewer external dependencies = fewer failure points = easier deployment = lower cost.
