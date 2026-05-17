import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from loguru import logger

from app.auth.utils import get_current_user
from app.models.documents import User, Resume
from app.schemas.schemas import ResumeOut, ResumeListOut, MessageResponse
from app.core.config import settings

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeOut, status_code=201)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    # Validate
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, current_user.id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    # Create DB record
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        status="uploaded",
    )
    await resume.insert()
    logger.info(f"Resume uploaded: {resume.id} by user {current_user.id}")

    # Kick off background parsing
    background_tasks.add_task(process_resume_task, resume.id)

    return ResumeOut(**resume.model_dump())


@router.get("/", response_model=ResumeListOut)
async def list_resumes(current_user: User = Depends(get_current_user)):
    resumes = await Resume.find(Resume.user_id == current_user.id).to_list()
    return ResumeListOut(
        resumes=[ResumeOut(**r.model_dump()) for r in resumes],
        total=len(resumes),
    )


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: str, current_user: User = Depends(get_current_user)):
    resume = await Resume.get(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeOut(**resume.model_dump())


@router.delete("/{resume_id}", response_model=MessageResponse)
async def delete_resume(resume_id: str, current_user: User = Depends(get_current_user)):
    resume = await Resume.get(resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Remove file from disk
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)

    await resume.delete()
    return MessageResponse(message="Resume deleted successfully")


# ─── Background task (stub — real logic in workers/) ──────────────────────────
async def process_resume_task(resume_id: str):
    """
    Stub for background processing.
    In Phase 2, this dispatches to a Dramatiq worker.
    """
    from app.resumes.service import ResumeService
    try:
        await ResumeService.parse_and_embed(resume_id)
    except Exception as e:
        logger.error(f"Resume processing failed: {resume_id} — {e}")
        resume = await Resume.get(resume_id)
        if resume:
            resume.status = "failed"
            resume.error = str(e)
            await resume.save()