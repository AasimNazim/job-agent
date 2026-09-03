from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        "sqlite:///job_agent.db",
        validation_alias=AliasChoices("DATABASE_URL", "DASHBOARD_DATABASE_URL", "database_url")
    )

    # Agent settings
    dry_run: bool = True
    match_threshold: int = 75
    max_daily_drafts: int = 5
    max_concurrent_companies: int = 5
    job_max_age_days: int = 14
    
    # Secrets (Optional in Phase 1)
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    llm_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Global settings instance
settings = Settings()
