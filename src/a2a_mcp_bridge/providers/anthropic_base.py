"""Shared Anthropic Messages API turn logic.

Both Claude on Vertex AI (``AnthropicVertex``) and the direct Anthropic API
(``Anthropic``) expose an identical ``messages.create`` surface, so the turn
logic lives here once and the two concrete providers only differ in how they
build the client.
"""

from __future__ import annotations

from typing import Any

from .base import LLMResponse, ToolCall


class AnthropicMessagesProvider:
    """Drives one Claude turn against any Anthropic Messages client."""

    def __init__(self, client: Any, model: str, name: str) -> None:
        self._client = client
        self._model = model
        self.name = name

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        message = self._client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        content_blocks: list[dict[str, Any]] = []

        for block in message.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(block.text)
                content_blocks.append({"type": "text", "text": block.text})
            elif btype == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, input=dict(block.input or {}))
                )
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": dict(block.input or {}),
                    }
                )

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=message.stop_reason or "end_turn",
            content_blocks=content_blocks,
        )
