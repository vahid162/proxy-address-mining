# AI Phase 3 Task

Status: active implementation boundary

This document defines what AI coding agents may implement during Phase 3.

Phase 3 is:

```text
CLI + Internal API Foundation
```

Phase 3 is not customer onboarding, firewall apply, proxy data-plane activation, usage automation, abuse automation, UI, buyer UI, Telegram, production import, or worker enforcement.

## Current Accepted State

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

## Required Reading

Before implementing Phase 3, read in order:

1. `AGENTS.md`
2. `README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/ARCHITECTURE.md`
6. `docs/SAFETY.md`
7. `docs/ROADMAP.md`
8. `docs/DATA_MODEL.md`
9. `docs/PHASE_2_SERVER_RESULT.md`
10. this file

If documents conflict, follow the stricter safety rule and update documentation before implementation.

## Phase 3 Goal

Expose safe read-only and foundation-level operations through service boundaries.

The main work is to move interfaces away from owning logic and toward this pattern:

```text
CLI / internal API
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> response DTO
```

Phase 3 may create service/repository/API skeletons, but they must not mutate production customer state or production traffic.

## Required Commands

Phase 3 should prepare or implement these read-only commands:

```bash
mpf config show
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
mpf doctor
```

The commands must use services, not direct business logic in CLI handlers.

## Allowed Work

Allowed:

```text
- read-only CLI commands
- service-layer skeletons
- repository skeletons
- internal API foundation, local/internal only
- response DTOs for config, DB, lanes, customers, jobs, and doctor status
- DB read-only inspection
- DB-only planning objects that do not create live firewall rules
- tests proving CLI/API use service boundaries
- documentation updates preserving phase gates
```

## Forbidden Work

Do not implement or activate:

```text
- production customer create/edit/delete/renew
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
- public API binding
- any switch away from firewall.apply_mode=plan_only
```

## Internal API Boundary

The internal API foundation must be safe and early-phase only.

Rules:

```text
- bind local-only when runtime binding is introduced: 127.0.0.1 or Unix socket
- no public 0.0.0.0 binding
- no direct DB writes from API route handlers
- no direct firewall commands from API route handlers
- no customer mutation endpoints during Phase 3
- no firewall apply endpoints during Phase 3
- no abuse run/hard/unhard endpoints during Phase 3
```

Phase 3 may define API shape or app skeleton, but runtime exposure must remain safe and local-only.

## Repository and Service Boundaries

Required direction:

```text
mpf/services/
  config_service.py
  db_service.py
  lane_service.py
  customer_read_service.py
  job_service.py
  doctor_service.py

mpf/repositories/
  lane_repo.py
  customer_repo.py
  job_repo.py

mpf/interfaces/
  cli.py
  api.py
```

Repositories may read PostgreSQL.
Services own validation and response shaping.
Interfaces call services and print/return DTOs.

## Read-only Customer Rule

`mpf customer list` is allowed only as read-only.

Forbidden during Phase 3:

```text
mpf customer add
mpf customer edit
mpf customer delete
mpf customer renew
mpf customer set-ips
any customer mutation API endpoint
```

Customer CRUD belongs to Phase 5.

## Read-only Lane Rule

`mpf lanes list` is allowed only as read-only.

Forbidden during Phase 3:

```text
lane create
lane edit
lane enable/disable mutation
forwarder activation
lane firewall rule creation
```

## Job Status Rule

`mpf jobs status` may read `job_runs`.

Forbidden during Phase 3:

```text
mpf jobs run abuse
mpf jobs run usage-snapshot
mpf jobs run backup
systemd timer activation
cron activation
```

## Firewall Rule

No Phase 3 code may call or wrap production firewall apply behavior.

Forbidden:

```text
iptables -A
iptables -D
iptables -I
iptables -F
iptables-restore for production apply
NAT REDIRECT creation
customer chain creation
backend exposure changes
```

Firewall model/planner implementation belongs to Phase 6.

## Abuse Rule

The one-hour abuse invariant must remain documented and represented, but automation is forbidden in Phase 3.

Required invariant:

```text
normal -> over_tracking -> over_grace -> hard
sustained miner-abuse hardens after about 3600 seconds
all active customers in all enabled lanes must be scanned when abuse automation exists
```

Forbidden during Phase 3:

```text
abuse runner
abuse hard
abuse unhard
conntrack flush
policy mutation from abuse
firewall apply from abuse
```

## Server Execution Notes

The accepted farm5 Phase 2 source artifact is:

```text
/opt/mpf-py-src
```

The current production runtime remains unchanged:

```text
/opt/mpf-py
/usr/local/bin/mpf
```

On farm5, Alembic commands must be run from `/opt/mpf-py-src` so the `mpf` user can read project-local files:

```bash
sudo -u mpf bash -lc '
cd /opt/mpf-py-src
PYTHONPATH=/opt/mpf-py-src .venv/bin/alembic -c alembic.ini current
PYTHONPATH=/opt/mpf-py-src .venv/bin/alembic -c alembic.ini heads
'
```

Do not run Alembic as the `mpf` user from `/root`.

## Phase 3 Acceptance Gate

Phase 3 is complete only when:

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

## Review Checklist

Before submitting a Phase 3 patch:

```text
[ ] Current phase guard was read.
[ ] CLI handlers are thin.
[ ] API handlers are thin.
[ ] Services own response shaping.
[ ] Repositories own DB reads.
[ ] No production customer mutation was added.
[ ] No firewall mutation was added.
[ ] No NAT redirect was added.
[ ] No proxy data-plane was started.
[ ] No usage timer was added.
[ ] No abuse automation was added.
[ ] No UI, buyer UI, or Telegram service was added.
[ ] Tests cover interface/service boundaries.
[ ] firewall.apply_mode remains plan_only.
```
