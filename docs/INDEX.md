# Documentation Index

This is the canonical documentation map for human contributors and AI coding agents.

## Authority and Precedence

Use documents according to their role. Do not create a second source of truth by copying dynamic state into another document.

1. **Current phase, gates, and next required step:** [`PHASE_STATUS.md`](PHASE_STATUS.md)
2. **Safety restrictions and runtime boundaries:** [`SAFETY.md`](SAFETY.md), then the active gate documents named by `PHASE_STATUS.md`
3. **AI entrypoint and task routing:** [`../AGENTS.md`](../AGENTS.md)
4. **Architecture and service boundaries:** [`ARCHITECTURE.md`](ARCHITECTURE.md)
5. **Domain contracts:** the relevant document in the domain map below
6. **Release history:** [`../CHANGELOG.md`](../CHANGELOG.md)
7. **Historical evidence and prior phase material:** reference-only; it never opens a gate or overrides current state

When two documents conflict, follow the stricter safety rule and update the stale document in the same PR.

## Required Reading for Every Change

1. [`../AGENTS.md`](../AGENTS.md)
2. [`../README.md`](../README.md)
3. [`PHASE_STATUS.md`](PHASE_STATUS.md)
4. [`SAFETY.md`](SAFETY.md)
5. [`ARCHITECTURE.md`](ARCHITECTURE.md)
6. The task-specific contracts below
7. The active gate/task documents named by `PHASE_STATUS.md`

`AI_CODING_RULES.md` is supplementary implementation guidance. It must not be used as the authority for current gates or the next required step.

## Core Contracts

| Topic | Document | Use it for |
|---|---|---|
| Current phase and gate | [`PHASE_STATUS.md`](PHASE_STATUS.md) | Current accepted/working state, next step, allowed and forbidden work |
| Safety | [`SAFETY.md`](SAFETY.md) | Runtime restrictions, fail-closed behavior, operator boundaries |
| Architecture | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Service/repository/adapter boundaries and target deployment model |
| Roadmap | [`ROADMAP.md`](ROADMAP.md) | Long-term product sequence; never use it as current state |
| Data model | [`DATA_MODEL.md`](DATA_MODEL.md) | PostgreSQL entities, migration impact, data ownership |
| Artifact taxonomy | [`TAXONOMY.md`](TAXONOMY.md) | Expected versus unknown MPF artifacts and classifications |
| AI implementation guidance | [`AI_CODING_RULES.md`](AI_CODING_RULES.md) | Supplementary coding constraints; not dynamic state |
| Runtime-first operating contract | [`AI_SAFE_RUNTIME_FIRST.md`](AI_SAFE_RUNTIME_FIRST.md) | Runtime-affecting package, preflight, verification, and rollback work |

## Domain Map

| Task | Read these documents before editing |
|---|---|
| Firewall, NAT, backend exposure, or rollback | [`FIREWALL.md`](FIREWALL.md), [`BACKEND_PORT_POLICY.md`](BACKEND_PORT_POLICY.md), [`TAXONOMY.md`](TAXONOMY.md), [`AI_SAFE_RUNTIME_FIRST.md`](AI_SAFE_RUNTIME_FIRST.md) |
| Customer lifecycle, activation, expiry, or onboarding | [`CUSTOMER_LIFECYCLE.md`](CUSTOMER_LIFECYCLE.md), [`DATA_MODEL.md`](DATA_MODEL.md), [`FIREWALL.md`](FIREWALL.md), active gate documents |
| Abuse, pause, block, expire, or control intent | [`ABUSE.md`](ABUSE.md), [`CONTROL_RULES.md`](CONTROL_RULES.md), [`DATA_MODEL.md`](DATA_MODEL.md) |
| Usage, reports, checks, workers, shares, or timelines | [`OBSERVABILITY_HASHRATE.md`](OBSERVABILITY_HASHRATE.md), [`WORKER_POLICY.md`](WORKER_POLICY.md), [`DATA_MODEL.md`](DATA_MODEL.md) |
| Database schema or migration | [`DATA_MODEL.md`](DATA_MODEL.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), active gate documents |
| Runtime or production operations | [`AI_SAFE_RUNTIME_FIRST.md`](AI_SAFE_RUNTIME_FIRST.md), [`SAFETY.md`](SAFETY.md), [`FIREWALL.md`](FIREWALL.md), active gate documents |
| Documentation-only change | The document being changed, its inbound links, and this index |

## Active Gate Documents

`PHASE_STATUS.md` determines the current phase and names the task/gate documents required for that phase. Read exactly those documents before changing code or runtime behavior. Do not use historical phase documents as authorization unless `PHASE_STATUS.md` explicitly reopens them.

## Historical and Evidence Documents

Historical phase reports, farm evidence, acceptance packages, and compatibility anchors preserve context. They are reference-only unless the current phase document explicitly requires a named evidence file for verification. They do not define current authorization, next steps, or runtime permissions.

Release summaries belong in [`../CHANGELOG.md`](../CHANGELOG.md), not in this index.
