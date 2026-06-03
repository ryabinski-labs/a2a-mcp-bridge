"""The Researcher agent.

An A2A server that demonstrates both protocols in one task:

1. **MCP** — runs an agentic loop with the *research* tools (web_search,
   fetch_document) to gather sources on a topic.
2. **A2A** — delegates the gathered findings to the Analyst agent over loopback
   and waits for the structured analysis.
3. Composes a final answer from its findings and the Analyst's analysis.
"""

from __future__ import annotations

import logging

from ..a2a_client import call_agent
from ..config import Settings, load_settings
from ..providers import get_provider
from ..providers.base import LLMProvider
from .a2a_common import build_agent_card, run_server
from .llm_loop import run_agent_loop
from .mcp_client import McpToolset

logger = logging.getLogger(__name__)

RESEARCH_MCP_SERVER = "a2a_mcp_bridge.mcp_servers.research_tools"

RESEARCH_SYSTEM_PROMPT = (
    "You are a Researcher agent. Use your tools to gather sources about the "
    "user's topic: search with web_search, then fetch the most relevant document "
    "with fetch_document. Produce a concise 'Findings' section with the key facts "
    "and cite the doc_id of each source you used."
)

COMPOSE_SYSTEM_PROMPT = (
    "You are a Researcher agent writing the final answer for the user. You are "
    "given your own findings and an Analyst agent's analysis of them. Combine "
    "them into a clear, well-structured final answer with a short summary, the "
    "key findings, and the analyst's assessment. Do not invent new facts."
)


def build_handler(provider: LLMProvider, settings: Settings):
    async def handle(topic: str) -> str:
        # 1. MCP research phase.
        async with McpToolset(RESEARCH_MCP_SERVER) as toolset:
            research = await run_agent_loop(
                provider=provider,
                system=RESEARCH_SYSTEM_PROMPT,
                user_text=topic,
                toolset=toolset,
                max_tokens=settings.max_tokens,
            )
        logger.info("Research phase done in %d turn(s); delegating to Analyst", research.turns)

        # 2. A2A delegation to the Analyst.
        delegation = f"Topic: {topic}\n\nResearch findings to analyze:\n{research.text}"
        analysis = await call_agent(settings.analyst_url, delegation)
        logger.info("Received analysis from Analyst (%d chars)", len(analysis))

        # 3. Compose the final answer from findings + analysis.
        compose_input = (
            f"Topic: {topic}\n\n"
            f"== Your findings ==\n{research.text}\n\n"
            f"== Analyst's analysis ==\n{analysis}"
        )
        composed = await run_agent_loop(
            provider=provider,
            system=COMPOSE_SYSTEM_PROMPT,
            user_text=compose_input,
            toolset=None,
            max_tokens=settings.max_tokens,
        )
        return composed.text

    return handle


def make_card(settings: Settings):
    return build_agent_card(
        name="Researcher",
        description=(
            "Researches a topic with MCP tools, then delegates analysis to the "
            "Analyst agent over A2A."
        ),
        url=settings.researcher_url,
        skill_id="research-topic",
        skill_name="Research a topic",
        skill_description=("Gather sources on a topic and return a researched, analyzed answer."),
        examples=["Research the impact of remote work on team productivity."],
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[researcher] %(message)s")
    settings = load_settings()
    provider = get_provider(settings)
    logger.info("Provider: %s | serving on %s", provider.name, settings.researcher_url)
    run_server(
        make_card(settings),
        build_handler(provider, settings),
        settings.host,
        settings.researcher_port,
    )


if __name__ == "__main__":
    main()
