# ROADMAP

Status: active implementation roadmap

This document defines the numbered roadmap for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

The roadmap must be followed in order. Do not start a later phase until the current phase acceptance gate passes.

`docs/PHASE_STATUS.md` remains the authoritative current gate. This roadmap does not open any runtime, firewall, customer, abuse, UI, Telegram, or worker-enforcement gate by itself.

## Current Backend-First Continuation

Phase 11 continuation follows `docs/AI_SAFE_RUNTIME_FIRST.md`.

The project is now backend-first after Phase 10:

```text
Phase 10 — Session / Worker / Policy / Share Timeline
Phase 11 — Production / Customer Activation Gate
Phase 12 — Worker Policy Enforcement
Phase 13 — Local UI
Phase 14 — Operator UI Actions
Phase 15 — Telegram
```

Reason:

```text
complete the backend/control-plane first
make the server operational through CLI/service-layer gates
then add worker enforcement on top of reliable session/worker evidence
then expose Local UI, Operator UI Actions, and Telegram as interfaces only
```

UI and Telegram must never become the implementation backend. They may call only the same service layer used by CLI/API.

## Current Phase Alignment Note

Phase 10 is accepted on farm5 as Session / Worker / Policy / Share Timeline evidence/readiness.
Phase 11 is the current working phase. It remains non-authorizing until explicit accepted gates, but now follows AI-safe Runtime-first to move toward controlled runtime evidence in small accepted steps.
Phase 11 currently does not authorize production traffic, controlled CLI canary, limited real customer onboarding, customer NAT/customer firewall rules, firewall apply, abuse automation, worker enforcement, UI, or Telegram.

Historical Phase 6 apply-gate material remains reference-only unless a current explicit gate reopens it.
Production activation remains closed until Phase 11 has explicit acceptance evidence.

## 0. Project Objective

Build a Python-first, API-first, PostgreSQL-backed mining customer gateway control plane.

The project must preserve the operational capabilities of the existing MPF shell-based system while replacing the implementation with a clean, testable, service-layer architecture.

This is a greenfield implementation, not a direct migration or patching of old shell scripts.

## 1. Target Scenario

The server role is:

```text
forward-only customer gateway
```

The target data plane is:

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

Future coins such as ZEC/LTC must be added through the lane model. Do not copy scripts per coin.

## 2. Product Scope

Required core capabilities:

1. API-first service architecture
2. PostgreSQL source of truth
3. central config at `/etc/mpf/mpf.yaml`
4. lane-based data model
5. customer CRUD
6. policy versioning
7. firewall plan/diff/apply/verify/rollback
8. backend exposure guard
9. usage accounting
10. policy/reject accounting
11. one-hour miner-abuse state machine
12. block and pause controls
13. event/audit log
14. backup and restore points
15. `mpf check` final verdict
16. systemd service/timer model
17. session/worker/policy/share evidence
18. production activation gate
19. worker policy enforcement after evidence and adapters
20. UI and Telegram as later service-layer interfaces

Out of scope for early/backend phases:

1. public web panel
2. public API exposure
3. Telegram write actions
4. multi-server central dashboard
5. billing/payment execution
6. auto-tuning policy algorithms
7. direct nftables migration
8. real-time packet streaming UI
9. RBAC-heavy enterprise user system
10. fee-aware Stratum routing
11. production worker enforcement before Phase 10 evidence, Phase 11 production gate, and Phase 12 adapter support

## 3. Architecture Commitments

The roadmap assumes these fixed decisions:

1. code path: `/opt/mpf-py`
2. config path: `/etc/mpf/mpf.yaml`
3. data path: `/var/lib/mpf`
4. log path: `/var/log/mpf`
5. backup path: `/var/backups/mpf`
6. CLI command: `mpf`
7. database: local PostgreSQL
8. first lane: BTC
9. BTC backend port: `60010`
10. firewall backend: iptables first
11. apply mechanism: `iptables-save` / `iptables-restore` only after an explicit accepted apply/production gate
12. scheduler: systemd timers, not mixed cron/systemd
13. early/current firewall mode: `plan_only`
14. local API/UI binding only: `127.0.0.1` or Unix socket

## 4. API-First Rule

Every phase must preserve this boundary:

```text
interface
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Interfaces include:

```text
CLI
internal API
local Web UI
operator UI
Telegram bot
future integrations
```

Forbidden:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly edits DB
UI directly runs firewall commands
Telegram runs shell commands
Telegram directly writes DB
job bypasses service validation
```

