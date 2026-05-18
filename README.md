# Proxy Address Mining

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed greenfield rewrite of a mining customer gateway control plane.

It preserves the required operational capabilities of the old shell-script setup, but it must not become a direct migration, patch series, or extension of those old scripts.

## Current Status

Source of truth for the current phase:

```text
docs/PHASE_STATUS.md
```

Current repository/server gate:

```text
accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

The accepted Phase 4 runtime remains intentionally limited and local-only:

```text
v2rayA UI: 127.0.0.1:2015 -> container 2017
BTC backend: 127.0.0.1:60010 -> forwarder -> v2rayA -> pool
```

Do not use this repository for production customer traffic yet.
Latest recorded farm5 sync evidence is 0.1.136. Phase 10 Session / Worker / Policy / Share Timeline is accepted on farm5. Current target is Phase 11 Production / Customer Activation Gate planning/readiness. Production traffic, controlled CLI canary, limited real customer onboarding, firewall apply, iptables-restore, abuse automation runner, customer NAT/customer firewall rules, unrestricted production DB execution, hard/soft block automation, pause automation, UI, and Telegram remain disabled.

Historical compatibility anchors are kept in docs/HISTORICAL_COMPATIBILITY_ANCHORS.md.


## Current Accepted/Working Boundary (Phase 10 accepted / Phase 11 planning)

`docs/PHASE_STATUS.md` is authoritative. Current state is accepted Phase 10 / working Phase 11 planning-readiness with production_traffic=none, firewall_apply_allowed=no, abuse_automation_allowed=no, customer_onboarding_allowed=db_only, proxy_data_plane_allowed=limited_runtime_local_only, ui_allowed=no, telegram_allowed=no, live_snapshot_read_allowed=iptables_save_read_only, and restore_lock_record_execution_allowed=controlled_boundary_only.

Current advancement target is Phase 11 Production / Customer Activation Gate planning/readiness. Historical anchors only: Phase 8 Abuse 1h Core, Phase 9 Check / Report / Diagnostics, and Phase 10 Session / Worker / Policy / Share Timeline are completed accepted context and are not active implementation targets unless `docs/PHASE_STATUS.md` explicitly reopens them.

Phase 6 apply-gate materials (D1/E0/E1/E2/E3/F/G/H and apply slices) are historical/reference-only context and remain non-authorizing for current active work. Phase 6 Dedicated Apply Gate Proposal/Review is historical/completed context. Apply Slice 3 and Apply Slice 4 are server-synced and accepted only as documentation/test-only boundaries. Historical compatibility anchor: Future Dedicated Phase 6 Apply Gate Proposal/Review.

No production traffic, controlled CLI canary, limited real customer onboarding, firewall apply, iptables-restore, customer NAT/customer firewall rules, usage automation, abuse automation, worker automation, UI, or Telegram is authorized.

Historical/reference-only notes from accepted Phase 6 boundaries:

```text
repository/documentation cleanup that preserves phase gates
firewall desired-state model refinement
firewall planner/diff contracts
human-readable firewall plan/report output
machine-readable JSON firewall plan/report output
offline snapshot parser and file-backed offline diff fixtures
offline restore payload artifacts
offline apply-readiness contracts
offline apply package reports
offline rollback artifacts from explicit snapshot files
offline preflight inspection/failure matrix
planner/contract/preflight safety tests
proxy/backend safety checks that preserve internal reachability and external non-exposure
```

Forbidden now:

```text
production traffic
controlled CLI canary execution
limited real customer onboarding
customer NAT redirects
customer firewall rules
live firewall apply
live firewall rollback
live firewall verify
unauthorized iptables-save execution
iptables-restore execution
conntrack flush
usage timers
hash-rate/share collectors
abuse runner automation
worker automation
block or pause automation
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

