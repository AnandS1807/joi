from datetime import datetime
from loguru import logger
from app.models.documents import AnalysisResult


class MatchingService:
    @staticmethod
    async def run(result_id: str) -> None:
        result = await AnalysisResult.find_one(AnalysisResult.id == result_id)
        if not result:
            raise ValueError(f"AnalysisResult {result_id} not found")

        result.status = "running"
        await result.save()

        logger.info(f"[MatchingService] Running analysis {result_id}")

        # Phase 3: real pipeline
        # 1. Load resume embedding from Qdrant
        # 2. Load job embedding from Qdrant
        # 3. Cosine similarity → semantic_score
        # 4. Keyword overlap → ats_score
        # 5. Compute missing/matched/extra skills
        # 6. Call LLM for suggestions
        # 7. Compute overall_score

        result.status = "completed"
        result.updated_at = datetime.utcnow()
        await result.save()
        logger.info(f"[MatchingService] Completed: {result_id}")