# Free-Tier Architecture

This project is intentionally designed to run entirely within free tiers.

## Cost: $0/month

| Component | Service | Free Tier |
|-----------|---------|-----------|
| Database | Supabase PostgreSQL | 500 MB, pgvector included |
| LLM | Groq API | 14,400 requests/day (llama-3.1-70b) |
| Embeddings | sentence-transformers | Runs locally, zero cost |
| Frontend | Vercel | Unlimited hobby deployments |
| Backend | Railway / Render | 500 hrs/month free |
| Storage | Supabase Storage / Local | 1 GB free |

## Design Decisions for Free Tier

### 1. DB-Backed Job Queue (No Redis)
Traditional background processing uses Redis + Celery. Instead, we use a PostgreSQL-backed job queue:
- `background_jobs` table with `status`, `retry_count`, `max_retries`
- Worker polls with `SELECT ... FOR UPDATE SKIP LOCKED` for atomic job claiming
- Automatic retry with configurable max attempts
- **Trade-off**: Lower throughput (~10 jobs/sec vs ~1000/sec with Redis). Perfectly fine for a learning companion.

### 2. Local Embeddings (No OpenAI)
- `sentence-transformers/all-MiniLM-L6-v2` runs locally in ~200ms per batch
- 384-dimensional vectors → efficient pgvector storage
- Zero API cost for embeddings
- **Trade-off**: Slightly lower quality than text-embedding-3-large. Negligible for educational RAG.

### 3. Groq Instead of OpenAI
- Groq offers 14,400 free requests/day with llama-3.1-70b-versatile
- Faster inference than OpenAI (< 500ms vs 2-5 seconds)
- **Trade-off**: Lower parameter count than GPT-4. For educational tutoring, Llama 3.1 70B performs well.

### 4. Single Database (No Separate Vector DB)
- pgvector extension on PostgreSQL handles vector similarity search
- No need for Pinecone, Qdrant, or Weaviate
- Transactional consistency between metadata and vectors
- **Trade-off**: At >1M vectors, a dedicated vector DB would perform better. For educational use (<100k vectors), pgvector is efficient.

### 5. JWT Auth (No Auth Service)
- bcrypt password hashing + JWT tokens
- No Auth0, Firebase Auth, or Clerk dependency
- Admin role via database field
- **Trade-off**: No social login, MFA, or session management. Acceptable for a prototype.

## Scaling Path

When the app grows beyond free tiers:

1. **Redis/RabbitMQ** for job queue → higher throughput
2. **Pinecone/Qdrant** for vector search → sub-10ms at millions of vectors
3. **OpenAI GPT-4o** for higher quality responses
4. **Clerk/Auth0** for social login + MFA
5. **S3/GCS** for file storage → unlimited scale
6. **Kubernetes** for container orchestration
