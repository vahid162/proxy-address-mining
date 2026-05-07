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
accepted_phase: Phase 3 — CLI + Internal API Foundation
working_phase: Phase 4 — Compose Forward-only + Proxy Doctor Planning
server_state: farm5 Phase 3 read-only CLI/API foundation completed and verified
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: planning_only
ui_allowed: no
telegram_allowed: no
```

Phase 4 is planning-only until a dedicated runbook/task is accepted. It may prepare Compose/proxy doctor design and safe read-only inspection helpers, but it must not start proxy data-plane containers yet.

Do not use this repository for production traffic yet.

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
Phase 3 read-only CLI/API foundation accepted on farm5
read-only DB status, lane list, customer list, and job status commands
service/repository boundaries for Phase 3 commands
internal API foundation with stable read-only response DTOs
foundation taxonomy and request context/correlation_id contracts
future-ready buyer/account and worker-policy boundaries
extension-ready control-plane schema contracts
pytest CI on GitHub Actions
```

## Not Implemented Yet

```text
production customer CRUD
live firewall planner/apply
NAT redirects
proxy data-plane containers
usage timers
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
future-ready for local UI, buyer UI, Telegram, and worker intelligence
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

They must not become production customer, firewall, usage, or abuse state.

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

## Future-Ready Boundaries Already Reserved

These are allowed as schema/contracts in Phase 2, but not active runtime features yet:

```text
buyer_accounts / buyer_users
customer_service_links / permissions
action_requests
plans / plan_versions
subscriptions / entitlements
feature_flags
notification_rules
customer_health_snapshots
incidents / runbook_steps
config_snapshots
secret_references
restore_drills
maintenance_windows
import_staging
server_profiles / preflight_runs
worker_identities / worker_policies / worker_blocks
abuse_profiles
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
```

Current phase contracts/results:

```text
docs/PHASE_1_SERVER_RUNBOOK.md
docs/PHASE_2_SERVER_RESULT.md
docs/PHASE_3_SERVER_RESULT.md
docs/AI_PHASE_3_TASK.md
docs/INTRANET_INSTALL.md
```

## Roadmap Summary

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
Phase 12 — Buyer-safe Read-only Reporting
Phase 13 — UI Actions With Confirmation
Phase 14 — Telegram Notifications, Read-only Commands, Restricted Actions
Phase 15 — Worker Policy Enforcement, after worker evidence and adapter support
```

Do not start a later phase until the current phase acceptance gate passes.

## Phase 4 Planning Rule

Phase 4 work must begin with planning and runbook definition.

During Phase 4 planning, the project must not:

```text
create or mutate production customers
create customer firewall rules
create NAT redirects
start proxy containers without an accepted Phase 4 execution runbook
run usage timers
activate abuse automation
activate block/pause automation
expose UI components
activate Telegram
onboard production customers
run production import
switch away from firewall.apply_mode=plan_only
```

## Current Server Warnings

`farm5` passed Phase 3 read-only CLI/API foundation checks, but time synchronization is still not confirmed. This must be fixed before production traffic, usage accuracy, or abuse automation because the one-hour abuse process depends on reliable timestamps.

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
firewall rollback
abuse state machine
all-active-customer abuse coverage
usage counter delta
job locking
backup/restore
interface boundary tests
```

## Security Guardrails

```text
never expose backend ports publicly
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
```

## License

License is not defined yet.

Choose and add a license before public or multi-person use.
