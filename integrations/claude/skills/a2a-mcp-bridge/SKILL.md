---
name: a2a-mcp-bridge
description: Research a topic with two collaborating Claude agents (a Researcher and an Analyst) that coordinate over the A2A protocol and use MCP tools. Use when the user wants a researched, cross-checked, and analyzed answer — with sources gathered, summarized, relevance-scored, and key entities extracted — rather than a single-model response. Requires the a2a-mcp-bridge MCP server to be configured.
---

# a2a-mcp-bridge skill

This skill delegates research-and-analysis requests to a local multi-agent
system exposed through the `research_and_analyze` MCP tool.

## When to use

Use this skill when the user asks to **research and analyze** a topic, wants
**sources gathered and assessed**, or asks for an answer that should be
**cross-checked by more than one agent** (for example: "research X and tell me
what the evidence says", "gather and analyze findings on Y").

Do **not** use it for quick factual questions you can answer directly, or for
tasks unrelated to research/analysis.

## How it works

Calling `research_and_analyze(topic)` starts two collaborating Claude agents on
the local machine:

1. A **Researcher** agent gathers sources using MCP research tools.
2. It delegates to an **Analyst** agent over the **A2A** protocol.
3. The Analyst summarizes, scores relevance, and extracts entities using its own
   MCP tools, then returns a structured analysis.
4. The Researcher composes the final answer.

## Usage

1. Ensure the `a2a-mcp-bridge` MCP server is configured (see the project's
   `integrations/README.md`).
2. Call the tool with the user's topic:
   - Tool: `research_and_analyze`
   - Argument: `topic` — the subject or question to research.
3. Present the returned answer to the user. If they want the raw research or the
   analysis separately, mention that the answer already folds in both the
   Researcher's findings and the Analyst's assessment.

## Notes

- The first call takes a few seconds while the agent pair starts; subsequent
  calls reuse the warm agents.
- With no model credentials configured, the system runs in a deterministic
  offline mode (useful for trying the flow, not for real research quality).
