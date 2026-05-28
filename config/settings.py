from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB Config
    MONGO_URI: str
    DB_NAME: str
    CHUNKS_COLLECTION: str
    HISTORY_COLLECTION: str
    USERS_COLLECTION: str

    # Groq Config
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-8b-8192"

    # JWT Config
    JWT_SECRET_KEY: str = "your-fallback-secret-key-please-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # App Config
    APP_NAME: str = "doc_qa_system"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Document Processing Config
    MAX_FILE_SIZE_MB: int = 10
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Search & Reranking Config
    SIMILARITY_THRESHOLD: float = 0.01
    TOP_K_RESULTS: int = 20
    RERANK_TOP_K: int = 5

    # Rate Limiting Config
    RATE_LIMIT_REQUESTS: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
