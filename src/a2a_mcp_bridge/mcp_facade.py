"""MCP façade — exposes the whole two-agent system as a single MCP tool.

This is what makes ``a2a-mcp-bridge`` usable as a *skill* from any MCP-capable
host (Claude Code, Codex, opencode): the host connects to this stdio MCP server
and calls ``research_and_analyze(topic)``. Internally that spins up the
Researcher + Analyst agents (once, kept warm) and runs the A2A + MCP
collaboration, returning the analyzed answer.

So the project both *uses* MCP internally (agent → tools) and *is exposed via*
MCP externally (host → multi-agent system).
"""

from __future__ import annotations

import asyncio
import atexit
import logging

from mcp.server.fastmcp import FastMCP

from .a2a_client import call_agent
from .config import Settings, load_settings
from .launcher import AgentProcesses

logger = logging.getLogger(__name__)

mcp = FastMCP("a2a-mcp-bridge")

_procs: AgentProcesses | None = None
_settings: Settings | None = None
_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


async def _ensure_agents() -> Settings:
    """Start the agent pair on first use and keep it warm for the process."""
    global _procs, _settings
    async with _get_lock():
        if _procs is None:
            settings = load_settings()
            procs = AgentProcesses(settings)
            await procs.__aenter__()
            _procs, _settings = procs, settings
            logger.info("Agent pair started for MCP façade")
    assert _settings is not None
    return _settings


@atexit.register
def _shutdown() -> None:
    if _procs is not None:
        _procs.stop()


@mcp.tool()
async def research_and_analyze(topic: str) -> str:
    """Research a topic and return an analyzed answer produced by two
    collaborating Claude agents.

    A Researcher agent gathers sources with MCP tools, delegates to an Analyst
    agent over A2A, and the Analyst summarizes, scores relevance, and extracts
    entities. Use this when you want a researched, cross-checked answer rather
    than a single-model response.

    Args:
        topic: The subject or question to research and analyze.
    """
    settings = await _ensure_agents()
    answer = await call_agent(settings.researcher_url, topic)
    return answer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[a2a-mcp-facade] %(message)s")
    mcp.run()


if __name__ == "__main__":
    main()
