# AI Coding Rules

## Current Gate Update (0.1.247)

Phase 11 is accepted on farm5 only for `controlled_cli_limited` BTC operation. The working phase is Phase 11 operational completion — Full CLI Production Operations; Phase 12 — Worker Policy Enforcement remains blocked. Full CLI Production Operations acceptance must prove restart/autostart, production customer lifecycle CLI execution, production firewall plan/apply/verify/rollback for real customer ports, production onboarding through CLI, usage/report/check evidence, abuse runner coverage for all active customers in all enabled lanes, pause/block/expire-run controls, backup/restore drill, and final acceptance to `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`. Worker enforcement remains disabled until Phase 12 acceptance; UI, Telegram, buyer panel, public API, public backend exposure, unrestricted production expansion, and unrestricted miner expansion remain closed. Controlled authorization does not relax default `plan_only` config or authorize PR-development runtime mutation. `docs/PHASE_STATUS.md` is authoritative. farm5 0.1.245 post-reboot evidence found a restart/autostart persistence gap: partial runtime container return, missing `mpf-v2raya-socks-bridge`, and absent known controlled Phase 11 firewall artifacts after reboot. Keep `restart_autostart_proof=missing_or_partial`; this version adds the controlled repair plan/package/evidence path for `fix_restart_autostart_persistence_gap`, and the gap inventory may point operators to `run_restart_autostart_persistence_fix_on_farm5` without treating the proof or Full CLI Production Operations as accepted.

Status: active implementation contract

This file defines rules for AI coding agents working on `proxy-address-mining`.
It complements `AGENTS.md`, `docs/PHASE_STATUS.md`, `docs/SAFETY.md`, and the domain contracts.

## Mandatory Reading

Before changing code, scripts, migrations, config, services, jobs, UI, or documentation, read:

```text
AGENTS.md
README.md
docs/INDEX.md
docs/PHASE_STATUS.md
docs/SAFETY.md
docs/ROADMAP.md
docs/DATA_MODEL.md
docs/FIREWALL.md
docs/ABUSE.md
docs/AI_CODING_RULES.md
```

For current Phase 11 production/customer activation planning-readiness work, also read:

```text
docs/AI_PHASE_11_TASK.md
docs/PRODUCTION_ACTIVATION_GATE.md
docs/AI_SAFE_RUNTIME_FIRST.md
docs/BACKEND_PORT_POLICY.md
```

For historical Phase 6 firewall-planner/reference context, also read:

```text
docs/AI_PHASE_6_TASK.md
docs/BACKEND_PORT_POLICY.md
```

For hash-rate, share, worker, or observability work, also read:

```text
docs/OBSERVABILITY_HASHRATE.md
docs/WORKER_POLICY.md
```

## Phase Gate Rule

AI-safe Runtime-first does not override `docs/PHASE_STATUS.md`. It means prefer the shortest safe path to a controlled runtime gate, while preserving fail-closed behavior, operator approval, service-layer boundaries, rollback evidence, and explicit phase authorization.


The current phase in `docs/PHASE_STATUS.md` is authoritative.

If a requested change belongs to a later phase, do not implement runtime behavior. Instead, refine the contract, add safe tests, and keep production behavior disabled.

Current gate:


