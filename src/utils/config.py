import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    """Application settings from environment variables."""
    openrouter_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""  # Can be comma-separated for multiple users
    newsapi_key: str = ""
    user_timezone: str = "Europe/Moscow"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_chat_ids(self) -> list[str]:
        """Get list of chat IDs (supports comma-separated values)."""
        if not self.telegram_chat_id:
            return []
        return [cid.strip() for cid in self.telegram_chat_id.split(",") if cid.strip()]


def load_yaml_config(config_path: str = "config/config.yaml") -> dict:
    """Load YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_region_sources(region: str) -> dict:
    """Load sources configuration for a specific region."""
    config_path = Path(f"config/sources/{region}.yaml")
    if not config_path.exists():
        return {"rss_sources": [], "api_sources": []}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


def get_config() -> dict:
    """Get full application configuration."""
    return load_yaml_config()


def get_region_info(region: str) -> dict:
    """Get information about a specific region."""
    config = get_config()
    return config.get("region_info", {}).get(region, {})
