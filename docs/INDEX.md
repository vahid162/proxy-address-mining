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
6. `docs/AI_PHASE_10_TASK.md`
7. `docs/REMAINING_PHASE_PLAN.md`

`AGENTS.md` is the general implementation contract.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the authoritative current phase guard.
`docs/AI_CODING_RULES.md` defines active AI coding rules and stop conditions.
`docs/AI_PHASE_8_TASK.md` and `docs/AI_PHASE_9_TASK.md` are historical/accepted context. `docs/AI_PHASE_10_TASK.md` is active/current.
Phase 6 documents remain historical/reference-only and non-authorizing.

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
Phase 9 — Check / Report / Diagnostics accepted on farm5
```

Current working phase:

```text
Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness
```

Current active add-on read first: `docs/AI_PHASE_10_TASK.md`.

Current Phase 10 step:

```text
Phase 10 planning/readiness foundation, report-only and non-mutating.
No real worker runtime, no background worker loop, no scheduler/timer, no collector, no live share ingestion, no production DB transition, no enforcement, no firewall apply, no iptables-restore, no customer NAT/customer firewall rules, no hard/soft block, no pause automation, no production traffic, no UI, no Telegram.
Fresh farm5 0.1.129 sync/test evidence is required after merge before any Phase 10 runtime/worker/scheduler/collector implementation PRs.
```

Read:

1. `docs/PHASE_STATUS.md`
2. `docs/AI_CODING_RULES.md`
3. `docs/AI_PHASE_10_TASK.md`
4. `docs/REMAINING_PHASE_PLAN.md`
5. `docs/SAFETY.md`
6. `docs/DATA_MODEL.md`
7. `docs/TAXONOMY.md`
8. `docs/ABUSE.md`
9. `docs/FIREWALL.md`
10. `docs/BACKEND_PORT_POLICY.md`
11. `docs/OBSERVABILITY_HASHRATE.md`
12. `docs/WORKER_POLICY.md`

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

- Phase 10 starts as planning/readiness only.
- report-only/read-only/non-mutating surfaces are allowed.
- no real worker runtime.
- no background worker loop.
- no scheduler/timer.
- no collector.
- no live share ingestion.
- no production DB transition.
- no enforcement.
- no firewall apply.
- no iptables-restore.
- no customer NAT/customer firewall rules.
- no hard/soft block.
- no pause automation.
- no production traffic.
- no UI.
- no Telegram.
- future runtime/worker/scheduler/collector implementation PRs require fresh farm5 sync/test evidence and explicit gates.

### Firewall, proxy, backend port, or apply-gate work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/SAFETY.md`
5. `docs/FIREWALL.md`
6. `docs/BACKEND_PORT_POLICY.md`
7. `docs/DATA_MODEL.md`
8. relevant phase/domain document

Rules:

- no ad-hoc production firewall mutation.
- desired model first.
- plan/diff before apply.
- restore point before any future apply.
- atomic apply through `iptables-restore` only after a future explicit apply gate.
- backend direct external exposure is critical.
- backend internal reachability failure is also critical.
- never hide backend ports by breaking valid internal paths.
- current boundary must not execute `iptables-save`, `iptables-restore`, live apply, live rollback, live verify, or conntrack flush unless a specific accepted gate authorizes it.

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
- hard/unhard must use restore points, events, audit, and firewall service after accepted gates.
- abuse automation remains forbidden unless explicitly accepted.

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
- every job writes `job_runs` after the accepted runtime gate.
- overlapping jobs use `scheduler_locks` after the accepted runtime gate.
- jobs call services, not direct DB/firewall logic.
- runtime jobs for lifecycle, controls, worker scanning, usage, or abuse remain forbidden until accepted phases.

## Documentation Summary

### `docs/PHASE_STATUS.md`

Defines the accepted phase, current working phase, allowed work, forbidden work, and next safe step.

### `docs/AI_PHASE_10_TASK.md`

Defines the active AI coding boundary for Phase 10 planning/readiness foundation work.

### `docs/AI_PHASE_9_TASK.md`

Historical active task for accepted Phase 9 Check / Report / Diagnostics.

### `docs/AI_PHASE_8_TASK.md`

Historical active task for accepted Phase 8 Abuse 1h Core.

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

1. firewall apply before explicit apply gate acceptance
2. live firewall read/write dependency before explicit apply gate acceptance
3. `iptables-save` execution before explicit apply gate acceptance
4. `iptables-restore` execution before explicit apply gate acceptance
5. conntrack flush before the relevant runtime gate
6. abuse automation without explicit acceptance
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
25. Phase 10 runtime/worker/scheduler/collector implementation before fresh farm5 sync/test evidence and explicit gate

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.