## 5. Phase Roadmap

## Phase 0 — Architecture Freeze

Goal: freeze scope and safety rules before implementation.

Acceptance gate:

```text
architecture frozen
safety rules documented
API-first boundaries documented
data model contract documented
firewall lifecycle documented
abuse 1h requirement documented
Phase 1 preflight checklist documented
```

## Phase 1 — Preflight + Bootstrap Without Traffic Changes

Goal: prepare the server and skeleton without touching production traffic.

Allowed:

```text
inspect OS/kernel/timezone/network/DNS
inspect firewall backend
inspect Docker/PostgreSQL/tool availability
install base tools
create standard directories
prepare local PostgreSQL database/user
create Python virtual environment
create initial project skeleton
create /etc/mpf/mpf.yaml with apply_mode=plan_only
run smoke tests
```

Forbidden:

```text
customer rule creation
NAT redirect
backend public exposure
abuse automation
block automation
pause automation
UI actions
Telegram actions
production customer onboarding
```

Acceptance gate:

```bash
mpf --help
mpf doctor
mpf config validate
mpf db ping
python -m pytest
systemctl status postgresql
docker version
docker compose version
conntrack -V
iptables --version
```

## Phase 2 — PostgreSQL + Config + Domain Model

Goal: implement the source-of-truth schema and core domain objects.

Required work:

```text
SQLAlchemy models
Alembic migrations
config loader and validator
lane/customer/policy models
abuse state model
event/audit model
job_runs and scheduler_locks
restore_points and firewall_snapshots
worker/session/share evidence model foundations
```

Acceptance gate:

```text
migration upgrade passes
restore strategy documented
config validation passes
DB ping passes
BTC lane seed exists or is clearly represented
customer policy versioning works
abuse state is representable
worker blocks are not firewall-only
feature flags do not bypass phase gates
no live firewall apply exists
no customer firewall rule exists
no NAT redirect exists
```

## Phase 3 — CLI + Internal API Foundation

Goal: expose safe read-only and DB-only operations through the service layer.

Required commands:

```bash
mpf config show
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
mpf doctor
```

Acceptance gate:

```text
CLI uses services
internal API uses services
read-only commands work
DB-only commands are audited where needed
no firewall rule is created
```

## Phase 4 — Compose Forward-only + Proxy Doctor

Goal: start the proxy data-plane without customer firewall redirects.

Required work:

```text
v2rayA service
v2raya bridge when needed
BTC simple-forwarder / gost on backend 60010
healthchecks
Docker Compose doctor
proxy reachability probe
backend exposure detection
```

Acceptance gate:

```text
forwarder listens on BTC backend
v2rayA UI is local-only
backend direct public exposure is blocked or detected as critical
proxy doctor passes
no customer NAT redirect exists yet
```

## Phase 5 — Customer CRUD in DB Only

Status: accepted on farm5.

Goal: manage customer state without creating live firewall rules.

Required work:

```text
add/edit/delete/renew/list customers
days/expiry
miners/farms/maxconn/rate/burst
optional IP whitelist
active/paused/expired/deleted status model
policy versioning
event/audit records
port/lane collision detection
```

Acceptance gate:

```text
customer CRUD works in DB
policy history is preserved
events are recorded
port collisions are detected
lane collisions are detected
no iptables rule is created
```

## Phase 6 — Firewall Planner + Apply/Verify/Rollback

Status: accepted as planner/reporting/readiness context; live production apply still requires explicit later gate.

Goal: implement safe firewall state management.

Required commands:

```bash
mpf firewall doctor
mpf firewall plan
mpf firewall diff
mpf firewall apply --yes
mpf firewall verify
mpf firewall rollback <apply_id> --yes
```

Required behavior:

```text
desired model generation
live firewall snapshot parsing after allowed gates
human-readable plan
JSON plan
restore point before apply
iptables-save backup before apply
lock before apply
atomic iptables-restore after allowed gates
verify after apply
rollback from stored restore artifact
backend exposure guard
drift detection
```

Acceptance gate:

```text
plan output is human-readable and JSON
plan with errors cannot be applied
backup is created before apply
verify is mandatory after apply
rollback is tested
backend exposure blocks unsafe apply
drift is detected
firewall tests pass
```

## Phase 7 — Usage + Policy/Reject Accounting

