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
7. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only Phase 6-D1 boundary contract)

`AGENTS.md` is the general implementation contract.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the authoritative current phase guard.
`docs/AI_CODING_RULES.md` defines active AI coding rules and stop conditions.
`docs/AI_PHASE_6_TASK.md` and `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` define the current Phase 6 firewall-planner/offline-apply-contract boundary.
This file is the documentation map.

## Core Contracts

Read these before implementation work:

1. `docs/ARCHITECTURE.md`
2. `docs/SAFETY.md`
3. `docs/ROADMAP.md`
4. `docs/DATA_MODEL.md`
5. `docs/TAXONOMY.md`
7. `docs/FIREWALL.md`
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

Current Phase 6 step:

```text
Phase 6-C accepted (offline apply-gate readiness/review only)
next safe step: Phase 6-D0 / Phase 6-D documentation/test-only live-apply boundary review
```

Read:

1. `docs/PHASE_STATUS.md`
2. `docs/AI_PHASE_6_TASK.md`
3. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only)
4. `docs/FIREWALL.md`
5. `docs/BACKEND_PORT_POLICY.md`
6. `docs/PHASE_6_C0_APPLY_GATE_READINESS.md`
6. `docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md`
7. `docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md`
8. `docs/REMAINING_PHASE_PLAN.md`
8. `docs/SAFETY.md`
9. `docs/DATA_MODEL.md`
9. `docs/TAXONOMY.md`
10. `docs/ABUSE.md`
11. `docs/PHASE_5_FINAL_ACCEPTANCE.md`
12. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`
13. `docs/OBSERVABILITY_HASHRATE.md`
14. `docs/INTRANET_INSTALL.md`

Phase 6-C is accepted as offline apply-gate readiness/review only. The next safe step is Phase 6-D0 / Phase 6-D documentation/test-only boundary review. It may align docs/tests and inspect offline artifacts only. It must not create NAT redirects, apply firewall rules, execute `iptables-save`, execute `iptables-restore`, activate usage/abuse automation, add lifecycle timers, add block/pause runtime, add worker runtime, expose UI/API publicly, or enable Telegram.

`docs/PHASE_6_C0_APPLY_GATE_READINESS.md` is a future live apply gate readiness contract and manual canary runbook only; it does not authorize live apply in the current phase.

`docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md` is a future apply gate risk matrix and operator approval checklist only; it does not authorize live apply.

Historical note: Phase 6-A established planner/model/diff foundations. Phase 5 — Customer CRUD in DB Only included documentation-only contract clarification for customer lifecycle, control rules, worker policy, and future abuse coverage. These historical notes do not authorize runtime behavior now.

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
6. `docs/SAFETY.md`
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
- no runtime block/pause command in Phase 5
- no worker scanner or worker enforcement in Phase 5
- no usage or abuse automation
- customer validation must avoid future schema/service dead ends for lifecycle, controls, and worker policy

### Firewall, proxy, backend port, or current Phase 6 work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/AI_PHASE_6_TASK.md`
5. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only)
6. `docs/SAFETY.md`
7. `docs/FIREWALL.md`
8. `docs/BACKEND_PORT_POLICY.md`
8. `docs/DATA_MODEL.md`
9. `docs/CONTROL_RULES.md`
10. relevant phase/domain document

Rules:

- no ad-hoc production firewall mutation
- desired model first
- plan/diff before apply
- restore point before any future apply
- atomic apply through `iptables-restore` only after a future explicit apply gate
- backend direct external exposure is critical
- backend internal reachability failure is also critical
- never hide backend ports by breaking valid internal paths
- current post-Phase-6-C boundary must remain offline/artifact-only/inspection-only until a dedicated apply gate is accepted
- current post-Phase-6-C boundary must not execute `iptables-save`, `iptables-restore`, live apply, live rollback, live verify, or conntrack flush

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
6. `docs/SAFETY.md`
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

### `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md`

Defines the active Phase 6 firewall-planner/offline-apply-contract boundary.

### `docs/AI_PHASE_5_TASK.md`

Historical active task for accepted Phase 5 Customer CRUD in DB Only.

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
2. live firewall read/write dependency before explicit apply gate acceptance
3. `iptables-save` execution before explicit apply gate acceptance
4. `iptables-restore` execution before explicit apply gate acceptance
5. conntrack flush before the relevant runtime gate
6. abuse automation before Phase 8
7. customer rules before their phase
8. NAT redirects before their phase
9. backend public exposure
10. backend internal reachability failure
11. UI direct DB write
12. Telegram shell command execution
13. bypassing `firewall.apply_mode=plan_only`
14. production TSV/SQLite source of truth
15. silent abuse scan exclusion
16. ad-hoc production firewall mutation
17. missing event/audit for mutation
18. missing restore point for dangerous action
19. proxy data-plane activation outside accepted runtime gates
20. high-volume share/hash-rate collection before retention and partitioning review
21. UI charts reading raw high-volume share events directly
22. worker/block/pause/usage/abuse runtime before accepted phase
23. public v2rayA UI exposure
24. public backend exposure

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.


Phase 6-C is accepted as offline apply-gate readiness/review only and does not authorize live apply.
