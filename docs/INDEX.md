# Documentation Index

Status: Draft v1

This index defines the required reading path for `proxy-address-mining`.
It is intended for human contributors and AI coding agents.

## Start Here

Read these first:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`

`AGENTS.md` is the implementation contract for AI agents.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the current phase guard and decides what work is allowed now.
This file is the documentation map.

## Core Contracts

Read these before any implementation work:

1. `docs/ARCHITECTURE.md`
2. `docs/SAFETY.md`
3. `docs/ROADMAP.md`
4. `docs/DATA_MODEL.md`
5. `docs/FIREWALL.md`
6. `docs/ABUSE.md`

## Phase Contracts

Current phase documents:

1. `docs/PHASE_STATUS.md`
2. `docs/PHASE_0.md`
3. `docs/PHASE_1.md`
4. `docs/PHASE_1_SERVER_RUNBOOK.md`
5. `docs/INTRANET_INSTALL.md`
6. `docs/AI_PHASE_2_TASK.md`

Follow phase gates in `docs/ROADMAP.md`.
Do not implement a later phase until the current phase acceptance gate passes.

## Reading Order by Task

### Documentation-only change

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. the document being changed
6. related core contracts

### Architecture or roadmap change

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SAFETY.md`
5. `docs/ROADMAP.md`
6. `docs/DATA_MODEL.md`
7. `docs/FIREWALL.md`
8. `docs/ABUSE.md`
9. all phase documents affected by the change

### Phase 0 work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SAFETY.md`
5. `docs/ROADMAP.md`
6. `docs/PHASE_0.md`

Phase 0 is documentation-only.

### Phase 1 work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/SAFETY.md`
4. `docs/ROADMAP.md`
5. `docs/PHASE_0.md`
6. `docs/PHASE_1.md`
7. `docs/INTRANET_INSTALL.md`, if the server has no direct GitHub access

Phase 1 must not change traffic.

### Phase 2 work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/SAFETY.md`
4. `docs/DATA_MODEL.md`
5. `docs/ROADMAP.md`
6. `docs/AI_PHASE_2_TASK.md`
7. `docs/PHASE_1_SERVER_RUNBOOK.md`

Phase 2 is repository-only database and domain-model groundwork.
It must not apply firewall rules, create NAT redirects, start proxy containers, or activate abuse automation.

### Database or migration work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SAFETY.md`
5. `docs/DATA_MODEL.md`
6. `docs/ROADMAP.md`
7. `docs/AI_PHASE_2_TASK.md`
8. relevant phase document

Rules:

- PostgreSQL is source of truth.
- Migrations are required.
- Customer policy must be versioned.
- Restore points and job_runs must be representable.
- Do not run production migrations until reviewed and explicitly approved.

### Firewall work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/SAFETY.md`
4. `docs/FIREWALL.md`
5. `docs/DATA_MODEL.md`
6. `docs/ROADMAP.md`
7. relevant phase document

Rules:

- no ad-hoc production iptables mutation
- desired model first
- plan/diff before apply
- restore point before apply
- atomic apply through `iptables-restore`
- verify after apply
- rollback from stored artifacts

### Abuse work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/SAFETY.md`
4. `docs/ABUSE.md`
5. `docs/DATA_MODEL.md`
6. `docs/FIREWALL.md`
7. `docs/ROADMAP.md`
8. relevant phase document

Rules:

- all active customers in all enabled lanes are scanned
- no silent skip
- farms-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- hard/unhard must use restore points, events, audit, and firewall service

### CLI/API/UI/Telegram interface work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SAFETY.md`
5. `docs/ROADMAP.md`
6. relevant domain document
7. relevant phase document

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
3. `docs/SAFETY.md`
4. `docs/DATA_MODEL.md`
5. `docs/ROADMAP.md`
6. relevant domain document

Rules:

- use systemd timers
- no mixed cron/systemd model
- every job writes `job_runs`
- overlapping jobs use `scheduler_locks`
- jobs call services, not direct DB/firewall logic

## Documentation Summary

### `docs/PHASE_STATUS.md`

Defines the currently accepted phase, current working phase, allowed work, forbidden work, and next safe step.

### `docs/ARCHITECTURE.md`

Defines target architecture, API-first boundary, module layout, lane model, source of truth, firewall lifecycle, jobs, events, and future UI/Telegram boundaries.

### `docs/SAFETY.md`

Defines safety guardrails, phase gates, firewall safety, locking, restore points, abuse safety, secrets, UI/API exposure, job safety, canary policy, and AI safety checklist.

### `docs/ROADMAP.md`

Defines numbered phases, acceptance gates, MVP scope, stop conditions, and required tests by risk area.

### `docs/DATA_MODEL.md`

Defines PostgreSQL schema contract, table groups, relationships, ownership by services, indexes, retention, imports, and acceptance checklist.

### `docs/FIREWALL.md`

Defines firewall planner contract, apply modes, chain model, NAT, backend guard, plan/diff/apply/rollback lifecycle, doctor requirements, and tests.

### `docs/ABUSE.md`

Defines mandatory one-hour miner-abuse state machine, coverage requirements, exemption rules, hard/unhard behavior, evidence sources, reports, failure behavior, and tests.

### `docs/PHASE_0.md`

Defines documentation-only architecture freeze.

### `docs/PHASE_1.md`

Defines preflight and bootstrap without traffic changes.

### `docs/PHASE_1_SERVER_RUNBOOK.md`

Records the accepted Phase 1 bootstrap result for the target server and current operational warning about time sync.

### `docs/INTRANET_INSTALL.md`

Defines the safe workflow for servers without direct GitHub or internet access.

### `docs/AI_PHASE_2_TASK.md`

Defines the active Phase 2 implementation boundary for AI coding agents.

## Current Roadmap Snapshot

```text
Phase 0  — Architecture Freeze
Phase 1  — Preflight + Bootstrap Without Traffic Changes
Phase 2  — PostgreSQL + Config + Domain Model
Phase 3  — CLI + Internal API Foundation
Phase 4  — Compose Forward-only + Proxy Doctor
Phase 5  — Customer CRUD in DB Only
Phase 6  — Firewall Planner + Apply/Verify/Rollback
Phase 7  — Usage + Policy/Reject Accounting
Phase 8  — Abuse 1h Core
Phase 9  — Check / Report / Diagnostics
Phase 10 — Session / Worker / Policy Timeline
Phase 11 — Local Web UI Read-only
Phase 12 — UI Actions With Confirmation
Phase 13 — Telegram Notifications, Read-only Commands, Restricted Actions
```

## Stop Conditions

Stop and revise if any change introduces:

1. firewall apply before Phase 6
2. abuse automation before Phase 8
3. customer rules during Phase 1
4. NAT redirects during Phase 1
5. backend public exposure
6. UI direct DB write
7. Telegram shell command execution
8. bypassing `firewall.apply_mode=plan_only`
9. production TSV/SQLite source of truth
10. silent abuse scan exclusion
11. ad-hoc production firewall mutation
12. missing event/audit for mutation
13. missing restore point for dangerous action

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.
