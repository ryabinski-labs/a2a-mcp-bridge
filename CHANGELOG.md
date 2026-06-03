# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-03

### Added

- Initial release: two collaborating Claude agents on one machine.
- **Researcher** agent (A2A server) using MCP research tools (`web_search`,
  `fetch_document`) that delegates to the Analyst over A2A.
- **Analyst** agent (A2A server) using MCP analysis tools (`summarize`,
  `score_relevance`, `extract_entities`).
- Provider abstraction with **Claude on Vertex AI** (primary), **Anthropic API**
  (fallback), and a deterministic **offline mock** (tests/CI).
- `a2a-mcp-bridge` CLI that launches both agents and runs the collaboration.
- `a2a-mcp-bridge-mcp` MCP façade exposing `research_and_analyze(topic)` as a
  single tool, usable as a skill from **Claude Code**, **Codex**, and
  **opencode** (see `integrations/`).
- Offline test suite covering providers, MCP servers, the A2A round-trip, the
  full end-to-end collaboration, and the MCP façade.

[Unreleased]: https://github.com/GipsyChef/a2a-mcp-bridge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GipsyChef/a2a-mcp-bridge/releases/tag/v0.1.0
