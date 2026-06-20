# Documentation Index

This index routes readers to authoritative documents without duplicating dynamic phase state, release narratives, runtime authorization, or historical evidence.

## Authority order

1. [`AGENTS.md`](../AGENTS.md) = AI operating instructions.
   Compatibility label: `AGENTS.md` = AI operating instructions.
2. [`docs/PHASE_STATUS.md`](PHASE_STATUS.md) = only dynamic project-state and runtime-authorization authority.
   Compatibility label: `docs/PHASE_STATUS.md` = only dynamic project-state authority.
3. [`docs/PRD.md`](PRD.md) = canonical product scope.
4. [`docs/GUIDELINES.md`](GUIDELINES.md) = canonical engineering rules.
5. [`docs/SAFETY.md`](SAFETY.md) = safety restrictions.
   Compatibility label: `docs/SAFETY.md` = safety restrictions.
6. [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) = architecture boundaries.
   Compatibility label: `docs/ARCHITECTURE.md` = architecture boundaries.
7. [`docs/ROADMAP.md`](ROADMAP.md) = long-term product evolution, not current authorization.
8. [`docs/ADR/`](ADR/) = architectural decisions.
9. [`CHANGELOG.md`](../CHANGELOG.md) = release history.
   Compatibility label: `CHANGELOG.md` = release history.
10. [`docs/history/`](history/) = non-authorizing historical context.
    Compatibility label: `docs/history/` = non-authorizing historical context.

If documents conflict, follow the stricter safety rule and the current dynamic state in `docs/PHASE_STATUS.md`.

## Required reading

For most tasks, read only the documents needed for the requested scope, in this order:

1. [`AGENTS.md`](../AGENTS.md)
2. [`docs/PHASE_STATUS.md`](PHASE_STATUS.md)
3. [`docs/INDEX.md`](INDEX.md)
4. Scope-specific canonical contracts and domain documents
5. Active gate or task documents named by `docs/PHASE_STATUS.md`

## Core contracts

- Product scope: [`docs/PRD.md`](PRD.md).
- Engineering rules: [`docs/GUIDELINES.md`](GUIDELINES.md).
- Architecture: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).
- Safety: [`docs/SAFETY.md`](SAFETY.md).
- Long-term roadmap: [`docs/ROADMAP.md`](ROADMAP.md).
- Architectural decisions: [`docs/ADR/`](ADR/) and [`ADR 0001`](ADR/0001-runtime-first-service-layer-boundary.md).
- Current state, gates, and runtime authorization: [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).
- Historical material: [`docs/history/`](history/).
- Data model: [`docs/DATA_MODEL.md`](DATA_MODEL.md).
- Firewall policy: [`docs/FIREWALL.md`](FIREWALL.md).
- Abuse controls: [`docs/ABUSE.md`](ABUSE.md).
- Customer lifecycle: [`docs/CUSTOMER_LIFECYCLE.md`](CUSTOMER_LIFECYCLE.md).
- Control rules: [`docs/CONTROL_RULES.md`](CONTROL_RULES.md).
- Backend port policy: [`docs/BACKEND_PORT_POLICY.md`](BACKEND_PORT_POLICY.md).
- Observability: [`docs/OBSERVABILITY_HASHRATE.md`](OBSERVABILITY_HASHRATE.md).
- Worker policy boundaries: [`docs/WORKER_POLICY.md`](WORKER_POLICY.md).

## Task routing

- Product-scope decisions: use [`docs/PRD.md`](PRD.md).
- Engineering implementation rules: use [`docs/GUIDELINES.md`](GUIDELINES.md).
- Current phase, gate, runtime permission, and next-step decisions: use only [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).
- Firewall/runtime work: read `docs/PHASE_STATUS.md`, [`docs/SAFETY.md`](SAFETY.md), [`docs/ARCHITECTURE.md`](ARCHITECTURE.md), [`docs/FIREWALL.md`](FIREWALL.md), and active gate documents named by `docs/PHASE_STATUS.md`.
- Abuse/control work: read `docs/PHASE_STATUS.md`, [`docs/ABUSE.md`](ABUSE.md), [`docs/CONTROL_RULES.md`](CONTROL_RULES.md), and active task documents named by `docs/PHASE_STATUS.md`.
- Customer lifecycle work: read `docs/PHASE_STATUS.md`, [`docs/CUSTOMER_LIFECYCLE.md`](CUSTOMER_LIFECYCLE.md), [`docs/DATA_MODEL.md`](DATA_MODEL.md), and active gate/task documents named by `docs/PHASE_STATUS.md`.
- Database/migration work: read `docs/PHASE_STATUS.md`, [`docs/DATA_MODEL.md`](DATA_MODEL.md), [`docs/GUIDELINES.md`](GUIDELINES.md), and service/repository contracts.
- Documentation-only work: preserve historical context without making archives authoritative; keep active entrypoints concise and route dynamic state to `docs/PHASE_STATUS.md`.
- Release history: use [`CHANGELOG.md`](../CHANGELOG.md); do not treat release notes as current authorization.

## Historical references

The [`docs/history/`](history/) directory preserves former active documents for audit and continuity only. These files are non-authorizing and must not override `AGENTS.md`, `docs/PHASE_STATUS.md`, `docs/SAFETY.md`, `docs/ARCHITECTURE.md`, or other current active contracts.
