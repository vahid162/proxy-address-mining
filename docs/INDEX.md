Phase 11 operational completion full CLI production scope note (0.1.245): Phase 11 remains accepted on farm5 for the controlled_cli_limited BTC boundary. The active working gate is now Phase 11 operational completion — Full CLI Production Operations; Phase 12 Worker Policy Enforcement is blocked until final operational completion acceptance.

Phase 11 controlled-boundary clarification note (0.1.235): clarified README and agent-rule wording after final acceptance; runtime behavior and conservative config defaults remain unchanged.
Phase 11 final acceptance note (0.1.234, historical transition context): Phase 11 is accepted on farm5 only for controlled_cli_limited BTC operation. Phase 12 does not start immediately; the current Phase 11 operational completion gate must pass first.
Phase 11 planning/readiness note (0.1.231): recorded farm5 0.1.230 observation-window/final-readiness READY evidence and added a read-only limited acceptance decision gate while keeping Current State and all dangerous gates closed.
Phase 11 planning/readiness note (0.1.230): recorded farm5 0.1.229 limited activation observation/review READY evidence and added read-only limited customer observation-window and final-acceptance readiness-planning reports while keeping Current State closed.
Phase 11 planning/readiness note (0.1.208): recorded farm5 0.1.206 runtime-path BLOCKED evidence and added non-mutating single-customer runtime probe diagnostics while keeping production/miner/acceptance gates closed.
Phase 11 planning/readiness note (0.1.205): recorded farm5 0.1.204 controlled single-customer firewall/NAT apply execution evidence for limited-btc-001/20101 and added non-mutating post-apply evidence classifier while keeping global gates closed.
Phase 11 planning/readiness note (0.1.204): added controlled single-customer firewall apply execution package/execute path and recorded 0.1.203 apply-gate evidence while keeping global gates closed.
# Documentation Index

Phase 11 controlled artifact reapply note (0.1.249): the resolver, desired-state, plan/package, guarded executor, verification, helper, and evidence collector are implemented for exactly the two accepted BTC customers, but no farm5 mutation has been performed. Next step: `sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5`; restart/autostart proof and Full CLI Production Operations remain unaccepted, Phase 12/worker enforcement/UI/Telegram remain blocked. See `docs/PHASE_11_CONTROLLED_ARTIFACT_REAPPLY_RUNBOOK.md`.

Phase 11 persistence alignment note (0.1.248): farm5 0.1.247 post-sync evidence showed healthy runtime containers/listeners and absent controlled customer firewall artifacts. The next step is `implement_controlled_artifact_reapply_execute_package`; restart/autostart proof remains `missing_or_partial`, Full CLI Production Operations is not accepted, and Phase 12/worker enforcement/UI/Telegram remain blocked. See `docs/PHASE_11_FARM5_0_1_247_PERSISTENCE_POST_SYNC_EVIDENCE.md`.

Status: active documentation map

This index defines the required reading path for `proxy-address-mining` for human contributors and AI coding agents.

## Start Here

Read these first:

