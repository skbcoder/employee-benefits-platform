from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI Gateway configuration."""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"

    # Benefits APIs
    enrollment_service_url: str = "http://localhost:8080"
    processing_service_url: str = "http://localhost:8081"

    # MCP Server
    mcp_server_url: str = "http://localhost:8100"

    # Knowledge Service
    knowledge_service_url: str = "http://localhost:8300"

    # Orchestrator (Phase 2 — multi-agent LangGraph)
    orchestrator_url: str = "http://localhost:8400"
    use_orchestrator: bool = True  # delegate to orchestrator when available

    # Gateway
    ai_gateway_port: int = 8200
    ai_gateway_host: str = "0.0.0.0"

    # Agent
    max_agent_iterations: int = 10

    # Rate limiting
    rate_limit_rpm: int = 20
    rate_limit_window_seconds: int = 60

    # Audit
    audit_log_file: str = "audit.log"

    # Response refinement (loopback)
    enable_refinement: bool = True
    refinement_min_length: int = 50  # responses shorter than this trigger refinement
    refinement_max_passes: int = 1  # max refinement attempts (keep low for latency)

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
