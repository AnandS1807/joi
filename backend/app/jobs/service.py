from datetime import datetime
from loguru import logger
from app.models.documents import JobDescription
import asyncio
from app.embeddings.engine import embed_text
from app.jobs.nlp import extract_job_fields
from app.vectorstore import upsert_vector


class JobService:
    @staticmethod
    async def parse_and_embed(job_id: str) -> None:
        job = await JobDescription.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        logger.info(f"[JobService] Processing {job_id}")

        try:
            job.status = "processing"
            job.updated_at = datetime.utcnow()
            await job.save()

            text = job.raw_text or ""
            fields = extract_job_fields(text)
            job.required_skills = fields.get("required_skills", [])
            job.preferred_skills = fields.get("preferred_skills", [])
            job.keywords = fields.get("keywords", [])

            # compute job embedding and upsert to Qdrant
            embedding = await asyncio.to_thread(lambda: embed_text(text))
            await upsert_vector(
                point_id=job.id,
                vector=embedding.tolist(),
                payload={"type": "job", "doc_id": job.id, "user_id": job.user_id},
            )
            job.qdrant_point_id = job.id

            job.status = "ready"
            job.updated_at = datetime.utcnow()
            await job.save()
            logger.info(f"[JobService] Done: {job_id}")
        except Exception as e:
            logger.exception(f"[JobService] Failed: {e}")
            job.status = "failed"
            job.error = str(e)
            job.updated_at = datetime.utcnow()
            await job.save()