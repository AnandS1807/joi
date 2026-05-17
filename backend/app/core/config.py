from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Resume Analyzer API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "resume_analyzer"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "resume_embeddings"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()