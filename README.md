# AI Study Companion

> AI-Powered Learning & Growth Workspace — Upload materials, get AI tutoring with citations, take adaptive quizzes, and track mastery growth.

---

## 🏗️ Architecture

```text
Browser → Next.js Frontend → FastAPI REST API → Business Logic → PostgreSQL + pgvector
                                                     ↓
                                              Background Worker
                                 (Document Processing, Embeddings, Concepts)
                                                     ↓
                                               Groq AI (LLM)
```

---

## ✨ Key Features

- **Personalized Workspaces**: Organize your learning into custom Spaces and Projects.
- **Retrieval-Augmented Generation (RAG)**: Upload PDFs and chat with an AI tutor that strictly grounds its answers in your documents with real-time citation linking.
- **Adaptive Quizzes**: Take Multiple Choice and Open-Ended quizzes that dynamically adapt to your mastery level.
- **Mastery Tracking**: Automatically extract core concepts from your materials and track your proficiency over time.
- **AI Evaluations**: LLM-as-a-Judge architecture objectively scores your open-ended quiz answers and provides constructive feedback.
- **Admin Dashboard**: Comprehensive observability into AI requests, token usage, system health, and user journeys.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Groq API key ([get one free](https://console.groq.com))

### 1. Clone & Setup Environment
```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY and DATABASE_URL
```

### 2. Start PostgreSQL with pgvector

**Docker (recommended):**
```bash
docker-compose up db -d
```

**Or use Supabase** (free PostgreSQL with pgvector built-in):
- Create project at [supabase.com](https://supabase.com)
- Copy the connection string to `DATABASE_URL` in `.env`

### 3. Backend Setup
```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed demo data (creates admin + demo user)
python ../scripts/seed_demo_data.py

# Start the API
uvicorn app.main:app --reload --port 8000
```

### 4. Start Background Worker (separate terminal)
```bash
cd backend
.venv\Scripts\activate  # or source .venv/bin/activate
python -m app.workers.runner
```

### 5. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 6. Open the app
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hlo.com | adminpassword |
| Student | demo@studycompanion.ai | demo123456 |

---

## 📋 Demo Flow

1. Register or login
2. Create a Space (e.g., "Computer Science")
3. Create a Project (e.g., "Machine Learning Fundamentals")
4. Upload a PDF → see QUEUED → PROCESSING → READY states
5. Open AI Tutor → ask a grounded question → see citations
6. Ask a question NOT covered by your materials → see insufficient-evidence response
7. Start an Adaptive Quiz → answer MCQ and open-ended questions
8. View evaluation with detailed feedback
9. Check Mastery page → see concept mastery levels
10. View Growth page → see improving/stable/needs-attention categories
11. Generate a Recommendation → get actionable next steps
12. Check Analytics → see real charts from your data
13. Admin dashboard → inspect users, AI logs, system health

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Database** | PostgreSQL 15 + pgvector |
| **Auth** | JWT (bcrypt + python-jose) |
| **AI/LLM** | Groq API (llama-3.1-70b-versatile) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **PDF** | PyMuPDF (fitz) |
| **Background Jobs** | DB-backed queue (PostgreSQL) |

---

## 📁 Project Structure

```text
ai-study-companion/
├── frontend/          # Next.js 14 app
│   ├── src/app/       # Pages (login, dashboard, spaces, projects, admin)
│   └── src/lib/       # API client, auth context
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic
│   │   ├── ai/        # Groq AI provider
│   │   ├── retrieval/ # RAG, vector search, embeddings
│   │   ├── workers/   # Background processing
│   │   ├── models/    # SQLAlchemy models (20+ tables)
│   │   └── schemas/   # Pydantic schemas
│   ├── alembic/       # Database migrations
│   └── tests/         # Backend tests
├── docs/              # Documentation
├── scripts/           # Utilities
└── docker-compose.yml
```

---

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Free Tier Architecture](docs/FREE_TIER_ARCHITECTURE.md)
- [Adaptive Quiz Algorithm](docs/ADAPTIVE_QUIZ.md)
- [AI Evaluation](docs/AI_EVALUATION.md)
- [Engineering Decisions](docs/ENGINEERING_DECISIONS.md)
- [AI Usage](docs/AI_USAGE.md)
- [Limitations](docs/LIMITATIONS.md)

---

## 🔑 Environment Variables

See `.env.example` for all variables. Required:
- `DATABASE_URL` — PostgreSQL connection string
- `GROQ_API_KEY` — Groq API key
- `JWT_SECRET` — Secret for JWT tokens

---

## License

MIT
