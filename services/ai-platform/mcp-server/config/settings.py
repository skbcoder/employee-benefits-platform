from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MCP Server configuration."""

    enrollment_service_url: str = "http://localhost:8080"
    processing_service_url: str = "http://localhost:8081"
    mcp_server_port: int = 8100
    mcp_server_host: str = "0.0.0.0"

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
