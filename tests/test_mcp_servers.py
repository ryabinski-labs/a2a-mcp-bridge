"""Exercise the MCP stdio servers through the real client (offline)."""

from __future__ import annotations

import pytest

from a2a_mcp_bridge.agents.mcp_client import McpToolset

RESEARCH = "a2a_mcp_bridge.mcp_servers.research_tools"
ANALYSIS = "a2a_mcp_bridge.mcp_servers.analysis_tools"


@pytest.mark.asyncio
async def test_research_tools_search_and_fetch():
    async with McpToolset(RESEARCH) as toolset:
        assert set(toolset.tool_names) == {"web_search", "fetch_document"}
        schemas = toolset.anthropic_tools()
        assert all("input_schema" in s for s in schemas)

        hits = await toolset.call("web_search", {"query": "remote work productivity"})
        assert "doc_id:" in hits
        assert "remote-work-productivity" in hits

        doc = await toolset.call("fetch_document", {"doc_id": "remote-work-productivity"})
        assert "8-13%" in doc

        missing = await toolset.call("fetch_document", {"doc_id": "nope"})
        assert "No document" in missing


@pytest.mark.asyncio
async def test_analysis_tools():
    text = (
        "Remote work raises focused output by 8-13% while lengthening decision "
        "cycles. Acme Corp and Globex report better retention with short core hours."
    )
    async with McpToolset(ANALYSIS) as toolset:
        assert set(toolset.tool_names) == {"summarize", "score_relevance", "extract_entities"}

        summary = await toolset.call("summarize", {"text": text, "max_sentences": 1})
        assert summary and "[tool error]" not in summary
        # The summary must be drawn from the source text, not an error string.
        assert "remote work" in summary.lower() or "retention" in summary.lower()

        score = await toolset.call(
            "score_relevance", {"text": text, "query": "remote work productivity"}
        )
        assert "relevance:" in score and "/100" in score

        entities = await toolset.call("extract_entities", {"text": text})
        assert "Acme Corp" in entities or "Globex" in entities
