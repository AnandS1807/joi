from __future__ import annotations

import re
from typing import Any
from loguru import logger


SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "technologies", "stack", "competencies"],
    "experience": ["experience", "work experience", "employment", "career"],
    "education": ["education", "academic", "qualification", "degree"],
    "projects": ["projects", "personal projects", "side projects", "portfolio"],
    "summary": ["summary", "objective", "profile", "about"],
}


def _match_section(line: str) -> str | None:
    l = line.lower().strip(":- ")
    for section, keys in SECTION_HEADERS.items():
        if any(l == k or l.startswith(k) for k in keys):
            return section
    return None


def _split_skills(lines: list[str]) -> list[str]:
    skills: list[str] = []
    for line in lines:
        parts = re.split(r"[\|,;/]", line)
        for p in parts:
            s = p.strip().lower()
            if s:
                skills.append(s)
    # de-dup
    return sorted(list(set(skills)))


def parse_resume(text: str) -> dict[str, Any]:
    """Parse resume into sections using simple heading detection.

    Returns: dict with keys skills, experience, education, projects, summary
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sections: dict[str, list[str]] = {k: [] for k in SECTION_HEADERS.keys()}
    current: str | None = None

    for line in lines:
        sec = _match_section(line)
        if sec:
            current = sec
            continue

        if current:
            sections[current].append(line)

    # Build structured output
    output: dict[str, Any] = {}
    output["skills"] = _split_skills(sections.get("skills", []))
    output["experience"] = [{"text": l} for l in sections.get("experience", [])]
    output["education"] = [{"text": l} for l in sections.get("education", [])]
    output["projects"] = [{"text": l} for l in sections.get("projects", [])]
    summary_lines = sections.get("summary", [])
    output["summary"] = " ".join(summary_lines) if summary_lines else None

    return output


def load_spacy_model():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception as e:
        logger.error("spaCy model not available. Run: python -m spacy download en_core_web_sm")
        raise e
