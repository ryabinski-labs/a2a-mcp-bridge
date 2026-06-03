"""Shared A2A server plumbing.

Builds agent cards and wires an ``AgentExecutor`` into a Starlette/uvicorn app
that speaks A2A JSON-RPC on loopback. The per-agent logic is supplied as an
async ``handler(user_text) -> str`` callback so the two agents only differ in
their handler.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import uvicorn
from a2a.helpers import new_task, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TaskState,
)
from a2a.utils import TransportProtocol
from starlette.applications import Starlette

HandlerFn = Callable[[str], Awaitable[str]]


def build_agent_card(
    *,
    name: str,
    description: str,
    url: str,
    skill_id: str,
    skill_name: str,
    skill_description: str,
    examples: list[str],
    version: str = "0.1.0",
) -> AgentCard:
    """Build a single-skill A2A agent card served on loopback."""
    return AgentCard(
        name=name,
        description=description,
        version=version,
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        supported_interfaces=[
            AgentInterface(
                url=url,
                protocol_binding=TransportProtocol.JSONRPC,
                protocol_version="0.3.0",
            )
        ],
        skills=[
            AgentSkill(
                id=skill_id,
                name=skill_name,
                description=skill_description,
                tags=["a2a", "mcp", "claude"],
                examples=examples,
            )
        ],
    )


class CallbackExecutor(AgentExecutor):
    """Adapts a simple async ``handler(text) -> text`` into an A2A executor."""

    def __init__(self, handler: HandlerFn) -> None:
        self._handler = handler

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            task = new_task(context.task_id, context.context_id, TaskState.TASK_STATE_SUBMITTED)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.start_work()
        try:
            answer = await self._handler(context.get_user_input())
        except Exception as exc:  # noqa: BLE001 - surface failures to the A2A client
            await updater.failed(updater.new_agent_message([new_text_part(f"agent error: {exc}")]))
            return
        await updater.complete(updater.new_agent_message([new_text_part(answer)]))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancellation is not supported in the local demo")


def build_app(agent_card: AgentCard, handler: HandlerFn) -> Starlette:
    """Build the Starlette app that serves one agent over A2A JSON-RPC."""
    request_handler = DefaultRequestHandler(
        agent_executor=CallbackExecutor(handler),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    routes = create_agent_card_routes(agent_card) + create_jsonrpc_routes(
        request_handler, "/", enable_v0_3_compat=True
    )
    return Starlette(routes=routes)


def run_server(agent_card: AgentCard, handler: HandlerFn, host: str, port: int) -> None:
    """Blocking: serve the agent until the process is stopped."""
    app = build_app(agent_card, handler)
    uvicorn.run(app, host=host, port=port, log_level="warning")
