from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Orchestrator configuration."""

    # LLM provider: "ollama" or "bedrock"
    llm_provider: str = "ollama"

    # Ollama (local development)
    ollama_base_url: str = "http://localhost:11434"
    ollama_router_model: str = "llama3.1:8b"
    ollama_agent_model: str = "llama3.1:8b"

    # AWS Bedrock (production)
    bedrock_region: str = "us-east-1"
    bedrock_router_model_id: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    bedrock_agent_model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    # Service URLs
    enrollment_service_url: str = "http://localhost:8080"
    processing_service_url: str = "http://localhost:8081"
    knowledge_service_url: str = "http://localhost:8300"
    governance_service_url: str = "http://localhost:8500"

    # Orchestrator
    orchestrator_port: int = 8400
    orchestrator_host: str = "0.0.0.0"
    max_agent_iterations: int = 10

    # Token budget per request
    token_budget_max: int = 8192
    token_budget_warn_pct: float = 0.8

    # Routing confidence threshold — below this, escalate
    routing_confidence_threshold: float = 0.3

    # Compliance auto-check threshold — actions above this risk score require approval
    compliance_risk_threshold: float = 0.7

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
