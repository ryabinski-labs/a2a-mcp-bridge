"""Claude on Vertex AI provider (the primary, documented backend)."""

from __future__ import annotations

import os

from .anthropic_base import AnthropicMessagesProvider


def build_vertex_provider(
    model: str, project_id: str | None, region: str
) -> AnthropicMessagesProvider:
    """Construct a provider backed by ``AnthropicVertex``.

    Project and region fall back to the standard environment variables used by
    the Anthropic Vertex SDK and gcloud:
    ``ANTHROPIC_VERTEX_PROJECT_ID`` / ``GOOGLE_CLOUD_PROJECT`` and
    ``CLOUD_ML_REGION`` / ``ANTHROPIC_VERTEX_REGION``.
    """
    from anthropic import AnthropicVertex

    project_id = (
        project_id
        or os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    region = (
        region
        or os.environ.get("CLOUD_ML_REGION")
        or os.environ.get("ANTHROPIC_VERTEX_REGION")
        or "us-east5"
    )
    if not project_id:
        raise RuntimeError(
            "Vertex provider needs a GCP project id. Set A2A_MCP_VERTEX_PROJECT_ID "
            "or GOOGLE_CLOUD_PROJECT, and authenticate with `gcloud auth "
            "application-default login`."
        )

    client = AnthropicVertex(project_id=project_id, region=region)
    return AnthropicMessagesProvider(client=client, model=model, name=f"vertex:{model}")


def vertex_is_configured(project_id: str | None) -> bool:
    """True when enough is present to *attempt* a Vertex connection."""
    return bool(
        project_id
        or os.environ.get("ANTHROPIC_VERTEX_PROJECT_ID")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
