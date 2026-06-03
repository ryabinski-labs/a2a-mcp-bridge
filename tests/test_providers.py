"""Provider abstraction and selection logic (offline)."""

from __future__ import annotations

from a2a_mcp_bridge.config import load_settings
from a2a_mcp_bridge.providers import get_provider
from a2a_mcp_bridge.providers.base import LLMProvider
from a2a_mcp_bridge.providers.mock import MockProvider

TOOLS = [
    {"name": "web_search", "description": "search", "input_schema": {"type": "object"}},
]


def test_mock_requests_tool_then_finalizes():
    provider = MockProvider()
    # First turn: only a user message -> the mock should ask for the web_search tool.
    first = provider.complete(
        system="sys",
        messages=[{"role": "user", "content": "remote work productivity"}],
        tools=TOOLS,
        max_tokens=256,
    )
    assert first.wants_tools
    assert first.tool_calls[0].name == "web_search"
    assert first.tool_calls[0].input["query"]

    # Second turn: after a tool_result, with the only tool already used, it finalizes.
    messages = [
        {"role": "user", "content": "remote work productivity"},
        {"role": "assistant", "content": first.content_blocks},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": first.tool_calls[0].id,
                    "content": "Search results: doc_id: remote-work-productivity",
                }
            ],
        },
    ]
    second = provider.complete(system="sys", messages=messages, tools=TOOLS, max_tokens=256)
    assert not second.wants_tools
    assert second.stop_reason == "end_turn"
    assert "remote-work-productivity" in second.text


def test_factory_defaults_to_mock_without_credentials(monkeypatch):
    for var in ["GOOGLE_CLOUD_PROJECT", "ANTHROPIC_VERTEX_PROJECT_ID", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(var, raising=False)
    settings = load_settings(provider="auto", vertex_project_id=None)
    provider = get_provider(settings)
    assert isinstance(provider, MockProvider)
    assert isinstance(provider, LLMProvider)


def test_factory_explicit_mock():
    provider = get_provider(load_settings(provider="mock"))
    assert provider.name == "mock"
