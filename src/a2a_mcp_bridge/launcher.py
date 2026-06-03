"""Start and supervise the two agent processes locally.

Each agent runs in its own process (faithful to A2A's inter-service model) and is
considered ready when its agent card is reachable on loopback.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
import sys

import httpx

from .config import Settings

ANALYST_MODULE = "a2a_mcp_bridge.agents.analyst"
RESEARCHER_MODULE = "a2a_mcp_bridge.agents.researcher"
AGENT_CARD_PATH = "/.well-known/agent-card.json"


class AgentProcesses:
    """Spawns the analyst and researcher processes and waits until both are ready."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._procs: list[subprocess.Popen] = []

    def _spawn(self, module: str) -> subprocess.Popen:
        env = os.environ.copy()
        # Ensure children inherit the same provider/port configuration.
        env.setdefault("A2A_MCP_PROVIDER", self._settings.provider)
        return subprocess.Popen([sys.executable, "-m", module], env=env)

    async def __aenter__(self) -> AgentProcesses:
        # Start the Analyst first; the Researcher depends on it at request time.
        self._procs.append(self._spawn(ANALYST_MODULE))
        self._procs.append(self._spawn(RESEARCHER_MODULE))
        await self._wait_ready(self._settings.analyst_url)
        await self._wait_ready(self._settings.researcher_url)
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.stop()

    def stop(self) -> None:
        """Synchronously terminate both agent processes (idempotent)."""
        for proc in self._procs:
            with contextlib.suppress(ProcessLookupError):
                proc.terminate()
        for proc in self._procs:
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)
        for proc in self._procs:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
        self._procs = []

    async def _wait_ready(self, base_url: str, timeout: float = 30.0) -> None:
        url = base_url + AGENT_CARD_PATH
        deadline = asyncio.get_event_loop().time() + timeout
        async with httpx.AsyncClient(timeout=2.0) as client:
            while asyncio.get_event_loop().time() < deadline:
                self._assert_alive()
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.25)
        raise TimeoutError(f"agent at {base_url} did not become ready within {timeout}s")

    def _assert_alive(self) -> None:
        for proc in self._procs:
            code = proc.poll()
            if code is not None and code != 0:
                raise RuntimeError(f"agent process {proc.args} exited early with code {code}")
