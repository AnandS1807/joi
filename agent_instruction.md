# AI Agent Instructions — Resume Analyzer (ATS + Semantic Matching)

## Who you are and what you are doing

You are an AI coding agent. Your job is to build a production-quality resume analyzer
backend in stages. The human developer (Ronin) has already set up the project skeleton.
Your job is to read the existing code, understand it fully, extend it stage by stage,
and ensure every endpoint is testable in Swagger after each stage is complete.

Do not rush. Do not skip stages. Do not assume. Read first, build second, verify third.

---

## Project goal

Build a system where a user can:

1. Register and log in (JWT auth)
2. Upload their resume as a PDF
3. Paste a job description (JD)
4. Get back:
   - An ATS score (keyword overlap, 0–100)
   - A semantic similarity score (embedding cosine similarity, 0–100)
   - A combined overall score (weighted)
   - Matched skills (resume ∩ JD)
   - Missing skills (JD skills the resume lacks)
   - Extra skills (resume has, JD doesn't require)
   - Per-section scores (skills, experience, education)
   - AI-generated improvement suggestions (via Ollama LLM)
   - A plain-English summary of the analysis

This is not a simple keyword matcher. It uses real NLP (spaCy), real embeddings
(sentence-transformers), a real vector DB (Qdrant), and a local LLM (Ollama).

---

## Infrastructure

These services must be running before you start:

| Service   | Default Port | Purpose                          |
|-----------|-------------|----------------------------------|
| MongoDB   | 27017       | Primary data store (users, resumes, jobs, results) |
| Qdrant    | 6333        | Vector database for embeddings   |
| Redis     | 6379        | Cache, task queue (Phase 4)      |
| Ollama    | 11434       | Local LLM inference              |

Start them with: `docker compose up -d` from the project root.

Check Ollama has a model: `ollama list`. If empty, pull one: `ollama pull llama3.2`.

---

## Step 0: Read and understand the existing code

Before writing a single line, do the following in order:

### 0a. Read the file structure

```
backend/
├── app/
│   ├── main.py                          ← FastAPI app, lifespan, router registration
│   ├── core/
│   │   ├── config.py                    ← All settings via pydantic-settings (.env file)
│   │   └── database.py                  ← Async connections: MongoDB, Qdrant, Redis
│   ├── models/
│   │   └── documents.py                 ← Beanie ODM models (MongoDB collections)
│   ├── schemas/
│   │   └── schemas.py                   ← Pydantic v2 request/response schemas
│   ├── auth/
│   │   └── utils.py                     ← JWT creation/decoding, bcrypt, get_current_user dependency
│   ├── api/v1/endpoints/
│   │   ├── auth.py                      ← POST /auth/register, POST /auth/login
│   │   ├── resumes.py                   ← POST /resumes/upload, GET /resumes/, GET /resumes/{id}, DELETE /resumes/{id}
│   │   └── jobs_analysis.py             ← POST /jobs/, GET /jobs/, GET /jobs/{id}, POST /analysis/, GET /analysis/, GET /analysis/{id}
│   ├── resumes/
│   │   └── service.py                   ← STUB: parse_and_embed() — needs real implementation
│   ├── jobs/
│   │   └── service.py                   ← STUB: parse_and_embed() — needs real implementation
│   ├── matching/
│   │   └── service.py                   ← STUB: run() — needs real implementation
│   ├── embeddings/                      ← EMPTY: create engine.py here
│   ├── llm/                             ← EMPTY: create client.py here
│   ├── vectorstore/                     ← EMPTY: create store.py here
│   └── workers/                         ← EMPTY: create tasks.py here (Phase 4)
├── requirements.txt
└── .env.example                         ← Copy to .env and fill values
```

### 0b. Read every existing file

Read them ALL. Understand:

- How `config.py` exposes `settings` — every other module imports from here
- How `database.py` creates global singletons for MongoDB, Qdrant, Redis clients, and how `get_qdrant()` / `get_redis()` provide access to them
- How `documents.py` defines `Resume`, `JobDescription`, `AnalysisResult`, and `User` as Beanie documents — understand each field and its status lifecycle
- How `schemas.py` defines request/response models — these are SEPARATE from DB models
- How `auth/utils.py` implements `get_current_user` as a FastAPI dependency
- How `resumes.py` endpoint calls `process_resume_task` as a `BackgroundTask` that calls `ResumeService.parse_and_embed(resume_id)`
- How `jobs_analysis.py` endpoint calls `JobService.parse_and_embed(job_id)` and `MatchingService.run(result_id)` as background tasks

### 0c. Evaluate the architecture

After reading, decide:

- Is the file structure sensible for where this project is going? If you want to reorganize, do it now before writing any logic. Document why you changed things.
- Is there anything in the existing code that will cause problems in later stages? Fix it now.
- Are there any missing `__init__.py` files? Add them.
- Does `requirements.txt` have everything you'll need for all 4 phases? If not, update it.

If you make structural changes, re-verify that `python -c "from app.main import app"` still works before continuing.

---

## The .env file

The developer must have this file at `backend/.env`. Verify it exists before running anything.
If it doesn't exist, tell the developer to run `cp .env.example .env` and fill in the values.

Key values:

```env
APP_NAME=Resume Analyzer API
APP_VERSION=0.1.0
DEBUG=true
SECRET_KEY=<any-long-random-string>
ALLOWED_ORIGINS=http://localhost:3000

MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=resume_analyzer

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=resume_embeddings

REDIS_URL=redis://localhost:6379/0

LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2          # ← must match output of `ollama list`

EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10
```

---

## How to run and test

Always run from the `backend/` directory with the venv activated:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Test every stage at: **http://localhost:8000/docs**

Swagger workflow:
1. `POST /api/v1/auth/register` → create a user
2. `POST /api/v1/auth/login` → copy `access_token`
3. Click **Authorize** button (top right in Swagger) → enter `Bearer <token>`
4. All subsequent requests will be authenticated

After every single stage, the developer must be able to hit Swagger and test all
endpoints successfully. If an endpoint returns 500, that is a failure — fix it.

---

## Stage 1: Auth + Upload (already built — verify it works)

### Goal

Confirm the skeleton works end-to-end before adding any AI logic.

### What should already exist

- `POST /api/v1/auth/register` — creates a user in MongoDB
- `POST /api/v1/auth/login` — returns JWT token
- `POST /api/v1/resumes/upload` — saves PDF to disk, creates Resume document in MongoDB with status `"uploaded"`, fires background task (which currently just sets status to `"ready"` immediately as a stub)
- `GET /api/v1/resumes/` — lists user's resumes
- `GET /api/v1/resumes/{id}` — single resume (sections will be null)
- `DELETE /api/v1/resumes/{id}` — deletes from disk + DB
- `POST /api/v1/jobs/` — creates job description
- `GET /api/v1/jobs/` — lists user's jobs
- `GET /api/v1/jobs/{id}` — single job (skills/keywords will be empty)
- `POST /api/v1/analysis/` — creates analysis result with status `"pending"`
- `GET /api/v1/analysis/{id}` — gets analysis (will be empty for now)
- `GET /health` — returns `{"status": "ok"}`

### Verification checklist

- [ ] `uvicorn app.main:app --reload` starts without errors
- [ ] MongoDB connected log line appears
- [ ] Qdrant/Redis show warnings (not errors) if not running — app must not crash
- [ ] All routes appear in Swagger at http://localhost:8000/docs
- [ ] Register → Login → Upload PDF → List resumes all work
- [ ] MongoDB actually has documents (check with `mongosh resume_analyzer`)

If anything in Stage 1 is broken, fix it before moving to Stage 2.

---

## Stage 2: PDF Parsing + NLP Skill Extraction + Embeddings

### Goal

When a resume PDF is uploaded, a background task must:
1. Extract raw text from the PDF
2. Parse it into structured sections (skills, experience, education, projects, summary)
3. Generate a vector embedding of the full text
4. Store the embedding in Qdrant
5. Update the Resume document in MongoDB with parsed data and status `"ready"`

Same pipeline for job descriptions: extract skills and keywords from raw text, generate embedding, store in Qdrant.

### Files to create

#### `app/resumes/parser.py`

```python
# PDF text extraction using pdfplumber
# Must handle:
# - Multi-page PDFs
# - PDFs with no text layer (return empty string, log warning)
# - File not found errors
#
# Returns: (raw_text: str, page_count: int)
#
# Use pdfplumber as primary, fall back to pymupdf (fitz) if pdfplumber fails
```

#### `app/resumes/nlp.py`

```python
# NLP parsing of resume text into structured sections
# Use spaCy (en_core_web_sm model) for:
# - Named entity recognition
# - Section detection by heading keywords
#
# Section detection strategy:
# - Split text into lines
# - Detect section headings by keywords:
#     SKILLS: ["skills", "technical skills", "technologies", "stack", "competencies"]
#     EXPERIENCE: ["experience", "work experience", "employment", "career"]
#     EDUCATION: ["education", "academic", "qualification", "degree"]
#     PROJECTS: ["projects", "personal projects", "side projects", "portfolio"]
#     SUMMARY: ["summary", "objective", "profile", "about"]
# - Extract bullet points / lines under each section
# - For skills section: split by commas, pipes, newlines, bullets → list of strings
# - Clean each skill: strip whitespace, lowercase, remove empty strings
#
# Returns: dict with keys: skills, experience, education, projects, summary
# All values must be JSON-serializable
```

#### `app/embeddings/engine.py`

```python
# Embedding generation using sentence-transformers
# Model: all-MiniLM-L6-v2 (384 dimensions)
# Must be a singleton — load model once at startup, reuse
#
# Functions:
# - embed_text(text: str) -> list[float]  (384 values)
# - embed_batch(texts: list[str]) -> list[list[float]]  (batch for efficiency)
#
# Truncate input text to 512 tokens max (model limit)
# Log a warning if text was truncated
```

#### `app/vectorstore/store.py`

```python
# Qdrant operations
# Uses get_qdrant() from database.py to get the async client
#
# Functions:
# - upsert_vector(point_id: str, vector: list[float], payload: dict) -> None
#     Stores embedding with metadata (type: "resume"|"job", doc_id, user_id)
# - get_vector(point_id: str) -> list[float] | None
#     Retrieves embedding by point ID
# - search_similar(vector: list[float], limit: int = 5) -> list[dict]
#     Finds similar vectors by cosine similarity
# - delete_vector(point_id: str) -> None
#
# Point ID format: use the MongoDB document ID (resume.id or job.id)
# Payload must include: {"type": "resume"|"job", "doc_id": str, "user_id": str}
```

#### Update `app/resumes/service.py`

Replace the stub with real implementation:

```python
# ResumeService.parse_and_embed(resume_id: str) -> None
# Full pipeline:
# 1. Find Resume document in MongoDB
# 2. Set status = "parsing", save
# 3. Extract text using PDFParser
# 4. Parse sections using NLPParser
# 5. Set status = "embedding", save
# 6. Generate embedding using EmbeddingEngine.embed_text(raw_text)
# 7. Store in Qdrant using VectorStore.upsert_vector()
# 8. Update Resume: raw_text, sections, pages, word_count, qdrant_point_id, status = "ready"
# 9. Save
# Handle any exception: set status = "failed", error = str(e), save, re-raise
```

#### Update `app/jobs/service.py`

Replace the stub with real implementation:

```python
# JobService.parse_and_embed(job_id: str) -> None
# Full pipeline:
# 1. Find JobDescription document
# 2. Set status = "processing", save
# 3. Use NLP to extract skills and keywords from raw_text:
#    - required_skills: technical terms, tools, languages detected
#    - preferred_skills: terms near "preferred", "nice to have", "plus"
#    - keywords: important nouns and noun phrases (use spaCy noun chunks)
# 4. Generate embedding of raw_text
# 5. Store in Qdrant
# 6. Update JobDescription: required_skills, preferred_skills, keywords, qdrant_point_id, status = "ready"
# 7. Save
```

### spaCy model download

The `en_core_web_sm` model must be downloaded. Add this to setup instructions or check for it on startup:

```bash
python -m spacy download en_core_web_sm
```

If the model is missing, the app must log a clear error and set status to "failed" — not crash.

### Status lifecycle after Stage 2

Resume: `uploaded` → `parsing` → `embedding` → `ready` (or `failed`)
Job:    `uploaded` → `processing` → `ready` (or `failed`)

### Verification checklist — Stage 2

- [ ] Upload a real PDF resume → after a few seconds, GET /resumes/{id} returns `status: "ready"` and `sections` is populated with actual skills/experience data
- [ ] POST a job description → after a few seconds, GET /jobs/{id} returns `status: "ready"` and `required_skills`, `keywords` are populated
- [ ] Qdrant collection has points (check at http://localhost:6333/dashboard)
- [ ] If you upload a non-PDF or corrupt file, status becomes `"failed"` with an error message
- [ ] All Stage 1 endpoints still work

---

## Stage 3: Matching Engine + ATS Scoring + LLM Suggestions

### Goal

When the user POSTs to `/api/v1/analysis/` with a `resume_id` and `job_id`, a background task runs the full analysis pipeline and stores results in MongoDB. The GET endpoint returns the complete result.

### Files to create

#### `app/llm/client.py`

```python
# Ollama LLM client
# Uses httpx (async) to call Ollama REST API
# Base URL from settings.OLLAMA_BASE_URL
# Model from settings.OLLAMA_MODEL
#
# Function: generate(prompt: str, system: str = "") -> str
#   POST to /api/generate
#   Body: {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": false}
#   Returns: response["response"] string
#   Timeout: 120 seconds (LLM can be slow)
#   On failure: log error, return empty string (do not crash the analysis)
#
# If LLM_PROVIDER == "openai":
#   Use openai library instead (client = openai.AsyncOpenAI(api_key=...))
#   Call client.chat.completions.create(model=settings.OPENAI_MODEL, messages=[...])
```

#### Update `app/matching/service.py`

Replace the stub with the real pipeline:

```python
# MatchingService.run(result_id: str) -> None
#
# STEP 1: Load documents
#   - Find AnalysisResult, Resume, JobDescription from MongoDB
#   - Verify both resume and job have status "ready"
#   - If either is not ready, set analysis status = "failed", error = "Resume/Job not yet processed"
#
# STEP 2: ATS Score (keyword matching)
#   resume_skills = set of lowercased skills from resume.sections["skills"]
#   job_required  = set of lowercased skills from job.required_skills
#   job_preferred = set of lowercased skills from job.preferred_skills
#   job_keywords  = set of lowercased keywords from job.keywords
#
#   all_job_terms = job_required | job_preferred | job_keywords
#
#   matched_skills = list(resume_skills & job_required)   ← exact intersection
#   missing_skills = list(job_required - resume_skills)   ← required but missing
#   extra_skills   = list(resume_skills - all_job_terms)  ← candidate has but JD doesn't mention
#
#   ats_score = (len(matched_skills) / len(job_required)) * 100  if job_required else 50.0
#   ats_score = min(ats_score, 100.0)  ← cap at 100
#
# STEP 3: Semantic Score (embedding cosine similarity)
#   resume_vec = VectorStore.get_vector(resume.qdrant_point_id)
#   job_vec    = VectorStore.get_vector(job.qdrant_point_id)
#   If either vector is None: set semantic_score = 0.0, log warning
#   Otherwise:
#   cosine_sim = dot(resume_vec, job_vec) / (norm(resume_vec) * norm(job_vec))
#   semantic_score = max(0.0, cosine_sim) * 100   ← cosine is -1..1, map to 0..100
#
# STEP 4: Section Scores
#   score each section independently:
#   - skills: len(resume_skills & job_required) / max(len(job_required), 1) * 100
#   - experience: heuristic — count years mentioned in resume experience vs job's experience_years
#     Simple version: if resume has any experience entries, score 70; if years mentioned ≥ required, 90
#   - education: if resume has education entries, score 80; else 40
#
# STEP 5: Overall Score
#   overall_score = (ats_score * 0.4) + (semantic_score * 0.6)
#   (ATS 40%, semantic 60% — semantic is more meaningful)
#
# STEP 6: LLM Suggestions
#   Build a prompt for Ollama:
#
#   system = "You are an expert ATS resume coach. Be specific, actionable, and concise."
#
#   prompt = f"""
#   Analyze this resume against the job description and provide improvement advice.
#
#   RESUME SKILLS: {", ".join(resume.sections.get("skills", []))}
#   RESUME EXPERIENCE SUMMARY: {resume.sections.get("summary", "N/A")}
#
#   JOB REQUIRED SKILLS: {", ".join(job.required_skills)}
#   JOB KEYWORDS: {", ".join(job.keywords)}
#
#   ATS SCORE: {ats_score:.1f}/100
#   SEMANTIC SCORE: {semantic_score:.1f}/100
#   MISSING SKILLS: {", ".join(missing_skills)}
#
#   Provide:
#   1. Three specific suggestions to improve this resume for this job (numbered list)
#   2. Three improvement tips for better ATS performance (numbered list)
#   3. A 2-sentence summary of the candidate's fit
#
#   Format your response as JSON:
#   {{
#     "suggestions": ["...", "...", "..."],
#     "improvement_tips": ["...", "...", "..."],
#     "summary": "..."
#   }}
#   """
#
#   Call LLMClient.generate(prompt, system)
#   Parse the JSON from the response
#   If JSON parsing fails: use empty lists and a generic summary — do not crash
#
# STEP 7: Save results
#   Update AnalysisResult:
#     status = "completed"
#     ats_score, semantic_score, overall_score
#     matched_skills, missing_skills, extra_skills
#     section_scores
#     suggestions, improvement_tips, summary
#     processing_time_ms = elapsed milliseconds
#   Save to MongoDB
#
# Error handling:
#   Wrap entire pipeline in try/except
#   On any exception: set status = "failed", error = str(e), save, log the full traceback
```

### Verification checklist — Stage 3

Test this full flow in Swagger:

1. Register + Login
2. Upload a real PDF resume (use your own or any sample)
3. POST a real job description (paste a real JD from LinkedIn/Naukri)
4. Wait for both to reach `status: "ready"` (poll GET endpoints)
5. POST to `/api/v1/analysis/` with the resume_id and job_id
6. Poll GET `/api/v1/analysis/{id}` every 2 seconds until `status: "completed"`
7. Verify the response contains:
   - [ ] `ats_score` between 0 and 100
   - [ ] `semantic_score` between 0 and 100
   - [ ] `overall_score` between 0 and 100
   - [ ] `matched_skills` is a non-empty list (if resume and JD have overlapping skills)
   - [ ] `missing_skills` is populated
   - [ ] `suggestions` has 3 items from the LLM
   - [ ] `improvement_tips` has 3 items from the LLM
   - [ ] `summary` is a non-empty string
   - [ ] `processing_time_ms` is present

If the LLM is slow, wait longer. If Ollama is not running, suggestions will be empty but scores must still be correct.

---

## Stage 4: Async Workers + Redis Queue

### Goal

Move the heavy processing (PDF parsing, embedding generation, LLM calls) out of FastAPI background tasks and into proper Dramatiq workers backed by Redis. This makes the system production-grade and prevents the API server from being blocked by slow jobs.

### Files to create

#### `app/workers/tasks.py`

```python
# Dramatiq actors (workers)
# Import dramatiq, configure Redis broker
# from dramatiq.brokers.redis import RedisBroker
#
# broker = RedisBroker(url=settings.REDIS_URL)
# dramatiq.set_broker(broker)
#
# @dramatiq.actor(max_retries=3, time_limit=300_000)  ← 5 min time limit
# def process_resume(resume_id: str):
#     import asyncio
#     asyncio.run(ResumeService.parse_and_embed(resume_id))
#
# @dramatiq.actor(max_retries=3, time_limit=120_000)
# def process_job(job_id: str):
#     import asyncio
#     asyncio.run(JobService.parse_and_embed(job_id))
#
# @dramatiq.actor(max_retries=2, time_limit=600_000)  ← 10 min (LLM can be slow)
# def run_analysis(result_id: str):
#     import asyncio
#     asyncio.run(MatchingService.run(result_id))
```

#### Update endpoints to dispatch to Dramatiq instead of BackgroundTasks

In `resumes.py`: replace `background_tasks.add_task(process_resume_task, resume.id)` with `process_resume.send(resume.id)`
In `jobs_analysis.py`: same for jobs and analysis

#### Add worker startup command to README

```bash
# Run workers in a separate terminal:
dramatiq app.workers.tasks --processes 2 --threads 4
```

#### Optional: WebSocket endpoint for live status updates

Add to `jobs_analysis.py`:

```python
# GET /api/v1/analysis/{id}/ws  (WebSocket)
# @router.websocket("/{result_id}/ws")
# async def analysis_ws(websocket: WebSocket, result_id: str):
#   await websocket.accept()
#   while True:
#     result = await AnalysisResult.find_one(AnalysisResult.id == result_id)
#     await websocket.send_json({"status": result.status, "overall_score": result.overall_score})
#     if result.status in ("completed", "failed"):
#       break
#     await asyncio.sleep(1.5)
#   await websocket.close()
```

### Verification checklist — Stage 4

- [ ] Start workers: `dramatiq app.workers.tasks`
- [ ] Upload resume → worker picks up job from Redis queue → resume reaches `"ready"` within 30 seconds
- [ ] Full analysis completes via worker, not blocked API thread
- [ ] API stays responsive while workers process (test by uploading multiple resumes at once)
- [ ] Redis queue is visible in Redis CLI: `redis-cli LRANGE dramatiq:default.msgs 0 -1`
- [ ] All Stage 1–3 endpoints still pass Swagger tests

---

## Rules you must always follow

### Always read before writing

Before editing ANY file, read its current content. Do not overwrite logic that already works.

### Never break what works

After every change, run: `python -c "from app.main import app"` and verify no import errors.
After every stage, manually test all endpoints in Swagger before declaring a stage complete.

### Never leave stubs in production code

The stubs in `resumes/service.py`, `jobs/service.py`, and `matching/service.py` must be replaced
with real logic. Do not ship a stage that returns fake/empty data.

### Handle errors explicitly

Every background task must catch exceptions and update the document's `status` to `"failed"` with
an `error` field. A 500 from Swagger is a failure. The user must always get a meaningful error.

### Status fields are contracts

The `status` field on Resume, JobDescription, and AnalysisResult tells the frontend what happened.
Treat these as strict state machines:

```
Resume:       uploaded → parsing → embedding → ready  (or → failed at any step)
JobDesc:      uploaded → processing → ready            (or → failed)
AnalysisResult: pending → running → completed          (or → failed)
```

Never set `status = "ready"` unless the data is actually ready and complete.

### Log everything meaningful

Use `loguru`. Log at the start and end of every background task, every status transition,
every LLM call (with timing), every Qdrant operation, and every error with full traceback.
Good logs are what let you debug without a debugger.

### Keep Swagger always working

At any point in time, the developer must be able to:
1. Open http://localhost:8000/docs
2. Register a user
3. Log in and authorize
4. Upload a resume
5. Create a job description
6. Run an analysis
7. Get the result

If any of these break, stop everything and fix it.

---

## What to do if something doesn't work

1. Read the full traceback. Don't guess.
2. Check if the service is running (MongoDB, Qdrant, Redis, Ollama).
3. Check the `.env` file values match the running services.
4. Check if the spaCy model is downloaded: `python -m spacy download en_core_web_sm`
5. Check if the Qdrant collection exists and has the right dimension (384).
6. If Ollama returns nothing, run `ollama run llama3.2 "hello"` in the terminal to verify it works.
7. Check logs — every background task logs its steps.

---

## Deliverables summary

After all 4 stages are complete, the following must be true:

| Endpoint | Works | Returns real data |
|----------|-------|-------------------|
| POST /auth/register | ✅ | User object |
| POST /auth/login | ✅ | JWT token |
| POST /resumes/upload | ✅ | Resume object (status: uploaded) |
| GET /resumes/ | ✅ | List of user's resumes |
| GET /resumes/{id} | ✅ | Resume with sections (after processing) |
| DELETE /resumes/{id} | ✅ | Deleted from disk + DB |
| POST /jobs/ | ✅ | Job object (status: uploaded) |
| GET /jobs/ | ✅ | List of user's jobs |
| GET /jobs/{id} | ✅ | Job with skills/keywords (after processing) |
| POST /analysis/ | ✅ | Analysis result (status: pending) |
| GET /analysis/{id} | ✅ | Full result with all scores + LLM output |
| GET /analysis/ | ✅ | List of user's analyses |
| GET /health | ✅ | {"status": "ok"} |

The system is complete when a real resume PDF and a real job description produce a
meaningful analysis with numerical scores, skill gaps, and actionable LLM suggestions —
all visible in Swagger without touching any code.