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
6. `docs/AI_PHASE_11_TASK.md`
7. `docs/PRODUCTION_ACTIVATION_GATE.md`
8. `docs/AI_PHASE_10_TASK.md` (accepted Phase 10 context)
9. `docs/REMAINING_PHASE_PLAN.md`

`AGENTS.md` is the general implementation contract.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the authoritative current phase guard.
`docs/AI_CODING_RULES.md` defines active AI coding rules and stop conditions.
`docs/AI_PHASE_11_TASK.md` and `docs/PRODUCTION_ACTIVATION_GATE.md` define the current Phase 11 planning/readiness boundary.
`docs/AI_PHASE_10_TASK.md` is accepted Phase 10 context and is not the active implementation target.

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
Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
```

Current working phase:

```text
Phase 11 — Production / Customer Activation Gate planning/readiness
```

Current active add-on read first:

```text
docs/AI_PHASE_11_TASK.md
docs/PRODUCTION_ACTIVATION_GATE.md
```

Historical/reference-only context:

```text
docs/AI_PHASE_10_TASK.md
docs/AI_PHASE_9_TASK.md
docs/AI_PHASE_8_TASK.md
Phase 6 apply-gate and apply-slice documents
```

## Current Phase 11 Boundary

```text
Phase 11 is planning/readiness only.
Production activation is not enabled.
Controlled CLI canary is not authorized yet.
Limited real customer onboarding is not authorized yet.
docs/PHASE_STATUS.md is authoritative for active phase language.
```

Forbidden in the current boundary:

```text
production traffic
controlled CLI canary execution
limited real customer onboarding
firewall apply
iptables-restore
customer NAT/customer firewall rules
abuse automation runner
real worker runtime
scheduler/timer
collector daemon
production DB execution
hard/soft block automation
pause automation
UI
Telegram
```

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

### Phase 11 production/customer activation work

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/AI_PHASE_11_TASK.md`
6. `docs/PRODUCTION_ACTIVATION_GATE.md`
7. `docs/SAFETY.md`
8. `docs/FIREWALL.md`
9. `docs/BACKEND_PORT_POLICY.md`
10. `docs/ABUSE.md`
11. `docs/DATA_MODEL.md`
12. `docs/TAXONOMY.md`
13. relevant phase/domain document

Rules:

- Phase 11 starts as planning/readiness only.
- no controlled CLI canary until explicit Phase 11 gate.
- no production traffic until explicit Phase 11 gate.
- no firewall apply or `iptables-restore` until explicit controlled gate.
- customer NAT/customer firewall rules must go through the planner only after the explicit gate.
- abuse 1h runtime coverage must be proven before real customer activation.
- restart/container-order safety and rollback/restore-plan evidence are required before acceptance.
- UI and Telegram remain disabled in Phase 11.

### Phase 10 session, worker, policy, share timeline, or enforcement-boundary work

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/AI_PHASE_10_TASK.md`
6. `docs/SAFETY.md`
7. `docs/DATA_MODEL.md`
8. `docs/TAXONOMY.md`
9. `docs/OBSERVABILITY_HASHRATE.md`
10. `docs/WORKER_POLICY.md`
11. `docs/ABUSE.md`
12. relevant phase/domain document

Rules:

- Phase 10 is accepted context.
- do not reopen Phase 10 runtime, worker, scheduler, collector, or enforcement behavior unless `docs/PHASE_STATUS.md` explicitly authorizes it.
- worker enforcement remains Phase 12.

### Customer CRUD DB-only work

Read:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/CUSTOMER_LIFECYCLE.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. `docs/CONTROL_RULES.md`
9. `docs/WORKER_POLICY.md`
10. `docs/SAFETY.md`
11. `docs/ABUSE.md`

Rules:

- customer mutations remain DB-only unless the current gate explicitly authorizes activation.
- no customer NAT redirects.
- no customer firewall rules.
- no firewall apply.
- no lifecycle timer unless accepted by the current phase gate.
- no worker scanner or worker enforcement before the relevant accepted phase.

### Firewall, proxy, or backend-port work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/SAFETY.md`
5. `docs/FIREWALL.md`
6. `docs/BACKEND_PORT_POLICY.md`
7. `docs/PRODUCTION_ACTIVATION_GATE.md`
8. `docs/DATA_MODEL.md`
9. `docs/CONTROL_RULES.md`
10. relevant phase/domain document

Rules:

- no ad-hoc production firewall mutation.
- desired model first.
- plan/diff before apply.
- restore point before any future apply.
- atomic apply through `iptables-restore` only after an explicit accepted gate.
- backend direct external exposure is critical.
- backend internal reachability failure is also critical.
- never hide backend ports by breaking valid internal paths.

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

- accepted/rejected hash-rate per device is a future first-class capability.
- do not implement it as UI-only calculations.
- do not collect high-volume share events without retention and partitioning policy.
- UI charts must read aggregate samples, not raw high-volume events.
- worker name alone is not a guaranteed physical device identity.
- worker enforcement is future-only until evidence and adapter phases are accepted.

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

- all active customers in all enabled lanes are scanned.
- no silent skip.
- farms-over alone must not harden.
- worker-over alone must not harden.
- sustained miner-abuse hardens after about 3600 seconds.
- hard/unhard must use restore points, events, audit, and firewall service.
- abuse automation remains forbidden until the current gate explicitly authorizes it.

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

- interfaces are thin.
- no direct DB writes.
- no direct firewall commands.
- call services only.
- UI/API bind local-only in early phases.
- Telegram starts notification-only.
- UI and Telegram remain future phases after backend activation and worker enforcement boundaries.

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

- use systemd timers.
- no mixed cron/systemd model.
- every job writes `job_runs`.
- overlapping jobs use `scheduler_locks`.
- jobs call services, not direct DB/firewall logic.
- runtime jobs for lifecycle, controls, worker scanning, usage, or abuse remain forbidden until accepted phases.

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
Phase 11  — Production / Customer Activation Gate
Phase 12  — Worker Policy Enforcement
Phase 13  — Local UI
Phase 14  — Operator UI Actions
Phase 15  — Telegram
```

## Stop Conditions

Stop and revise if any change introduces:

1. production traffic before explicit Phase 11 authorization
2. controlled CLI canary before explicit Phase 11 authorization
3. limited real customer onboarding before explicit Phase 11 authorization
4. firewall apply before explicit Phase 11 controlled gate acceptance
5. live firewall write dependency before explicit controlled gate acceptance
6. `iptables-restore` execution before explicit controlled gate acceptance
7. conntrack flush before the relevant runtime gate
8. abuse automation before the relevant accepted runtime gate
9. customer rules before their accepted gate
10. NAT redirects before their accepted gate
11. backend public exposure
12. backend internal reachability failure
13. UI direct DB write
14. Telegram shell command execution
15. bypassing `firewall.apply_mode=plan_only`
16. production TSV/SQLite source of truth
17. silent abuse scan exclusion
18. ad-hoc production firewall mutation
19. missing event/audit for mutation
20. missing restore point for dangerous action
21. proxy data-plane activation outside accepted runtime gates
22. high-volume share/hash-rate collection before retention and partitioning review
23. UI charts reading raw high-volume share events directly
24. worker/block/pause/usage/abuse runtime before accepted phase
25. public v2rayA UI exposure
26. public backend exposure

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.
