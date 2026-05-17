from datetime import datetime
from loguru import logger
from app.models.documents import JobDescription


class JobService:
    @staticmethod
    async def parse_and_embed(job_id: str) -> None:
        job = await JobDescription.find_one(JobDescription.id == job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        logger.info(f"[JobService] Processing {job_id}")

        # Phase 2: NLP skill extraction, keyword extraction, embeddings
        # from app.jobs.parser import JobParser
        # skills, keywords = await JobParser.extract(job.raw_text)
        # embedding = await EmbeddingEngine.embed(job.raw_text)

        job.status = "ready"
        job.updated_at = datetime.utcnow()
        await job.save()
        logger.info(f"[JobService] Done: {job_id}")