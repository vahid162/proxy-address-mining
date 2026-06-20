# Proxy Address Mining

Proxy Address Mining is a Python-first control plane for a customer-facing mining gateway. It is intended to route customer mining ports through service-layer validated planning, auditing, and safety boundaries.

It is not a shell-script migration, an unrestricted production traffic switch, a public web panel, or a source of runtime authorization. Current phase state and operational permission live only in the authoritative documents linked below.

## Start here

- [AGENTS.md](AGENTS.md) — AI operating instructions and repository task-routing rules.
- [Documentation index](docs/INDEX.md) — concise map for humans and AI agents.
- [Product requirements](docs/PRD.md) — canonical product scope and success criteria.
- [Engineering guidelines](docs/GUIDELINES.md) — canonical engineering and AI-safe implementation rules.
- [Phase status](docs/PHASE_STATUS.md) — only authority for dynamic project state.
- [Safety](docs/SAFETY.md) — safety restrictions and non-negotiable guardrails.
- [Architecture](docs/ARCHITECTURE.md) — architecture boundaries and service-layer rules.
- [Roadmap](docs/ROADMAP.md) — long-term product evolution, not current authorization.
- [ADRs](docs/ADR/) — architectural decisions.
- [Changelog](CHANGELOG.md) — release history.
- [Version](VERSION) — current package/version metadata.

## Development checks

Verified repository checks used by this documentation contract:

```bash
git diff --check
python -m pytest -q
python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
```

Use narrower pytest selections when a task only changes focused documentation or tests, then run the full suite before delivery.

## Contribution orientation

Before making changes, follow the authority order in [docs/INDEX.md](docs/INDEX.md) and the safety constraints in [docs/SAFETY.md](docs/SAFETY.md). Keep interfaces thin and route behavior through documented service, repository, adapter, event, and audit boundaries.

Historical README content is preserved as non-authorizing context in [docs/history/README_LEGACY_0.1.299.md](docs/history/README_LEGACY_0.1.299.md).
