# Architecture

## System Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│   Browser        │────▶│  Next.js 14       │────▶│  FastAPI Backend     │
│   (React)        │◀────│  (TypeScript)     │◀────│  (Python 3.12)       │
└─────────────────┘     └──────────────────┘     └──────────┬───────────┘
                                                            │
                    ┌───────────────────────────────────────┼──────────┐
                    │                                       │          │
              ┌─────▼──────┐  ┌───────────────┐  ┌────────▼────────┐ │
              │ PostgreSQL  │  │ Background     │  │ Groq API        │ │
              │ + pgvector  │  │ Worker         │  │ (LLM)           │ │
              │             │  │ (DB Queue)     │  │                 │ │
              └─────────────┘  └───────┬───────┘  └─────────────────┘ │
                                       │                              │
                                ┌──────▼──────┐  ┌─────────────────┐ │
                                │ PyMuPDF      │  │ sentence-       │ │
                                │ (PDF Extract)│  │ transformers    │ │
                                └─────────────┘  │ (Embeddings)    │ │
                                                 └─────────────────┘ │
                                                                     │
                                                  ┌─────────────────┐│
                                                  │ Local Storage /  ││
                                                  │ Supabase Storage ││
                                                  └─────────────────┘│
                                                                     │
                    └────────────────────────────────────────────────-┘
```

## Frontend Architecture

**Next.js 14 App Router** with client-side rendering for interactive pages.

- **Pages**: Login, Register, Dashboard, Spaces, Projects (with sub-pages for Materials, Tutor, Quiz, Mastery, Growth, Analytics), Admin
- **State**: React Context for auth, component state for data
- **API**: Centralized `api.ts` client with JWT header injection
- **Design**: Dark glassmorphism with CSS custom properties (no component library dependency)
- **Charts**: Recharts for analytics visualizations

## Backend Architecture

**FastAPI** with async SQLAlchemy for database operations.

- **Routers**: Clean separation — auth, spaces, projects, materials, tutor, quiz, mastery, recommendations, analytics, admin
- **Services**: Business logic layer (mastery_service, event_service)
- **AI**: Abstracted provider pattern — `GroqProvider` implements `generate_text()`, `generate_structured()`, `generate_with_messages()`
- **Retrieval**: pgvector-based similarity search with project scoping
- **Workers**: DB-backed job queue with retry logic

## Database Design

20+ tables with proper relationships:
- **Core**: users, spaces, projects
- **Knowledge**: materials, document_chunks (with vector embeddings), concepts, project_concepts
- **Learning**: conversations, messages, learning_context
- **Assessment**: quiz_attempts, questions, answers
- **Progress**: mastery_records, learning_events, recommendations
- **System**: background_jobs, ai_usage_logs, ai_evaluations

## Technology Selection Rationale

| Choice | Reason |
|--------|--------|
| Next.js 14 | Modern React with App Router, great DX, Vercel deployment |
| FastAPI | Async Python, auto OpenAPI docs, Pydantic validation |
| PostgreSQL + pgvector | Free-tier friendly, single DB for everything including vectors |
| Groq | Free tier, fast inference, supports llama-3.1 models |
| sentence-transformers | Free local embeddings, no API key needed |
| DB-backed job queue | Eliminates Redis dependency, simpler free-tier deployment |
| JWT auth | Stateless, simple, no external auth service needed |
