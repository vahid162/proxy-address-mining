# Proxy Address Mining

Proxy Address Mining is a Python-first control plane for a customer-facing mining gateway. This README is intentionally concise for human orientation only; it does not define current phase state, runtime authorization, or operational gates.

## Start here

- [AGENTS.md](AGENTS.md) — AI operating instructions and repository task-routing rules.
- [Documentation index](docs/INDEX.md) — concise map for humans and AI agents.
- [Phase status](docs/PHASE_STATUS.md) — only authority for dynamic project state.
- [Safety](docs/SAFETY.md) — safety restrictions and non-negotiable guardrails.
- [Architecture](docs/ARCHITECTURE.md) — architecture boundaries and service-layer rules.
- [Changelog](CHANGELOG.md) — release history.
- [Version](VERSION) — current package/version metadata.

## Contribution orientation

Before making changes, follow the authority order in [docs/INDEX.md](docs/INDEX.md) and the safety constraints in [docs/SAFETY.md](docs/SAFETY.md). Keep interfaces thin and route behavior through the documented service, repository, adapter, event, and audit boundaries.

Historical README content is preserved as non-authorizing context in [docs/history/README_LEGACY_0.1.299.md](docs/history/README_LEGACY_0.1.299.md).