1. `../AGENTS.md`
2. `../README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`
6. `docs/AI_SAFE_RUNTIME_FIRST.md`
7. `docs/AI_PHASE_8_TASK.md`
8. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only Phase 6-D1 boundary contract)
9. `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; non-authorizing)
10. `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md` (isolated/non-production harness contracts only; non-authorizing)
11. `docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; non-authorizing)
12. `docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md` (isolated/non-production hardening contract; non-authorizing)
13. `docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; non-authorizing)
14. `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md` (accepted step contract; isolated/non-production only, non-authorizing)
15. `docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; non-authorizing)
16. `docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md` (accepted, isolated/non-production only, non-authorizing)
17. `docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; non-authorizing)
18. `docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md` (accepted scope contract, documentation/test-only, non-authorizing)
19. `docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; non-authorizing)
20. `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md` (accepted planning scope, documentation/test-only, non-authorizing)
21. `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; documentation/test-only, non-authorizing)
22. `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md` (accepted scope, documentation/test-only, non-authorizing)
23. `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md` (accepted farm5 evidence; documentation/test-only, non-authorizing)
24. `docs/PHASE_6_APPLY_SLICE_1_LIVE_SNAPSHOT_READINESS_BOUNDARY.md` (planned readiness boundary, documentation/test-only, non-authorizing)
25. `docs/PHASE_6_APPLY_SLICE_2_RESTORE_LOCK_DB_APPLY_RECORD_READINESS.md` (planned readiness boundary, documentation/test-only, non-authorizing)
26. `docs/PHASE_6_APPLY_SLICE_3_CONTROLLED_NO_CUSTOMER_HARNESS.md` (planned contract, documentation/test-only, non-authorizing)
27. `docs/PHASE_6_APPLY_SLICE_4_MANUAL_CANARY_APPLY_GATE_PROPOSAL.md` (planned contract, documentation/test-only, non-authorizing)
28. `docs/PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md` (proposal/review contract only, documentation/test-only, non-authorizing)
29. `docs/REMAINING_PHASE_PLAN.md` (finite remaining project/Phase 8 plan aligned to PHASE_STATUS)

`AGENTS.md` is the general implementation contract.
`README.md` is the project overview.
`docs/PHASE_STATUS.md` is the authoritative current phase guard.
`docs/AI_CODING_RULES.md` defines active AI coding rules and stop conditions.
`docs/AI_PHASE_11_OPERATIONAL_COMPLETION_TASK.md` and `docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md` are active/current for Phase 11 operational completion — Full CLI Production Operations. Version 0.1.248 records current step `implement_controlled_artifact_reapply_execute_package` after farm5 0.1.247 showed healthy runtime containers/listeners but absent controlled customer firewall artifacts; restart/autostart proof and Full CLI Production Operations are not accepted without source-backed evidence. `docs/AI_PHASE_11_TASK.md`, `docs/PRODUCTION_ACTIVATION_GATE.md`, and `docs/AI_SAFE_RUNTIME_FIRST.md` remain Phase 11 controlled-boundary context. `docs/AI_PHASE_10_TASK.md` is accepted Phase 10 context. `docs/AI_PHASE_8_TASK.md`, `docs/AI_PHASE_9_TASK.md`, and Phase 6 documents below are historical/reference-only and non-authorizing unless `docs/PHASE_STATUS.md` explicitly reopens them.
This file is the documentation map.

Historical/reference note:

- `docs/HISTORICAL_COMPATIBILITY_ANCHORS.md` (historical compatibility/reference-only, non-authorizing; does not override `docs/PHASE_STATUS.md`)

- `docs/PHASE_11_FARM5_0_1_229_LIMITED_ACTIVATION_OBSERVATION_REVIEW_READY.md` — farm5 0.1.229 read-only limited activation observation/review READY evidence; non-authorizing.
- `docs/PHASE_11_FARM5_0_1_230_OBSERVATION_FINAL_READINESS_READY.md` — farm5 0.1.230 read-only observation-window/final-readiness READY evidence; non-authorizing.
- `docs/PHASE_11_FARM5_0_1_231_LIMITED_ACCEPTANCE_DECISION_READY.md` — farm5 0.1.231 limited acceptance decision READY evidence; non-authorizing.
- `docs/PHASE_11_FARM5_0_1_232_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY.md` — farm5 0.1.232 controlled boundary acceptance package READY evidence; non-authorizing.
- `docs/PHASE_11_FARM5_0_1_233_FINAL_ACCEPTANCE_PR_READINESS_READY.md` — farm5 0.1.233 final acceptance PR readiness READY evidence.
- `docs/PHASE_11_FINAL_ACCEPTANCE.md` — accepted controlled CLI-limited Phase 11 boundary and remaining restrictions.

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
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
```

Current working phase:

```text
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
```

Current active add-on read first: `docs/AI_PHASE_11_OPERATIONAL_COMPLETION_TASK.md`, `docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md`, `docs/AI_PHASE_11_TASK.md`, `docs/PRODUCTION_ACTIVATION_GATE.md`, and `docs/AI_SAFE_RUNTIME_FIRST.md` (active/current). `docs/AI_PHASE_10_TASK.md` remains accepted Phase 10 context.
Phase 6 documents below remain historical/reference/non-authorizing context.

Current Phase 11 step:

