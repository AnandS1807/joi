"""
MongoDB document models using Beanie ODM.
These define the schema for all collections.
"""

from datetime import datetime
from typing import Optional, Any
from beanie import Document, Indexed
from pydantic import Field, EmailStr
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


# ─── User ─────────────────────────────────────────────────────────────────────
class User(Document):
    id: str = Field(default_factory=new_id)
    email: Indexed(EmailStr, unique=True)  # type: ignore
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"


# ─── Resume ───────────────────────────────────────────────────────────────────
class ResumeSection(Document):
    skills: list[str] = []
    experience: list[dict[str, Any]] = []
    education: list[dict[str, Any]] = []
    projects: list[dict[str, Any]] = []
    certifications: list[str] = []
    summary: Optional[str] = None


class Resume(Document):
    id: str = Field(default_factory=new_id)
    user_id: str
    filename: str
    file_path: str

    # Raw + parsed
    raw_text: Optional[str] = None
    sections: Optional[dict[str, Any]] = None  # flexible parsed output

    # Processing status
    status: str = "uploaded"  # uploaded | parsing | parsed | embedding | ready | failed
    error: Optional[str] = None

    # Embedding reference
    qdrant_point_id: Optional[str] = None

    # Metadata
    pages: Optional[int] = None
    word_count: Optional[int] = None
    parser_version: str = "v1"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "resumes"


# ─── Job Description ──────────────────────────────────────────────────────────
class JobDescription(Document):
    id: str = Field(default_factory=new_id)
    user_id: str
    title: Optional[str] = None
    company: Optional[str] = None

    raw_text: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    experience_years: Optional[int] = None
    responsibilities: list[str] = []
    keywords: list[str] = []

    status: str = "uploaded"  # uploaded | processing | ready | failed
    qdrant_point_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "job_descriptions"


# ─── Analysis Result ──────────────────────────────────────────────────────────
class AnalysisResult(Document):
    id: str = Field(default_factory=new_id)
    user_id: str
    resume_id: str
    job_id: str

    # Scores
    ats_score: Optional[float] = None          # keyword-based 0–100
    semantic_score: Optional[float] = None     # embedding cosine 0–100
    overall_score: Optional[float] = None      # weighted composite

    # Gaps & matches
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    extra_skills: list[str] = []               # candidate has but JD doesn't mention

    # Section scores
    section_scores: dict[str, float] = {}      # e.g. {"skills": 80, "experience": 65}

    # Highlighted spans from resume for UI rendering
    # Each item: {"type": "matched"|"irrelevant", "text": str, "start": int, "end": int, "score": float}
    highlights: list[dict] = []

    # LLM output
    suggestions: list[str] = []
    improvement_tips: list[str] = []
    summary: Optional[str] = None

    # Processing
    status: str = "pending"  # pending | running | completed | failed
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "analysis_results"


# ─── All models list (for Beanie init) ────────────────────────────────────────
ALL_MODELS = [User, Resume, JobDescription, AnalysisResult]