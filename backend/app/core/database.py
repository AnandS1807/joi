from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
import redis.asyncio as aioredis
from loguru import logger

from app.core.config import settings

# ─── Clients (module-level singletons) ────────────────────────────────────────
mongo_client: AsyncIOMotorClient | None = None
qdrant_client: AsyncQdrantClient | None = None
redis_client: aioredis.Redis | None = None


# ─── MongoDB ──────────────────────────────────────────────────────────────────
async def connect_mongo(document_models: list) -> None:
    global mongo_client
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = mongo_client[settings.MONGODB_DB_NAME]
    await init_beanie(database=db, document_models=document_models)
    logger.info(f"MongoDB connected → {settings.MONGODB_DB_NAME}")


async def close_mongo() -> None:
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")


# ─── Qdrant ───────────────────────────────────────────────────────────────────
async def connect_qdrant() -> None:
    global qdrant_client
    qdrant_client = AsyncQdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )

    try:
        # Create collection if it doesn't exist
        collections = await qdrant_client.get_collections()
        existing = [c.name for c in collections.collections]

        if settings.QDRANT_COLLECTION_NAME not in existing:
            await qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Qdrant collection created → {settings.QDRANT_COLLECTION_NAME}")
        else:
            logger.info(f"Qdrant connected → {settings.QDRANT_COLLECTION_NAME}")
    except Exception as e:
        logger.warning(f"Qdrant not available: {e}")


async def close_qdrant() -> None:
    if qdrant_client:
        await qdrant_client.close()
        logger.info("Qdrant connection closed")


def get_qdrant() -> AsyncQdrantClient:
    if qdrant_client is None:
        raise RuntimeError("Qdrant client not initialized")
    return qdrant_client


# ─── Redis ────────────────────────────────────────────────────────────────────
async def connect_redis() -> None:
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        redis_client = None
        logger.warning(f"Redis not available: {e}")


async def close_redis() -> None:
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis connection closed")


def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client