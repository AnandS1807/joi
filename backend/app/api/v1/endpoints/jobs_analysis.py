from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from loguru import logger

from app.auth.utils import get_current_user
from app.models.documents import User, JobDescription, AnalysisResult
from app.schemas.schemas import JobCreate, JobOut, AnalysisRequest, AnalysisOut, MessageResponse

# ─── Jobs ─────────────────────────────────────────────────────────────────────
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@jobs_router.post("/", response_model=JobOut, status_code=201)
async def create_job(
    data: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    job = JobDescription(
        user_id=current_user.id,
        title=data.title,
        company=data.company,
        raw_text=data.raw_text,
        status="uploaded",
    )
    await job.insert()

    background_tasks.add_task(process_job_task, job.id)
    return JobOut(**job.model_dump())


@jobs_router.get("/", response_model=list[JobOut])
async def list_jobs(current_user: User = Depends(get_current_user)):
    jobs = await JobDescription.find(JobDescription.user_id == current_user.id).to_list()
    return [JobOut(**j.model_dump()) for j in jobs]


@jobs_router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, current_user: User = Depends(get_current_user)):
    job = await JobDescription.find_one(
        JobDescription.id == job_id,
        JobDescription.user_id == current_user.id,
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(**job.model_dump())


async def process_job_task(job_id: str):
    from app.jobs.service import JobService
    try:
        await JobService.parse_and_embed(job_id)
    except Exception as e:
        logger.error(f"Job processing failed: {job_id} — {e}")


# ─── Analysis ─────────────────────────────────────────────────────────────────
analysis_router = APIRouter(prefix="/analysis", tags=["analysis"])


@analysis_router.post("/", response_model=AnalysisOut, status_code=201)
async def run_analysis(
    data: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    result = AnalysisResult(
        user_id=current_user.id,
        resume_id=data.resume_id,
        job_id=data.job_id,
        status="pending",
    )
    await result.insert()

    background_tasks.add_task(run_analysis_task, result.id)
    return _to_out(result)


@analysis_router.get("/{result_id}", response_model=AnalysisOut)
async def get_analysis(result_id: str, current_user: User = Depends(get_current_user)):
    result = await AnalysisResult.find_one(
        AnalysisResult.id == result_id,
        AnalysisResult.user_id == current_user.id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _to_out(result)


@analysis_router.get("/", response_model=list[AnalysisOut])
async def list_analyses(current_user: User = Depends(get_current_user)):
    results = await AnalysisResult.find(AnalysisResult.user_id == current_user.id).to_list()
    return [_to_out(r) for r in results]


def _to_out(r: AnalysisResult) -> AnalysisOut:
    from app.schemas.schemas import ScoreBreakdown
    scores = None
    if r.overall_score is not None:
        scores = ScoreBreakdown(
            ats_score=r.ats_score,
            semantic_score=r.semantic_score,
            overall_score=r.overall_score,
            section_scores=r.section_scores,
        )
    return AnalysisOut(
        id=r.id,
        resume_id=r.resume_id,
        job_id=r.job_id,
        status=r.status,
        scores=scores,
        matched_skills=r.matched_skills,
        missing_skills=r.missing_skills,
        extra_skills=r.extra_skills,
        suggestions=r.suggestions,
        improvement_tips=r.improvement_tips,
        summary=r.summary,
        processing_time_ms=r.processing_time_ms,
        created_at=r.created_at,
    )


async def run_analysis_task(result_id: str):
    from app.matching.service import MatchingService
    try:
        await MatchingService.run(result_id)
    except Exception as e:
        logger.error(f"Analysis failed: {result_id} — {e}")
        result = await AnalysisResult.find_one(AnalysisResult.id == result_id)
        if result:
            result.status = "failed"
            result.error = str(e)
            await result.save()