# Contributing

Thanks for your interest in `a2a-mcp-bridge`! This is a reference implementation,
so contributions that make the A2A + MCP pattern clearer, more correct, or more
useful are very welcome.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest          # fully offline, uses the mock provider
ruff check .
```

The entire test suite runs without any cloud credentials. Please keep it that
way: tests must pass with `A2A_MCP_PROVIDER=mock` (the default when no
credentials are present).

## Guidelines

- **Keep the two protocols distinct.** MCP is for agent↔tool; A2A is for
  agent↔agent. Changes that blur this should explain why.
- **Add a test** for new behavior. End-to-end tests may spawn agent processes on
  loopback ports — use dedicated ports (see `tests/test_end_to_end.py`).
- **No secrets in code or tests.** Configuration comes from environment
  variables / `.env`.
- **Run `ruff check .`** before opening a PR.
- Keep dependencies minimal and pinned to compatible ranges in `pyproject.toml`.

## Pull requests

1. Fork and create a feature branch.
2. Make your change with tests and docs.
3. Ensure `pytest` and `ruff check .` pass.
4. Open a PR describing the change and the protocol behavior it affects.

## Reporting issues

Please include your OS, Python version, the provider you used (`mock`/`vertex`/
`anthropic`), and the exact command and output. For security issues, see
[SECURITY.md](SECURITY.md) instead of opening a public issue.

By contributing, you agree that your contributions are licensed under the
project's [Apache-2.0](LICENSE) license.
