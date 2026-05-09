# Documentation Index

Status: active documentation map

This index defines the required reading path for `proxy-address-mining`.
It is intended for human contributors and AI coding agents.

## Start Here

Read these first:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`

`AGENTS.md` is the general implementation contract.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the current phase guard.
`docs/AI_CODING_RULES.md` defines the current AI coding rules and stop conditions.
This file is the documentation map.

## Core Contracts

Read these before implementation work:

1. `docs/ARCHITECTURE.md`
2. `docs/SAFETY.md`
3. `docs/ROADMAP.md`
4. `docs/DATA_MODEL.md`
5. `docs/TAXONOMY.md`
6. `docs/FIREWALL.md`
7. `docs/ABUSE.md`
8. `docs/BACKEND_PORT_POLICY.md`
9. `docs/OBSERVABILITY_HASHRATE.md`

## Current Phase Contracts

Current accepted phase:

```text
Phase 4.2 — Runtime Activation Runbook Planning, synced and verified on farm5
```

Current working phase:

```text
Phase 4 Runtime Activation Execution Review
```

Read:

1. `docs/PHASE_STATUS.md`
2. `docs/AI_PHASE_4_TASK.md`
3. `docs/AI_PHASE_4_2_TASK.md`
4. `docs/PHASE_4_SERVER_RUNBOOK.md`
5. `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`
6. `docs/PHASE_4_2_SERVER_SYNC_RESULT.md`
7. `docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md`
8. `docs/PHASE_4_1_SERVER_RESULT.md`
9. `docs/PHASE_3_1_PRE_PHASE4_ALIGNMENT.md`
10. `docs/BACKEND_PORT_POLICY.md`
11. `docs/OBSERVABILITY_HASHRATE.md`
12. `docs/INTRANET_INSTALL.md`

The current step is review-only until a dedicated runtime activation execution task is explicitly accepted.
It must not start proxy containers, create NAT redirects, apply firewall rules, onboard customers, or activate usage/abuse automation.

## Reading Order by Task

### Documentation-only change

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`
6. the document being changed
7. related core contracts

### Architecture or roadmap change

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SAFETY.md`
6. `docs/ROADMAP.md`
7. `docs/DATA_MODEL.md`
8. `docs/TAXONOMY.md`
9. `docs/FIREWALL.md`
10. `docs/ABUSE.md`
11. all phase/domain documents affected by the change

### Phase 4 runtime activation execution review

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/AI_PHASE_4_TASK.md`
6. `docs/AI_PHASE_4_2_TASK.md`
7. `docs/PHASE_4_SERVER_RUNBOOK.md`
8. `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`
9. `docs/PHASE_4_2_SERVER_SYNC_RESULT.md`
10. `docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md`
11. `docs/SAFETY.md`
12. `docs/FIREWALL.md`
13. `docs/BACKEND_PORT_POLICY.md`

Rules:

- review is not runtime approval
- no `docker compose up` during review
- no Docker/proxy runtime startup without a later explicit execution approval
- no customer NAT redirects
- no customer firewall rules
- no firewall apply
- no usage timers
- no abuse automation
- backend internal reachability and external exposure must be validated only in the later approved execution step

### Phase 4 planning work

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/AI_PHASE_4_TASK.md`
6. `docs/AI_PHASE_4_2_TASK.md`
7. `docs/PHASE_4_SERVER_RUNBOOK.md`
8. `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`
9. `docs/ROADMAP.md`
10. `docs/SAFETY.md`
11. `docs/FIREWALL.md`
12. `docs/BACKEND_PORT_POLICY.md`

Phase 4 planning may add Compose/proxy doctor design, read-only inspection helpers, validation scripts, and tests.
It must not activate Docker data-plane, firewall apply, NAT redirects, customers, usage timers, hash-rate collectors, abuse automation, UI, or Telegram.

### Phase 3.1 reference work

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/PHASE_3_1_PRE_PHASE4_ALIGNMENT.md`
6. `docs/PHASE_3_SERVER_RESULT.md`
7. `docs/BACKEND_PORT_POLICY.md`
8. `docs/OBSERVABILITY_HASHRATE.md`
9. `docs/INTRANET_INSTALL.md`