```text
accepted: Phase 11 — Production / Customer Activation Gate accepted on farm5
working: Phase 11 operational completion — Full CLI Production Operations
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled_operator_gated
customer_onboarding_allowed: controlled_cli_limited
worker_enforcement_allowed: no
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

Historical pre-final-acceptance Phase 11 planning-readiness stop condition (non-authorizing reference only): no production traffic, no controlled CLI canary execution, no limited real customer onboarding, no firewall apply, no iptables-restore, no customer NAT/customer firewall rules, no abuse automation runner, no background worker/scheduler/timer, no collector daemon, no unrestricted production DB execution, no hard/soft block automation, no pause automation, no UI, no Telegram.

Phase 8 dry-run evaluator stop condition: synthetic/in-memory only, no real customer evaluation, no live evidence collection, no DB reads/writes, no abuse runner, no hard/soft blocks, no pause automation, no runtime automation.

Phase 8 runtime/worker readiness stop condition: no worker start, no scheduler/timer, no abuse runner, no real customer evaluation, no production DB execution, no firewall/customer mutation, no hard/soft blocks, no pause automation, no production traffic.

Historical Phase 8 forbidden runtime behaviors (still forbidden unless future explicit gate opens them):
- no abuse runner
- no abuse automation
- no abuse_states writes
- no abuse_events writes
- no hard/soft blocks
- no pause automation
- no runtime Phase 8 implementation before explicit gate
- no live firewall apply, no customer NAT/rules, no iptables-restore, no production traffic, no UI, no Telegram


## Phase 6 Historical Safety Continuity (reference only)

Phase 6-B and adjacent Phase 6 slices modeled apply/rollback/preflight boundaries and are now historical/accepted reference context only. They do not define current active work in Phase 11 unless `docs/PHASE_STATUS.md` explicitly reopens a gate.

Historical Phase 6-B allowed work (accepted reference):

```text
repository/documentation cleanup that preserves gates
firewall desired-state model refinement
firewall planner/diff contracts
human-readable and JSON plan/report rendering
dry-run evidence generation
offline snapshot parser and file-backed diff fixtures
offline restore payload artifacts
offline apply-readiness contracts
offline apply package reports
offline rollback artifacts from explicit snapshot files
offline preflight inspection/failure matrix
planner/contract/preflight tests
backend exposure classification tests
internal backend reachability classification tests
```

Historical Phase 6-C forbidden work (non-authorizing reference only; does not override the accepted Phase 11 controlled boundary):

```text
production traffic
customer NAT redirects
customer firewall rules
live firewall apply
live firewall rollback
live firewall verify
iptables-save execution
iptables-restore execution
conntrack flush
usage timers
hash-rate/share collectors
abuse runner automation
block or pause automation
UI service
buyer UI service
Telegram bot
production import
worker enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

Phase 11 acceptance authorizes only the controlled, planner-driven, operator-gated firewall apply path. Unrestricted or direct/ad-hoc firewall mutation remains forbidden, and conservative config defaults remain unchanged.

Historical compatibility anchor: Slice 3 / Apply Slice 3 and Future Dedicated Phase 6 Apply Gate Proposal/Review are retained as non-authorizing Phase 6 references only; they do not reopen any current gate.

## Service Boundary Rule

Business logic belongs in services and domain modules.

Required pattern:

```text
interface or job
  -> request DTO or command object
  -> service
  -> repository or adapter
  -> event and audit
  -> response DTO
```

Interfaces must stay thin. Repositories own persistence. Adapters own external-system interaction. Services own validation, transitions, audit, and side-effect ordering.

## Migration Rule

Schema changes require:

```text
SQLAlchemy model update
Alembic migration
migration test or documented restore strategy
phase approval before server migration
acceptance output recorded after server migration
```

Future production migrations should use explicit Alembic operations instead of relying on bootstrap-style `create_all/drop_all` patterns.

## Runtime Alignment Rule

The official server command must match the accepted repository phase.

For farm5, the following commands must report the current accepted/working gate before Phase 11 work can be trusted:

```bash
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor
bash scripts/verify_current_phase_gate.sh
```

If `/usr/local/bin/mpf` reports an older phase or the current gate script fails, the server is not runtime-aligned.

## Backend Port Rule

Backend ports are internal service ports. They must be closed to direct external/public access while remaining reachable from valid internal server and Docker paths.

Required invariant:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not make internal health checks fail in order to hide backend ports from the outside.

Docker-managed local-only DNAT for the accepted limited runtime is informational; it is not MPF customer NAT.

## Hash-rate and Share Observability Rule

Accepted/rejected hash-rate per device is a first-class future capability.

Do not implement it as a UI-only calculation or a loose log parser.

Required future layers:

```text
Stratum/share evidence collection
share_events evidence table
device_hashrate_samples aggregated time-series
customer_hashrate_samples aggregated time-series
report service/API response DTOs
UI charts from aggregated samples
retention policy before high-volume collection
```

The term device must be modeled carefully. In early phases, device identity may be derived from:

```text
customer + lane + normalized_worker_name + src_ip + session evidence
```

Worker name alone must not be treated as a guaranteed physical device.

