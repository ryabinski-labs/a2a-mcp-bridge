# Using a2a-mcp-bridge as a skill

The whole two-agent system is exposed as a **single MCP tool**:

```
research_and_analyze(topic: str) -> str
```

Calling it spins up the Researcher + Analyst agents (kept warm) and runs the full
A2A + MCP collaboration, returning the analyzed answer. Because it is plain MCP,
any MCP-capable agent can use it — here are copy-paste setups for **Claude Code**,
**Codex**, and **opencode**.

## Prerequisites

Install the package into a Python environment and note the path to the
`a2a-mcp-bridge-mcp` entry point (the MCP server):

```bash
python -m venv .venv && source .venv/bin/activate
pip install a2a-mcp-bridge   # or: pip install -e . from a clone
which a2a-mcp-bridge-mcp     # -> /abs/path/to/.venv/bin/a2a-mcp-bridge-mcp
```

MCP hosts launch the server as a subprocess, so use the **absolute path** to the
entry point (or `python -m a2a_mcp_bridge.mcp_facade` with the right interpreter).

By default the server uses the offline **mock** model so it works immediately.
To use a real Claude model, add the same environment variables described in the
top-level README (`A2A_MCP_PROVIDER`, `A2A_MCP_VERTEX_PROJECT_ID`, …) to the
`env` block of whichever config you use below.

---

## Claude Code

Two pieces: register the MCP server, and (optionally) install the Agent Skill
that tells Claude when to reach for it.

**Register the MCP server** (one line):

```bash
claude mcp add a2a-mcp-bridge -- /abs/path/to/.venv/bin/a2a-mcp-bridge-mcp
```

…or commit a project-scoped [`claude/.mcp.json`](claude/.mcp.json) to your repo.

**Install the skill** (so Claude knows when to use the tool): copy
[`claude/skills/a2a-mcp-bridge/`](claude/skills/a2a-mcp-bridge/) to
`~/.claude/skills/a2a-mcp-bridge/` (user-level) or `.claude/skills/…`
(project-level). See [`claude/README.md`](claude/README.md).

---

## Codex

Add to `~/.codex/config.toml` (or a project `.codex/config.toml`) — see
[`codex/config.toml`](codex/config.toml):

```toml
[mcp_servers.a2a-mcp-bridge]
command = "/abs/path/to/.venv/bin/a2a-mcp-bridge-mcp"
args = []
# Optional: use a real model instead of the offline mock.
# [mcp_servers.a2a-mcp-bridge.env]
# A2A_MCP_PROVIDER = "vertex"
# A2A_MCP_VERTEX_PROJECT_ID = "your-gcp-project"
```

Or via the CLI:

```bash
codex mcp add a2a-mcp-bridge -- /abs/path/to/.venv/bin/a2a-mcp-bridge-mcp
```

---

## opencode

Add to `opencode.json` (project) or `~/.config/opencode/opencode.json` (global)
— see [`opencode/opencode.json`](opencode/opencode.json):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "a2a-mcp-bridge": {
      "type": "local",
      "command": ["/abs/path/to/.venv/bin/a2a-mcp-bridge-mcp"],
      "enabled": true
    }
  }
}
```

---

## Verifying

In any of the three tools, ask the agent to *"use the research_and_analyze tool
to research the impact of remote work on team productivity."* You should see it
call the tool and return an analyzed answer. The first call takes a few seconds
while the agent pair starts; later calls reuse the warm pool.
