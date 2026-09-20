# AI Study Companion

![Status](https://img.shields.io/badge/status-prototype-orange)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-App%20Router-000000?logo=nextdotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-frontend-3178C6?logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20Llama%203.1%2070B-F55036)
![Embeddings](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-yellow)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)
![Storage](https://img.shields.io/badge/Storage-Supabase-3ECF8E?logo=supabase&logoColor=white)

A full-stack learning platform that restricts an LLM to a student's own uploaded coursework (PDFs). It provides a citation-grounded AI tutor, adaptive quizzes, per-concept mastery tracking, and study recommendations, with an admin dashboard for observability of AI usage, background jobs, and system health.

The system is designed to run within free-tier hosting limits: PostgreSQL with pgvector for relational data, vectors, and the job queue; local embeddings; and Groq as the only external AI dependency.

> **Status:** Prototype / portfolio project. See [Known Limitations](#known-limitations).

---

## Table of Contents

1. [Features](#features)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [How It Works](#how-it-works)
5. [Getting Started](#getting-started)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [API Overview](#api-overview)
9. [AI Usage, Cost, and Evaluation](#ai-usage-cost-and-evaluation)
10. [Engineering Decisions](#engineering-decisions)
11. [Security and Data Isolation](#security-and-data-isolation)
12. [Known Limitations](#known-limitations)
13. [Documentation Index](#documentation-index)

---

## Features

**Workspace organization**
- Two-level hierarchy: **Spaces** (e.g., a course or subject area) contain **Projects** (a specific topic with an optional learning goal).
- Every project has a dashboard summarizing mastery, quiz statistics, recommendations, and recent activity.

**Document ingestion**
- PDF upload with asynchronous background processing: text extraction, page-aware chunking, embedding, and LLM-based concept extraction.
- Processing status is visible per material; failed materials can be retried.

**AI tutor (RAG)**
- Answers are grounded in retrieved chunks from the active project's materials, with page-level citations.
- If retrieved evidence is insufficient, the tutor flags this (`has_sufficient_evidence: false`) and declines to answer from general knowledge.
- Conversations and messages are persisted.

**Adaptive quizzes**
- Multiple-choice and open-ended questions generated from the student's materials.
- Concept selection is weighted toward weaker concepts; difficulty is calibrated to average mastery.
- Open-ended answers are scored by an LLM evaluator with structured feedback.

**Mastery, growth, and recommendations**
- Per-concept mastery is updated after each answered question using a weighted moving average, with an evidence trail.
- Growth analysis classifies progress as improving, stable, or needs attention.
- AI-generated study recommendations target concepts with mastery below 60%.

**Administration and observability**
- Admin endpoints for user activity, per-user learning journeys, system health, AI usage logs (latency, tokens, estimated cost), and background job monitoring.
- An AI evaluation framework that records results to an `ai_evaluations` table.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js (App Router), TypeScript, React, Recharts |
| Backend | FastAPI, Python 3.12, async SQLAlchemy, Pydantic, Alembic |
| PDF processing | PyMuPDF (`fitz`) |
| Authentication | JWT (`python-jose`), bcrypt password hashing (`passlib`) |
| Database | PostgreSQL with the pgvector extension (hosted on Supabase in the documented deployment) |
| Job queue | PostgreSQL-backed queue (`background_jobs` table) |
| LLM | Groq API, `llama-3.1-70b-versatile` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, 384 dimensions) |
| File storage | Supabase Storage |
| Deployment | Render web services (Blueprint via `render.yaml`); Docker Compose for self-hosting |


---

## System Architecture

```mermaid
flowchart LR
    Browser["Browser (React)"] --> Frontend["Next.js frontend"]
    Frontend -->|"REST + JWT"| API["FastAPI backend"]

    API --> DB[("PostgreSQL + pgvector")]
    API --> Groq["Groq API (LLM)"]
    API --> Embed["sentence-transformers (local embeddings)"]
    API --> Storage["Supabase Storage (uploaded PDFs)"]

    Worker["Background worker (DB-backed queue)"] --> DB
    Worker --> PDF["PyMuPDF (text extraction)"]
    Worker --> Embed
    Worker --> Groq
```

### Backend layout

- **Routers:** `auth`, `spaces`, `projects`, `materials`, `tutor`, `quiz`, `mastery`, `recommendations`, `analytics`, `admin`
- **Services:** business logic such as `mastery_service` and `event_service`
- **AI layer:** a provider abstraction (`GroqProvider`) exposing `generate_text()`, `generate_structured()`, and `generate_with_messages()`
- **Retrieval:** pgvector similarity search scoped by project
- **Workers:** a DB-backed job queue with retry logic

### Frontend layout

- Next.js App Router with client-side rendering for interactive pages
- Pages: Login, Register, Dashboard, Spaces, Projects (Materials, Tutor, Quiz, Mastery, Growth, Analytics), Admin
- React Context for authentication; component state for data
- Centralized `api.ts` client that injects the JWT header
- Recharts for analytics visualizations

### Database

20+ tables, grouped as follows:

| Group | Tables |
|-------|--------|
| Core | `users`, `spaces`, `projects` |
| Knowledge | `materials`, `document_chunks` (with vector embeddings), `concepts`, `project_concepts` |
| Learning | `conversations`, `messages`, `learning_context` |
| Assessment | `quiz_attempts`, `questions`, `answers` |
| Progress | `mastery_records`, `learning_events`, `recommendations` |
| System | `background_jobs`, `ai_usage_logs`, `ai_evaluations` |

---

## How It Works

### 1. Document ingestion

1. The user uploads a PDF; a background job is enqueued with an idempotency key (`process_material:{material.id}`).
2. A worker claims the job using `SELECT ... FOR UPDATE SKIP LOCKED`.
3. **Extraction:** PyMuPDF extracts text with page numbers.
4. **Chunking:** Text is split into chunks of roughly 500 tokens with a 50-token overlap, retaining `page_number` for citations.
5. **Embedding:** Chunks are embedded locally with `all-MiniLM-L6-v2` (384 dimensions) and stored in `document_chunks`.
6. **Concept extraction:** The LLM is given a sample of the first 10 pages and returns 5–15 concept names with descriptions. These concepts drive quiz generation and mastery tracking.

### 2. AI tutor (RAG)

1. The student's question is embedded.
2. pgvector cosine-similarity search retrieves the most relevant chunks (top 5) within the project.
3. The chunks are injected into the prompt as reference data; the prompt instructs the model to treat document content as data, not instructions.
4. The model returns JSON containing the answer, an evidence flag, and cited sources (`material_name`, `page_number`).
5. If there are no chunks, or all retrieved chunks have similarity below `0.3`, the response is flagged as having insufficient evidence.

### 3. Adaptive quiz generation

```
1. Gather mastery data for all concepts
2. Compute concept weights (weaker concepts weighted higher)
3. Retrieve relevant document chunks for the weighted concepts
4. Build the prompt: context + mastery data + difficulty calibration
5. Generate questions via Groq (structured JSON output)
6. Parse, validate, and store questions
```

**Concept weighting**

| Concept mastery | Weight |
|-----------------|--------|
| < 50% | 3× |
| 50–80% | 2× |
| > 80% | 1× |

**Difficulty calibration (based on average mastery)**

| Average mastery | Difficulty | Question style |
|-----------------|-----------|----------------|
| < 40% | Easy | Recognition, basic recall |
| 40–70% | Medium | Application, comparison |
| > 70% | Hard | Analysis, synthesis, edge cases |

**Question types**

- **MCQ:** four options, one correct answer, distractors generated from common misconceptions. Graded deterministically (100 or 0).
- **Open-ended:** free-text answer evaluated by the LLM against the correct answer and material context. Scoring rubric: accuracy (0–40), completeness (0–30), understanding (0–30). The evaluator returns a score, `understood` / `missing` / `mistakes` lists, an explanation, and a suggested review topic.

### 4. Mastery update

After each answered question, concept mastery is updated with a weighted moving average:

```python
if evidence_count > 3:
    new_mastery = old_mastery * 0.7 + score * 0.3   # established concept
else:
    new_mastery = old_mastery * 0.5 + score * 0.5   # new concept, more responsive
```

Each update is recorded in an evidence trail (date, score, source of quiz or tutor, mastery before and after), kept as a rolling window of the last 50 data points.

---

## Getting Started

### Prerequisites

- Python 3.12
- Node.js (for the Next.js frontend)
- PostgreSQL with the `pgvector` extension (a Supabase project works), or Docker for the bundled Compose setup
- A [Groq](https://console.groq.com) API key

### 1. Clone and configure

```bash
git clone https://github.com/HemanthTempalli/Study_companion.git
cd Study_companion
```

Create a `.env` file (see [Configuration](#configuration)).

### 2. Backend

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Background worker

Document processing is handled by the worker. Run it as a separate process:

```bash
cd backend
python -m app.workers.runner
```

`PROJECT_REPORT.md` also describes a single-container mode in which the worker is started inside the FastAPI `lifespan` event via `asyncio.create_task()`, intended for memory-constrained free-tier instances.

### 4. Frontend

The frontend lives in `frontend/`. It reads the backend URL from `NEXT_PUBLIC_API_URL` (for local development, `http://localhost:8000`).

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose (self-hosted)

```bash
docker-compose up -d --build
docker-compose exec backend alembic upgrade head
```

This brings up the full stack, including the pgvector-enabled database.

### Admin access

Roles (`user` and `admin`) are stored in the database. Admin endpoints require the admin role, and an existing admin can promote another user with `POST /api/admin/make-admin/{user_id}`.

---

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL / Supabase (pgvector) connection string | `postgresql://user:pass@host:5432/postgres` |
| `JWT_SECRET` | Secret used to sign auth tokens (use a 64+ character random string) | — |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `FRONTEND_URL` | Allowed CORS origin for the frontend | `https://your-frontend.onrender.com` |
| `NEXT_PUBLIC_API_URL` | Backend base URL used by the frontend | `https://your-api.onrender.com` |

The database layer automatically converts `postgresql://` URLs to `postgresql+asyncpg://` for the SQLAlchemy async driver.

Never commit real secrets. Keep `.env` out of version control.

---

## Deployment

The project is deployed on **Render web services**, with **Supabase** providing PostgreSQL (pgvector) and Supabase Storage for uploaded PDFs. Full instructions are in `DEPLOYMENT.md`.

| Component | Where it runs | Notes |
|-----------|---------------|-------|
| Backend API | Render web service | FastAPI on Uvicorn |
| Frontend | Render web service | Next.js; needs `NEXT_PUBLIC_API_URL` pointing at the backend |
| Background worker | Render | Separate process, or started inside the API process (see below) |
| Database | Supabase PostgreSQL | pgvector enabled |
| File storage | Supabase Storage | Uploaded PDFs |
| LLM | Groq API | Requires `GROQ_API_KEY` |

### Deploying on Render

**Option 1: Blueprint.** The repository root includes a `render.yaml` Blueprint.

1. Connect the GitHub repository to Render.
2. Create a new **Blueprint** service from the repository.
3. Provide the environment secrets when prompted (`DATABASE_URL`, `JWT_SECRET`, `GROQ_API_KEY`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`).
4. Render builds the backend API, the worker process, and the frontend.

**Option 2: Manual web services.** Create the services yourself using these commands, and set the environment variables from [Configuration](#configuration):

- Build: `cd backend && pip install -r requirements.txt && alembic upgrade head`
- Backend start: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Worker start: `cd backend && python -m app.workers.runner`

Migrations are applied with `alembic upgrade head`.

**Worker on small instances.** `PROJECT_REPORT.md` describes a single-container mode for Render free-tier instances in which the worker is started inside the FastAPI `lifespan` event, so no separate worker service is needed. On 512 MB RAM instances it also describes limiting PyTorch to a single thread (`OMP_NUM_THREADS=1`) and using reduced embedding batch sizes to avoid out-of-memory crashes.

### Alternative: Docker Compose

`DEPLOYMENT.md` also documents a self-hosted setup on a single VPS (see [Docker Compose](#docker-compose-self-hosted)).

### Free-tier services (as documented)

| Component | Service | Free-tier limit |
|-----------|---------|-----------------|
| Database | Supabase PostgreSQL | 500 MB, pgvector included |
| File storage | Supabase Storage | 1 GB |
| LLM | Groq API | 14,400 requests/day |
| Embeddings | sentence-transformers | Runs locally, no API cost |
| Web services | Render | 500 hrs/month |

> Free-tier limits are taken from the project's documentation and may change. Verify against each provider's current terms.

---

## API Overview

Base URL (local): `http://localhost:8000`. All endpoints except `/api/health` and the auth endpoints require a JWT. Project-scoped endpoints additionally enforce ownership; admin endpoints require the admin role.

| Area | Endpoints |
|------|-----------|
| **Auth** | `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me` |
| **Spaces** | `POST /api/spaces/` · `GET /api/spaces/` · `GET/PUT/DELETE /api/spaces/{id}` |
| **Projects** | `POST /api/projects/` · `GET /api/projects/?space_id=` · `GET /api/projects/{id}` · `GET /api/projects/{id}/dashboard` |
| **Materials** | `POST` / `GET /api/projects/{id}/materials/` · `DELETE /api/projects/{id}/materials/{material_id}` · `POST .../{material_id}/retry` |
| **Tutor** | `POST /api/projects/{id}/tutor/chat` · `GET .../tutor/conversations` · `GET .../tutor/conversations/{conv_id}/messages` |
| **Quiz** | `POST /api/projects/{id}/quiz/generate` · `POST .../quiz/{quiz_id}/submit` · `GET .../quiz/history` |
| **Mastery & growth** | `GET /api/projects/{id}/mastery` · `GET /api/projects/{id}/growth` |
| **Recommendations** | `POST .../recommendations/generate` · `GET .../recommendations/` · `POST .../recommendations/{rec_id}/dismiss` |
| **Analytics** | `GET /api/projects/{id}/analytics` · `GET /api/admin/analytics` (admin) |
| **Admin** | `GET /api/admin/users` · `GET /api/admin/users/{user_id}/journey` · `GET /api/admin/health` · `GET /api/admin/ai-logs` · `GET /api/admin/jobs` · `POST /api/admin/make-admin/{user_id}` |
| **Health** | `GET /api/health` (public) |

**Example: tutor chat**

```json
// POST /api/projects/{id}/tutor/chat
// Request
{ "message": "What is gradient descent?", "conversation_id": null }

// Response
{
  "answer": "...",
  "citations": [ ... ],
  "has_sufficient_evidence": true,
  "conversation_id": "uuid"
}
```

**Example: quiz generation and submission**

```json
// POST /api/projects/{id}/quiz/generate
{ "num_questions": 5, "difficulty": null }
// -> { "id": "uuid", "questions": [ ... ] }

// POST /api/projects/{id}/quiz/{quiz_id}/submit
[ { "question_id": "uuid", "user_answer": "..." } ]
// -> { "score": 80, "question_results": [ ... ], "mastery_updates": [ ... ] }
```

Full request/response details are in `API.md`.

---

## AI Usage, Cost, and Evaluation

### Models

All LLM features (tutor, quiz generation, quiz evaluation, concept extraction, recommendations) use `llama-3.1-70b-versatile` through Groq. Embeddings use `all-MiniLM-L6-v2` locally.

### Approximate per-feature usage

The figures below are the estimates recorded in `AI_USAGE.md`, not benchmarked results.

| Feature | Avg. tokens (in / out) | Approx. latency |
|---------|------------------------|-----------------|
| AI tutor | ~2000 / ~500 | ~800 ms |
| Quiz generation | ~3000 / ~1500 | ~1500 ms |
| Quiz evaluation (open-ended) | ~800 / ~400 | ~500 ms |
| Concept extraction | ~2000 / ~800 | ~1000 ms |
| Recommendations | ~1000 / ~300 | ~500 ms |

Every AI call is logged to `ai_usage_logs` (feature, model, latency, token counts, estimated cost, success/failure, request ID). Using the documented Groq pricing ($0.59 / 1M input tokens, $0.79 / 1M output tokens), the estimated cost of one session (upload, 5 tutor questions, 1 quiz) is roughly $0.005.

### Structured output handling

1. First attempt uses a prompt with JSON format instructions.
2. Markdown code fences in the response are stripped before parsing.
3. If parsing fails, the call is retried once with a stricter "respond only with JSON" prompt.
4. If the retry also fails, a safe default (`{}`) is returned so malformed output does not crash the request.

### Hallucination mitigation

- Answers are grounded in retrieved chunks from the active project.
- The prompt requires compact citations and forbids fabricated ones.
- The tutor is instructed not to fall back to general knowledge when the material lacks the answer.
- Low-similarity retrieval is flagged as insufficient evidence.
- Structured JSON output constrains response shape.

### Evaluation framework

The framework covers four areas: quiz question quality, tutor response quality, quiz evaluation accuracy, and recommendation quality. Results are stored in `ai_evaluations` (feature, test case, input, expected/actual output, score, pass/fail, details) and can be run programmatically:

```python
from app.ai.evaluation import run_evaluation_suite

results = await run_evaluation_suite(db, feature="quiz_generation")
```

**Target thresholds** (defined quality targets, not measured results):

| Feature | Metric | Target |
|---------|--------|--------|
| Quiz generation | Valid JSON output | 100% |
| Quiz generation | Relevant questions | > 80% |
| Tutor response | Grounded answers | > 90% |
| Tutor response | Citation accuracy | > 85% |
| Quiz evaluation | MCQ accuracy | 100% |
| Quiz evaluation | Open-ended consistency | > 75% |
| Recommendations | Actionable output | > 90% |

---

## Engineering Decisions

A summary of the decisions documented in `ENGINEERING_DECISIONS.md` and `FREE_TIER_ARCHITECTURE.md`:

| Decision | Rationale |
|----------|-----------|
| Ownership-based authorization checked at the API layer | Simpler than full RBAC for a single-owner-per-project model; queries are scoped to the user. |
| Structured JSON from the LLM, with retry and fallback | Avoids brittle free-text parsing; one stricter retry, then a safe default. |
| Idempotent job queue (`idempotency_key`) | Prevents duplicate chunks on double uploads or worker crashes. |
| DB-backed job queue instead of Redis/Celery | Removes a dependency for free-tier deployment. Trade-off: lower throughput (~10 jobs/sec documented vs. ~1000/sec with Redis). |
| Event-sourced learning activity (`learning_events`) | Analytics and growth analysis derive from recorded events rather than hardcoded data. |
| Full AI call logging | Provides real usage and cost data in the admin dashboard and helps track free-tier limits. |
| Page-aware chunking | Enables page-level citations. |
| Weighted moving average for mastery | Smooths noise so a single mistake does not sharply reduce mastery, while still responding to real change. |
| Concept extraction on upload | Supplies the concept names needed for targeted quizzes and mastery tracking without manual tagging. |
| Insufficient-evidence detection in RAG | Prefers an explicit "not enough evidence" response over a fabricated answer. |
| Single database (pgvector) | Transactional consistency between metadata and vectors; adequate for the documented scale (under ~100k vectors). |
| Local embeddings | No embedding API cost. Trade-off: lower quality than larger hosted embedding models. |
| Minimal external dependencies | Groq is the only external API in core flows. |

---

## Security and Data Isolation

- **Passwords:** hashed with bcrypt.
- **Sessions:** stateless JWT bearer tokens.
- **Roles:** `user` and `admin`, stored in the database. Admin endpoints require the admin role.
- **Ownership checks:** project-scoped endpoints verify that the authenticated user owns the project (403 otherwise).
- **Retrieval scoping:** chunks, conversations, and embeddings are tied to a `project_id`, and similarity search is scoped to the active project.
- **Prompt handling:** the tutor prompt instructs the model to treat document content as reference data, not as instructions.
- **Not implemented:** per-user rate limiting, MFA, and social login (see below).

---

## Known Limitations

Documented in `LIMITATIONS.md`:

1. **PDF only.** DOCX, PPTX, images, and video are not processed.
2. **No real-time updates.** Processing status is polled by the frontend every 5 seconds; there is no WebSocket channel.
3. **Single-user projects.** No shared projects or collaboration.
4. **Email/password only.** No OAuth providers or social login.
5. **Single storage provider.** Uploaded PDFs are stored in Supabase Storage; other providers such as S3/GCS are not integrated.
6. **No rate limiting.** The API has no per-user limits; Groq's own limits (documented as 14,400 requests/day) apply.
7. **Embedding model.** `all-MiniLM-L6-v2` (384 dimensions) is lightweight; larger hosted models may retrieve better but require API keys.
8. **Requires connectivity for AI features.** Embeddings are local, but LLM calls need Groq.
9. **English only.** UI and AI responses are in English.
10. **Test coverage.** Integration tests exist for critical paths; there is no comprehensive unit test suite and no E2E tests.

### Documented scaling path

Not implemented; recorded in `FREE_TIER_ARCHITECTURE.md` as next steps beyond free tiers: Redis/RabbitMQ for the job queue, a dedicated vector database at larger scale, a higher-capability LLM, a managed auth provider, object storage (S3/GCS), and container orchestration.

---

## Documentation Index

| File | Contents |
|------|----------|
| `ARCHITECTURE.md` | System overview, frontend/backend/database design, technology rationale |
| `API.md` | Endpoint reference |
| `ADAPTIVE_QUIZ.md` | Quiz generation, difficulty calibration, evaluation, mastery updates |
| `AI_USAGE.md` | Models, per-feature usage, cost tracking, hallucination prevention |
| `AI_EVALUATION.md` | Evaluation dimensions, schema, and quality targets |
| `PROMPTS.md` | System prompts for tutor, evaluator, concept extraction, and recommendations |
| `ENGINEERING_DECISIONS.md` | Design decisions and rationale |
| `FREE_TIER_ARCHITECTURE.md` | Free-tier design choices, trade-offs, and scaling path |
| `DEPLOYMENT.md` | Deployment guide (Render Blueprint, split deployment, Docker Compose) |
| `LIMITATIONS.md` | Known limitations and mitigations |
| `PROJECT_REPORT.md` | Detailed technical project report |
