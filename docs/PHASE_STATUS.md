# PHASE STATUS

Status: Active project control file

This file tells humans and AI coding agents what phase is currently allowed.
It must be checked before writing code, scripts, deployment files, services, jobs, or tests.

## Current State

```text
current_accepted_phase: Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
current_working_phase: Phase 4 — Compose Forward-only + Proxy Doctor Planning
server_state: farm5 Phase 3.1 runtime alignment completed and verified
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: planning_only
ui_allowed: no
telegram_allowed: no
```

Phase 4 is planning-only until a dedicated Phase 4 runbook/task is accepted. It may prepare Compose/proxy doctor design and safe read-only inspection helpers, but it must not start proxy data-plane containers yet.

## Phase 1 Server Result

Phase 1 bootstrap was completed and verified on `farm5`.

Accepted Phase 1 checks:

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

## Phase 2 Server Result

Phase 2 schema migration was completed and verified on `farm5`.

Accepted Phase 2 checks:

```text
backup/snapshot created before migration
pytest passed from /opt/mpf-py-src/.venv
alembic heads/history passed
alembic current worked as system user mpf
alembic upgrade head completed
alembic_version = 0001_phase2_initial_schema
public schema table count = 64
required table check passed
missing required table count = 0
runtime tables remain empty
Docker has no containers
No MPF firewall rules exist
firewall.apply_mode remains plan_only
no proxy data-plane was started
no production traffic was changed
```

Backup artifact recorded on server:

```text
/var/backups/mpf/phase2-align-20260507T085831Z
```

## Phase 3 Server Result

Phase 3 read-only CLI/API foundation source was completed and verified on `farm5` under:

```text
/opt/mpf-py-src
```

Accepted Phase 3 source checks:

```text
source aligned from uploaded GitHub main archive
backup created before source alignment
pytest passed: 48 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK from Phase 3 source path
mpf lanes list OK and read-only from Phase 3 source path
mpf customer list OK and read-only from Phase 3 source path
mpf jobs status OK and read-only from Phase 3 source path
alembic current/head = 0001_phase2_initial_schema
public schema table count = 64
runtime tables remain empty
Docker has no containers
No MPF firewall or NAT rules exist
No MPF systemd units/timers exist
No MPF cron jobs exist
firewall.apply_mode remains plan_only
no production traffic was changed
```

Backup artifact recorded on server:

```text
/var/backups/mpf/phase3-source-align-20260507T140233Z
```

See also:

```text
docs/PHASE_3_SERVER_RESULT.md
```

## Phase 3.1 Server Result

Phase 3.1 runtime alignment was completed and verified on `farm5`.

Accepted Phase 3.1 checks:

```text
official /usr/local/bin/mpf runtime exposes Phase 3 read-only commands
mpf --version reported 0.1.0
mpf phase-status reported Phase 3 accepted / Phase 3.1 working during verification
mpf config validate OK
mpf config show OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
pytest passed: 48 passed
alembic current/head = 0001_phase2_initial_schema
runtime-facing tables remain empty
Docker has no containers
No MPF firewall/NAT rules exist
No MPF systemd/cron automation exists
No risky backend/UI ports are listening
firewall.apply_mode remains plan_only
no production traffic was changed
```

Source backup before final Phase 3.1 verification:

```text
/var/backups/mpf/source-before-phase3-1-20260508T133637Z
```

Runtime backup before final promotion:

```text
/var/backups/mpf/phase3-runtime-promote-20260508T133650Z
```

See also:

```text
docs/PHASE_3_1_SERVER_RESULT.md
```

## Current Server Warning

Time synchronization is still not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This warning is not a Phase 1, Phase 2, Phase 3, or Phase 3.1 blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## What Is Allowed Now

Allowed work is limited to safe Phase 4 planning and repository implementation:

```text
- Phase 4 runbook/task documentation
- Compose/proxy doctor design
- backend internal reachability probe design
- backend external exposure probe design
- local-only v2rayA/forwarder binding plan
- safe configuration schema refinement for proxy doctor needs
- read-only Docker/Compose inspection helpers
- tests for proxy doctor boundaries
- documentation updates that preserve phase gates
```

Phase 4 may prepare Compose forward-only and proxy doctor foundations, but runtime activation must wait for an explicit Phase 4 execution task/runbook and server validation plan.

## What Is Forbidden Now

Do not implement or activate:

```text
- live customer onboarding
- customer CRUD mutation
- customer firewall rules
- live firewall apply
- NAT redirects
- usage timers
- hash-rate/share collectors
- abuse runner automation
- block or pause automation
- Docker proxy data-plane containers without an accepted Phase 4 execution runbook
- v2rayA runtime without an accepted Phase 4 execution runbook
- forwarder/gost runtime without an accepted Phase 4 execution runbook
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
- public API binding
```

Customer schema/model work is already represented, but live customer operations must wait for the proper later phase.

## Current Safety Invariant

The accepted server and repository must preserve:

```text
firewall.apply_mode = plan_only
```

Any patch that bypasses `plan_only` or introduces traffic-changing behavior before the correct phase must be rejected.

## Backend Port Invariant

Backend ports must be blocked from direct external/public access only. They must remain reachable from valid internal server and Docker paths.

Required future proxy/firewall doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by blocking loopback, local server paths, required Docker/internal paths, or the future MPF-owned NAT redirect path.

## Hash-rate and Share Observability Invariant

Accepted/rejected hash-rate per device is a future first-class capability.

It must be planned through:

```text
share evidence
share_events
device_hashrate_samples
customer_hashrate_samples
report services
UI charts from aggregate samples
retention before high-volume collection
```

Do not implement it later as UI-only calculations or unstructured log parsing.

## Phase 4 Planning Gate

Before any Phase 4 runtime activation, these must exist:

```text
Phase 4 task/runbook
local-only v2rayA/forwarder binding plan
proxy doctor acceptance checks
backend internal reachability check
backend direct exposure detection plan
Docker Compose rollback/stop plan
server validation script
explicit confirmation that no customer NAT redirect will be created
explicit confirmation that firewall.apply_mode remains plan_only
```

## Next Planned Step

Plan Phase 4 in the repository first:

```text
Compose Forward-only + Proxy Doctor
```

Do not move to customer CRUD, firewall apply, customer NAT redirects, usage timers, hash-rate collectors, or abuse automation until the relevant later phase gates pass.
