from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from loguru import logger


_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def _truncate_text(text: str, max_tokens: int) -> str:
    model = get_model()
    tokenizer = getattr(model, "tokenizer", None)
    if not tokenizer:
        return text

    tokens = tokenizer(text, truncation=False, return_tensors=None)
    input_ids = tokens.get("input_ids", [])
    if len(input_ids) <= max_tokens:
        return text

    truncated = tokenizer.decode(input_ids[:max_tokens], skip_special_tokens=True)
    logger.warning(f"Embedding text truncated to {max_tokens} tokens")
    return truncated


def embed_text(text: str) -> np.ndarray:
    model = get_model()
    max_tokens = getattr(model, "max_seq_length", 512)
    text = _truncate_text(text, max_tokens)
    emb = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return emb


def embed_sentences(sentences: List[str]) -> np.ndarray:
    model = get_model()
    embs = model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
    return embs


def embed_batch(texts: List[str]) -> np.ndarray:
    model = get_model()
    max_tokens = getattr(model, "max_seq_length", 512)
    texts = [_truncate_text(t, max_tokens) for t in texts]
    embs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embs
