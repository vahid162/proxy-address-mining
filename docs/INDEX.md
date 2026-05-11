# Documentation Index

Status: active documentation map

This index defines the required reading path for `proxy-address-mining` for human contributors and AI coding agents.

## Start Here

Read these first:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`
6. `docs/AI_PHASE_6_TASK.md`

`AGENTS.md` is the general implementation contract.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the current phase guard.
`docs/AI_CODING_RULES.md` defines the current AI coding rules and stop conditions.
`docs/AI_PHASE_6_TASK.md` defines the current Phase 6-A planner-first task boundary.
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
10. `docs/CUSTOMER_LIFECYCLE.md`
11. `docs/CONTROL_RULES.md`
12. `docs/WORKER_POLICY.md`

## Current Phase Contracts

Current accepted phase:

```text
Phase 5 — Customer CRUD in DB Only accepted on farm5
```

Current working phase:

```text
Phase 6 — Firewall Planner
```

Read:

1. `docs/PHASE_STATUS.md`
2. `docs/AI_PHASE_6_TASK.md`
3. `docs/FIREWALL.md`
4. `docs/BACKEND_PORT_POLICY.md`
5. `docs/SAFETY.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. `docs/ABUSE.md`
9. `docs/PHASE_5_FINAL_ACCEPTANCE.md`
10. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`
11. `docs/OBSERVABILITY_HASHRATE.md`
12. `docs/INTRANET_INSTALL.md`

The current step is Phase 6-A repository cleanup plus firewall planner contract and desired-state model work.
It must not create NAT redirects, apply firewall rules, activate usage/abuse automation, add lifecycle timers, add block/pause runtime, add worker runtime, expose UI/API publicly, or enable Telegram.

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
11. `docs/CUSTOMER_LIFECYCLE.md`
12. `docs/CONTROL_RULES.md`
13. `docs/WORKER_POLICY.md`
14. all phase/domain documents affected by the change

### Phase 5 Customer CRUD DB-only work

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/AI_PHASE_5_TASK.md`
6. `docs/CUSTOMER_LIFECYCLE.md`
7. `docs/DATA_MODEL.md`
8. `docs/TAXONOMY.md`
9. `docs/CONTROL_RULES.md`
10. `docs/WORKER_POLICY.md`
11. `docs/SAFETY.md`
12. `docs/ABUSE.md`

Rules:

- customer mutations are DB-only
- customer lifecycle is DB-only in Phase 5
- first-connect activation is contract-only in Phase 5
- auto-expire and auto-delete are contract/report/preview only in Phase 5
- soft-delete means `status=deleted` and `deleted_at=now()`
- no customer NAT redirects
- no customer firewall rules
- no firewall apply
- no lifecycle timer
- no block/pause runtime
- no worker runtime
- no usage or abuse automation
- customer validation must avoid future schema/service dead ends for lifecycle, controls, and worker policy

### Customer lifecycle work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/AI_PHASE_5_TASK.md`
5. `docs/CUSTOMER_LIFECYCLE.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. `docs/ABUSE.md`
9. relevant phase/domain document

Rules:

- `activation_mode` is explicit: `immediate` or `first_connect`
- first-connect runtime detection is future-only
- do not add `pending_activation` customer status
- auto-expire runtime is forbidden in Phase 5
- auto-delete runtime is forbidden in Phase 5
- delete is soft-delete by default
- active customers must remain abuse-evaluable
- DB-only lifecycle reports and dry-run previews must not mutate firewall, NAT, timers, or runtime state

### Database or migration work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SAFETY.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. `docs/CUSTOMER_LIFECYCLE.md`
9. `docs/CONTROL_RULES.md`
10. `docs/WORKER_POLICY.md`
11. relevant phase/domain document

Rules:

- PostgreSQL is source of truth.
- Migrations are required for schema changes.
- Future production migrations should use explicit Alembic operations.
- Do not run production migrations until reviewed and explicitly approved.
- Control-rule and worker-routing migrations are not authorized by documentation-only contracts.
- On farm5, run Alembic from `/opt/mpf-py-src`, not from `/root`.

### Firewall, proxy, or backend port work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/AI_PHASE_6_TASK.md`
5. `docs/SAFETY.md`
6. `docs/FIREWALL.md`
7. `docs/BACKEND_PORT_POLICY.md`
8. `docs/DATA_MODEL.md`
9. `docs/CONTROL_RULES.md`
10. relevant phase/domain document

