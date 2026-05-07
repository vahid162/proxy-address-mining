# PHASE STATUS

Status: Active project control file

This file tells humans and AI coding agents what phase is currently allowed.
It must be checked before writing code, scripts, deployment files, services, jobs, or tests.

## Current State

```text
current_accepted_phase: Phase 3 — CLI + Internal API Foundation
current_working_phase: Phase 4 — Compose Forward-only + Proxy Doctor Planning
server_state: farm5 phase 3 read-only CLI/API foundation completed and verified
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: planning_only
ui_allowed: no
telegram_allowed: no
```

## Phase 1 Server Result

Phase 1 bootstrap has been completed and verified on the target server `farm5`.

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

Current warning:

```text
system clock synchronization is not confirmed
systemd-timesyncd is active, but public NTP replies timed out
```

This warning is not a Phase 1, Phase 2, or Phase 3 blocker, but it must be fixed before production traffic, usage accuracy, or abuse automation.

## Phase 2 Server Result

Phase 2 schema migration has been completed and verified on `farm5`.

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

Phase 3 read-only CLI/API foundation has been completed and verified on `farm5`.

Accepted Phase 3 checks:

```text
source aligned from uploaded GitHub main archive
backup created before source alignment
pytest passed: 48 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
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

Current server source artifact:

```text
/opt/mpf-py-src
```

Current production runtime remains unchanged:

```text
/opt/mpf-py
/usr/local/bin/mpf
```

## What Is Allowed Now

Allowed work is limited to safe Phase 4 planning and repository implementation:

```text
- Phase 4 runbook/task documentation
- Compose/proxy doctor design
- local-only proxy data-plane planning
- safe configuration schema refinement for proxy doctor needs
- read-only Docker/Compose inspection helpers
- tests for proxy doctor boundaries
- documentation updates that preserve phase gates
```

Phase 4 may prepare Compose forward-only and proxy doctor foundations, but runtime activation must wait for an explicit Phase 4 task/runbook and server validation plan.

## What Is Forbidden Now

Do not implement or activate:

```text
- live customer onboarding
- customer CRUD mutation
- customer firewall rules
- live firewall apply
- NAT redirects
- usage timers
- abuse runner automation
- block or pause automation
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
- public API binding
```

Do not start Docker proxy data-plane containers, v2rayA, or forwarders until the dedicated Phase 4 execution task/runbook is written and accepted.

Customer CRUD commands that mutate production customer state are not allowed yet. Customer schema/model work is already represented, but live customer operations must wait for the proper later phase.

## Current Safety Invariant

The accepted server and repository must preserve:

```text
firewall.apply_mode = plan_only
```

Any patch that bypasses `plan_only` or introduces traffic-changing behavior before the correct phase must be rejected.

## Phase 4 Planning Gate

Before any Phase 4 runtime activation, these must exist:

```text
Phase 4 task/runbook
local-only v2rayA/forwarder binding plan
proxy doctor acceptance checks
backend direct exposure detection plan
Docker Compose rollback/stop plan
server validation script
explicit confirmation that no customer NAT redirect will be created
```

## Next Planned Step

Plan Phase 4 in the repository first:

```text
Compose Forward-only + Proxy Doctor
```

Do not move to customer CRUD, firewall apply, customer NAT redirects, usage timers, or abuse automation until the relevant later phase gates pass.
