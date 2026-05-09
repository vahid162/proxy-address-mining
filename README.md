# Proxy Address Mining

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed rewrite of a mining customer gateway control plane.

This is a **greenfield implementation**, not a direct migration or patching of old shell scripts.

## Current Status

Source of truth for the current phase:

```text
docs/PHASE_STATUS.md
```

Current repository/server state:

```text
accepted_phase: Phase 4 Runtime Activation — Limited Proxy Runtime Startup accepted on farm5
working_phase: Phase 5 — Customer CRUD in DB Only
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only_after_phase5_gate
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

The accepted Phase 4 runtime is intentionally limited and local-only:

```text
v2rayA UI: 127.0.0.1:2015 -> container 2017
BTC backend: 127.0.0.1:60010 -> forwarder -> v2rayA -> pool
```

Do not use this repository for production customer traffic yet.

## Implemented So Far

```text
Phase 0 architecture and safety contracts
Phase 1 preflight/bootstrap runbook and Ubuntu 24.04 bootstrap script
safe CLI smoke skeleton
config validator
PostgreSQL DB ping helper
SQLAlchemy model skeletons
Alembic bootstrap
Phase 2 schema representation
Phase 2 migration accepted on farm5
Phase 3 read-only CLI/API foundation accepted in source artifact
Phase 3.1 official runtime alignment accepted on farm5
read-only DB status, lane list, customer list, and job status commands
service/repository boundaries for Phase 3 commands
internal API foundation with stable read-only response DTOs
foundation taxonomy and request context/correlation_id contracts
future-ready buyer/account and worker-policy boundaries
extension-ready control-plane schema contracts
pytest CI on GitHub Actions
backend internal/external reachability policy contract
accepted/rejected hash-rate and share observability contract
AI coding rules for phase-gated development
Phase 4 planning task and server runbook foundations
Phase 4.1 Compose template and server config planning result recorded
Phase 4.2 runtime activation runbook planning synced and verified on farm5
Phase 4 runtime activation execution review completed
Phase 4 limited runtime activation accepted on farm5
```

## Current Phase 5 Scope

Allowed now:

```text
customer domain DTOs and service contracts
DB-only customer create/read/update/disable planning
DB-only validation for lane, port, expiry, and status
repository tests for customer CRUD state transitions
CLI/API contracts that do not touch firewall/NAT
audit/event planning for future mutation tracking
documentation updates that preserve phase gates
proxy doctor/status refinements for the accepted limited runtime state
```

Forbidden now:

```text
production traffic
customer NAT redirects
customer firewall rules
live firewall apply
iptables-restore
usage timers
hash-rate/share collectors
abuse runner automation
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
```

## Required Before Phase 5 Acceptance

Phase 5 must remain DB-only:

```text
docs/AI_PHASE_5_TASK.md exists
customer CRUD remains DB-only
no firewall apply is introduced
no NAT redirect is introduced
no production customer traffic is enabled
all customer mutations go through service/repository boundaries
ports are validated against lane and collision rules
customer state changes are auditable or prepared for audit/event recording
pytest passes
server sync evidence is reviewed
```

## Not Implemented Yet

```text
production customer traffic
live firewall planner/apply
NAT redirects
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

Build a new MPF control plane that preserves the operational capabilities of the old shell-based setup while replacing the implementation with a testable Python architecture.

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

The server is a **forward-only customer gateway**:

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

Future coins such as ZEC and LTC must be implemented through the lane model.
Do not clone scripts per coin.

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
firewall apply mechanism: iptables-save / iptables-restore
scheduler: systemd timers
initial firewall mode: plan_only
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
hard uses firewall plan/apply/verify path
hard flushes affected conntrack scope
manual unhard is audited
```

A patch that weakens this requirement must be rejected.

## Backend Port Policy

Backend ports are internal service ports.

They must be blocked from direct external/public access only, while remaining reachable from valid internal server and Docker paths.

Required future doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not block loopback, required Docker/internal paths, or the future MPF-owned NAT redirect path just to hide backend ports externally.

See:

```text
docs/BACKEND_PORT_POLICY.md
```

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

See:

```text
docs/OBSERVABILITY_HASHRATE.md
```

## Firewall Safety Model

Firewall changes must be model-driven.

Required lifecycle:

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

## Documentation Map

Start here:

```text
AGENTS.md
README.md
docs/INDEX.md
docs/PHASE_STATUS.md
docs/AI_CODING_RULES.md
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

Current phase contracts/results:

```text
docs/PHASE_3_SERVER_RESULT.md
docs/PHASE_3_1_PRE_PHASE4_ALIGNMENT.md
docs/PHASE_3_1_SERVER_RESULT.md
docs/PHASE_4_1_SERVER_RESULT.md
docs/PHASE_4_2_SERVER_SYNC_RESULT.md
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
docs/AI_PHASE_5_TASK.md
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
Phase 11  — Local Web UI Read-only
Phase 12  — Buyer-safe Read-only Reporting
Phase 13  — UI Actions With Confirmation
Phase 14  — Telegram Notifications, Read-only Commands, Restricted Actions
Phase 15  — Worker Policy Enforcement
```

Do not start a later phase until the current phase acceptance gate passes.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This warning is not a Phase 5 planning blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Testing Strategy

Minimum risk areas:

```text
config validation
database migrations
schema constraints
policy versioning
buyer/customer separation
worker block boundary
lane collision
port collision
firewall planner
firewall drift detection
backend exposure detection
backend internal reachability detection
firewall rollback
abuse state machine
all-active-customer abuse coverage
usage counter delta
hash-rate/share aggregation contracts
job locking
backup/restore
interface boundary tests
proxy doctor classification
```

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
