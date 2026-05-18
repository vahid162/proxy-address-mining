# ROADMAP

Status: active implementation roadmap

This document defines the numbered roadmap for `proxy-address-mining`. It is an implementation contract for humans and AI coding agents.

The roadmap must be followed in order. Do not start a later phase until the current phase acceptance gate passes.

`docs/PHASE_STATUS.md` remains the authoritative current gate. This roadmap does not open any runtime, firewall, customer, abuse, UI, Telegram, or worker-enforcement gate by itself.

## Current Backend-First Continuation

The project is backend-first after Phase 10:

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
Phase 11 is the current working phase and is planning/readiness only.
Phase 11 currently does not authorize production traffic, controlled CLI canary, customer NAT/customer firewall rules, firewall apply, abuse automation, worker enforcement, UI, or Telegram.

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

Status: accepted.

Goal: freeze scope and safety rules before implementation.

## Phase 1 — Preflight + Bootstrap Without Traffic Changes

Status: accepted.

Goal: prepare the server and skeleton without touching production traffic.

## Phase 2 — PostgreSQL + Config + Domain Model

Status: accepted.

Goal: implement the source-of-truth schema and core domain objects.

## Phase 3 — CLI + Internal API Foundation

Status: accepted.

Goal: expose safe read-only and DB-only operations through the service layer.

## Phase 4 — Compose Forward-only + Proxy Doctor

Status: accepted as limited local-only proxy runtime.

Goal: start the proxy data-plane without customer firewall redirects.

## Phase 5 — Customer CRUD in DB Only

Status: accepted on farm5.

Goal: manage customer state without creating live firewall rules.

## Phase 6 — Firewall Planner + Apply/Verify/Rollback

Status: accepted as planner/reporting/readiness context; live production apply still requires explicit later gate.

Goal: implement safe firewall state management.

## Phase 7 — Usage + Policy/Reject Accounting

Status: accepted on farm5 as report-only/service-contract/readiness.

Goal: collect reliable usage and reject data before abuse automation.

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

## Phase 10 — Session / Worker / Policy / Share Timeline

Status: accepted on farm5.

Goal: provide forensic history, worker evidence, policy/reject timeline, share timeline, and evidence packs before production activation or worker enforcement.

Acceptance boundary:

```text
no worker enforcement is active
no production traffic is active
```

## Phase 11 — Production / Customer Activation Gate

Status: current planning/readiness target.

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

Current Phase 11 planning/readiness boundary:

```text
production_traffic: none
controlled_cli_canary: no
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
ui_allowed: no
telegram_allowed: no
```

Future Phase 11 acceptance gate:

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

Status: future.

Goal: enforce worker policy only after Phase 10 worker/session evidence and Phase 11 controlled production activation exist.

Allowed enforcement modes:

```text
detection_only
manual_operator_action
stratum_proxy, only after adapter is implemented and tested
```

## Phase 13 — Local UI

Status: future.

Goal: provide a local-only UI after the backend/CLI production path and worker-enforcement boundary are defined.

Rules:

```text
bind only to 127.0.0.1 or Unix socket
no direct DB writes
no direct firewall writes
use service/API layer only
read-only first unless a later explicit Operator UI Actions phase opens actions
```

## Phase 14 — Operator UI Actions

Status: future.

Goal: add controlled local operator UI actions after the read-only UI exists.

## Phase 15 — Telegram

Status: future.

Goal: add Telegram safely after backend, production activation, worker-enforcement boundary, local UI, and operator UI action patterns are established.

Stages:

```text
notifications only
read-only commands
restricted actions with allowlist and confirmation
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
controlled CLI canary is executed before explicit Phase 11 authorization
limited real customer onboarding starts before explicit Phase 11 authorization
UI writes directly to DB
UI directly mutates firewall state
Telegram runs shell commands
Telegram directly writes DB
customer rules are created before their accepted gate
NAT redirects are created before their accepted gate
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
