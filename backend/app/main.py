from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import (
    connect_mongo, close_mongo,
    connect_qdrant, close_qdrant,
    connect_redis, close_redis,
)
from app.models.documents import ALL_MODELS
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.resumes import router as resumes_router
from app.api.v1.endpoints.jobs_analysis import jobs_router, analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("🚀 Starting Resume Analyzer API...")
    await connect_mongo(ALL_MODELS)
    await connect_qdrant()
    await connect_redis()
    logger.info("✅ All connections established")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    logger.info("🛑 Shutting down...")
    await close_mongo()
    await close_qdrant()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth_router, prefix=PREFIX)
app.include_router(resumes_router, prefix=PREFIX)
app.include_router(jobs_router, prefix=PREFIX)
app.include_router(analysis_router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}