Phase 3.1 is accepted and recorded on farm5. Its result remains a safety baseline for Phase 4 review work.

### Database or migration work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SAFETY.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. relevant phase/domain document

Rules:

- PostgreSQL is source of truth.
- Migrations are required.
- Future production migrations should use explicit Alembic operations.
- Do not run production migrations until reviewed and explicitly approved.
- On farm5, run Alembic from `/opt/mpf-py-src`, not from `/root`.

### Firewall, proxy, or backend port work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/SAFETY.md`
5. `docs/FIREWALL.md`
6. `docs/BACKEND_PORT_POLICY.md`
7. `docs/DATA_MODEL.md`
8. `docs/AI_PHASE_4_TASK.md`
9. `docs/AI_PHASE_4_2_TASK.md`
10. `docs/PHASE_4_SERVER_RUNBOOK.md`
11. `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`
12. relevant phase/domain document

Rules:

- no ad-hoc production firewall mutation
- desired model first
- plan/diff before apply
- restore point before apply
- atomic apply through `iptables-restore`
- backend direct external exposure is critical
- backend internal reachability failure is also critical
- never hide backend ports by breaking valid internal paths
- Phase 4 proxy doctor work is read-only until runtime activation is explicitly accepted

### Hash-rate, share, worker, or observability work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/DATA_MODEL.md`
5. `docs/TAXONOMY.md`
6. `docs/OBSERVABILITY_HASHRATE.md`
7. relevant phase/domain document

Rules:

- accepted/rejected hash-rate per device is a future first-class capability
- do not implement it as UI-only calculations
- do not collect high-volume share events without retention and partitioning policy
- UI charts must read aggregate samples, not raw high-volume events
- worker name alone is not a guaranteed physical device identity

### Abuse work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/SAFETY.md`
5. `docs/ABUSE.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. `docs/FIREWALL.md`
9. relevant phase/domain document

Rules:

- all active customers in all enabled lanes are scanned
- no silent skip
- farms-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- hard/unhard must use restore points, events, audit, and firewall service
- abuse automation remains forbidden until Phase 8

### CLI/API/UI/Telegram interface work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SAFETY.md`
6. `docs/ROADMAP.md`
7. `docs/TAXONOMY.md`
8. relevant phase/domain document

Rules:

- interfaces are thin
- no direct DB writes
- no direct firewall commands
- call services only
- UI/API bind local-only in early phases
- Telegram starts notification-only

### Job or scheduler work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/SAFETY.md`
5. `docs/DATA_MODEL.md`
6. `docs/TAXONOMY.md`
7. relevant phase/domain document

Rules:

- use systemd timers
- no mixed cron/systemd model
- every job writes `job_runs`
- overlapping jobs use `scheduler_locks`
- jobs call services, not direct DB/firewall logic

## Documentation Summary

### `docs/PHASE_STATUS.md`

Defines the accepted phase, current working phase, allowed work, forbidden work, and next safe step.

### `docs/AI_PHASE_4_TASK.md`

Defines the repository-side Phase 4 AI task, allowed planning work, forbidden runtime behavior, required proxy doctor checks, tests, and stop conditions.

### `docs/AI_PHASE_4_2_TASK.md`

Defines the repository-side Phase 4.2 runtime activation runbook planning task and forbidden runtime behavior.

### `docs/PHASE_4_SERVER_RUNBOOK.md`

Defines Phase 4 server safety boundaries, allowed read-only checks, forbidden runtime actions, Compose requirements, proxy doctor acceptance fields, and the future runtime activation gate.

### `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`

Defines the exact future runtime activation procedure, stop/rollback commands, and post-run evidence checklist. It does not authorize runtime activation by itself.

### `docs/PHASE_4_2_SERVER_SYNC_RESULT.md`

