# AGENTS.md

## Purpose

This is the canonical entrypoint for GPT, Codex, and other AI coding agents working in this repository.

Read this file before planning or editing. Use it to locate the authoritative project documents; do not treat it as the source of current runtime state, release history, or phase evidence.

## Project Identity

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed control plane for a mining customer gateway. It is a greenfield rewrite that preserves required operational capability without copying, patching, or extending the former shell-script system.

## Canonical Sources

| Question | Authoritative source |
|---|---|
| What is the project and how is it developed? | `README.md` |
| What is the current phase, gate, and next required step? | `docs/PHASE_STATUS.md` |
| Which document applies to this task? | `docs/INDEX.md` |
| What runtime work is safe or prohibited? | `docs/SAFETY.md` and the active gate documents named by `docs/PHASE_STATUS.md` |
| What architecture must code follow? | `docs/ARCHITECTURE.md` |
| What changed in past releases? | `CHANGELOG.md` |
| What is the repository version? | `VERSION`, `pyproject.toml`, and `mpf/__init__.py` |

`docs/PHASE_STATUS.md` is the only authority for dynamic project state. Do not infer the current gate or next step from `README.md`, this file, old evidence, historical phase documents, or release notes.

## Required Reading

Before any change, read in this order:

1. `README.md`
2. `docs/INDEX.md`
3. `docs/PHASE_STATUS.md`
4. `docs/SAFETY.md`
5. `docs/ARCHITECTURE.md`
6. The task-specific documents selected by `docs/INDEX.md`
7. The active gate/task documents named by `docs/PHASE_STATUS.md`

Read `docs/AI_CODING_RULES.md` only as supplementary implementation guidance. It does not define current phase state or override the sources above.

## Task Routing

- **Runtime, firewall, lifecycle, or deployment work:** also read `docs/AI_SAFE_RUNTIME_FIRST.md`, `docs/FIREWALL.md`, `docs/BACKEND_PORT_POLICY.md`, and the active gate documents.
- **Abuse or controls work:** also read `docs/ABUSE.md`, `docs/CONTROL_RULES.md`, and `docs/DATA_MODEL.md`.
- **Customer lifecycle work:** also read `docs/CUSTOMER_LIFECYCLE.md`, `docs/DATA_MODEL.md`, and `docs/FIREWALL.md` when policy or activation is affected.
- **Observability, worker, share, or reporting work:** also read `docs/OBSERVABILITY_HASHRATE.md` and `docs/WORKER_POLICY.md`.
- **Documentation-only work:** read the authoritative document being changed plus every document that links to or depends on it.

## Non-Negotiable Safety Rules

- Preserve fail-closed behavior.
- Do not perform direct or ad-hoc mutation of PostgreSQL, firewall rules, Docker, systemd, or conntrack.
- Do not bypass service-layer validation, package/preflight/verify/rollback contracts, or operator gates.
- Do not open a future phase, worker enforcement, UI, Telegram, public exposure, or unrestricted expansion unless `docs/PHASE_STATUS.md` and the active acceptance contract explicitly authorize it.
- Keep interfaces thin: CLI, API, UI, Telegram, and jobs must call services; services own validation and side-effect ordering; repositories own persistence; adapters own external-system access.

When documents conflict, stop and apply the stricter safety rule. Update the stale document in the same PR before relying on it.

## Validation and Delivery

Run the relevant targeted tests and the full suite when the change can affect shared behavior:

```bash
python -m pytest -q
```

For PR text, run:

```bash
python scripts/validate_runtime_first_pr_body.py /tmp/pr_body.md
```

Use Conventional Commits. A PR must have only these headings:

```text
Why
What
How to test
```

Follow the repository release policy: keep `VERSION`, `pyproject.toml`, `mpf/__init__.py`, `CHANGELOG.md`, and version-consistency tests aligned whenever the PR requires a version bump.
