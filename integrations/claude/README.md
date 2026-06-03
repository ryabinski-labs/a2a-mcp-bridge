# Claude Code integration

## 1. Register the MCP server

Either run:

```bash
claude mcp add a2a-mcp-bridge -- /abs/path/to/.venv/bin/a2a-mcp-bridge-mcp
```

or copy [`.mcp.json`](.mcp.json) into your project root and edit the `command`
path (and `env`) to match your environment.

## 2. Install the Agent Skill (optional but recommended)

The skill in [`skills/a2a-mcp-bridge/`](skills/a2a-mcp-bridge/) tells Claude *when*
to use the `research_and_analyze` tool. Install it at user or project scope:

```bash
# user-level
cp -r skills/a2a-mcp-bridge ~/.claude/skills/a2a-mcp-bridge
# or project-level
mkdir -p .claude/skills && cp -r skills/a2a-mcp-bridge .claude/skills/
```

## 3. Use it

Ask Claude something research-shaped, e.g. *"Research the impact of remote work on
team productivity and give me an analyzed answer."* Claude will call the
`research_and_analyze` tool, which runs the Researcher + Analyst collaboration
over A2A + MCP and returns the result.
