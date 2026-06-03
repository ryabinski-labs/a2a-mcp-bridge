"""Provider-agnostic types for a single Claude "turn".

The agentic loop (``agents/llm_loop.py``) speaks only this small vocabulary, so
Vertex AI, the direct Anthropic API, and the mock all plug into the same loop
and the same MCP tool-call plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ToolCall:
    """A tool-use request emitted by the model."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    """The result of one model turn.

    ``content_blocks`` is the assistant message in Anthropic Messages API shape;
    it is appended verbatim to the running transcript so the next turn has the
    model's own tool_use blocks in context.
    """

    text: str
    tool_calls: list[ToolCall]
    stop_reason: str
    content_blocks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def wants_tools(self) -> bool:
        return self.stop_reason == "tool_use" and bool(self.tool_calls)


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface every backend implements."""

    name: str

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        """Run one model turn and return a normalized response."""
        ...