Rules:

- no ad-hoc production firewall mutation
- desired model first
- plan/diff before apply
- restore point before apply
- atomic apply through `iptables-restore`
- backend direct external exposure is critical
- backend internal reachability failure is also critical
- never hide backend ports by breaking valid internal paths
- Phase 6-A must remain planner/model/diff/test only until a dedicated apply gate is accepted

### Hash-rate, share, worker, or observability work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/DATA_MODEL.md`
5. `docs/TAXONOMY.md`
6. `docs/OBSERVABILITY_HASHRATE.md`
7. `docs/WORKER_POLICY.md`
8. relevant phase/domain document

Rules:

- accepted/rejected hash-rate per device is a future first-class capability
- do not implement it as UI-only calculations
- do not collect high-volume share events without retention and partitioning policy
- UI charts must read aggregate samples, not raw high-volume events
- worker name alone is not a guaranteed physical device identity
- worker enforcement is future-only until evidence and adapter phases are accepted

### Control rules, block, pause, or worker policy work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/SAFETY.md`
5. `docs/DATA_MODEL.md`
6. `docs/TAXONOMY.md`
7. `docs/CONTROL_RULES.md`
8. `docs/WORKER_POLICY.md`
9. `docs/FIREWALL.md`
10. `docs/ABUSE.md`
11. relevant phase/domain document

Rules:

- runtime block/pause commands are future work
- worker scanner or worker enforcement are future work
- control rules are future intent, not firewall rules by themselves
- worker blocking must not be modeled as firewall-only
- abuse coverage for all active customers must remain intact

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
9. `docs/CUSTOMER_LIFECYCLE.md`
10. `docs/CONTROL_RULES.md`
11. `docs/WORKER_POLICY.md`
12. relevant phase/domain document

Rules:

- all active customers in all enabled lanes are scanned
- no silent skip
- farms-over alone must not harden
- worker-over alone must not harden
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
- runtime jobs for lifecycle, controls, worker scanning, usage, or abuse remain forbidden until accepted phases

## Documentation Summary

### `docs/PHASE_STATUS.md`

Defines the accepted phase, current working phase, allowed work, forbidden work, and next safe step.

### `docs/AI_PHASE_6_TASK.md`

Defines Phase 6-A cleanup and firewall planner-first boundaries.

### `docs/AI_PHASE_5_TASK.md`

Historical active task for accepted Phase 5 Customer CRUD in DB Only.

### `docs/CUSTOMER_LIFECYCLE.md`

Defines accepted Phase 5 customer lifecycle contracts for activation modes, first-connect deferral, auto-expire and auto-delete deferral, soft-delete, customer_key, DB-only reports, dry-run expectations, and abuse coverage preservation.

### `docs/CONTROL_RULES.md`

Defines future control-intent concepts for block, pause, whitelist, rate-limit, worker block, worker route, and notify-only behavior. It has no current runtime effect.

### `docs/WORKER_POLICY.md`

Defines the future worker policy and worker routing boundary. It forbids firewall-only worker blocking and keeps worker enforcement future-only until evidence and adapter phases are accepted.

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
Phase 4 Runtime — Limited Proxy Runtime Startup
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

1. firewall apply before explicit Phase 6 apply gate acceptance
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
15. proxy data-plane activation outside accepted runtime gates
16. high-volume share/hash-rate collection before retention and partitioning review
17. UI charts reading raw high-volume share events directly
18. worker/block/pause/usage/abuse runtime before accepted phase
19. public v2rayA UI exposure
20. public backend exposure

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.
