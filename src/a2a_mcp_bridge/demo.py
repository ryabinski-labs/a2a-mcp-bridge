"""CLI: run the two-agent collaboration end to end.

Starts the Analyst and Researcher locally, sends a research topic to the
Researcher over A2A, and prints the final answer. With no model credentials it
uses the offline mock provider, so ``a2a-mcp-bridge`` works out of the box.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .a2a_client import call_agent
from .config import load_settings
from .launcher import AgentProcesses

DEFAULT_TOPIC = "the impact of remote work on team productivity"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="a2a-mcp-bridge",
        description="Two Claude agents collaborating locally over A2A and MCP.",
    )
    parser.add_argument(
        "topic",
        nargs="*",
        help="research topic (default: a remote-work example)",
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "vertex", "anthropic", "mock"],
        help="model backend (overrides A2A_MCP_PROVIDER; default: auto)",
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="do not start agents; use ones already running on the configured ports",
    )
    return parser.parse_args(argv)


async def _run(topic: str, *, launch: bool, provider_override: str | None) -> str:
    overrides = {"provider": provider_override} if provider_override else {}
    settings = load_settings(**overrides)
    if not launch:
        return await call_agent(settings.researcher_url, topic)
    async with AgentProcesses(settings):
        return await call_agent(settings.researcher_url, topic)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    topic = " ".join(args.topic) if args.topic else DEFAULT_TOPIC

    print(f"\n🔎 Topic: {topic}\n", flush=True)
    print("Starting agents and running the A2A + MCP collaboration...\n", flush=True)
    try:
        answer = asyncio.run(
            _run(topic, launch=not args.no_launch, provider_override=args.provider)
        )
    except KeyboardInterrupt:  # pragma: no cover
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - present any failure cleanly, no traceback
        print(f"\nError: {exc}", file=sys.stderr)
        if args.no_launch:
            print(
                "Hint: --no-launch expects agents already running on the configured "
                "ports. Start them with `python -m a2a_mcp_bridge.agents.analyst` and "
                "`python -m a2a_mcp_bridge.agents.researcher`, or drop --no-launch.",
                file=sys.stderr,
            )
        return 1
    print("=" * 72)
    print("FINAL ANSWER (from the Researcher, analyzed by the Analyst)")
    print("=" * 72)
    print(answer)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