```text
Phase 12 Worker Policy Enforcement remains blocked until final Phase 11 operational completion acceptance.
UI, Telegram, worker enforcement, buyer panel, public API, and public backend exposure remain closed.
Full CLI Production Operations acceptance must prove the expanded matrix: restart/autostart proof, production customer lifecycle CLI execution, production firewall plan/apply/verify/rollback for real customer ports, production onboarding flow through CLI, production usage/report/check evidence, production abuse runner for all active customers in all enabled lanes, pause/block/expire-run operational controls, backup/restore drill, and final acceptance that sets production_traffic=cli_production and customer_onboarding_allowed=cli_production.
docs/PHASE_STATUS.md is authoritative for active phase language.
Until final acceptance, current production/onboarding gates remain controlled_cli_limited and direct/ad-hoc DB or firewall mutation remains forbidden.
Phase 10 is accepted context only unless docs/PHASE_STATUS.md explicitly reopens it.
Phase 6-G accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing.
Phase 6-H accepted as dedicated apply gate entry criteria / authorization boundary only, documentation/test-only and non-authorizing.

```

Read:

1. `docs/PHASE_STATUS.md`
2. `docs/AI_PHASE_6_TASK.md`
3. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only)
4. `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md`
5. `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md`
6. `docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md`
7. `docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md`
8. `docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md`
9. `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md`
10. `docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md`
11. `docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md`
12. `docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md`
13. `docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md`
14. `docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md`
15. `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`
16. `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md`
17. `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md`
18. `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md`
19. `docs/FIREWALL.md`
20. `docs/BACKEND_PORT_POLICY.md`
21. `docs/PHASE_6_C0_APPLY_GATE_READINESS.md`
22. `docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md`
23. `docs/PHASE_6_C_ACCEPTANCE_EVIDENCE.md`
24. `docs/REMAINING_PHASE_PLAN.md`
25. `docs/SAFETY.md`
26. `docs/DATA_MODEL.md`
27. `docs/TAXONOMY.md`
28. `docs/ABUSE.md`
29. `docs/PHASE_5_FINAL_ACCEPTANCE.md`
30. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`
31. `docs/OBSERVABILITY_HASHRATE.md`
32. `docs/INTRANET_INSTALL.md`

Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing.
Future dedicated Phase 6 apply gate remains not accepted and not authorized.
Reference: `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md` and `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md`.

Current Phase 11 read-first add-on: `docs/AI_PHASE_11_TASK.md`, `docs/PRODUCTION_ACTIVATION_GATE.md`, `docs/AI_SAFE_RUNTIME_FIRST.md`, `docs/SAFETY.md`, `docs/FIREWALL.md`, `docs/BACKEND_PORT_POLICY.md`, `docs/ABUSE.md`, `docs/DATA_MODEL.md`, and `docs/TAXONOMY.md`.
Current Phase 11A implementation document: `docs/PHASE_11A_PRODUCTION_READINESS_INVENTORY.md` (report-only, non-authorizing).

Current Phase Contracts add-on: `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`, `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md`, `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md`, and `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md` (documentation/test-only, non-authorizing).

Phase 6-F may define manual canary criteria, operator approval requirements, evidence templates, and rollback-readiness checks only. It does not authorize live firewall read/write, live apply/rollback/verify, `iptables-save`, `iptables-restore`, real adapters, DB apply writes, lock acquisition, restore point writes, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

`docs/PHASE_6_C0_APPLY_GATE_READINESS.md` is a future live apply gate readiness contract and manual canary runbook only; it does not authorize live apply in the current phase.

`docs/PHASE_6_C1_APPLY_GATE_RISK_MATRIX.md` is a future apply gate risk matrix and operator approval checklist only; it does not authorize live apply.

Historical note: Phase 6-A established planner/model/diff foundations. Phase 5 — Customer CRUD in DB Only included documentation-only contract clarification for customer lifecycle, control rules, worker policy, and future abuse coverage. These historical notes do not authorize runtime behavior now.

- `scripts/phase11_collect_restart_autostart_proof.sh` — read-only farm5 helper for Phase 11 restart/autostart proof evidence; it does not reboot, restart Docker/systemd, mutate DB/firewall, run iptables-restore, or flush conntrack.
- `scripts/phase11_diagnose_restart_autostart_persistence.sh` — read-only farm5 helper for diagnosing the Phase 11 post-reboot restart/autostart persistence gap; it captures MPF status, Docker listings, listeners, iptables-save snapshots, current artifact gate output, restart/autostart proof, and persistence diagnosis without runtime, DB, firewall, restore, or connection-table mutation.

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
7. `docs/AI_SAFE_RUNTIME_FIRST.md`
8. `docs/SAFETY.md`
9. `docs/FIREWALL.md`
10. `docs/BACKEND_PORT_POLICY.md`
11. `docs/ABUSE.md`
12. `docs/DATA_MODEL.md`
13. `docs/TAXONOMY.md`
14. relevant phase/domain document

Rules:

- Phase 11 is planning/readiness only.
- no production traffic, no controlled CLI canary, and no limited real customer onboarding.
- no firewall apply and no iptables-restore.
- no customer NAT/customer firewall rules.
- no abuse automation runner.
- no real worker runtime, scheduler/timer, or collector daemon.
- no unrestricted production DB execution.
- no hard/soft block automation and no pause automation.
- no UI and no Telegram.
- `docs/AI_PHASE_10_TASK.md` is accepted Phase 10 context only and not an active implementation target unless `docs/PHASE_STATUS.md` reopens it.

### Phase 10 session, worker, policy, share timeline, or enforcement-boundary context

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
- no production traffic.
- no firewall apply.
- no iptables-restore.
- no customer NAT/customer firewall rules.
- no hard/soft block automation.
- no pause automation.
- no UI.
- no Telegram.

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

### Firewall, proxy, backend port, or historical Phase 6 context work

Read:

1. `../AGENTS.md`
2. `docs/PHASE_STATUS.md`
3. `docs/AI_CODING_RULES.md`
4. `docs/AI_PHASE_6_TASK.md`
5. `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` (non-authorizing, documentation/test-only)
6. `docs/SAFETY.md`
7. `docs/FIREWALL.md`
8. `docs/BACKEND_PORT_POLICY.md`
9. `docs/DATA_MODEL.md`
10. `docs/CONTROL_RULES.md`
11. relevant phase/domain document

Rules:

- no ad-hoc production firewall mutation
- desired model first
- plan/diff before apply
- restore point before any future apply
- atomic apply through `iptables-restore` only after a future explicit apply gate
- backend direct external exposure is critical
- backend internal reachability failure is also critical
- never hide backend ports by breaking valid internal paths
- historical post-Phase-6-C boundary must remain offline/artifact-only/inspection-only until a dedicated apply gate is accepted
- historical post-Phase-6-C boundary must not execute `iptables-save`, `iptables-restore`, live apply, live rollback, live verify, or conntrack flush unless the current phase gate explicitly authorizes it

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
- abuse automation remains forbidden until the relevant explicit Phase 11 runtime/production gate authorizes it

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
- UI remains future phase work and disabled now
- Telegram starts notification-only in its future phase and remains disabled now

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

### `docs/AI_PHASE_11_TASK.md`

Defines the active AI coding boundary for Phase 11 production/customer activation gate planning/readiness.

### `docs/PRODUCTION_ACTIVATION_GATE.md`

Defines the current production/customer activation boundary and closed-gate restrictions.

### `docs/AI_SAFE_RUNTIME_FIRST.md`

Defines the Phase 11 AI-safe Runtime-first operating principle. It does not override `docs/PHASE_STATUS.md` and does not open any production, firewall, customer, abuse, worker, UI, or Telegram gate by itself.

### `docs/AI_PHASE_10_TASK.md`

Defines accepted Phase 10 context (historical/reference-only unless `docs/PHASE_STATUS.md` reopens it).

### `docs/AI_PHASE_6_TASK.md`

Defines the active AI coding boundary for current Phase 6 planner/offline contract work and references the Phase 6-D1 boundary. Historical/reference-only in current Phase 11 unless docs/PHASE_STATUS.md explicitly reopens it.

### `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md`

Defines the non-authorizing documentation/test-only live-apply boundary contract for Phase 6-D1.

### `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md`

Defines the accepted farm5 evidence for Phase 6-D1 and confirms that the next safe step is Phase 6-E0 isolated/non-production planning only. It does not authorize live apply, live firewall reads/writes, iptables-save, iptables-restore, customer NAT/firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md`

