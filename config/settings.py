from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-3.5-flash-lite")
    gemini_embedding_model: str = Field(default="gemini-embedding-001")
    gemini_temperature: float = Field(default=0.0)
    gemini_max_output_tokens: int = Field(default=350)

    qdrant_path: str = Field(default="./data/qdrant")
    qdrant_collection_name: str = Field(default="academy_knowledge")

    top_k: int = Field(default=5)
    rag_score_threshold: float = Field(default=0.20)

    cache_enabled: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=3600)

    max_history_messages: int = Field(default=4)

    database_path: str = Field(default="./data/academy.db")


settings = Settings()