Records the accepted farm5 Phase 4.2 server sync evidence.

### `docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md`

Defines the review gate before any limited Phase 4 runtime activation execution can be approved.

### `docs/AI_CODING_RULES.md`

Defines current AI coding rules, phase limits, runtime alignment rules, backend port rules, hash-rate/share planning rules, and stop conditions.

### `docs/PHASE_3_1_PRE_PHASE4_ALIGNMENT.md`

Defines the required server alignment gate that was completed before Phase 4 planning.

### `docs/BACKEND_PORT_POLICY.md`

Defines the backend-port invariant: internal reachability must remain OK while external direct exposure must be blocked.

### `docs/OBSERVABILITY_HASHRATE.md`

Defines future accepted/rejected hash-rate and share observability contracts.

### `docs/ARCHITECTURE.md`

Defines target architecture, API-first boundary, module layout, lane model, source of truth, firewall lifecycle, jobs, events, and future UI/Telegram boundaries.

### `docs/SAFETY.md`

Defines safety guardrails, phase gates, firewall safety, locking, restore points, abuse safety, secrets, UI/API exposure, job safety, canary policy, and AI safety checklist.

### `docs/ROADMAP.md`

Defines numbered phases, acceptance gates, MVP scope, stop conditions, and required tests by risk area.

### `docs/DATA_MODEL.md`

Defines PostgreSQL schema contract, table groups, relationships, ownership by services, indexes, retention, imports, and acceptance checklist.

### `docs/TAXONOMY.md`

Defines event/action/status taxonomy, actor/request context, phase gates, retention/partitioning timing, aggregate reporting timing, and evidence artifact reference rules.

### `docs/FIREWALL.md`

Defines firewall planner contract, apply modes, chain model, NAT, backend guard, plan/diff/apply/rollback lifecycle, doctor requirements, and tests.

### `docs/ABUSE.md`

Defines mandatory one-hour miner-abuse state machine, coverage requirements, exemption rules, hard/unhard behavior, evidence sources, reports, failure behavior, and tests.

## Current Roadmap Snapshot

```text
Phase 0   — Architecture Freeze
Phase 1   — Preflight + Bootstrap Without Traffic Changes
Phase 2   — PostgreSQL + Config + Domain Model
Phase 3   — CLI + Internal API Foundation
Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
Phase 4   — Compose Forward-only + Proxy Doctor
Phase 4.1 — Compose Template + Server Config Planning
Phase 4.2 — Runtime Activation Runbook Planning
Phase 4 Review — Runtime Activation Execution Review
Phase 5   — Customer CRUD in DB Only
Phase 6   — Firewall Planner + Apply/Verify/Rollback
Phase 7   — Usage + Policy/Reject Accounting
Phase 8   — Abuse 1h Core
Phase 9   — Check / Report / Diagnostics
Phase 10  — Session / Worker / Policy / Share Timeline
Phase 11  — Local Web UI Read-only
Phase 12  — Buyer-safe Read-only Reporting
Phase 13  — UI Actions With Confirmation
Phase 14  — Telegram Notifications, Read-only Commands, Restricted Actions
Phase 15  — Worker Policy Enforcement
```

## Stop Conditions

Stop and revise if any change introduces:

1. firewall apply before Phase 6
2. abuse automation before Phase 8
3. customer rules before their phase
4. NAT redirects before their phase
5. backend public exposure
6. backend internal reachability failure
7. UI direct DB write
8. Telegram shell command execution
9. bypassing `firewall.apply_mode=plan_only`
10. production TSV/SQLite source of truth
11. silent abuse scan exclusion
12. ad-hoc production firewall mutation
13. missing event/audit for mutation
14. missing restore point for dangerous action
15. production customer mutation before Phase 5
16. proxy data-plane activation before accepted Phase 4 runtime runbook
17. high-volume share/hash-rate collection before retention and partitioning review
18. UI charts reading raw high-volume share events directly
19. Phase 4 planning code that starts Docker/proxy runtime
20. public v2rayA UI exposure

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.
