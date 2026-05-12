# ROADMAP

Status: Draft v1

This document defines the numbered roadmap for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

The roadmap must be followed in order.
Do not start a later phase until the current phase acceptance gate passes.


## Current Phase Alignment Note

Phase 6-E3 is accepted.
Next planned step is Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review.
Phase 6-G is documentation/test-only and non-authorizing until a separate apply gate is explicitly accepted.
It does not authorize live firewall read/write, live apply/rollback/verify, iptables-save, iptables-restore, real adapters, DB apply writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

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

Future coins such as ZEC/LTC must be added through the lane model.
Do not copy scripts per coin.

## 2. Product Scope

### 2.1 In Scope

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
17. local-only API/UI design for future phases
18. buyer-safe reporting design for future phases
19. Telegram notification design for future phases
20. worker identity and enforcement boundary for future phases

### 2.2 Out of Scope for Early Phases

Do not include in early implementation:

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
11. production worker enforcement before evidence and adapter support

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
11. apply mechanism: `iptables-save` / `iptables-restore`
12. scheduler: systemd timers, not mixed cron/systemd
13. early firewall mode: `plan_only`
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

- CLI
- internal API
- local Web UI
- buyer UI, later
- Telegram bot
- future integrations

Forbidden:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly edits DB
buyer UI directly mutates production state
Telegram directly runs shell commands
job bypasses service validation
```

## 5. Phase Roadmap

## Phase 0 — Architecture Freeze

Goal: freeze scope and safety rules before implementation.

Allowed:

- documentation
- architecture decisions
- safety guardrails
- data model design
- phase gate design

Forbidden:

- package installation
- service activation
- firewall mutation
- NAT redirect
- customer onboarding
- abuse automation
- block automation
- UI exposure
- Telegram activation

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

- inspect OS/kernel/timezone/network/DNS
- inspect firewall backend
- inspect Docker/PostgreSQL/tool availability
- install base tools
- create standard directories
- prepare PostgreSQL local database/user
- create Python virtual environment
- create initial project skeleton
- create `/etc/mpf/mpf.yaml` with `apply_mode: plan_only`
- run smoke tests

Forbidden:

- customer rule creation
- NAT redirect
- backend public exposure
- abuse automation
- block automation
- pause automation
- UI actions
- Telegram actions
- production customer onboarding

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

Safety acceptance:

```text
no customer firewall rule exists
no NAT redirect exists
no backend public exposure exists
no abuse automation is active
no block automation is active
firewall.apply_mode is still plan_only
```

## Phase 2 — PostgreSQL + Config + Domain Model

Goal: implement the source-of-truth schema and core domain objects.

Required work:

1. SQLAlchemy models
2. Alembic migrations
3. config loader and validator
4. lane model
5. customer model
6. policy model
7. abuse state model
8. event/audit model
9. job_runs and scheduler_locks
10. restore_points and firewall_snapshots
11. seed BTC lane contract
12. buyer/account boundary representation
13. plans/entitlements representation
14. action request representation
15. worker policy/block representation
16. feature flag representation
17. notification rule representation
18. server profile/preflight history representation
19. import staging representation
20. health/incident/runbook representation

Acceptance gate:

```text
migration upgrade passes
migration rollback or restore strategy documented
config validation passes
DB ping passes
BTC lane seed exists or is clearly represented
customer policy versioning works
abuse state is representable
buyer accounts are separate from customer service rows
worker blocks are not firewall-only
feature flags do not bypass phase gates
import staging cannot directly create production rules
no live firewall apply exists
no customer firewall rule exists
no NAT redirect exists
no proxy data-plane is started
```

## Phase 3 — CLI + Internal API Foundation

Goal: expose safe read-only and DB-only operations through the service layer.

Phase 6 start gate:

```text
planning/diff/modeling may be worked on
live firewall apply remains forbidden until explicit Phase 6 apply gate acceptance
no customer NAT redirects yet
no production customer traffic yet
no abuse automation yet
```

Required commands:

```bash
mpf config show
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
mpf doctor
```

Rules:

- CLI must not own business logic.
- API must not write DB directly.
- No firewall mutation yet.

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

1. v2rayA service
2. v2raya bridge when needed
3. BTC simple-forwarder / gost on backend `60010`
4. healthchecks
5. Docker Compose doctor
6. proxy reachability probe
7. backend exposure detection

Acceptance gate:

```text
forwarder listens on BTC backend
v2rayA UI is local-only
backend direct public exposure is blocked or detected as critical
proxy doctor passes
no customer NAT redirect exists yet
```

## Phase 5 — Customer CRUD in DB Only

Status: accepted on farm5 (final acceptance recorded in `docs/PHASE_5_FINAL_ACCEPTANCE.md`).

Goal: manage customer state without creating live firewall rules.

Required work:

1. add/edit/delete/renew/list customers
2. days/expiry
3. miners/farms/maxconn/rate/burst
4. optional IP whitelist
5. active/paused/expired/deleted status model
6. policy versioning
7. event/audit records
8. port/lane collision detection

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

Status: current working phase (planner-first only).

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

1. desired model generation
2. live firewall snapshot parsing
3. human-readable plan
4. JSON plan
5. restore point before apply
6. `iptables-save` backup
7. lock before apply
8. atomic `iptables-restore`
9. verify after apply
10. rollback from stored restore artifact
11. backend exposure guard
12. drift detection

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

Goal: collect reliable usage and reject data before abuse automation.

Required work:

1. usage snapshots
2. usage deltas
3. 1h/1d/30d reports
4. connlimit reject events
5. hashlimit reject events
6. pause reject events
7. block reject events
8. usage doctor
9. missing accounting rule detection

Acceptance gate:

```text
every active customer has accounting rules
missing accounting rule count is zero
counter deltas are reliable
usage reports work
reject events are explainable
```

## Phase 8 — Abuse 1h Core

Goal: enforce one-hour miner-abuse handling for all active customers.

Required state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Required hard behavior:

```text
restore point
policy backup
set effective maxconn to miners
firewall plan/apply/verify
scoped conntrack flush
event/audit record
```

Acceptance gate:

```text
all active customers in all enabled lanes are scanned
no silent skip exists
abuse exemption requires reason and expiry
farms-over alone does not harden
sustained miner-abuse hardens after about 3600s
manual unhard is audited
abuse tests pass
```

## Phase 9 — Check / Report / Diagnostics

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

`mpf check` must answer:

1. is the customer connected?
2. does the customer have live rules?
3. does NAT hit?
4. are rejects from connlimit/hashlimit/block/pause?
5. is usage normal?
6. is there IP/worker mismatch?
7. what is the abuse state?
8. what should the operator do next?

Acceptance gate:

```text
common failures produce final verdicts
reports are understandable
operator action is clear
read-only diagnostics do not mutate state
```

## Phase 10 — Session / Worker / Policy Timeline

Goal: provide forensic history and worker evidence.

Required work:

1. flow sessions
2. worker events
3. customer worker timeline
4. policy/reject timeline
5. session reconcile
6. worker binding from Stratum authorize/submit when available
7. evidence pack
8. worker policy reporting without enforcement

Acceptance gate:

```text
active sessions visible per customer
recent closed sessions visible
unique IPs visible
unique workers visible
reject timeline visible
worker timeline visible
evidence pack can be generated
worker policy can be reported without enforcement
```

## Phase 11 — Local Web UI Read-only

Goal: provide a local-only read-only panel.

Required pages:

1. Dashboard
2. Customers
3. Customer detail
4. Report
5. Abuse status
6. Usage
7. Blocks
8. Runbook

Rules:

- bind only to `127.0.0.1` or Unix socket
- no direct DB writes
- no direct firewall writes
- use service layer/API only

Acceptance gate:

```text
UI is local-only
UI is read-only
UI uses service/API layer
no action buttons mutate state
```

## Phase 12 — Buyer-safe Read-only Reporting

Goal: provide buyer-safe read-only visibility after local UI foundations exist.

Required behavior:

1. buyer account/service mapping
2. buyer service list
3. buyer-safe customer detail
4. expiry and status visibility
5. usage/report visibility
6. abuse status visibility without dangerous actions
7. action request creation only, where allowed

Rules:

- buyer UI is read-only first
- buyer UI must not mutate customer policy
- buyer UI must not apply firewall
- buyer UI must not hard/unhard abuse
- buyer UI must not create block/pause directly
- buyer requests go through `action_requests`

Acceptance gate:

```text
buyer accounts are separate from customers
buyer reports use service/API layer
buyer UI is read-only
buyer action request creation is non-mutating
no production state mutation path exists
```

## Phase 13 — UI Actions With Confirmation

Goal: add controlled local operator UI actions.

Required actions:

1. add/edit/renew/delete customer
2. set IPs
3. firewall plan/apply
4. block/unblock
5. note add
6. pause/unpause
7. manual unhard

Rules:

- every action requires confirmation
- dangerous actions show plan first
- dangerous actions create restore points
- all actions are audited

Acceptance gate:

```text
confirmation exists
event/audit exists
restore point exists where needed
plan output is visible before apply
```

## Phase 14 — Telegram Notifications, Read-only Commands, Restricted Actions

Goal: add Telegram safely in stages.

Stages:

1. notifications only
2. read-only commands
3. restricted actions with allowlist and confirmation

Rules:

- no raw token in repository
- no direct DB write
- no direct firewall command
- use service/API layer only

Acceptance gate:

```text
notifications work
read-only commands work
actions require allowlist and confirmation
actions are audited
```

## Phase 15 — Worker Policy Enforcement

Goal: enforce worker policy only after worker evidence and data-plane adapter support exist.

Allowed enforcement modes:

```text
detection_only
manual_operator_action
stratum_proxy, only after adapter is implemented and tested
```

Rules:

- worker block is not firewall-only
- worker evidence must exist before enforcement
- adapter failure behavior must be documented
- enforcement must create event/audit records

Acceptance gate:

```text
worker-to-session mapping is reliable
worker policy service is tested
adapter behavior is tested
detection-only mode is safe
strict enforcement does not rely on firewall-only worker names
```

## 6. MVP Definition

### MPF Python v1

Must include:

1. config loader and validation
2. PostgreSQL schema and migrations
3. lane model
4. customer CRUD
5. firewall plan/apply/doctor/rollback
6. backend guard for `60010` and future lanes
7. usage accounting
8. abuse 1h for all active customers
9. block global/per-port with expiry
10. pause/unpause
11. event/audit log
12. backup/restore-plan
13. `mpf check` final verdict
14. systemd services/timers
15. test suite for firewall planner and abuse state machine

### MPF Python v1.5

Add:

1. worker timeline
2. session ledger
3. policy/reject timeline
4. advanced reports
5. evidence pack
6. worker policy reporting without enforcement

### MPF Python v2

Add:

1. local Web UI read-only
2. buyer-safe read-only reporting
3. local Web UI actions with confirmation

### MPF Python v3

Add:

1. Telegram notifications
2. Telegram read-only commands
3. restricted Telegram actions

### MPF Python v4

Add:

1. worker policy enforcement
2. advanced worker adapters
3. additional backend adapters where justified

## 7. Stop Conditions

Stop implementation and review when any of these happen:

- firewall apply is introduced before Phase 6
- abuse automation is introduced before Phase 8
- UI writes directly to DB
- buyer UI mutates production state directly
- Telegram runs shell commands
- customer rules are created during Phase 1/2
- NAT redirects are created during Phase 1/2
- backend is publicly exposed
- `apply_mode=plan_only` is bypassed
- TSV/SQLite becomes production source of truth
- customer is excluded from abuse without valid exemption
- worker block is implemented as firewall-only IP block
- worker enforcement is introduced before worker evidence and adapter support
- import directly creates production firewall/customer state
- feature flags bypass phase gates

## 8. Required Tests by Risk Area

### Firewall

- planner tests
- collision tests
- backend exposure tests
- drift tests
- rollback tests
- failed verify tests

### Abuse

- state machine tests
- all-active-customer coverage test
- farms-over-only test
- exemption expiry test
- hard/unhard audit test

### Data Model

- migration tests
- constraints tests
- policy versioning tests
- restore point relationship tests
- buyer/customer separation tests
- worker block boundary tests
- extension-ready schema tests

### Interfaces

- CLI uses services
- API uses services
- no interface directly mutates DB/firewall
- buyer UI uses service layer and starts read-only

## 9. Final Roadmap Rule

When in doubt, choose safety over speed.

A phase is not complete because code exists.
A phase is complete only when its acceptance gate passes.


## Remaining Plan Alignment (post Phase 6-C acceptance)

6-D, 6-E, 6-F, 6-G, 7, 8, 9, 10, 11, 12, 13, 14 remain in order.

Phase 6-D is documentation/test-only and does not open live apply.
