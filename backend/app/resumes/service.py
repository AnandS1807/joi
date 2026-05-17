"""
Resume service — PDF parsing + embedding dispatch.
Phase 2 will fill in the real logic.
"""
from datetime import datetime
from loguru import logger
from app.models.documents import Resume


class ResumeService:
    @staticmethod
    async def parse_and_embed(resume_id: str) -> None:
        resume = await Resume.find_one(Resume.id == resume_id)
        if not resume:
            raise ValueError(f"Resume {resume_id} not found")

        logger.info(f"[ResumeService] Processing {resume_id}")

        # Phase 2: import and call PDFParser, EmbeddingEngine
        # from app.resumes.parser import PDFParser
        # from app.embeddings.engine import EmbeddingEngine
        # text, sections = await PDFParser.extract(resume.file_path)
        # embedding = await EmbeddingEngine.embed(text)
        # point_id = await VectorStore.upsert(resume_id, embedding, metadata)

        resume.status = "ready"  # placeholder until Phase 2
        resume.updated_at = datetime.utcnow()
        await resume.save()
        logger.info(f"[ResumeService] Done: {resume_id}")