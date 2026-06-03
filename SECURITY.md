# Security Policy

## Scope and threat model

`a2a-mcp-bridge` is a **local-first reference implementation**. In its default
("initial phase") configuration:

- All servers bind to **`127.0.0.1`** (loopback) only.
- The A2A endpoints have **no authentication** — they are meant for same-machine
  use during the local phase.
- The MCP tool servers run as **child processes over stdio** (no network).
- The bundled research tools read a **local document corpus**, not the internet.

**Do not expose these ports to untrusted networks.** Binding the agents to a
public interface without adding authentication and TLS would let anyone reach
the agents and, through them, the model backend. Making the system remote is an
explicit, out-of-scope hardening step (see `docs/ARCHITECTURE.md`).

## Handling of secrets

- Credentials (GCP project, `ANTHROPIC_API_KEY`, application-default
  credentials) are read from the environment / `.env` and are **never logged**.
- `.env` is git-ignored; only `.env.example` (no secrets) is committed.

## Supported versions

This project is pre-1.0; security fixes are applied to the latest `main`.

## Reporting a vulnerability

Please report suspected vulnerabilities privately via GitHub's **"Report a
vulnerability"** (Security advisories) on this repository, rather than opening a
public issue. Include reproduction steps and impact. We aim to acknowledge
reports within a few days.
