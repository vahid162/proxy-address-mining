# AI Coding Rules

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

The current phase in `docs/PHASE_STATUS.md` is authoritative.

If a requested change belongs to a later phase, do not implement runtime behavior. Instead, refine the contract, add safe tests, and keep production behavior disabled.

Current gate:


```text
accepted: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5
working: Phase 8 — Abuse 1h Core planning/readiness
current_phase6_step: Phase 6-H accepted (dedicated apply gate entry criteria / authorization boundary only, documentation/test-only, non-authorizing); Apply Slice 3 and Apply Slice 4 are server-synced and accepted only as documentation/test-only boundaries; next planning target: Future Dedicated Phase 6 Apply Gate Proposal/Review; future dedicated Phase 6 apply gate remains not accepted and not authorized
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

Phase 8 current safe work: report-only/service-contract/readiness only.

Phase 8 dry-run evaluator stop condition: synthetic/in-memory only, no real customer evaluation, no live evidence collection, no DB reads/writes, no abuse runner, no hard/soft blocks, no pause automation, no runtime automation.

Forbidden in current Phase 8 work:
- no abuse runner
- no abuse automation
- no abuse_states writes
- no abuse_events writes
- no hard/soft blocks
- no pause automation
- no runtime Phase 8 implementation before explicit gate
- no live firewall apply, no customer NAT/rules, no iptables-restore, no production traffic, no UI, no Telegram


## Phase 6 Historical Safety Continuity (reference only)

Phase 6-B and adjacent Phase 6 slices modeled apply/rollback/preflight boundaries and are now historical/accepted reference context only. They do not define current active work in Phase 8.

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

Forbidden now and still forbidden after Phase 6-C:

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

Live firewall apply remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.

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

For farm5, the following commands must report the current accepted/working gate before Phase 6 work can be trusted:

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

Stop and revise if a change introduces:

```text
traffic-changing behavior before the matching phase
live firewall apply before explicit Phase 6 apply gate acceptance
live firewall read/write dependency before explicit apply gate acceptance
iptables-save execution before explicit apply gate acceptance
iptables-restore execution before explicit apply gate acceptance
conntrack flush before the relevant runtime gate
abuse automation before Phase 8
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