Status: accepted on farm5 as report-only/service-contract/readiness.

Goal: collect reliable usage and reject data before abuse automation.

Acceptance gate:

```text
every active customer has accounting rules
missing accounting rule count is zero
counter deltas are reliable
usage reports work
reject events are explainable
```

## Phase 8 — Abuse 1h Core

Status: accepted on farm5.

Goal: enforce one-hour miner-abuse handling for all active customers after the relevant production/automation gate opens.

Required state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Required invariant:

```text
all active customers in all enabled lanes are covered
no silent skip
farms-over alone does not harden
worker-over alone does not harden
sustained miner-abuse hardens after about 3600s
manual unhard is audited
```

## Phase 9 — Check / Report / Diagnostics

Status: accepted on farm5.

Goal: produce clear operator verdicts.

Required commands:

```bash
mpf check <name|port>
mpf report <name|port>
mpf monitor summary
mpf monitor port <target>
mpf diag <target>
mpf audit miners-over
mpf audit farms-over
mpf audit suspicious
```

Acceptance gate:

```text
common failures produce final verdicts
reports are understandable
operator action is clear
read-only diagnostics do not mutate state
```

## Phase 10 — Session / Worker / Policy / Share Timeline

Goal: provide forensic history, worker evidence, policy/reject timeline, share timeline, and evidence packs before production activation or worker enforcement.

Required work:

```text
flow sessions
worker events
customer worker timeline
policy/reject timeline
share accepted/rejected timeline planning
session reconcile
worker binding from Stratum authorize/submit when available
evidence pack
worker policy reporting without enforcement
collector/readiness boundaries without production activation
```

Acceptance gate:

```text
active sessions visible per customer
recent closed sessions visible
unique IPs visible
unique workers visible
reject timeline visible
worker timeline visible
share timeline/evidence contract exists
evidence pack can be generated
worker policy can be reported without enforcement
no worker enforcement is active
no production traffic is active
```

## Phase 11 — Production / Customer Activation Gate

Goal: make the server operational for real customers through the standard `mpf` CLI and service layer before UI or Telegram work.

This is the first phase that may open controlled production/customer behavior, but only after explicit acceptance evidence.

Required work:

```text
fresh farm5 sync/test evidence
restart and container-order safety
controlled firewall apply/verify/rollback path
customer NAT/customer firewall rules through planner only
controlled CLI canary customer
limited real customer onboarding after canary evidence
usage/reject/session/worker visibility for real customers
abuse 1h runtime coverage for all active customers in enabled lanes
backup/restore-plan evidence
operator runbook and final activation report
```

Required CLI surface:

```text
mpf production readiness
mpf production canary-plan
mpf production canary-acceptance
mpf production final-activation
```

Initial operational boundary:

```text
production_traffic: controlled_cli_canary or controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled
customer_onboarding_allowed: controlled_cli_canary or controlled_cli_limited
ui_allowed: no
telegram_allowed: no
```

Acceptance gate:

```text
manual canary customer connects successfully
NAT hit is visible
usage/reject accounting works
check/report returns clear verdict
abuse scanner covers the customer
rollback or restore-plan evidence exists
server restarts without losing accepted runtime service
no unrestricted production onboarding is enabled
```

## Phase 12 — Worker Policy Enforcement

Goal: enforce worker policy only after Phase 10 worker/session evidence and Phase 11 controlled production activation exist.

Allowed enforcement modes:

```text
detection_only
manual_operator_action
stratum_proxy, only after adapter is implemented and tested
```

Required work:

```text
worker-to-session mapping confidence model
worker policy service
operator-visible enforcement plan
adapter failure behavior
safe fallback to detection_only
worker enforcement events/audit
no firewall-only worker block design
```

Acceptance gate:

```text
worker-to-session mapping is reliable enough for selected mode
worker policy service is tested
adapter behavior is tested
detection-only mode is safe
manual/operator enforcement is audited
strict enforcement does not rely on firewall-only worker names
```

## Phase 13 — Local UI

Goal: provide a local-only UI after the backend/CLI production path and worker-enforcement boundary are defined.

Required pages:

```text
Dashboard
Customers
Customer detail
Report
Abuse status
Usage
Blocks
Runbook
Worker/session timeline
Production activation status
```

Rules:

```text
bind only to 127.0.0.1 or Unix socket
no direct DB writes
no direct firewall writes
use service/API layer only
read-only first unless a later explicit Operator UI Actions phase opens actions
```