Defines Phase 6-E0 isolated/non-production-only harness contracts for deterministic fake/no-op ordering tests. It does not authorize host production firewall mutation, live firewall read/write, iptables-save, iptables-restore, apply, rollback, or verify.

### `docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-E0 and confirms that the next safe step is Phase 6-E1 isolated/non-production hardening only. It does not authorize live apply, live firewall reads/writes, iptables-save, iptables-restore, real iptables adapters, customer NAT/firewall rules, production traffic, DB apply writes, locks, restore points, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md`

Defines Phase 6-E1 isolated/non-production-only harness hardening scope for fake/no-op contracts and tests. It does not authorize host firewall mutation, live apply/rollback/verify, live firewall read/write, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, or restore points.

### `docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-E1 and confirms that the next safe step is Phase 6-E2 isolated/non-production boundary planning only. It does not authorize live apply, live firewall reads/writes, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md`

Defines the accepted Phase 6-E2 isolated/non-production evidence package and boundary planning contract. It remains non-authorizing. It does not authorize live apply, live firewall read/write, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-E2 and confirms that the historical next safe step was Phase 6-E3 isolated/non-production evidence review/checklist only. It does not authorize live apply, live firewall reads/writes, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md`

Defines the planned Phase 6-E3 isolated/non-production evidence review and non-authorizing gate checklist. It does not mark Phase 6-E3 accepted. It does not authorize live apply, live firewall read/write, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-E3 and confirms that the next planned step is Phase 6-F manual canary gate definition, documentation/test-only and non-authorizing. It does not authorize live apply, live firewall reads/writes, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md`

