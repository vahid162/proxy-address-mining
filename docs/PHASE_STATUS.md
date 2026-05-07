# PHASE STATUS

Status: Active project control file

This file tells humans and AI coding agents what phase is currently allowed.
It must be checked before writing code, scripts, deployment files, services, jobs, or tests.

## Current State

```text
current_accepted_phase: Phase 1 — Preflight + Bootstrap Without Traffic Changes
current_working_phase: Phase 2 — PostgreSQL + Config + Domain Model Planning
server_state: farm5 phase 1 bootstrapped and verified
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

This warning is not a Phase 1 blocker, but it must be fixed before production traffic or abuse automation.

## What Is Allowed Now

Allowed work is limited to safe Phase 2 repository implementation and documentation:

```text
- PostgreSQL schema design
- Alembic migration setup
- SQLAlchemy model skeletons
- config/domain model refinement
- lane model
- customer model in schema only
- policy model in schema only
- abuse state representation in schema only
- event/audit representation
- job_runs and scheduler_locks representation
- restore_points and firewall_snapshots representation
- tests for schema constraints and config safety
- documentation updates that preserve phase gates
```

Phase 2 may prepare database schema and domain contracts, but it must not activate production traffic.

## What Is Forbidden Now

Do not implement or activate:

```text
- live customer onboarding
- customer firewall rules
- live firewall planner/apply
- NAT redirects
- Docker proxy data-plane
- v2rayA or forwarder activation
- usage timers
- abuse runner automation
- block or pause automation
- local UI service
- Telegram bot
- production customer import
```

Customer CRUD commands that mutate production customer state are not allowed yet. Customer schema/model work is allowed only as Phase 2 groundwork.

## Current Safety Invariant

The accepted server and repository must preserve:

```text
firewall.apply_mode = plan_only
```

Any patch that bypasses `plan_only` or introduces traffic-changing behavior before the correct phase must be rejected.

## Phase 2 Completion Gate

Phase 2 is complete only after these are true:

```text
PostgreSQL schema is implemented through migrations
migration upgrade works
rollback or restore strategy is documented
config validation passes
DB ping passes
BTC lane seed exists or is clearly represented
customer policy versioning is represented
abuse state machine is representable
firewall restore/apply history is representable
job_runs and scheduler_locks are representable
event/audit is mandatory for mutations in later phases
tests cover critical constraints and relationships
no live firewall apply exists
no customer firewall rule exists
no NAT redirect exists
no proxy data-plane is started
```

## Next Planned Step

Implement Phase 2 in the repository only:

```text
PostgreSQL + Config + Domain Model
```

Do not move to customer CRUD, firewall apply, proxy containers, usage timers, or abuse automation until the relevant later phase gates pass.
