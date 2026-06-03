"""Deterministic, offline provider.

The mock does not call any model. Instead it plays a small script that exercises
the *real* MCP tool-call machinery: given the set of tools offered, it emits
genuine ``tool_use`` requests in a fixed order, then synthesizes a final text
answer from whatever the tools returned. This lets the whole two-agent demo and
the test suite run without cloud credentials while still going through the same
loop, MCP servers, and A2A wire as the live providers.
"""

from __future__ import annotations

import re
from typing import Any

from .base import LLMResponse, ToolCall

# The order in which the mock will reach for tools, if they are offered.
_TOOL_PLAN = [
    "web_search",
    "fetch_document",
    "summarize",
    "score_relevance",
    "extract_entities",
]

_DOC_ID_RE = re.compile(r"doc_id:\s*([A-Za-z0-9_-]+)")
_COUNTER = {"n": 0}


def _next_id() -> str:
    _COUNTER["n"] += 1
    return f"mocktool_{_COUNTER['n']:04d}"


def _last_user_text(messages: list[dict[str, Any]]) -> str:
    """Most recent plain-text user message (ignoring tool_result turns)."""
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if b.get("type") == "text"]
            if texts:
                return "\n".join(texts)
    return ""


def _called_tools(messages: list[dict[str, Any]]) -> set[str]:
    called: set[str] = set()
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if isinstance(content, list):
            for b in content:
                if b.get("type") == "tool_use":
                    called.add(b.get("name", ""))
    return called


def _tool_result_texts(messages: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, list):
            for b in content:
                if b.get("type") == "tool_result":
                    inner = b.get("content")
                    if isinstance(inner, str):
                        out.append(inner)
                    elif isinstance(inner, list):
                        out.extend(p.get("text", "") for p in inner if isinstance(p, dict))
    return out


def _input_for(tool: str, user_text: str, results: list[str]) -> dict[str, Any] | None:
    source = "\n\n".join(results) if results else user_text
    if tool == "web_search":
        return {"query": user_text[:300] or "research topic"}
    if tool == "fetch_document":
        joined = "\n".join(results)
        match = _DOC_ID_RE.search(joined)
        if not match:
            return None  # no doc id available -> skip this tool
        return {"doc_id": match.group(1)}
    if tool == "summarize":
        return {"text": source}
    if tool == "score_relevance":
        return {"text": source, "query": user_text[:300] or "topic"}
    if tool == "extract_entities":
        return {"text": source}
    return None


def _final_text(user_text: str, results: list[str]) -> str:
    header = "[mock] Synthesized answer (no live model was called)."
    topic = user_text.strip().splitlines()[0] if user_text.strip() else "the request"
    if results:
        joined = "\n\n".join(f"• {r.strip()}" for r in results if r.strip())
        return f"{header}\nTopic: {topic}\n\nGrounded in tool output:\n{joined}"
    # No tool output this turn (e.g. a compose turn that combines prior context):
    # echo the provided context so the synthesis is still meaningful offline.
    # The limit is generous so a compose step keeps both the findings and the
    # delegated analysis it was asked to combine.
    context = user_text.strip()
    snippet = context if len(context) <= 6000 else context[:5999] + "…"
    return f"{header}\nBased on the provided context:\n\n{snippet}"


class MockProvider:
    """Scripted provider that drives genuine MCP tool calls offline."""

    name = "mock"

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> LLMResponse:
        offered = {t["name"] for t in tools}
        called = _called_tools(messages)
        user_text = _last_user_text(messages)
        results = _tool_result_texts(messages)

        for tool in _TOOL_PLAN:
            if tool in offered and tool not in called:
                tool_input = _input_for(tool, user_text, results)
                if tool_input is None:
                    continue  # cannot run this tool yet; try the next planned one
                call = ToolCall(id=_next_id(), name=tool, input=tool_input)
                block = {
                    "type": "tool_use",
                    "id": call.id,
                    "name": call.name,
                    "input": call.input,
                }
                return LLMResponse(
                    text="",
                    tool_calls=[call],
                    stop_reason="tool_use",
                    content_blocks=[block],
                )

        text = _final_text(user_text, results)
        return LLMResponse(
            text=text,
            tool_calls=[],
            stop_reason="end_turn",
            content_blocks=[{"type": "text", "text": text}],
        )