Defines the accepted Phase 6-F manual canary gate definition scope only (documentation/test-only, non-authorizing). It allows only manual canary criteria, operator approval requirements, evidence templates, rollback-readiness checks, backend exposure preconditions, local-only runtime preconditions, and safety assertions. It does not authorize live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore point writes, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-F as historical context only; next planned implementation sub-step is Apply Slice 1 live snapshot readiness boundary (planned, documentation/test-only, non-authorizing). This acceptance does not authorize live apply, live firewall reads/writes, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md`

Defines planned Phase 6-G controlled live apply gate planning / pre-apply review scope only (documentation/test-only, non-authorizing). It does not authorize live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real iptables adapters, DB apply writes, locks, restore point writes, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-G and confirms Phase 6-G is accepted as documentation/test-only and non-authorizing. It does not authorize live apply, live firewall read/write, iptables-save, iptables-restore, real adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md`

Defines accepted Phase 6-H dedicated apply gate entry criteria / authorization boundary only. It is documentation/test-only and non-authorizing. It does not authorize live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, DB apply writes, locks, restore point writes, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

Defines `docs/PHASE_6_APPLY_SLICE_1_LIVE_SNAPSHOT_READINESS_BOUNDARY.md` for the planned Phase 6 Apply Slice 1 live snapshot readiness boundary only. It is documentation/test-only and non-authorizing. It does not authorize live firewall read, iptables-save, live firewall write/apply/rollback/verify, iptables-restore, real adapters, subprocess firewall calls, DB writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

### `docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md`

Records farm5 acceptance evidence for Phase 6-H. Confirms Phase 6-H is accepted as documentation/test-only and non-authorizing. It does not authorize live apply, live firewall read/write, iptables-save, iptables-restore, real adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.


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
Phase 11  — Production / Customer Activation Gate
Phase 11 operational completion — post-acceptance completion gate before Phase 12

- `AI_PHASE_11_OPERATIONAL_COMPLETION_TASK.md`
- `PHASE_11_OPERATIONAL_COMPLETION_GATE.md`

