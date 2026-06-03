"""Select a model provider from configuration."""

from __future__ import annotations

import logging

from ..config import Settings
from .base import LLMProvider

logger = logging.getLogger(__name__)


def get_provider(settings: Settings) -> LLMProvider:
    """Resolve the configured provider.

    ``auto`` prefers Claude on Vertex AI, then the direct Anthropic API, then
    falls back to the offline mock so the demo always runs.
    """
    choice = settings.provider.lower()

    if choice == "mock":
        from .mock import MockProvider

        return MockProvider()

    if choice == "vertex":
        from .vertex import build_vertex_provider

        return build_vertex_provider(
            settings.model, settings.vertex_project_id, settings.vertex_region
        )

    if choice == "anthropic":
        from .anthropic_api import build_anthropic_provider

        return build_anthropic_provider(settings.model)

    if choice == "auto":
        from .anthropic_api import anthropic_is_configured, build_anthropic_provider
        from .vertex import build_vertex_provider, vertex_is_configured

        if vertex_is_configured(settings.vertex_project_id):
            try:
                provider = build_vertex_provider(
                    settings.model, settings.vertex_project_id, settings.vertex_region
                )
                logger.info("Using Vertex AI provider")
                return provider
            except Exception as exc:  # noqa: BLE001 - fall through to next backend
                logger.warning("Vertex provider unavailable (%s); trying Anthropic API", exc)

        if anthropic_is_configured():
            logger.info("Using direct Anthropic API provider")
            return build_anthropic_provider(settings.model)

        from .mock import MockProvider

        logger.warning(
            "No Vertex or Anthropic credentials found; using the offline mock provider. "
            "Set A2A_MCP_VERTEX_PROJECT_ID (Vertex) or ANTHROPIC_API_KEY (Anthropic) for a live model."
        )
        return MockProvider()

    raise ValueError(f"Unknown provider {settings.provider!r}. Use auto|vertex|anthropic|mock.")
