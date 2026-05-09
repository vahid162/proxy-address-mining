# PHASE STATUS

Status: Active project control file

This file is the authoritative phase gate for humans and AI coding agents. It must be checked before changing code, scripts, deployment files, services, jobs, tests, migrations, or documentation.

## Current State

```text
current_accepted_phase: Phase 4 Runtime Activation — Limited Proxy Runtime Startup accepted on farm5
current_working_phase: Phase 5 — Customer CRUD in DB Only
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only_after_phase5_gate
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

Phase 4 is accepted as a limited local-only proxy runtime activation. The accepted runtime state is intentionally narrow: Docker proxy containers may run through the guarded `phase4-runtime` profile, v2rayA UI is local-only on `127.0.0.1:2015`, and the BTC backend is local-only on `127.0.0.1:60010`.

This does **not** authorize customer NAT redirects, customer firewall rules, firewall apply, production customer onboarding, usage timers, hash-rate/share collectors, abuse automation, UI, Telegram, or public API binding.

Compatibility notes for server sync from older gate scripts:

```text
compatibility_previous_current_accepted_phase: Phase 4.2 — Runtime Activation Runbook Planning, synced and verified on farm5
compatibility_previous_current_working_phase: Phase 4 Runtime Activation Execution Review
compatibility_previous_server_state: farm5 Phase 4.2 planning synced and verified; runtime activation still not authorized
compatibility_previous_proxy_data_plane_allowed: planning_only
compatibility_previous_runtime_activation: runtime activation still not authorized
compatibility_previous_current_accepted_phase: Phase 4.1 — Compose Template + Server Config Planning
```

The compatibility notes are not the current gate. The current gate is the `Current State` block above.

## Accepted Server Results

### Phase 1 Server Result

```text
PostgreSQL active
Docker active
containerd active
mpf config validate OK
mpf doctor OK
mpf db ping OK
pytest passed
Docker has no containers
No MPF firewall rules exist
firewall.apply_mode remains plan_only
```

### Phase 2 Server Result

```text
backup/snapshot created before migration
pytest passed from /opt/mpf-py-src/.venv
alembic current/head = 0001_phase2_initial_schema
public schema table count = 64
runtime tables remain empty
Docker has no containers
No MPF firewall rules exist
firewall.apply_mode remains plan_only
no proxy data-plane was started
no production traffic was changed
```

### Phase 3 Server Result

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

### Phase 3.1 Server Result

```text
official /usr/local/bin/mpf runtime exposed Phase 3 read-only commands
mpf --version reported 0.1.0
mpf phase-status was aligned for Phase 3.1 during verification
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
pytest passed: 48 passed
runtime-facing tables remained empty
Docker had no containers
No MPF firewall/NAT rules existed
No MPF systemd/cron automation existed
No risky backend/UI ports were listening
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 4.1 Server Result

See:

```text
docs/PHASE_4_1_SERVER_RESULT.md
```

Accepted evidence:

```text
pytest passed: 60 passed
mpf config validate OK
mpf proxy config-check final_verdict: OK
Phase 4 planning gate passed
Runtime activation was still not authorized at that stage
firewall.apply_mode remained plan_only
proxy.runtime_activation_allowed remained false
Docker had no proxy runtime containers
no customer NAT redirects
no customer firewall rules
no usage timers
no abuse automation
no UI or Telegram runtime
```

### Phase 4.2 Server Sync Result

See:

```text
docs/PHASE_4_2_SERVER_SYNC_RESULT.md
```

Accepted evidence:

```text
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf proxy config-check final_verdict: OK
Phase 4.2 planning gate passed
Runtime activation was still not authorized at that stage
Docker had no proxy runtime containers
no MPF/backend firewall references detected
no risky backend/UI ports listening
no customer NAT redirects
no customer firewall rules
no usage timers
no abuse automation
no UI or Telegram runtime
```

### Phase 4 Runtime Activation Server Result

See:

```text
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
```

Accepted evidence:

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

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This is not a Phase 4 acceptance blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## What Is Allowed Now

Allowed work is limited to Phase 5 DB-only customer CRUD planning and implementation:

```text
- customer domain DTOs and service contracts
- DB-only customer create/read/update/disable planning
- DB-only validation for lane, port, expiry, and status
- repository tests for customer CRUD state transitions
- CLI/API contracts that do not touch firewall/NAT
- audit/event planning for future mutation tracking
- documentation updates that preserve phase gates
- proxy doctor/status refinements for the accepted limited runtime state
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

## Current Safety Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = limited_runtime_local_only
customer_onboarding_allowed = db_only_after_phase5_gate
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

## Phase 5 Gate

Phase 5 is **Customer CRUD in DB Only**.

Before any Phase 5 implementation is accepted:

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

## Next Planned Step

Proceed to:

```text
Phase 5 — Customer CRUD in DB Only
```

Do not move to firewall apply, customer NAT redirects, usage timers, hash-rate collectors, or abuse automation until the relevant later phase gates pass.
