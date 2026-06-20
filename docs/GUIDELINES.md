# Engineering Guidelines

Status: Canonical engineering and AI-safe implementation contract

## Authority and reading order

Read only the documents needed for the task. Use [`AGENTS.md`](../AGENTS.md) for AI task routing, [`docs/PHASE_STATUS.md`](PHASE_STATUS.md) for current dynamic state and runtime authorization, this file for engineering rules, [`docs/SAFETY.md`](SAFETY.md) for safety constraints, [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for boundaries, and domain documents for task-specific rules. Historical material in [`docs/history/`](history/) is context only.

## Python rules

- Use clear names and small focused units.
- Prefer typed public interfaces where practical.
- Do not perform hidden runtime side effects during imports.
- Handle errors explicitly and return useful diagnostics.
- Do not broadly swallow exceptions; fail closed when safety is uncertain.

## Boundary rules

- Domain code is pure business logic and state transitions.
- Services orchestrate domain rules, repositories, adapters, transactions, events, and audit.
- Repositories own PostgreSQL read/write and do not make business decisions.
- Adapters own external I/O such as firewall, Docker, conntrack, systemd, network, and notifications.
- Interfaces remain thin and call services.
- Jobs call services and use locks, evidence, and audit records.

## Database and migration rules

- Migrations are additive and reversible where practical.
- Interfaces must not run direct ad-hoc production SQL.
- Preserve audit and event consistency with state changes.
- Use explicit transaction boundaries for multi-step changes.

## Runtime safety rules

- CLI, UI, API, Telegram, and job handlers must not run direct `iptables` commands.
- Do not mutate production without active-gate authorization from `docs/PHASE_STATUS.md`.
- Do not bypass planner, verifier, restore point, audit, or evidence flow.
- Do not apply hand-crafted server-only patches outside GitHub main.

## Testing rules

- Add a focused regression test for every bug.
- Run full pytest before delivery unless an environment limitation is documented.
- Run relevant validators and diff checks.
- Do not weaken existing safety assertions merely to pass tests.

## Security rules

- Do not commit secrets or print them in logs.
- Redact sensitive values in diagnostics.
- Validate external and operator input.
- Future UI must use context-aware output encoding and must not render untrusted HTML unsafely.

## AI delivery rules

- Deliver one complete outcome per PR.
- Do not invent server facts.
- Do not use history as authority.
- Do not hardcode a single customer or port where a domain model is required.
- Avoid repeated report-only PRs when a safe implementation outcome is possible.
