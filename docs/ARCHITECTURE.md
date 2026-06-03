# Architecture

`a2a-mcp-bridge` is a small, runnable reference for the pattern shown in the
Anthropic × Google Cloud webinar *"Deploying multi-agent systems using MCP and
A2A with Claude on Vertex AI."* It runs **two Claude agents on one machine** that
collaborate using two complementary open protocols:

- **MCP (Model Context Protocol)** — how an agent talks to its **tools**.
- **A2A (Agent2Agent Protocol)** — how an agent talks to **another agent**.

The guiding idea: *MCP is for tool integration; A2A is for task delegation.* This
project keeps that separation visible so it is obvious which protocol does what.

## Why these two protocols and how they differ locally

| Concern | Protocol | Transport used here | Networked? |
| --- | --- | --- | --- |
| Agent → its tools | MCP | **stdio** (child process, pipes) | No — pure IPC |
| Agent → another agent | A2A | **HTTP / JSON-RPC** on `127.0.0.1` | Loopback only |

MCP defines a native local transport (stdio), so an agent simply launches its
tool server as a subprocess. A2A is defined as an HTTP/JSON-RPC protocol — there
is no stdio transport in the spec — so "local" means *bind to loopback* rather
than a public address. No TLS, auth, service discovery, or cloud is required for
the local phase; making it remote later is a one-line host change.

## Topology

```
 launcher.py  (one command starts everything)
 │
 ├─► Analyst agent process ─────────► A2A server  http://127.0.0.1:8802
 │        └─ spawns analysis MCP server  (stdio subprocess)
 │             tools: summarize, score_relevance, extract_entities
 │
 ├─► Researcher agent process ──────► A2A server  http://127.0.0.1:8801
 │        ├─ spawns research MCP server  (stdio subprocess)
 │        │    tools: web_search, fetch_document
 │        └─ A2A client ──────────────► calls Analyst over loopback
 │
 └─► demo client ──────────────────► sends kickoff task to Researcher, prints result
```

## The collaboration flow

1. The **demo client** sends a research topic to the **Researcher** over A2A.
2. The Researcher runs an **agentic loop**: Claude (Vertex/Anthropic) decides to
   call its **MCP** tools (`web_search`, `fetch_document`) to gather sources.
3. The Researcher delegates analysis to the **Analyst** over **A2A**, passing the
   gathered findings.
4. The Analyst runs its own agentic loop using its **MCP** tools (`summarize`,
   `score_relevance`, `extract_entities`) and returns a structured analysis.
5. The Researcher composes the final answer and returns it to the client.

Each agent calls Claude independently, so the demo shows tool integration
(MCP), task delegation (A2A), and context sharing between two models.

## Layers

- `providers/` — a thin `LLMProvider` abstraction over the Anthropic Messages
  API. `vertex` (Claude on Vertex AI, primary), `anthropic_api` (direct API
  fallback), and `mock` (deterministic, offline — used by tests/CI so the repo
  is verifiable without cloud credentials). All three drive the *same* agentic
  loop and the *same* MCP tool-call plumbing.
- `mcp_servers/` — two `FastMCP` stdio servers exposing plain Python tools.
- `agents/mcp_client.py` — launches an MCP stdio server, lists its tools,
  converts them to Anthropic tool schemas, and executes tool calls.
- `agents/llm_loop.py` — the provider-agnostic Claude tool-use loop.
- `agents/a2a_common.py` — builds agent cards and runs an A2A server for an
  agent; `a2a_client.py` calls another agent and returns its final text.
- `agents/researcher.py`, `agents/analyst.py` — the two agents.
- `launcher.py` / `demo.py` — process supervision and the CLI entry point.

## Design decisions (ADR-style summary)

1. **A2A over loopback TCP, not in-process.** Keeps the wire protocol real and
   identical to the remote case; going multi-host is a host change. Trade-off:
   two localhost ports are in use.
2. **MCP over stdio.** Native local transport; no ports, FS-isolated child
   processes. Trade-off: tools must be launchable as a subprocess.
3. **Provider abstraction with a mock.** Vertex is the documented path, but the
   mock lets anyone run the demo and CI offline. Trade-off: the mock's
   "reasoning" is scripted, not a real model.
4. **MCP for tools, A2A for delegation — kept separate.** Pedagogically clear and
   matches the webinar framing. Trade-off: the Researcher's delegation to the
   Analyst is orchestrated in code rather than chosen by the model as a tool.
5. **Streaming A2A client.** The SDK's streaming path returns incremental
   updates cleanly; the demo prints them as a live transcript.

## Security & operational notes (local phase)

- Servers bind to `127.0.0.1` only. Do **not** expose these ports publicly; the
  local phase has **no authentication** on the A2A endpoints by design.
- Secrets (GCP project, API keys) come from environment variables / `.env`, are
  never logged, and `.env` is git-ignored.
- The `web_search`/`fetch_document` tools operate over a small bundled local
  corpus — they do not reach the internet — so the demo is deterministic and
  side-effect free. Swapping in a real search API is a documented extension.

## Path to "remote phase" (out of scope for v0.1)

Replace loopback URLs with real hostnames, add TLS termination, put an
authentication scheme on the agent cards (the A2A SDK supports security
schemes), and run each agent as its own service. The agent and tool code does
not change.
