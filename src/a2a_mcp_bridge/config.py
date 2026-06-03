"""Runtime configuration, sourced from environment variables / ``.env``.

Nothing here contains secrets at import time; values are read from the
environment so the same code runs against Vertex AI, the direct Anthropic API,
or the offline mock provider.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the bridge, the agents, and the model backend."""

    model_config = SettingsConfigDict(
        env_prefix="A2A_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Model backend selection ---------------------------------------
    # "auto"      -> Vertex if configured, else Anthropic API, else mock
    # "vertex"    -> force Claude on Vertex AI
    # "anthropic" -> force the direct Anthropic API
    # "mock"      -> force the deterministic offline provider (used in tests/CI)
    provider: str = "auto"
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024

    # --- Vertex AI ------------------------------------------------------
    # Read from these or the standard GOOGLE_CLOUD_* / ANTHROPIC_VERTEX_* vars.
    vertex_project_id: str | None = None
    vertex_region: str = "us-east5"

    # --- A2A loopback endpoints ----------------------------------------
    host: str = "127.0.0.1"
    researcher_port: int = 8801
    analyst_port: int = 8802

    @property
    def researcher_url(self) -> str:
        return f"http://{self.host}:{self.researcher_port}"

    @property
    def analyst_url(self) -> str:
        return f"http://{self.host}:{self.analyst_port}"


def load_settings(**overrides: object) -> Settings:
    """Load settings from the environment, with optional explicit overrides."""
    return Settings(**overrides)
