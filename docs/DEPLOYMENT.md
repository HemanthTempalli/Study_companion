# Production Deployment Guide — AI Study Companion

This guide covers deploying the **AI Study Companion** to production environments on a **$0/month free-tier setup** or using Docker / cloud platforms.

---

## 1. Environment Variable Summary

All required credentials in your `.env` file are mapped directly to runtime components:

| Key | Description | Production Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Supabase / PgVector connection string | `postgresql://user:pass@host:5432/postgres` |
| `JWT_SECRET` | Secret key for signing auth tokens | 64+ char random string |
| `GROQ_API_KEY` | Groq LLM API Key | `gsk_...` |
| `FRONTEND_URL` | CORS allowed origin for frontend | `https://your-app.vercel.app` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend calls | `https://your-api.onrender.com` |

---

## 2. Option A: One-Click Render Deployment (`render.yaml`)

The repository includes a root `render.yaml` Blueprint definition:

1. Connect your GitHub repository to [Render.com](https://render.com).
2. Create a new **Blueprint Service** selecting this repository.
3. Provide the environment secrets when prompted (`DATABASE_URL`, `GROQ_API_KEY`, etc.).
4. Render will automatically build:
   - **Backend API**: FastAPI on Uvicorn
   - **Worker Process**: Background PDF & embedding processor
   - **Frontend**: Next.js static/SSR site

---

## 3. Option B: Vercel + Render / Railway Split Deployment

### Frontend (Vercel)
1. Import `frontend/` folder into Vercel.
2. Set Environment Variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend-url.onrender.com`
3. Deploy.

### Backend & Worker (Render or Railway)
1. Set Build Command: `cd backend && pip install -r requirements.txt && alembic upgrade head`
2. Set Start Command (Backend): `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set Start Command (Worker): `cd backend && python -m app.workers.runner`
4. Set Environment Variables matching `.env`.

---

## 4. Option C: Docker Compose (Self-Hosted / VPS)

To deploy the entire stack including PgVector database on a single VPS:

```bash
# Build and start container cluster
docker-compose up -d --build

# Run database migrations
docker-compose exec backend alembic upgrade head
```

---

## 5. Automated Database Migrations

Migrations are automated via Alembic. To execute pending migrations against your production Supabase database:

```bash
cd backend
alembic upgrade head
```

The database configuration automatically transforms `postgresql://` connection strings into `postgresql+asyncpg://` for SQLAlchemy async driver compatibility.
