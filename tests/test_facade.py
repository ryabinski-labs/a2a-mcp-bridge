"""The MCP façade exposes the two-agent system as one callable tool.

This is the integration surface used by Claude Code, Codex, and opencode: a host
connects to the façade over MCP stdio and calls ``research_and_analyze``.
"""

from __future__ import annotations

import pytest

from a2a_mcp_bridge.agents.mcp_client import McpToolset

FACADE = "a2a_mcp_bridge.mcp_facade"


@pytest.mark.asyncio
async def test_facade_exposes_and_runs_collaboration(monkeypatch):
    # Offline + dedicated ports so the façade's internal agents do not collide.
    monkeypatch.setenv("A2A_MCP_PROVIDER", "mock")
    monkeypatch.setenv("A2A_MCP_RESEARCHER_PORT", "8911")
    monkeypatch.setenv("A2A_MCP_ANALYST_PORT", "8912")

    async with McpToolset(FACADE) as toolset:
        assert "research_and_analyze" in toolset.tool_names
        answer = await toolset.call(
            "research_and_analyze",
            {"topic": "the impact of remote work on team productivity"},
        )

    assert answer.strip()
    assert "remote-work-productivity" in answer or "8-13%" in answer
