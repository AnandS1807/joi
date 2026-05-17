from __future__ import annotations

from typing import Any
from loguru import logger
from app.core.database import get_qdrant
from app.core.config import settings


async def upsert_vector(point_id: str, vector: list[float], payload: dict[str, Any]) -> None:
    client = get_qdrant()
    logger.info(f"Qdrant upsert: {point_id}")
    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=[{"id": point_id, "vector": vector, "payload": payload}],
    )


async def get_vector(point_id: str) -> list[float] | None:
    client = get_qdrant()
    res = await client.retrieve(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        ids=[point_id],
        with_vectors=True,
    )
    if not res:
        return None
    return res[0].vector


async def search_similar(vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
    client = get_qdrant()
    res = await client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=vector,
        limit=limit,
    )
    return [r.payload for r in res]


async def delete_vector(point_id: str) -> None:
    client = get_qdrant()
    await client.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points_selector=[point_id],
    )
