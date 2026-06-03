"""Launch an MCP stdio server and expose its tools to the agent loop.

``McpToolset`` is an async context manager that spawns one of the bundled MCP
servers as a subprocess, performs the MCP handshake, and offers two things to
the agentic loop: the tool list in Anthropic ``tools`` schema, and a ``call``
method that invokes a tool and returns its text output.
"""

from __future__ import annotations

import os
import sys
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class McpToolset:
    """Async context manager around a single MCP stdio server."""

    def __init__(self, server_module: str, *, python: str | None = None) -> None:
        self._server_module = server_module
        self._python = python or sys.executable
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self._tools: list[Any] = []

    async def __aenter__(self) -> McpToolset:
        params = StdioServerParameters(
            command=self._python,
            args=["-m", self._server_module],
            # Inherit the parent environment so tool servers (and the façade,
            # which is itself launched this way) see the same configuration.
            env=dict(os.environ),
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._session = session
        self._tools = (await session.list_tools()).tools
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._stack.aclose()
        self._session = None

    @property
    def tool_names(self) -> list[str]:
        return [t.name for t in self._tools]

    def anthropic_tools(self) -> list[dict[str, Any]]:
        """Tool list in the schema the Anthropic Messages API expects."""
        schemas: list[dict[str, Any]] = []
        for tool in self._tools:
            schemas.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
                }
            )
        return schemas

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        """Invoke a tool and return its concatenated text output."""
        if self._session is None:
            raise RuntimeError("McpToolset used outside its async context")
        result = await self._session.call_tool(name, arguments)
        texts: list[str] = []
        for block in result.content:
            text = getattr(block, "text", None)
            if text is not None:
                texts.append(text)
        output = "\n".join(texts) if texts else "(tool returned no text)"
        if getattr(result, "isError", False):
            return f"[tool error] {output}"
        return output
