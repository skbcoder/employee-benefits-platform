from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "ai-platform"
    metrics_enabled: bool = True
    structured_logging: bool = True
    cost_tracking_enabled: bool = True

    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()
