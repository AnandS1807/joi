from __future__ import annotations

import re
from typing import Any
from loguru import logger


REQUIRED_HEADERS = ["required", "requirements", "must have", "qualifications"]
PREFERRED_HEADERS = ["preferred", "nice to have", "plus", "bonus"]


def _is_header(line: str, keywords: list[str]) -> bool:
    l = line.lower().strip(":- ")
    return any(l.startswith(k) for k in keywords)


def _clean_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip().lower())


def extract_job_fields(text: str) -> dict[str, Any]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    required: list[str] = []
    preferred: list[str] = []
    current = None

    for line in lines:
        if _is_header(line, REQUIRED_HEADERS):
            current = "required"
            continue
        if _is_header(line, PREFERRED_HEADERS):
            current = "preferred"
            continue

        bullet = re.match(r"^[\*\-\u2022]\s*(.+)", line)
        if bullet:
            val = _clean_skill(bullet.group(1))
            if current == "required":
                required.append(val)
            elif current == "preferred":
                preferred.append(val)

    # fallback: noun chunks as keywords
    keywords: list[str] = []
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        for chunk in doc.noun_chunks:
            kw = _clean_skill(chunk.text)
            if kw and len(kw) > 2:
                keywords.append(kw)
    except Exception:
        logger.warning("spaCy model not available for keyword extraction")

    # De-dup
    required = sorted(list(set(required)))
    preferred = sorted(list(set(preferred)))
    keywords = sorted(list(set(keywords)))

    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "keywords": keywords,
    }
