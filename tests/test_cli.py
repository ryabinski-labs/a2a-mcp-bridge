"""CLI behavior, including graceful failure (no raw tracebacks)."""

from __future__ import annotations

import os
import subprocess
import sys


def test_no_launch_without_agents_fails_cleanly():
    """`--no-launch` against no running agents must fail with a friendly message,
    not an uncaught traceback. Regression for the CLI swallowing connection errors.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "a2a_mcp_bridge.demo",
            "--no-launch",
            "--provider",
            "mock",
            "anything",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "A2A_MCP_RESEARCHER_PORT": "8999", "A2A_MCP_ANALYST_PORT": "8998"},
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "Error:" in result.stderr
    assert "--no-launch" in result.stderr  # the actionable hint


def test_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "a2a_mcp_bridge.demo", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "topic" in result.stdout