## Stop Conditions
- Historical Phase 8 controlled worker dry-run gate stop condition: no worker start, no scheduler/timer, no abuse runner, no real customer evaluation, no production DB execution, no DB reads/writes for worker execution, no firewall/customer mutation, no hard/soft blocks, no pause automation, no production traffic, and controlled dry-run remains future-gated synthetic dry-run only, and farm5 dry-run evidence remains future-gated until 0.1.121 is synced/tested after merge.

Stop and revise if a change introduces:

```text
traffic-changing behavior before the matching phase
controlled CLI canary before explicit Phase 11 authorization
limited real customer onboarding before explicit Phase 11 authorization
live firewall apply before explicit Phase 11 production/customer activation gate acceptance
live firewall write dependency before explicit Phase 11 production/customer activation gate acceptance
iptables-restore execution before explicit Phase 11 production/customer activation gate acceptance
conntrack flush before the relevant runtime gate
abuse automation before the relevant Phase 11 runtime gate
backend public exposure
backend internal reachability failure
NAT redirect before its phase
runtime CLI older than accepted phase
high-volume share collection without retention policy
UI charts reading raw high-volume events directly
worker blocking modeled as firewall-only
business logic inside interface handlers
secrets committed to the repository
```

When documents conflict, follow the stricter safety rule and update the docs before implementing code.

- Phase 8 evidence/reporting contract stop condition: no live evidence collection, no DB reads/writes, no abuse runner, no hard/soft blocks, no pause automation, no runtime automation.


Phase 8 DB-only transition readiness stop condition: no DB connection, no DB reads/writes, no migrations, no real customer evaluation, no live evidence collection, no abuse runner, no hard/soft blocks, no pause automation, no runtime automation.

## Phase 8 DB-only execution stop condition
- no runtime automation, no abuse runner, no firewall/customer mutation, no production traffic, manual confirmation required for any DB-only execution path, CLI defaults to dry-run, hard transitions require operator approval, manual unhard future-gated.


## Phase PR Body Format (Required)
- Phase PR bodies must use Why / What / How to test / Version / Risk + Rollback.
- Do not use Motivation / Description / Testing for Phase PRs.
- AI agents use PR bodies as operational context; stale PR body structure is a process defect.

## Phase 8 Runtime Worker Dry-Run Harness Stop Condition
- no worker start, no scheduler/timer, no abuse runner, no real customer evaluation, no production DB execution, no firewall/customer mutation, no hard/soft blocks, no pause automation, no production traffic.


## Phase 8 Controlled Worker Pre-Acceptance Stop Condition
- no worker start, no scheduler/timer, no abuse runner, no real customer evaluation, no production DB execution, no DB reads/writes for worker execution, no firewall/customer mutation, no hard/soft blocks, no pause automation, no production traffic.


## Phase 8 farm5 Controlled Worker Dry-Run Evidence Collection Preparation Stop Condition

no execution in PR, no dry-run evidence claimed before operator output exists, no background worker start, no scheduler/timer, no abuse runner, no real production customer evaluation, no production DB execution, no DB reads/writes for worker execution, no firewall/customer mutation, no hard/soft blocks, no pause automation, no production traffic, and farm5 dry-run evidence collection remains future-gated until 0.1.121 is synced/tested after merge.

Phase PR body format rule: Why / What / How to test / Version / Risk + Rollback.

- AI-safe operator rule: do not suggest root for DB write execute commands when `database.url` is local-peer `postgresql:///mpf`; use `sudo -u mpf mpf ...` for DB-only execute paths.

## Runtime-forward PR rule

After a controlled runtime boundary is accepted, AI agents must not create repeated report-only PRs that avoid implementation.

Report-only PRs are allowed only when they are:

1. the first entry gate for a new phase/subphase;
2. a fail-closed blocker investigation with concrete next implementation step;
3. evidence capture required before a dangerous controlled operation.

No two consecutive PRs in the same active phase/subphase may be report-only unless the second PR records a real farm5 blocker and includes the exact next implementation scope.

Every normal implementation PR must deliver at least one concrete implementation artifact:

- service-layer implementation
- repository/model/migration change
- CLI/API operator surface
- controlled execution package
- adapter behavior
- tests covering behavior
- gated runtime/runbook script

Documentation-only changes are allowed for safety clarification, but they must not become the default progression path.
