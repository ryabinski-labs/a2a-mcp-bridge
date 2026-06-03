"""The Analyst agent.

An A2A server. On receiving research findings it runs an agentic loop with the
*analysis* MCP tools (summarize, score_relevance, extract_entities) and returns
a structured analysis. It uses MCP only — it does not call other agents.
"""

from __future__ import annotations

import logging

from ..config import Settings, load_settings
from ..providers import get_provider
from ..providers.base import LLMProvider
from .a2a_common import build_agent_card, run_server
from .llm_loop import run_agent_loop
from .mcp_client import McpToolset

logger = logging.getLogger(__name__)

ANALYSIS_MCP_SERVER = "a2a_mcp_bridge.mcp_servers.analysis_tools"

SYSTEM_PROMPT = (
    "You are an Analyst agent. You receive research findings from another agent. "
    "Use your available tools to produce a tight, structured analysis: summarize "
    "the key points, score how relevant the findings are to the stated topic, and "
    "extract the notable named entities. Then write a short 'Analysis' section "
    "with bullet points and the relevance score. Be concise and grounded in the "
    "tool output."
)


def build_handler(provider: LLMProvider, settings: Settings):
    async def handle(user_text: str) -> str:
        async with McpToolset(ANALYSIS_MCP_SERVER) as toolset:
            result = await run_agent_loop(
                provider=provider,
                system=SYSTEM_PROMPT,
                user_text=user_text,
                toolset=toolset,
                max_tokens=settings.max_tokens,
            )
        logger.info("Analyst finished in %d turn(s)", result.turns)
        return result.text

    return handle


def make_card(settings: Settings):
    return build_agent_card(
        name="Analyst",
        description="Analyzes research findings using MCP analysis tools.",
        url=settings.analyst_url,
        skill_id="analyze-findings",
        skill_name="Analyze findings",
        skill_description=(
            "Summarize, score relevance, and extract entities from research findings."
        ),
        examples=["Analyze these findings about remote work productivity."],
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[analyst] %(message)s")
    settings = load_settings()
    provider = get_provider(settings)
    logger.info("Provider: %s | serving on %s", provider.name, settings.analyst_url)
    run_server(
        make_card(settings), build_handler(provider, settings), settings.host, settings.analyst_port
    )


if __name__ == "__main__":
    main()
