# Phase 2 Schema Review

Status: review record for Phase 2 repository work

This document reviews the current Phase 2 schema state and defines what is safe to do next.

## Current CI State

The latest repository CI has passed after the CLI help wording fix.

Validated by CI:

```text
pytest passes
Phase 2 schema tests pass
CLI phase-status regression test passes
```

## Current Phase State

Source of truth:

```text
docs/PHASE_STATUS.md
```

Current state:

```text
accepted_phase: Phase 1 — Preflight + Bootstrap Without Traffic Changes
working_phase: Phase 2 — PostgreSQL + Config + Domain Model
server_state: farm5 phase 1 bootstrapped and verified
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
```

## Schema Coverage Review

The current schema representation covers these groups:

```text
core config / metadata
operators / api tokens
lanes / lane upstreams
customers / policies / IP pins
events / audit / notes
firewall snapshots / applies / desired rules / live rules
restore points / backups
usage samples / policy events
flow sessions / flow events
worker events / customer workers
abuse states / abuse events
job runs / scheduler locks
blocks / pauses
notifications / notification targets
buyer accounts / buyer users / service links / permissions / action requests
worker identities / worker policies / worker blocks / worker enforcement events
plans / plan versions / subscriptions / entitlement tables
feature flags / notification rules
config snapshots / secret references
restore drills / maintenance windows
server profiles / preflight runs / preflight findings
import staging / validation errors
customer health snapshots
incidents / incident events / runbook steps
abuse profiles
```

This is intentionally broader than the first executable MVP. Many tables are future-ready contracts, not active runtime features.

## Positive Findings

### Buyer/customer separation exists

`customers` represent service/port allocations. Buyer-facing identities are represented separately by:

```text
buyer_accounts
buyer_users
customer_service_links
customer_service_permissions
action_requests
```

This prevents a future buyer panel from overloading customer service rows as login accounts.

### Worker block is not firewall-only

Worker identity and worker policy are represented separately by:

```text
worker_identities
worker_policies
worker_blocks
worker_enforcement_events
```

This preserves the fact that worker names are Stratum-layer identities, not firewall-layer identities.

### Abuse one-hour state is representable

Required state fields exist for:

```text
normal -> over_tracking -> over_grace -> hard
first_seen_over
last_seen_over
hard_applied_at
restore_point_id
policy_backup_id
last_event_id
```

The abuse runner is still forbidden until the correct later phase.

### Firewall history is representable without apply

The schema can represent:

```text
firewall_snapshots
firewall_applies
firewall_rules_desired
firewall_rules_live
restore_points
```

Live firewall apply is still forbidden in Phase 2.

### Operational control-plane extensions are represented

The schema now reserves space for:

```text
feature flags
notification rules
server profiles
preflight findings
config snapshots
secret references
restore drills
incidents
runbooks
maintenance windows
import staging
health snapshots
```

These are useful for future production hardening and UI/reporting.

## Important Risk: Dynamic Initial Migration

The current initial migration uses:

```python
Base.metadata.create_all(bind=bind)
Base.metadata.drop_all(bind=bind)
```

This is acceptable only as Phase 2 schema groundwork while the schema is still changing quickly.

Risks:

```text
- The migration is model-dependent rather than a fully frozen Alembic operation list.
- If models change later, the old migration behavior can change.
- Downgrade can drop all modeled tables.
```

Phase 2 server alignment may still test this on an empty local database, but production-style migration acceptance requires an explicit restore plan.

Before any real server migration:

```text
- verify database is empty or contains only known Phase 1 bootstrap state
- create PostgreSQL dump
- snapshot /etc/mpf
- confirm no Docker containers are running
- confirm no MPF firewall rules exist
- run migration only after review
- never run downgrade casually
```

Future improvement before production maturity:

```text
Replace dynamic create_all/drop_all migration with explicit Alembic op.create_table / op.drop_table operations once schema stabilizes.
```

## What Is Safe Now

Safe repository actions:

```text
python -m pytest
alembic heads
alembic history
alembic upgrade head on a disposable local/test database
schema review
migration dry-run planning
server alignment runbook preparation
```

Safe server actions before migration:

```text
copy repository artifact to server
inspect files
run read-only server precheck
create backup directory
run pytest if dependencies are available
run alembic heads/history without upgrade
```

## What Is Not Safe Yet

Do not run yet without explicit approval and backup:

```text
alembic upgrade head on farm5
alembic downgrade
any customer CRUD
any firewall apply
any NAT redirect
any proxy container activation
any abuse runner
any import into production tables
any UI or Telegram service
```

## Phase 2 Acceptance Remaining

Phase 2 is not accepted yet.

Remaining items:

```text
[ ] run migration against a disposable test DB
[ ] document backup/restore path for server migration
[ ] verify migration on farm5 only after explicit approval
[ ] confirm alembic_version table exists after migration
[ ] confirm expected tables exist
[ ] confirm no traffic/firewall/docker side effects
[ ] update PHASE_STATUS only after server migration verification
```

## Current Review Decision

Repository Phase 2 schema is ready for controlled test-database validation.

It is not yet approved for unguarded server execution.
