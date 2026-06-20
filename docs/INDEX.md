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
- [`docs/OBSERVABILITY_HASHRATE.md`](OBSERVABILITY_HASHRATE.md) defines observability concepts.
- [`docs/WORKER_POLICY.md`](WORKER_POLICY.md) defines worker-policy boundaries.

## Task routing

- Current phase, gate, and next-step decisions: use only [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).
- Firewall/runtime work: read `docs/PHASE_STATUS.md`, [`docs/SAFETY.md`](SAFETY.md), [`docs/ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/FIREWALL.md`](FIREWALL.md), and any active gate document named by `docs/PHASE_STATUS.md`.
- Abuse/control work: read `docs/PHASE_STATUS.md`, [`docs/ABUSE.md`](ABUSE.md), [`docs/CONTROL_RULES.md`](CONTROL_RULES.md), and the active Phase 8 or Phase 11 task document named by `docs/PHASE_STATUS.md`.
- Customer lifecycle work: read `docs/PHASE_STATUS.md`, [`docs/CUSTOMER_LIFECYCLE.md`](CUSTOMER_LIFECYCLE.md), [`docs/DATA_MODEL.md`](DATA_MODEL.md), and active gate/task documents named by `docs/PHASE_STATUS.md`.
- Database/migration work: read `docs/PHASE_STATUS.md`, [`docs/DATA_MODEL.md`](DATA_MODEL.md), migration-specific docs, and service/repository contracts; never infer DB authorization from this index.
- Observability/worker work: read `docs/PHASE_STATUS.md`, [`docs/OBSERVABILITY_HASHRATE.md`](OBSERVABILITY_HASHRATE.md), [`docs/WORKER_POLICY.md`](WORKER_POLICY.md), and active worker/usage task documents named by `docs/PHASE_STATUS.md`.
- Documentation-only work: preserve historical context without making archives authoritative; keep active entrypoints concise and route dynamic state to `docs/PHASE_STATUS.md`.
- Release history: use [`CHANGELOG.md`](../CHANGELOG.md); do not treat historical release notes as current authorization.

## Historical references

The [`docs/history/`](history/) directory preserves former active documents for audit and continuity only. These files are non-authorizing and must not override `AGENTS.md`, `docs/PHASE_STATUS.md`, `docs/SAFETY.md`, or `docs/ARCHITECTURE.md`.

Legacy entrypoints preserved for this documentation contract:

- [`docs/history/README_LEGACY_0.1.299.md`](history/README_LEGACY_0.1.299.md)
- [`docs/history/INDEX_LEGACY_0.1.299.md`](history/INDEX_LEGACY_0.1.299.md)
