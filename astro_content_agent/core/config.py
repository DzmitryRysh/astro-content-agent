from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment and optional `.env` file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "dev", "staging", "prod"] = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(default="sqlite:///./astro_content_agent.db", alias="DATABASE_URL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="omni-mini", alias="OPENAI_MODEL")

    assets_dir: str = Field(default="./assets", alias="ASSETS_DIR")

    # Asset hosting
    public_base_url: str = Field(default="http://localhost:8000", alias="PUBLIC_BASE_URL")
    storage_mode: str = Field(default="local", alias="STORAGE_MODE")

    # Admin protection
    admin_api_key: str | None = Field(default=None, alias="ADMIN_API_KEY")

    # Instagram publishing — set before running a real publish test
    # Obtain from Meta Developer Console (long-lived token recommended)
    instagram_access_token: str | None = Field(default=None, alias="INSTAGRAM_ACCESS_TOKEN")
    # Numeric Instagram Business/Creator account ID (not the @username)
    instagram_ig_user_id: str | None = Field(default=None, alias="INSTAGRAM_IG_USER_ID")
    # Base host/path for Instagram Graph publish endpoints.
    # Instagram Login token flows should default to graph.instagram.com.
    instagram_graph_base_url: str = Field(default="https://graph.instagram.com", alias="INSTAGRAM_GRAPH_BASE_URL")

    # Scheduler
    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    scheduler_timezone: str = Field(default="UTC", alias="SCHEDULER_TIMEZONE")
    daily_generation_hour: int = Field(default=6, alias="DAILY_GENERATION_HOUR")
    publish_queue_interval_minutes: int = Field(default=5, alias="PUBLISH_QUEUE_INTERVAL_MINUTES")
    analytics_refresh_hour: int = Field(default=8, alias="ANALYTICS_REFRESH_HOUR")


@lru_cache
def get_settings() -> Settings:
    return Settings()

