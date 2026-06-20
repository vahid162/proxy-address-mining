# Documentation Index

This index is the concise documentation map for `proxy-address-mining`. It routes readers to authoritative documents without duplicating dynamic phase state, release narratives, runtime authorization, or historical evidence.

## Authority order

1. `AGENTS.md` = AI operating instructions.
2. `docs/PHASE_STATUS.md` = only dynamic project-state authority.
3. `docs/SAFETY.md` = safety restrictions.
4. `docs/ARCHITECTURE.md` = architecture boundaries.
5. `CHANGELOG.md` = release history.
6. `docs/history/` = non-authorizing historical context.

If documents conflict, follow the stricter safety rule and the current dynamic state in `docs/PHASE_STATUS.md`.

## Required reading

For most tasks, read only the documents needed for the requested scope, in this order:

1. [`AGENTS.md`](../AGENTS.md)
2. [`docs/PHASE_STATUS.md`](PHASE_STATUS.md)
3. [`docs/INDEX.md`](INDEX.md)
4. [`docs/SAFETY.md`](SAFETY.md)
5. [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
6. Task-specific domain documents
7. Active gate or task documents named by `docs/PHASE_STATUS.md`

## Core contracts

- [`docs/SAFETY.md`](SAFETY.md) defines safety restrictions, phase gates, and non-negotiable operational guardrails.
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) defines architecture boundaries and the API-first service-layer pattern.
- [`docs/DATA_MODEL.md`](DATA_MODEL.md) defines data ownership and model contracts.
- [`docs/FIREWALL.md`](FIREWALL.md) defines firewall policy and planning contracts.
- [`docs/ABUSE.md`](ABUSE.md) defines abuse-control concepts and boundaries.
- [`docs/CUSTOMER_LIFECYCLE.md`](CUSTOMER_LIFECYCLE.md) defines customer lifecycle behavior.

## Task routing

- For current phase, gate, and next-step decisions, use only [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).
- For runtime, firewall, abuse, customer, scheduler, worker, UI, Telegram, or production work, follow the active gate/task documents named by `docs/PHASE_STATUS.md`.
- For implementation work, keep interfaces thin and route business logic through services, repositories, adapters, events, and audit.
- For release history, use [`CHANGELOG.md`](../CHANGELOG.md); do not treat historical release notes as current authorization.

## Historical references

The [`docs/history/`](history/) directory preserves former active documents for audit and continuity only. These files are non-authorizing and must not override `AGENTS.md`, `docs/PHASE_STATUS.md`, `docs/SAFETY.md`, or `docs/ARCHITECTURE.md`.

Legacy entrypoints preserved for this documentation contract:

- [`docs/history/README_LEGACY_0.1.299.md`](history/README_LEGACY_0.1.299.md)
- [`docs/history/INDEX_LEGACY_0.1.299.md`](history/INDEX_LEGACY_0.1.299.md)
