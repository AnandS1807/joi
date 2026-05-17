r"""Run the job parsing, resume parsing, and matching pipeline for fixed IDs.

Usage:
    .\.venv\Scripts\python.exe scripts\test_pipeline.py
    .\.venv\Scripts\python.exe scripts\test_pipeline.py --job-id <JOB_ID> --resume-id <RESUME_ID> --analysis-id <ANALYSIS_ID>

The default IDs match the records currently discussed in the workspace.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from app.core.database import connect_mongo, close_mongo
from app.models.documents import ALL_MODELS
from app.jobs.service import JobService
from app.matching.service import MatchingService
from app.models.documents import AnalysisResult, JobDescription, Resume
from app.resumes.service import ResumeService

DEFAULT_JOB_ID = "db353adc-c682-4517-93db-780ec60ecbc8"
DEFAULT_RESUME_ID = "e5b2ef19-ddb7-4276-8dbc-2e763305a1a5"
DEFAULT_ANALYSIS_ID = "c72f77a3-6cbd-4039-b8be-c5ee12504d0f"


async def _fetch_document(model: Any, document_id: str) -> dict[str, Any] | None:
    doc = await model.find_one({"id": document_id})
    if not doc:
        return None
    return doc.model_dump()


async def run_pipeline(job_id: str, resume_id: str, analysis_id: str) -> None:
    print(f"[1/5] Parsing job: {job_id}")
    await JobService.parse_and_embed(job_id)

    print(f"[2/5] Parsing resume: {resume_id}")
    await ResumeService.parse_and_embed(resume_id)

    print(f"[3/5] Running analysis: {analysis_id}")
    await MatchingService.run(analysis_id)

    print("[4/5] Fetching updated job/resume/analysis documents")
    job = await _fetch_document(JobDescription, job_id)
    resume = await _fetch_document(Resume, resume_id)
    analysis = await _fetch_document(AnalysisResult, analysis_id)

    print("\n=== Job ===")
    print(json.dumps(job, indent=2, default=str))

    print("\n=== Resume ===")
    print(json.dumps(resume, indent=2, default=str))

    print("\n=== Analysis ===")
    print(json.dumps(analysis, indent=2, default=str))

    print("\n[5/5] Done")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test the resume analysis pipeline end-to-end.")
    parser.add_argument("--job-id", default=DEFAULT_JOB_ID, help="JobDescription ID to process")
    parser.add_argument("--resume-id", default=DEFAULT_RESUME_ID, help="Resume ID to process")
    parser.add_argument("--analysis-id", default=DEFAULT_ANALYSIS_ID, help="AnalysisResult ID to process")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    async def runner():
        # ⭐ Initialize DB (same as FastAPI startup)
        await connect_mongo(ALL_MODELS)

        try:
            await run_pipeline(args.job_id, args.resume_id, args.analysis_id)
        finally:
            # ⭐ Clean shutdown
            await close_mongo()

    asyncio.run(runner())


if __name__ == "__main__":
    main()