Acceptance gate:

```text
UI is local-only
UI uses service/API layer
no direct mutation path exists
operator can inspect production/customer/worker status without shell access
```

## Phase 14 — Operator UI Actions

Goal: add controlled local operator UI actions after the read-only UI exists.

Required actions:

```text
add/edit/renew/delete customer
set IPs
firewall plan/apply with confirmation
block/unblock
note add
pause/unpause
manual unhard
worker enforcement manual action where allowed
```

Rules:

```text
every action requires confirmation
dangerous actions show plan first
dangerous actions create restore points
all actions are audited
UI actions call the same service layer as CLI
```

Acceptance gate:

```text
confirmation exists
event/audit exists
restore point exists where needed
plan output is visible before apply
UI cannot bypass service-layer gates
```

## Phase 15 — Telegram

Goal: add Telegram safely after backend, production activation, worker-enforcement boundary, local UI, and operator UI action patterns are established.

Stages:

```text
notifications only
read-only commands
restricted actions with allowlist and confirmation
```

Rules:

```text
no raw token in repository
no direct DB write
no direct firewall command
no shell command bridge
use service/API layer only
actions require allowlist and confirmation
actions are audited
```

Acceptance gate:

```text
notifications work
read-only commands work
actions require allowlist and confirmation
actions are audited
Telegram cannot bypass service-layer gates
```

## 6. MVP Definition

### MPF Python v1

Must include:

```text
config loader and validation
PostgreSQL schema and migrations
lane model
customer CRUD
firewall plan/apply/doctor/rollback contracts
backend guard for 60010 and future lanes
usage accounting
abuse 1h for all active customers
block global/per-port with expiry
pause/unpause
event/audit log
backup/restore-plan
mpf check final verdict
systemd services/timers
test suite for firewall planner and abuse state machine
```

### MPF Python v1.5

Add:

```text
worker timeline
session ledger
policy/reject timeline
share timeline/evidence pack
advanced reports
worker policy reporting without enforcement
```

### MPF Python v2

Add:

```text
Production / Customer Activation Gate
controlled CLI canary
limited real customer onboarding
```

### MPF Python v2.5

Add:

```text
Worker Policy Enforcement
safe detection/manual/adapter-backed modes
```

### MPF Python v3

Add:

```text
Local UI
Operator UI Actions
```

### MPF Python v4

Add:

```text
Telegram notifications
Telegram read-only commands
restricted Telegram actions
```

## 7. Stop Conditions

Stop implementation and review when any of these happen:

```text
firewall apply is introduced before an accepted apply/production gate
abuse automation is introduced before accepted automation gate
production traffic is opened before Phase 11 acceptance
UI writes directly to DB
UI directly mutates firewall state
Telegram runs shell commands
Telegram directly writes DB
customer rules are created during Phase 1/2
NAT redirects are created during Phase 1/2
backend is publicly exposed
apply_mode=plan_only is bypassed
TSV/SQLite becomes production source of truth
customer is excluded from abuse without valid exemption
worker block is implemented as firewall-only IP block
worker enforcement is introduced before Phase 10 evidence and Phase 12 acceptance
import directly creates production firewall/customer state
feature flags bypass phase gates
```

## 8. Required Tests by Risk Area

### Firewall

```text
planner tests
collision tests
backend exposure tests
drift tests
rollback tests
failed verify tests
```

### Abuse

```text
state machine tests
all-active-customer coverage test
farms-over-only test
worker-over-only test
exemption expiry test
hard/unhard audit test
```

### Data Model

```text
migration tests
constraints tests
policy versioning tests
restore point relationship tests
worker block boundary tests
extension-ready schema tests
```

### Interfaces

```text
CLI uses services
API uses services
UI uses services
Telegram uses services
no interface directly mutates DB/firewall
```

## 9. Final Roadmap Rule

When in doubt, choose safety over speed.

A phase is not complete because code exists. A phase is complete only when its acceptance gate passes.

## Remaining Phase 6 Alignment With Master Roadmap

Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.

Historical Phase 6 apply slices remain reference-only:

```text
Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary
Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness
Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness
Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal
```

Phase 7 starts only after Phase 6 final acceptance.

No live apply/read/write, iptables-save, iptables-restore, real adapters, DB writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram are allowed unless the current accepted gate explicitly authorizes them.