Required invariants remain:

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
proxy_data_plane_allowed = limited_runtime_local_only
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
customer_onboarding_allowed = db_only
ui_allowed = no
telegram_allowed = no
```

## Implemented So Far

```text
Phase 0 architecture and safety contracts
Phase 1 preflight/bootstrap runbook and Ubuntu 24.04 bootstrap script
safe CLI smoke skeleton
config validator
PostgreSQL DB ping helper
SQLAlchemy model skeletons
Alembic bootstrap
Phase 2 schema representation and migration accepted on farm5
Phase 3 read-only CLI/API foundation accepted on farm5
Phase 3.1 official runtime alignment accepted on farm5
read-only DB status, lane list, customer list, and job status commands
service/repository boundaries for CLI/API commands
internal API foundation with stable read-only response DTOs
foundation taxonomy and request context/correlation_id contracts
future-ready buyer/account and worker-policy boundaries
extension-ready control-plane schema contracts
pytest CI on GitHub Actions
backend internal/external reachability policy contract
accepted/rejected hash-rate and share observability contract
Phase 4 limited local-only proxy runtime accepted on farm5
Phase 5 DB-only customer CRUD accepted on farm5
Phase 6 firewall planner accepted on farm5 as planner/reporting/gate-readiness
Phase 7 usage + policy/reject accounting accepted on farm5 as report-only/service-contract/readiness
Phase 8 Abuse 1h Core accepted on farm5 as evidence/readiness only
Phase 9 Check / Report / Diagnostics accepted on farm5 as report-only/final diagnostics
Phase 10 Session / Worker / Policy / Share Timeline accepted on farm5
```

## Not Implemented Yet

```text
production customer traffic
live firewall apply
live firewall rollback
customer NAT redirects
customer firewall rules
usage timers
hash-rate/share collectors
abuse runner automation
block/pause automation
local UI
buyer UI
Telegram bot
authentication/billing
worker enforcement
production import
```

## Project Objective

Build a new MPF control plane that preserves the operational capabilities of the old shell-based setup while replacing it with a testable Python architecture.

The target system is:

```text
Python-first
API-first
PostgreSQL-backed
service-layer based
lane-based
firewall-plan based
safety-gated
future-ready for local UI, buyer UI, Telegram, worker intelligence, and hash-rate/share observability
```

## Target Data Plane

The server is a forward-only customer gateway:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

The first stable lane is BTC:

```text
BTC customer ports -> backend 60010 -> forwarder -> v2rayA -> pool
```

Future coins such as ZEC and LTC must be implemented through the lane model. Do not clone scripts per coin.

## Fixed Architecture Decisions

```text
server role: forward-only customer gateway
source of truth: local PostgreSQL
code path: /opt/mpf-py
config path: /etc/mpf/mpf.yaml
data path: /var/lib/mpf
logs path: /var/log/mpf
backup path: /var/backups/mpf
CLI name: mpf
first lane: BTC
BTC backend port: 60010
firewall backend: iptables first
future firewall apply mechanism: iptables-save / iptables-restore after explicit apply gate
scheduler: systemd timers
initial/current firewall mode: plan_only
local API/UI binding: 127.0.0.1 or Unix socket only
```

## API-First Rule

Business logic must live in domain/service modules.

Required flow:

```text
CLI / API / UI / Telegram / jobs
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Forbidden:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly writes DB
buyer UI directly mutates production state
Telegram directly runs shell commands
job bypasses service validation
```

## Source of Truth

PostgreSQL is the production source of truth.

Flat files and SQLite may be used only for:

```text
import from old scripts
export/debug artifacts
temporary migration tooling
generated restore artifacts
backups
```

They must not become production customer, firewall, usage, abuse, hash-rate, or share state.

## Mandatory Abuse Requirement

Miner-abuse handling is a core feature from day one.

Required state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Rules:

```text
all active customers in all enabled lanes must be scanned
no silent skip is allowed
exemption requires reason and expiry
farms-over alone must not harden
sustained miner-abuse hardens after about 3600 seconds
hard creates restore point and policy backup
hard uses firewall plan/apply/verify path after the relevant apply gate
hard flushes affected conntrack scope after the relevant runtime gate
manual unhard is audited
```

A patch that weakens this requirement must be rejected.

## Firewall Safety Model

Firewall changes must be model-driven.

Required future lifecycle:

```text
read DB/config
  -> build desired model
  -> compare desired with live firewall
  -> generate plan
  -> show human diff
  -> show JSON diff
  -> create restore point
  -> backup live firewall
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event/audit
  -> rollback or rollback-plan on failure