Phase 12  — Worker Policy Enforcement
Phase 13  — Local UI
Phase 14  — Operator UI Actions
Phase 15  — Telegram
```

## Stop Conditions

Stop and revise if any change introduces:

1. production traffic before explicit Phase 11 authorization
2. controlled CLI canary execution before explicit Phase 11 authorization
3. limited real customer onboarding before explicit Phase 11 authorization
4. firewall apply before explicit Phase 11 controlled gate acceptance
5. `iptables-restore` execution before explicit Phase 11 controlled gate acceptance
6. customer NAT/customer firewall rules before explicit gate acceptance
7. abuse automation runner before relevant Phase 11 runtime gate
8. runtime worker/scheduler/collector execution before explicit gate
9. UI before its later phase
10. Telegram before its later phase
11. backend public exposure
12. backend internal reachability failure
13. bypassing `firewall.apply_mode=plan_only`
14. production TSV/SQLite source of truth
15. ad-hoc production firewall mutation
16. missing event/audit for mutation
17. missing restore point for dangerous action
18. high-volume share/hash-rate collection before retention and partitioning review
19. public v2rayA UI exposure
20. public backend exposure
21. silent abuse scan exclusion
22. worker/block/pause/usage/abuse runtime before accepted phase
23. proxy data-plane activation outside accepted runtime gates

Historical/reference-only stop-condition notes from earlier Phase 6/8/10 materials do not authorize current-phase runtime behavior.

## Final Rule

When in doubt, read the stricter document and choose the safer implementation.


Phase 6-C is accepted as offline apply-gate readiness/review only and does not authorize live apply.


Documentation Summary: docs/PHASE_6_APPLY_SLICE_2_RESTORE_LOCK_DB_APPLY_RECORD_READINESS.md defines the planned Phase 6 Apply Slice 2 restore point, lock, and DB apply record readiness boundary only. It is documentation/test-only and non-authorizing. It does not authorize restore point writes, lock acquisition, DB apply writes, DB apply records, migrations, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.


Documentation Summary: docs/PHASE_6_APPLY_SLICE_3_CONTROLLED_NO_CUSTOMER_HARNESS.md defines the planned controlled no-customer harness contract only (documentation/test-only, non-authorizing). It does not authorize no-customer apply, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, restore point writes, lock acquisition, DB apply writes/records, migrations, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.


Historical Phase 7 planning/readiness document: `docs/AI_PHASE_7_TASK.md`.

- docs/AI_PHASE_8_TASK.md


Current phase gate flags:
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no

Historical compatibility note: previous Current Phase 8 step remains reference-only and non-authorizing in Phase 11.

Compatibility note: previous step was the Phase 8 abuse dry-run evaluator package (historical/reference-only).

Compatibility note: previous step also included the Phase 8 abuse evidence/reporting contract package (historical/reference-only).

DB-only controlled transition readiness package

Historical compatibility anchor: DB-only controlled transition execution package.



Historical compatibility anchor: runtime/worker integration readiness package.


Historical compatibility note: previous Current Phase 8 step remains reference-only and non-authorizing in Phase 11.


Current Phase 11B implementation document: `docs/PHASE_11B_CANARY_PLAN_REPORT.md` (report-only, non-authorizing).

Current Phase 11 evidence documents: `docs/PHASE_11_FARM5_0_1_143_SYNC_TEST_EVIDENCE.md` (farm5 sync/test evidence for Phase 11A + 11B, report-only, non-authorizing) and `docs/PHASE_11_FARM5_0_1_145_SYNC_TEST_EVIDENCE.md` (farm5 sync/test evidence for Phase 11C controlled activation harness, non-authorizing for Phase 11D/runtime execution).


Current Phase 11C implementation document: `docs/PHASE_11C_CONTROLLED_ACTIVATION_HARNESS.md` (controlled harness, non-mutating, non-authorizing).

- `docs/PHASE_11D_MANUAL_CANARY_ACCEPTANCE_PACKAGE.md`


Current Phase 11 evidence docs include:
- `docs/PHASE_11_FARM5_0_1_143_SYNC_TEST_EVIDENCE.md`
- `docs/PHASE_11_FARM5_0_1_145_SYNC_TEST_EVIDENCE.md`
- `docs/PHASE_11_FARM5_0_1_147_SYNC_TEST_EVIDENCE.md`
- `docs/PHASE_11_FARM5_0_1_149_SYNC_TEST_EVIDENCE.md`
- `docs/PHASE_11_FARM5_0_1_151_SYNC_TEST_EVIDENCE.md`
- `docs/PHASE_11_FARM5_0_1_153_SYNC_TEST_EVIDENCE.md`
- `docs/PHASE_11_FARM5_0_1_195_LIVE_CANARY_EVIDENCE_PACK.md`

- [PHASE_11D_MANUAL_CANARY_EXECUTION_GATE.md](./PHASE_11D_MANUAL_CANARY_EXECUTION_GATE.md)


- `docs/PHASE_11D_MANUAL_CANARY_EXECUTION_RUN_PREPARATION.md` (Phase 11D preparation package, non-authorizing)

- `docs/PHASE_11D_ACTUAL_MANUAL_CANARY_EXECUTION_RUN_PACKAGE.md`


## Phase 11 Docs/Evidence Additions

- `docs/PHASE_11D_CANARY_ACCEPTANCE_DECISION_GATE.md`

- docs/PHASE_11_FARM5_0_1_197_CANARY_ACCEPTANCE_DECISION_EVIDENCE.md
- docs/PHASE_11E_LIMITED_ONBOARDING_GATE.md

- `docs/PHASE_11_FARM5_0_1_198_LIMITED_ONBOARDING_GATE_EVIDENCE.md`

- `docs/PHASE_11E_LIMITED_ONBOARDING_EXECUTION_GATE.md`

- docs/PHASE_11_FARM5_0_1_199_LIMITED_ONBOARDING_EXECUTION_GATE_EVIDENCE.md
- docs/PHASE_11E_SINGLE_CUSTOMER_STAGING.md
- docs/PHASE_11_FARM5_0_1_200_SINGLE_CUSTOMER_DB_STAGING_EVIDENCE.md
- docs/PHASE_11E_SINGLE_CUSTOMER_FIREWALL_PLAN_GATE.md

- docs/PHASE_11_FARM5_0_1_202_FIREWALL_PLAN_GATE_EVIDENCE.md
- docs/PHASE_11E_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE.md


- docs/PHASE_11_FARM5_0_1_203_FIREWALL_APPLY_GATE_EVIDENCE.md
- docs/PHASE_11E_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTION.md

- docs/PHASE_11_FARM5_0_1_205_POST_APPLY_EVIDENCE_READY.md
- docs/PHASE_11E_SINGLE_CUSTOMER_RUNTIME_PATH_EVIDENCE.md
- docs/PHASE_11E_SINGLE_CUSTOMER_STRATUM_TRANSCRIPT_EVIDENCE.md
- docs/PHASE_11E_SINGLE_CUSTOMER_VISIBILITY_BUNDLE.md

Current Phase 11E operator runbook: `docs/PHASE_11E_SINGLE_CUSTOMER_RUNTIME_STRATUM_EVIDENCE_RUNBOOK.md` (evidence collection only, non-authorizing).

- `scripts/phase11e_collect_runtime_stratum_evidence.sh` — fail-closed Phase 11E synchronized runtime/Stratum evidence helper.

- docs/PHASE_11_FARM5_0_1_218_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY.md
- docs/PHASE_11E_SINGLE_CUSTOMER_ABUSE_RESTART_READINESS_RUNBOOK.md

- docs/PHASE_11E_SINGLE_CUSTOMER_ABUSE_RESTART_EVIDENCE_COLLECTION.md

- `docs/PHASE_11E_SOURCE_BACKED_READINESS_CLOSURE.md`

- `docs/PHASE_11E_LIMITED_ACTIVATION_EXECUTION_RUNBOOK.md` — gated limited-btc-001 execute, rollback, and post-evidence operator flow.
- `docs/PHASE_11E_LIMITED_ACTIVATION_OBSERVATION_ACCEPTANCE_REVIEW.md` — read-only hashed observation and limited acceptance review flow; non-authorizing.

- `docs/PHASE_11_FARM5_0_1_231_LIMITED_ACCEPTANCE_DECISION_READY.md` — farm5 0.1.231 READY limited acceptance decision evidence; next step is the read-only controlled boundary acceptance package PR.
