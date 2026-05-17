"""
Resume service — PDF parsing + embedding dispatch.
Phase 2 will fill in the real logic.
"""
from datetime import datetime
from loguru import logger
from app.models.documents import Resume
from app.embeddings.engine import embed_text
from app.resumes.parser import extract as extract_pdf
from app.resumes.nlp import parse_resume
from app.vectorstore import upsert_vector
import asyncio


class ResumeService:
    @staticmethod
    async def parse_and_embed(resume_id: str) -> None:
        resume = await Resume.get(resume_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")

        logger.info(f"[ResumeService] Processing {resume_id}")

        # Parse PDF (run in thread to avoid blocking)
        try:
            resume.status = "parsing"
            resume.updated_at = datetime.utcnow()
            await resume.save()

            text, sections = await asyncio.to_thread(lambda: extract_pdf(resume.file_path))
            parsed = parse_resume(text)
            resume.raw_text = text
            resume.sections = {**sections, **parsed}
            resume.pages = sections.get("pages")
            resume.word_count = sections.get("word_count")
            resume.status = "embedding"
            resume.updated_at = datetime.utcnow()
            await resume.save()

            # compute full-text embedding and upsert to Qdrant
            embedding = await asyncio.to_thread(lambda: embed_text(resume.raw_text or ""))
            await upsert_vector(
                point_id=resume.id,
                vector=embedding.tolist(),
                payload={"type": "resume", "doc_id": resume.id, "user_id": resume.user_id},
            )
            resume.qdrant_point_id = resume.id

            resume.status = "ready"
            resume.updated_at = datetime.utcnow()
            await resume.save()
            logger.info(f"[ResumeService] Done: {resume_id}")
        except Exception as e:
            logger.exception(f"[ResumeService] Failed: {e}")
            resume.status = "failed"
            resume.error = str(e)
            resume.updated_at = datetime.utcnow()
            await resume.save()