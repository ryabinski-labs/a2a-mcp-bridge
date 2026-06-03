"""The provider-agnostic Claude tool-use loop.

Given a model provider and an open ``McpToolset``, run the standard Anthropic
agentic loop: ask the model, execute any tool calls over MCP, feed the results
back, and repeat until the model stops asking for tools. Records a transcript of
every step so callers can show what happened.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..providers.base import LLMProvider
from .mcp_client import McpToolset


@dataclass
class LoopStep:
    kind: str  # "tool_call" | "tool_result" | "final"
    detail: str


@dataclass
class LoopResult:
    text: str
    steps: list[LoopStep] = field(default_factory=list)
    turns: int = 0


async def run_agent_loop(
    *,
    provider: LLMProvider,
    system: str,
    user_text: str,
    toolset: McpToolset | None,
    max_tokens: int,
    max_turns: int = 8,
) -> LoopResult:
    """Run the agentic loop and return the final text plus a transcript."""
    tools = toolset.anthropic_tools() if toolset else []
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_text}]
    result = LoopResult(text="")

    for turn in range(1, max_turns + 1):
        result.turns = turn
        response = provider.complete(
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=max_tokens,
        )
        messages.append({"role": "assistant", "content": response.content_blocks})

        if not response.wants_tools:
            result.text = response.text
            result.steps.append(LoopStep("final", response.text))
            return result

        tool_result_blocks: list[dict[str, Any]] = []
        for call in response.tool_calls:
            result.steps.append(LoopStep("tool_call", f"{call.name}({_fmt_args(call.input)})"))
            if toolset is None:
                output = f"[no toolset available for {call.name}]"
            else:
                output = await toolset.call(call.name, call.input)
            result.steps.append(LoopStep("tool_result", f"{call.name} -> {_truncate(output)}"))
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": output,
                }
            )
        messages.append({"role": "user", "content": tool_result_blocks})

    # Hit the turn ceiling without a final answer; return the best text we have.
    result.text = response.text or "[agent reached max turns without a final answer]"
    result.steps.append(LoopStep("final", result.text))
    return result


def _fmt_args(args: dict[str, Any]) -> str:
    parts = []
    for key, value in args.items():
        parts.append(f"{key}={_truncate(str(value), 60)!r}")
    return ", ".join(parts)


def _truncate(text: str, limit: int = 160) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"
