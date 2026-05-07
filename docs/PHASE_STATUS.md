# PHASE STATUS

Status: Active project control file

This file tells humans and AI coding agents what phase is currently allowed.
It must be checked before writing code, scripts, deployment files, services, jobs, or tests.

## Current State

```text
current_accepted_phase: Phase 2 — PostgreSQL + Config + Domain Model
current_working_phase: Phase 3 — CLI + Internal API Foundation Planning
server_state: farm5 phase 2 schema migration completed and verified
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
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

This warning is not a Phase 1 or Phase 2 blocker, but it must be fixed before production traffic, usage accuracy, or abuse automation.

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

Allowed work is limited to safe Phase 3 planning and repository implementation:

```text
- CLI read-only commands through services
- internal API foundation design
- service/repository skeletons without production traffic mutation
- DB read-only inspection commands
- DB-only planning commands that do not create live firewall rules
- tests for interface/service boundaries
- documentation updates that preserve phase gates
```

Phase 3 may prepare CLI/API foundations, but it must not activate production traffic.

## What Is Forbidden Now

Do not implement or activate:

```text
- live customer onboarding
- customer firewall rules
- live firewall apply
- NAT redirects
- Docker proxy data-plane
- v2rayA or forwarder activation
- usage timers
- abuse runner automation
- block or pause automation
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
```

Customer CRUD commands that mutate production customer state are not allowed yet. Customer schema/model work is already represented, but live customer operations must wait for the proper later phase.

## Current Safety Invariant

The accepted server and repository must preserve:

```text
firewall.apply_mode = plan_only
```

Any patch that bypasses `plan_only` or introduces traffic-changing behavior before the correct phase must be rejected.

## Phase 3 Completion Gate

Phase 3 is complete only after these are true:

```text
CLI uses services, not direct business logic
internal API foundation uses services
read-only DB-backed commands work
DB status command works
lane list command is read-only
customer list command is read-only
job status command is read-only
all interface commands are tested
no live firewall apply exists
no customer firewall rule exists
no NAT redirect exists
no proxy data-plane is started
no production customer mutation exists
```

## Next Planned Step

Plan and implement Phase 3 in the repository first:

```text
CLI + Internal API Foundation
```

Do not move to customer CRUD, firewall apply, proxy containers, usage timers, or abuse automation until the relevant later phase gates pass.
