# PHASE STATUS

Status: Active project control file

This file is the authoritative phase gate for humans and AI coding agents. It must be checked before changing code, scripts, deployment files, services, jobs, tests, migrations, or documentation.

## Current State

```text
current_accepted_phase: Phase 4.2 — Runtime Activation Runbook Planning, synced and verified on farm5
current_working_phase: Phase 4 Runtime Activation Execution Review
server_state: farm5 Phase 4.2 planning synced and verified; runtime activation still not authorized
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: planning_only
ui_allowed: no
telegram_allowed: no
```

Phase 4 runtime activation execution is **not authorized yet**. The current step is review only. It may prepare an explicit approval decision for a limited proxy runtime activation execution step, but it must not start proxy data-plane containers yet.

Compatibility notes for server sync from older gate scripts:

```text
compatibility_previous_current_accepted_phase: Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
compatibility_previous_current_accepted_phase: Phase 4.1 — Compose Template + Server Config Planning
compatibility_previous_current_working_phase: Phase 4.2 — Runtime Activation Runbook Planning
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

Phase 4.1 was accepted in GitHub as Compose Template + Server Config Planning.

See:

```text
docs/PHASE_4_1_SERVER_RESULT.md
```

Accepted evidence recorded there:

```text
pytest passed: 60 passed
mpf config validate OK
mpf proxy config-check final_verdict: OK
mpf proxy status final_verdict: WARN
mpf proxy doctor final_verdict: WARN
Phase 4 planning gate passed
Runtime activation is still NOT authorized
firewall.apply_mode remains plan_only
proxy.runtime_activation_allowed remains false
Docker has no proxy runtime containers
no customer NAT redirects
no customer firewall rules
no usage timers
no abuse automation
no UI or Telegram runtime
```

### Phase 4.2 Server Sync Result

Phase 4.2 planning artifacts were synced and verified on farm5.

See:

```text
docs/PHASE_4_2_SERVER_SYNC_RESULT.md
```

Accepted evidence recorded there:

```text
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf proxy config-check final_verdict: OK
mpf proxy status final_verdict: WARN
mpf proxy doctor final_verdict: WARN
Phase 4.2 planning gate passed
Runtime activation is still NOT authorized
Docker has no proxy runtime containers
no MPF/backend firewall references detected
no risky backend/UI ports listening
no customer NAT redirects
no customer firewall rules
no usage timers
no abuse automation
no UI or Telegram runtime
```

The expected remaining warning is:

```text
lane.btc.backend_internal_reachability: WARN
```

Reason: backend internal reachability cannot be checked until a later explicitly approved runtime activation execution step starts proxy containers.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This is not a Phase 4 runtime activation execution review blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## What Is Allowed Now

Allowed work is limited to safe review and repository implementation:

```text
- review Phase 4 runtime activation execution readiness
- document operator approval requirements
- exact future Docker Compose validation commands
- exact future startup command with explicit profile, documented only
- local-only v2rayA/forwarder binding checks, documented only
- backend internal reachability test plan
- backend external exposure test plan
- v2rayA UI local-only test plan
- stop/rollback commands for future runtime activation
- post-run evidence checklist
- server validation script updates that do not start runtime
- documentation updates that preserve phase gates
- tests that verify forbidden runtime commands remain unavailable
```

## What Is Forbidden Now

Do not implement, run, or activate:

```text
- docker compose up
- docker run
- v2rayA runtime
- forwarder/gost runtime
- live customer onboarding
- customer CRUD mutation
- customer firewall rules
- live firewall apply
- NAT redirects
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
```

## Current Safety Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
customer_onboarding_allowed = no
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = planning_only
```

Any patch that bypasses these invariants or introduces traffic-changing behavior before the correct accepted phase must be rejected.

## Backend Port Invariant

Backend ports are internal service ports. They must be blocked from direct external/public access only while remaining reachable from valid internal server and Docker paths.

Required future proxy/firewall doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by blocking loopback, local server paths, required Docker/internal paths, or the future MPF-owned NAT redirect path.

## Hash-rate and Share Observability Invariant

Accepted/rejected hash-rate per device is a future first-class capability. It must be planned through structured evidence, aggregate samples, services, retention, and UI/reporting boundaries. It must not be implemented as UI-only calculations or unstructured log parsing.

## Phase 4 Runtime Activation Execution Review Gate

Before any runtime activation execution can be approved, these must exist and be reviewed:

```text
docs/AI_PHASE_4_2_TASK.md
docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md
docs/PHASE_4_2_SERVER_SYNC_RESULT.md
docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md
local-only v2rayA/forwarder binding plan
proxy doctor acceptance checks
backend internal reachability check
backend direct exposure detection plan
Docker Compose stop/rollback plan
server validation evidence
explicit confirmation that no customer NAT redirect will be created
explicit confirmation that firewall.apply_mode remains plan_only
explicit confirmation that proxy.runtime_activation_allowed remains false until explicit runtime approval
post-run evidence checklist
```

## Next Planned Step

Review whether to approve a limited Phase 4 runtime activation execution step:

```text
Phase 4 Runtime Activation Execution Review
```

Do not move to proxy runtime activation, customer CRUD, firewall apply, customer NAT redirects, usage timers, hash-rate collectors, or abuse automation until the relevant explicit approval and later phase gates pass.
