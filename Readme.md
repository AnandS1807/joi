# Resume Analyzer — AI-Powered ATS + Semantic Matching

> FastAPI · MongoDB · Qdrant · Redis · Next.js · OpenAI

---

## Stack

| Layer | Tech |
|-------|------|
| Backend API | FastAPI + Pydantic v2 |
| Database | MongoDB (Beanie ODM) |
| Vector DB | Qdrant |
| Cache / Queue | Redis + Dramatiq |
| AI / Embeddings | sentence-transformers + OpenAI |
| Frontend | Next.js 14 + Tailwind |
| Infra | Docker Compose |

---

## Quick Start

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts MongoDB (27017), Qdrant (6333), Redis (6379).

---

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# → Edit .env and add your OPENAI_API_KEY

uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

### 3. Frontend setup

```bash
cd frontend
npm install

cp .env.local.example .env.local

npm run dev
```

App: http://localhost:3000

---

## Project Structure

```
resume-analyzer/
├── docker-compose.yml          # MongoDB + Qdrant + Redis
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app + lifespan
│   │   ├── core/
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   └── database.py     # DB connections
│   │   ├── models/
│   │   │   └── documents.py    # Beanie ODM models
│   │   ├── schemas/
│   │   │   └── schemas.py      # Pydantic request/response
│   │   ├── auth/
│   │   │   └── utils.py        # JWT + password hashing
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py         # /auth/register, /auth/login
│   │   │   ├── resumes.py      # /resumes/* (upload, list, get, delete)
│   │   │   └── jobs_analysis.py # /jobs/*, /analysis/*
│   │   ├── resumes/
│   │   │   └── service.py      # PDF parse + embed (Phase 2)
│   │   ├── jobs/
│   │   │   └── service.py      # JD parse + embed (Phase 2)
│   │   ├── embeddings/         # ← Phase 2
│   │   ├── llm/                # ← Phase 3
│   │   ├── matching/
│   │   │   └── service.py      # ATS + semantic scoring (Phase 3)
│   │   ├── workers/            # ← Phase 4 (Dramatiq)
│   │   └── vectorstore/        # ← Phase 2 (Qdrant ops)
│   └── requirements.txt
│
└── frontend/
    ├── lib/api.ts              # Axios client + all API calls
    ├── store/auth.ts           # Zustand auth state
    └── package.json
```

---

## Build Phases

| Phase | What | Status |
|-------|------|--------|
| 1 | Project setup, auth, file upload, DB models | ✅ Done |
| 2 | PDF parsing, embeddings, Qdrant storage | 🔜 Next |
| 3 | Semantic matching, ATS scoring, LLM suggestions | ⏳ |
| 4 | Async workers (Dramatiq), Redis queues, WebSocket | ⏳ |

---

## API Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login

POST   /api/v1/resumes/upload     (multipart/form-data)
GET    /api/v1/resumes/
GET    /api/v1/resumes/{id}
DELETE /api/v1/resumes/{id}

POST   /api/v1/jobs/
GET    /api/v1/jobs/
GET    /api/v1/jobs/{id}

POST   /api/v1/analysis/
GET    /api/v1/analysis/
GET    /api/v1/analysis/{id}

GET    /health
GET    /docs                      (Swagger UI)
```