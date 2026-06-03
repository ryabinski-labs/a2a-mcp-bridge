"""Direct Anthropic API provider (fallback when Vertex is not configured)."""

from __future__ import annotations

import os

from .anthropic_base import AnthropicMessagesProvider


def build_anthropic_provider(model: str) -> AnthropicMessagesProvider:
    """Construct a provider backed by the direct Anthropic API client."""
    from anthropic import Anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Anthropic provider needs ANTHROPIC_API_KEY. Set it in the "
            "environment or your .env file."
        )
    client = Anthropic()
    return AnthropicMessagesProvider(client=client, model=model, name=f"anthropic:{model}")


def anthropic_is_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
