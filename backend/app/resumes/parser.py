import pdfplumber
import re
from typing import Tuple
from loguru import logger

try:
    import fitz  # pymupdf
except Exception:
    fitz = None


def split_sentences(text: str) -> list[str]:
    # naive sentence splitter
    parts = re.split(r"(?<=[\.\?\!])\s+|\n\n", text)
    out = [p.strip() for p in parts if p and len(p.strip()) > 5]
    return out


def extract(file_path: str) -> Tuple[str, dict]:
    """Extract full text and basic sections from a PDF file."""
    text_parts: list[str] = []
    pages = 0

    try:
        with pdfplumber.open(file_path) as pdf:
            pages = len(pdf.pages)
            for p in pdf.pages:
                txt = p.extract_text() or ""
                text_parts.append(txt)
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        if fitz is None:
            raise
        # fallback to PyMuPDF
        doc = fitz.open(file_path)
        pages = doc.page_count
        for i in range(pages):
            page = doc.load_page(i)
            text_parts.append(page.get_text("text") or "")
        doc.close()

    full = "\n\n".join(text_parts).strip()
    sentences = split_sentences(full)
    word_count = len([w for w in full.split() if w.strip()])

    sections = {
        "sentences": sentences,
        "pages": pages,
        "word_count": word_count,
    }
    return full, sections
