# PHASE STATUS

Status: Active project control file

This file is the authoritative phase gate for humans and AI coding agents. It must be checked before changing code, scripts, deployment files, services, jobs, tests, migrations, or documentation.

## Current State

```text
current_accepted_phase: Phase 4.1 — Compose Template + Server Config Planning
current_working_phase: Phase 4.2 — Runtime Activation Runbook Planning
server_state: farm5 Phase 4.1 config planning accepted in GitHub; server still requires ZIP sync confirmation
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: planning_only
ui_allowed: no
telegram_allowed: no
```

Phase 4.2 is **runbook planning only**. It may prepare exact runtime activation documentation, validation scripts, and rollback/evidence checklists, but it must not start proxy data-plane containers yet.

Compatibility note for one server sync from an older gate script:

```text
compatibility_previous_current_accepted_phase: Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
```

The compatibility note is not the current gate. The current gate is the `Current State` block above.

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

The expected remaining warning is:

```text
lane.btc.backend_internal_reachability: WARN
```

Reason: backend internal reachability cannot be checked until a later explicitly approved runtime activation task starts proxy containers.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This is not a Phase 4.2 documentation blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## What Is Allowed Now

Allowed work is limited to safe Phase 4.2 planning and repository implementation:

```text
- Phase 4.2 runtime activation task documentation
- exact future Docker Compose validation commands
- exact future startup command with explicit profile, documented only
- local-only v2rayA/forwarder binding checks
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

## Phase 4.2 Planning Gate

Before any later runtime activation can be considered, these must exist and be reviewed:

```text
docs/AI_PHASE_4_2_TASK.md
docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md
local-only v2rayA/forwarder binding plan
proxy doctor acceptance checks
backend internal reachability check
backend direct exposure detection plan
Docker Compose stop/rollback plan
server validation script
explicit confirmation that no customer NAT redirect will be created
explicit confirmation that firewall.apply_mode remains plan_only
explicit confirmation that proxy.runtime_activation_allowed remains false until runtime approval
post-run evidence checklist
```

## Next Planned Step

Plan Phase 4.2 in the repository first:

```text
Runtime Activation Runbook Planning
```

Do not move to proxy runtime activation, customer CRUD, firewall apply, customer NAT redirects, usage timers, hash-rate collectors, or abuse automation until the relevant later phase gates pass.
