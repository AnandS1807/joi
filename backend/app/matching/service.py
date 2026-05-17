from datetime import datetime
from loguru import logger
from app.models.documents import AnalysisResult
from app.core.config import settings
from app.embeddings.engine import embed_text, embed_sentences
from app.vectorstore import get_vector
from app.llm.client import generate, parse_llm_json
import asyncio
import numpy as np


class MatchingService:
    @staticmethod
    async def run(result_id: str) -> None:
        result = await AnalysisResult.get(result_id)
        if not result:
            raise ValueError(f"AnalysisResult {result_id} not found")

        start_time = datetime.utcnow()
        result.status = "running"
        await result.save()

        logger.info(f"[MatchingService] Running analysis {result_id}")

        # Phase 3: basic pipeline implementation
        # - Use sentence-transformers to compute embeddings for resume/job text
        # - Compute cosine similarity -> semantic_score (0-100)
        # - Compute simple keyword overlap -> ats_score (0-100)
        # - Fill matched/missing/extra skills and section scores
        # Note: This is a synchronous embedder wrapped with asyncio.to_thread

        try:
            # Load resume and job documents
            from app.models.documents import Resume, JobDescription

            resume = await Resume.get(result.resume_id)
            job = await JobDescription.get(result.job_id)

            if not resume or not job:
                result.status = "failed"
                result.error = "Resume or Job not found"
                await result.save()
                return

            # Require raw_text to be present (Phase 2 will populate these)
            if not resume.raw_text or not job.raw_text:
                result.status = "failed"
                result.error = "Missing parsed text for resume or job. Run parsers first."
                await result.save()
                return

            # semantic score via Qdrant vectors (fallback to local embedding)
            resume_vec = None
            job_vec = None
            if resume.qdrant_point_id:
                resume_vec = await get_vector(resume.qdrant_point_id)
            if job.qdrant_point_id:
                job_vec = await get_vector(job.qdrant_point_id)

            if resume_vec is None:
                resume_vec = (await asyncio.to_thread(lambda: embed_text(resume.raw_text))).tolist()
            if job_vec is None:
                job_vec = (await asyncio.to_thread(lambda: embed_text(job.raw_text))).tolist()

            resume_emb = np.array(resume_vec)
            job_emb = np.array(job_vec)

            # cosine similarity in [ -1, 1 ] -> convert to 0-100 scale
            cosine = float(np.dot(resume_emb, job_emb))
            semantic_score = max(0.0, min(100.0, (cosine + 1.0) / 2.0 * 100.0))

            # ATS keyword overlap: use extracted skills/keywords where possible
            job_required = set([k.lower() for k in (job.required_skills or []) if k.strip()])
            job_preferred = set([k.lower() for k in (job.preferred_skills or []) if k.strip()])
            job_keywords = set([k.lower() for k in (job.keywords or []) if k.strip()])
            all_job_terms = job_required | job_preferred | job_keywords

            resume_skills = set()
            if resume.sections and isinstance(resume.sections, dict):
                resume_skills = set([s.lower() for s in resume.sections.get("skills", []) if isinstance(s, str)])

            if not resume_skills:
                resume_skills = set([w.lower().strip(".,()[]") for w in (resume.raw_text or "").split() if len(w) > 2])

            matched = list(sorted(resume_skills & job_required))
            missing = list(sorted(job_required - resume_skills))
            extra = list(sorted(resume_skills - all_job_terms))[:50]

            ats_score = 0.0
            if job_required:
                ats_score = round(len(matched) / max(1, len(job_required)) * 100, 2)
            else:
                ats_score = 50.0

            # section_scores: basic skills/experience/education heuristics
            section_scores = {
                "skills": ats_score,
                "semantic": round(semantic_score, 2),
            }
            if resume.sections and isinstance(resume.sections, dict):
                section_scores["education"] = 80.0 if resume.sections.get("education") else 40.0
                section_scores["experience"] = 70.0 if resume.sections.get("experience") else 40.0

            # overall: weighted (semantic 60%, ats 40%)
            overall = round((semantic_score * 0.6) + (ats_score * 0.4), 2)

            # Build sentence-level highlights from resume sentences (if available)
            highlights: list[dict] = []
            try:
                sentences = []
                if resume.sections and isinstance(resume.sections, dict):
                    sentences = resume.sections.get("sentences", [])
                else:
                    # fallback split
                    import re
                    sentences = [s.strip() for s in re.split(r"(?<=[\.\?\!])\s+|\n\n", resume.raw_text) if s and len(s.strip())>5]

                if sentences:
                    sent_embs = await asyncio.to_thread(lambda: embed_sentences(sentences))
                    # compute cosine similarities
                    # job_emb is 1d, sent_embs is NxD
                    sims = np.dot(sent_embs, job_emb)
                    # map sims to score 0-100
                    for i, sim in enumerate(sims.tolist()):
                        score = float(sim)
                        if score >= 0.65:
                            # matched
                            text = sentences[i]
                            # find span offset (first occurrence after cursor)
                            start = resume.raw_text.find(text)
                            end = start + len(text) if start >= 0 else -1
                            highlights.append({"type": "matched", "text": text, "start": start, "end": end, "score": round((score+1)/2*100,2)})
                        elif score <= 0.35:
                            text = sentences[i]
                            start = resume.raw_text.find(text)
                            end = start + len(text) if start >= 0 else -1
                            highlights.append({"type": "irrelevant", "text": text, "start": start, "end": end, "score": round((score+1)/2*100,2)})
            except Exception:
                highlights = []

            # LLM suggestions
            suggestions: list[str] = []
            improvement_tips: list[str] = []
            summary: str | None = None
            try:
                system = "You are an expert ATS resume coach. Be specific, actionable, and concise."
                prompt = f"""
Analyze this resume against the job description and provide improvement advice.

RESUME SKILLS: {", ".join(list(resume_skills))}
RESUME SUMMARY: {resume.sections.get("summary") if resume.sections else "N/A"}

JOB REQUIRED SKILLS: {", ".join(list(job_required))}
JOB KEYWORDS: {", ".join(list(job_keywords))}

ATS SCORE: {ats_score:.1f}/100
SEMANTIC SCORE: {semantic_score:.1f}/100
MISSING SKILLS: {", ".join(missing)}

Provide:
1. Three specific suggestions to improve this resume for this job (numbered list)
2. Three improvement tips for better ATS performance (numbered list)
3. A 2-sentence summary of the candidate's fit

Format your response as JSON:
{{
    "suggestions": ["...", "...", "..."],
    "improvement_tips": ["...", "...", "..."],
    "summary": "..."
}}
"""
                raw = await generate(prompt, system=system)
                data = parse_llm_json(raw)
                suggestions = data.get("suggestions", []) if isinstance(data, dict) else []
                improvement_tips = data.get("improvement_tips", []) if isinstance(data, dict) else []
                summary = data.get("summary") if isinstance(data, dict) else None
            except Exception as e:
                logger.warning(f"LLM suggestions failed: {e}")

            # Save into result
            result.ats_score = ats_score
            result.semantic_score = round(semantic_score, 2)
            result.overall_score = overall
            result.matched_skills = matched
            result.missing_skills = missing
            result.extra_skills = extra
            result.section_scores = section_scores
            result.highlights = highlights
            result.suggestions = suggestions
            result.improvement_tips = improvement_tips
            result.summary = summary
            result.status = "completed"
            result.updated_at = datetime.utcnow()
            result.processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await result.save()
            logger.info(f"[MatchingService] Completed: {result_id} (semantic={result.semantic_score} ats={result.ats_score})")

        except Exception as e:
            logger.exception(f"[MatchingService] Analysis failed: {e}")
            result.status = "failed"
            result.error = str(e)
            result.updated_at = datetime.utcnow()
            await result.save()