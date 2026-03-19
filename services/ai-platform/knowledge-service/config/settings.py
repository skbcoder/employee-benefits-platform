from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Knowledge Service configuration."""

    # Database
    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "employee_benefits_platform"
    db_username: str = "benefits_app"
    db_password: str = "benefits_app"

    # Ollama (embeddings)
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"

    # Chunking
    chunk_size: int = 512       # max tokens per chunk
    chunk_overlap: int = 50     # token overlap when splitting oversized sections
    min_chunk_size: int = 50    # sections smaller than this (tokens) get merged with neighbors

    # Service
    knowledge_service_port: int = 8300
    knowledge_service_host: str = "0.0.0.0"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
