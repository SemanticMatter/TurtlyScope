from __future__ import annotations

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TurtlyScope"
    debug: bool = False
    allowed_hosts: list[str] = ["*"]  # adjust in prod (e.g., ["turtlyscope.example.org"])
    cors_origins: list[AnyHttpUrl] = []  # set if used cross-origin
    max_turtle_chars: int = 250_000  # guardrails for input size
    theme_bgcolor: str = "#0b1020"  # forwarded to PyVis
    theme_fontcolor: str = "#e7ecf5"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