```

Forbidden production pattern:

```text
ad-hoc iptables commands
one-off NAT redirects
interface-triggered firewall shell commands
```

Phase 6-H is accepted as historical documentation/test-only context. Apply Slice 3 and Apply Slice 4 are server-synced documentation/test-only boundaries. Historical compatibility anchor: Future Dedicated Phase 6 Apply Gate Proposal/Review. Live apply remains disabled until the Phase 11 Production / Customer Activation Gate explicitly accepts a controlled apply path.

## Backend Port Policy

Backend ports are internal service ports. They must be blocked from direct external/public access only while remaining reachable from valid internal server and Docker paths.

Required future doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not block loopback, required Docker/internal paths, or the future MPF-owned NAT redirect path just to hide backend ports externally.

## Hash-rate and Share Observability

Accepted/rejected hash-rate per device is a future first-class capability.

It must be planned through structured data and services:

```text
share evidence
share_events
device_hashrate_samples
customer_hashrate_samples
report services
UI charts from aggregate samples
retention before high-volume collection
```

Do not add this later as UI-only calculations, unstructured logs, or raw chart queries over high-volume events.

## Documentation Map

Start here:

```text
AGENTS.md
README.md
docs/INDEX.md
docs/PHASE_STATUS.md
docs/AI_CODING_RULES.md
docs/AI_PHASE_11_TASK.md
```

Core contracts:

```text
docs/ARCHITECTURE.md
docs/SAFETY.md
docs/ROADMAP.md
docs/DATA_MODEL.md
docs/FIREWALL.md
docs/ABUSE.md
docs/FUTURE_EXTENSIONS.md
docs/TAXONOMY.md
docs/BACKEND_PORT_POLICY.md
docs/OBSERVABILITY_HASHRATE.md
```

Current phase and accepted result contracts:

```text
docs/PHASE_STATUS.md
docs/AI_PHASE_11_TASK.md
docs/PRODUCTION_ACTIVATION_GATE.md
docs/AI_PHASE_10_TASK.md
docs/PHASE_10_FARM5_0_1_136_SYNC_TEST_EVIDENCE.md
docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md
docs/PHASE_5_FINAL_ACCEPTANCE.md
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
docs/INTRANET_INSTALL.md
```

## Roadmap Summary

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

Do not start a later phase until the current phase acceptance gate passes.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This warning is not a Phase 11 documentation/planning blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Security Guardrails

```text
never expose backend ports publicly
never block backend ports from valid internal paths
never expose v2rayA UI publicly
never expose early Web UI/API publicly
never hardcode Telegram tokens
secrets must live outside the repository
firewall changes must be auditable
dangerous actions need restore points
direct DB edits are not normal operation
direct iptables edits are not normal operation
buyer UI must not directly mutate production state
worker block must not be modeled as firewall-only
hash-rate/share collectors need retention before activation
```

## License

License is not defined yet.

Choose and add a license before public or multi-person use.

Historical Phase 8 references: the Phase 8 abuse evidence/reporting contract, DB-only controlled transition readiness package, and DB-only controlled transition execution package are completed Phase 8 context only; they are not active targets.

Compatibility anchors for historical Phase 8 report surfaces:

```text
DB-only controlled transition readiness package
report-only/non-mutating/non-authorizing
Current advancement target is the Phase 8 DB-only controlled transition execution package, manual and dry-run-by-default/non-runtime/non-authorizing.
Current advancement target is the Phase 8 runtime/worker integration readiness package, report-only/readiness-only/non-runtime/non-authorizing.
```

Historical gate reference: accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5 / working_phase: Phase 8 — Abuse 1h Core planning/readiness.
