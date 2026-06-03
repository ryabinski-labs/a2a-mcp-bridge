# a2a-mcp-bridge

[![CI](https://github.com/GipsyChef/a2a-mcp-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/GipsyChef/a2a-mcp-bridge/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Protocols: A2A + MCP](https://img.shields.io/badge/protocols-A2A%20%2B%20MCP-6f42c1.svg)](#what-are-a2a-and-mcp)

**Two Claude agents collaborating on one machine over A2A and MCP — with Claude on Vertex AI.**

*For developers and architects who want a working, inspectable multi-agent
example they can run in one command and adapt.*

> **Open-source companion** to the Anthropic × Google Cloud webinar
> *["Deploying multi-agent systems using MCP and A2A with Claude on Vertex AI."](https://www.anthropic.com/webinars/deploying-multi-agent-systems-using-mcp-and-a2a-with-claude-on-vertex-ai)*

**The problem:** most "multi-agent" examples tangle tools and agents together, so
it is hard to see where the Model Context Protocol ends and the Agent2Agent
protocol begins — or how to run the whole thing locally without a cloud account.

**The purpose of this project** is to be a small, runnable reference for the
pattern from the Anthropic × Google Cloud webinar *"Deploying multi-agent systems
using MCP and A2A with Claude on Vertex AI."* It shows the two open protocols
doing the two different jobs they are good at:

- **MCP (Model Context Protocol)** — how an agent talks to its **tools**.
- **A2A (Agent2Agent Protocol)** — how an agent talks to **another agent**.

A **Researcher** agent gathers sources with MCP tools, then delegates to an
**Analyst** agent over A2A; the Analyst summarizes, scores relevance, and
extracts entities with its own MCP tools and hands the analysis back. Everything
runs locally — the agents are two processes on your machine talking over
loopback. No cloud account is required to try it.

```
 Researcher  127.0.0.1:8801  ──A2A / JSON-RPC──►  Analyst  127.0.0.1:8802
    │ MCP / stdio                                    │ MCP / stdio
    ▼                                                ▼
 research-tools (subprocess)                  analysis-tools (subprocess)
   web_search, fetch_document                  summarize, score_relevance,
                                                extract_entities
```

## At a glance

- **What:** a runnable reference for two collaborating Claude agents using A2A + MCP, local-first.
- **Who it's for:** developers and architects evaluating multi-agent patterns, MCP/A2A integrators, and anyone reproducing the Anthropic × Google Cloud webinar locally.
- **Outcome:** a working, inspectable example you can run in one command and adapt — clear on which protocol does what.
- **Status:** beta (v0.1, pre-1.0). APIs may change; the local demo is stable and tested in CI.

### When to use this (and when not)

**Use it** to learn or demo the A2A + MCP pattern, to bootstrap your own two-agent
system, or to expose a multi-agent capability as an MCP skill for Claude Code /
Codex / opencode.

**Don't use it** as a production research engine — the bundled tools search a tiny
local corpus, not the internet, and the local phase has no authentication. For
real research quality, point a real Claude model at real tools (a documented
extension), and add auth/TLS before going multi-host.

## Requirements

- **Python 3.10+**
- No accounts required for the offline demo. For a live model: a GCP project with
  Claude-on-Vertex access *or* an `ANTHROPIC_API_KEY`.

## Why this exists

Most "multi-agent" demos blur tools and agents together. This one keeps them
separate so it is obvious which protocol does what: **MCP for tool integration,
A2A for task delegation.** It is intentionally local-first (the webinar's
"initial phase"): going multi-host later is a host change, not a rewrite. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## What are A2A and MCP?

**MCP (Model Context Protocol)** is an open standard from Anthropic for connecting
an AI agent to its **tools and data** — the agent calls tools the way a program
calls functions. **A2A (Agent2Agent Protocol)** is an open standard (originally
from Google, now under the Linux Foundation) for one **agent to talk to another
agent** as a peer — discovering it via an "agent card" and delegating tasks to it.

They are complementary, not competing: **use MCP inside an agent, and A2A between
agents.** This project is the smallest end-to-end example that shows both at once,
running locally, with Claude as the model.

## How this differs from an "MCP ↔ A2A bridge"

Several good projects expose *existing* A2A agents to a single MCP client (an
adapter: "let Claude Desktop call any A2A agent"). **`a2a-mcp-bridge` is not that.**
It is a complete, runnable **two-agent system** — it *contains* the agents (a
Researcher and an Analyst), each using MCP tools, that collaborate over A2A. Use
it to **see and adapt the whole pattern**, not just to proxy calls. (It also ships
an MCP façade, so it can *additionally* be consumed as a single tool — see below.)

## Quick start (no credentials needed)

Requires Python 3.10+.

```bash
git clone https://github.com/GipsyChef/a2a-mcp-bridge.git
cd a2a-mcp-bridge
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the full two-agent collaboration (uses the offline mock model):
a2a-mcp-bridge "the impact of remote work on team productivity"
```

With no model credentials the demo uses a **deterministic offline mock provider**
so it runs anywhere, including CI. It still goes through the real MCP servers and
the real A2A wire — only the model "thinking" is scripted.

## Using a real Claude model

The model backend is selected automatically: **Vertex AI → Anthropic API →
mock**. Configure either path with environment variables (or a `.env` file; see
[`.env.example`](.env.example)).

**Claude on Vertex AI (primary):**

```bash
gcloud auth application-default login
export A2A_MCP_PROVIDER=vertex
export A2A_MCP_VERTEX_PROJECT_ID=your-gcp-project
export A2A_MCP_VERTEX_REGION=us-east5
export A2A_MCP_MODEL=claude-sonnet-4-6
a2a-mcp-bridge "your topic"
```

**Direct Anthropic API (fallback):**

```bash
export A2A_MCP_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
a2a-mcp-bridge "your topic"
```

## Use it as a skill in Claude Code, Codex, and opencode

The whole two-agent system is also exposed as a **single MCP tool**,
`research_and_analyze(topic)`, via the `a2a-mcp-bridge-mcp` stdio server. Any
MCP-capable agent can call it. Ready-to-use config lives in
[`integrations/`](integrations/):

- **Claude Code** — [`integrations/claude/`](integrations/claude/): an Agent
  Skill plus a one-line `claude mcp add` command.
- **Codex** — [`integrations/codex/`](integrations/codex/): an `~/.codex/config.toml`
  snippet.
- **opencode** — [`integrations/opencode/`](integrations/opencode/): an
  `opencode.json` snippet.

See [`integrations/README.md`](integrations/README.md) for copy-paste setup for
each tool.

## How it works

| Layer | What it does |
| --- | --- |
| `providers/` | `LLMProvider` over the Anthropic Messages API: `vertex`, `anthropic_api`, `mock`. Same agentic loop for all three. |
| `mcp_servers/` | Two `FastMCP` stdio servers: `research_tools`, `analysis_tools`. |
| `agents/mcp_client.py` | Launches an MCP server, lists tools, runs tool calls. |
| `agents/llm_loop.py` | The provider-agnostic Claude tool-use loop. |
| `agents/a2a_common.py`, `a2a_client.py` | Serve / call an agent over A2A. |
| `agents/researcher.py`, `agents/analyst.py` | The two agents. |
| `launcher.py`, `demo.py` | Start both agents and run the demo. |
| `mcp_facade.py` | Expose the whole system as one MCP tool (the "skill"). |

## Run the agents by hand

```bash
# Terminal 1
python -m a2a_mcp_bridge.agents.analyst
# Terminal 2
python -m a2a_mcp_bridge.agents.researcher
# Terminal 3
a2a-mcp-bridge --no-launch "your topic"
```

## Development

```bash
pip install -e ".[dev]"
pytest            # runs fully offline with the mock provider
ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

## Support

This is a community reference project maintained on a best-effort basis. For
questions and bugs, open a [GitHub issue](https://github.com/GipsyChef/a2a-mcp-bridge/issues);
for vulnerabilities, follow [SECURITY.md](SECURITY.md). Maintainers are listed in
[MAINTAINERS.md](MAINTAINERS.md).

## Security & scope

The local phase has **no authentication** on the A2A endpoints and binds only to
`127.0.0.1` — do not expose these ports publicly. The bundled research tools
search a small **local corpus**, not the internet, so the demo is deterministic
and side-effect free. See [`SECURITY.md`](SECURITY.md).

## FAQ

**Do I need a Google Cloud account or Vertex AI to run it?**
No. The demo runs out of the box on a deterministic offline provider. Vertex AI
(or an Anthropic API key) is only needed for a *live* Claude model.

**Does it work offline / in CI?**
Yes. The mock provider drives the real MCP tool calls and the real A2A wire, so
the full collaboration runs with no credentials — that is exactly how CI tests it.

**Is this production-ready?**
No — it is a reference. The local phase has no auth and the tools search a small
local corpus. Add authentication/TLS and real tools before going multi-host.

**How is it different from the other "a2a mcp" repos?**
Most are *bridges/adapters* that let one MCP client call existing A2A agents.
This is a self-contained **two-agent system** you run and adapt. See
[How this differs](#how-this-differs-from-an-mcp--a2a-bridge).

**Can I use it from Claude Code, Codex, or opencode?**
Yes — it exposes a single MCP tool, `research_and_analyze`. See
[`integrations/`](integrations/).

**Which models work?**
Any Claude model available on Vertex AI or the Anthropic API (configurable via
`A2A_MCP_MODEL`).

## License

[Apache-2.0](LICENSE).

## Maintainers

Built and maintained by [**GipsyChef**](https://github.com/GipsyChef). Contributions
welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and [MAINTAINERS.md](MAINTAINERS.md).

---

Not an official Anthropic or Google product. "Claude" is a trademark of Anthropic;
**A2A (Agent2Agent)** and **MCP (Model Context Protocol)** are open protocols.
"Vertex AI" and "Google Cloud" are trademarks of Google LLC.
