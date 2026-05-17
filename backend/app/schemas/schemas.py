"""
Pydantic v2 schemas for API request/response validation.
Keep these separate from DB models.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field


# ─── Auth ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime


# ─── Resume ───────────────────────────────────────────────────────────────────
class ResumeOut(BaseModel):
    id: str
    filename: str
    status: str
    raw_text: Optional[str] = None
    sections: Optional[dict[str, Any]] = None
    pages: Optional[int] = None
    word_count: Optional[int] = None
    created_at: datetime


class ResumeListOut(BaseModel):
    resumes: list[ResumeOut]
    total: int


# ─── Job Description ──────────────────────────────────────────────────────────
class JobCreate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    raw_text: str = Field(min_length=50)


class JobOut(BaseModel):
    id: str
    title: Optional[str]
    company: Optional[str]
    status: str
    required_skills: list[str]
    preferred_skills: list[str]
    keywords: list[str]
    created_at: datetime


# ─── Analysis ─────────────────────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    resume_id: str
    job_id: str


class ScoreBreakdown(BaseModel):
    ats_score: Optional[float]
    semantic_score: Optional[float]
    overall_score: Optional[float]
    section_scores: dict[str, float] = {}


class AnalysisOut(BaseModel):
    id: str
    resume_id: str
    job_id: str
    status: str

    scores: Optional[ScoreBreakdown] = None
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    extra_skills: list[str] = []

    suggestions: list[str] = []
    improvement_tips: list[str] = []
    summary: Optional[str] = None

    processing_time_ms: Optional[int] = None
    created_at: datetime


# ─── Generic ──────────────────────────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str