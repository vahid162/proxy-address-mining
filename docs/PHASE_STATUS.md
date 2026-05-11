# PHASE STATUS

Status: Active project control file

This file is the authoritative phase gate for humans and AI coding agents. It must be checked before changing code, scripts, deployment files, services, jobs, tests, migrations, or documentation.

## Current State

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

The `Current State` block above is the current gate. Historical compatibility notes and accepted evidence are informational only.

## Accepted Server Results

### Phase 1 — Bootstrap Without Traffic Changes

```text
PostgreSQL active
Docker active
containerd active
mpf config validate OK
mpf doctor OK
mpf db ping OK
pytest passed
Docker had no containers
No MPF firewall rules existed
firewall.apply_mode remained plan_only
```

### Phase 2 — PostgreSQL + Config + Domain Model

```text
backup/snapshot created before migration
pytest passed from /opt/mpf-py-src/.venv
alembic current/head = 0001_phase2_initial_schema
public schema table count = 64
runtime tables remained empty
Docker had no containers
No MPF firewall rules existed
firewall.apply_mode remained plan_only
no proxy data-plane was started
no production traffic was changed
```

### Phase 3 — CLI + Internal API Foundation

```text
Phase 3 read-only CLI/API foundation accepted on farm5
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
pytest passed: 48 passed
runtime tables remained empty
Docker had no containers
No MPF firewall or NAT rules existed
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 3.1 — Official Runtime Alignment

```text
official /usr/local/bin/mpf runtime exposed accepted read-only commands
mpf --version reported 0.1.0 during acceptance
mpf phase-status was aligned during verification
pytest passed: 48 passed
runtime-facing tables remained empty
Docker had no containers
No MPF firewall/NAT rules existed
No MPF systemd/cron automation existed
No risky backend/UI ports were listening
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 4 Runtime — Limited Proxy Runtime Startup

See:

```text
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
```

Accepted evidence summary:

```text
server source aligned with GitHub ZIP
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf proxy config-check final_verdict: OK
mpf-v2raya container started and healthy
mpf-forwarder-btc container started and healthy
v2rayA UI host/operator listener: 127.0.0.1:2015
v2rayA UI container target port: 2017
BTC backend listener: 127.0.0.1:60010
BTC backend internal reachability: OK
no public v2rayA UI exposure detected
no public BTC backend exposure detected
no MPF/customer firewall references detected
no customer NAT redirects detected
customers: 0
job_runs: 0
firewall_applies: 0
abuse_states: 0
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
```

Docker-managed local publish rules for `127.0.0.1:2015` and `127.0.0.1:60010` are accepted only as local Docker publish rules. They are not MPF customer NAT redirects.

### Phase 5 — Customer CRUD in DB Only

See:

```text
docs/PHASE_5_FINAL_ACCEPTANCE.md
```

Accepted evidence summary:

```text
Phase 5 accepted as DB-only customer CRUD + future-readiness contracts
version accepted on server: 0.1.21
final synced repository/server gate: 0.1.26
pytest passed: 182 passed during final clean sync evidence
alembic_version: 0002_phase5_customer_lifecycle
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
ui_allowed: no
telegram_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
no production customer traffic
no live firewall apply
runtime remained limited local-only
```

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This is not a Phase 6 planning blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## What Is Allowed Now

Allowed work is limited to **Phase 6 — Firewall Planner** preparation and planning-only implementation:

```text
- repository/documentation cleanup that preserves the current gate
- firewall desired-model design and implementation
- firewall planner/diff design and implementation
- human-readable and JSON plan output
- dry-run evidence generation
- planner tests and safety regression tests
- proxy/backend safety checks that preserve internal reachability + external non-exposure contracts
```

## What Is Forbidden Now

Do not implement, run, or activate:

```text
- production traffic
- customer NAT redirects
- customer firewall rules
- live firewall apply
- iptables-restore
- usage timers
- hash-rate/share collectors
- abuse runner automation
- block or pause automation
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
- public API binding
- public v2rayA UI exposure
- public backend exposure
```

Live firewall apply remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.

## Current Safety Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = limited_runtime_local_only
customer_onboarding_allowed = db_only
```

Any patch that bypasses these invariants or introduces traffic-changing behavior before the correct accepted phase must be rejected.

## Backend Port Invariant

Backend ports are internal service ports. They must be blocked from direct external/public access only while remaining reachable from valid internal server and Docker paths.

Required proxy/firewall doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by blocking loopback, local server paths, required Docker/internal paths, or the future MPF-owned NAT redirect path.

## Phase 5 Gate Status

Phase 5 is accepted and closed.

Current Phase 5 state is:

```text
customer CRUD works in DB only
policy history is preserved
events/audit are recorded for DB-only customer mutations
port/lane collisions are validated
no iptables rule is created
no NAT redirect is created
no runtime customer traffic is enabled
```

Future customer records remain DB-only until Phase 6 apply and customer NAT/customer firewall gates are accepted.

## Next Planned Step

Proceed to:

```text
Phase 6-A — Repository Cleanup + Firewall Planner Contract and Desired-State Model
```

Phase 6-A must remain planning/model/diff/test only. Do not move to live firewall apply, customer NAT redirects, usage timers, hash-rate collectors, or abuse automation until the relevant later phase gates pass.
