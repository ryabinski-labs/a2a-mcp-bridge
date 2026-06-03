"""Full two-agent collaboration over real A2A + MCP (offline mock model)."""

from __future__ import annotations

import pytest

from a2a_mcp_bridge.a2a_client import call_agent
from a2a_mcp_bridge.config import load_settings
from a2a_mcp_bridge.launcher import AgentProcesses


@pytest.mark.asyncio
async def test_researcher_delegates_to_analyst(monkeypatch):
    # Force the offline provider and use non-default ports so a stray dev server
    # on 8801/8802 cannot interfere.
    monkeypatch.setenv("A2A_MCP_PROVIDER", "mock")
    monkeypatch.setenv("A2A_MCP_RESEARCHER_PORT", "8901")
    monkeypatch.setenv("A2A_MCP_ANALYST_PORT", "8902")
    settings = load_settings()
    assert settings.researcher_port == 8901

    async with AgentProcesses(settings):
        answer = await call_agent(
            settings.researcher_url,
            "the impact of remote work on team productivity",
        )

        # The Researcher's answer must carry evidence that flowed through its MCP
        # research tools (web_search -> fetch_document).
        assert answer.strip()
        assert "remote-work-productivity" in answer or "8-13%" in answer
        # The compose step should fold in the Analyst's A2A contribution.
        assert "relevance:" in answer or "entities:" in answer

        # Independently verify the Analyst over A2A: it should run its own MCP
        # tools and return a structured analysis.
        analysis = await call_agent(
            settings.analyst_url,
            "Topic: remote work\n\nFindings: Acme Corp and Globex report 8-13% gains.",
        )
    assert "relevance:" in analysis
    assert "entities:" in analysis
