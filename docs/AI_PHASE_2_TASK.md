# AI Phase 2 Task Contract

Status: active task contract for AI coding agents

This file defines the safe task boundary for Phase 2 implementation.

Read it together with:

1. `AGENTS.md`
2. `README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/SAFETY.md`
6. `docs/DATA_MODEL.md`
7. `docs/ROADMAP.md`
8. `docs/FUTURE_EXTENSIONS.md`
9. `docs/PHASE_1_SERVER_RUNBOOK.md`
10. `docs/INTRANET_INSTALL.md`

## Current Allowed Scope

Only Phase 2 repository work is allowed:

```text
PostgreSQL + Config + Domain Model
```

Allowed work:

```text
- SQLAlchemy model refinement
- Alembic migration setup
- initial schema migration
- migration tests
- schema constraint tests
- DB-only seed planning for BTC lane
- config/domain model refinement
- repository skeletons without production mutations
- documentation that preserves phase gates
- extension-ready schema contracts without runtime activation
```

Forbidden work:

```text
- live customer onboarding
- customer firewall rules
- live firewall planner/apply
- NAT redirects
- Docker proxy data-plane activation
- v2rayA activation
- forwarder activation
- usage timers
- abuse runner automation
- block or pause automation
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- runtime feature flag activation for dangerous behavior
- worker enforcement
- Stratum-aware production proxy changes
- any command that changes traffic
```

## Required Safety Invariant

During this phase:

```text
firewall.apply_mode = plan_only
```

No code path may change production traffic state.

## Required Data Model Coverage

Phase 2 schema must represent at least:

```text
lanes
lane_upstreams
customers
customer_policies
customer_ip_pins
events
audit_log
notes
firewall_applies
firewall_snapshots
firewall_rules_desired
firewall_rules_live
restore_points
usage_samples
policy_events
flow_sessions
flow_events
worker_events
customer_workers
abuse_states
abuse_events
job_runs
scheduler_locks
blocks
pauses
operators
api_tokens
notifications
notification_targets
backups
settings
```

Future-ready boundaries that must remain represented:

```text
buyer_accounts
buyer_users
customer_service_links
customer_service_permissions
action_requests
plans
plan_versions
subscriptions
subscription_items
service_entitlements
customer_policy_overrides
worker_identities
worker_policies
worker_blocks
worker_enforcement_events
feature_flags
notification_rules
config_snapshots
restore_drills
server_profiles
preflight_runs
preflight_findings
import_batches
import_staged_customers
import_validation_errors
customer_health_snapshots
incidents
incident_events
runbook_steps
maintenance_windows
secret_references
abuse_profiles
```

These future-ready tables are schema contracts only. They do not permit runtime implementation before later phase gates.

## Abuse Representation Requirement

The one-hour abuse state machine must be representable from Phase 2, even though the abuse runner is not active yet.

Required representation:

```text
normal -> over_tracking -> over_grace -> hard
threshold >= 3600 seconds
exemption requires reason and expiry
hard references restore point and policy backup
manual unhard must be auditable in later phases
```

## Buyer Boundary Requirement

Buyer-facing identity must be separate from customer service/port records.

Required representation:

```text
buyer_accounts / buyer_users
  -> customer_service_links
  -> customers as service/port records
```

Buyer actions must be represented as action requests, not direct mutations.

## Worker Boundary Requirement

Worker names are Stratum-layer identities and must not be modeled as firewall-only IP blocks.

Required representation:

```text
worker_identities
worker_policies
worker_blocks
worker_enforcement_events
```

Production worker enforcement must wait for worker/session evidence and an approved adapter in later phases.

## Firewall Representation Requirement

Firewall apply is forbidden in Phase 2, but its history and restore model must be representable.

Required representation:

```text
firewall snapshots
firewall applies
restore points
desired rules
live rules
plan JSON
snapshot before/after references
```

## Job Representation Requirement

All future recurring jobs must be observable and lockable.

Required representation:

```text
job_runs
scheduler_locks
```

## Acceptance Gate

Phase 2 can be accepted only when:

```text
[ ] SQLAlchemy models cover required schema groups.
[ ] Alembic environment exists.
[ ] Initial migration exists.
[ ] Migration upgrade works on a test database or reviewed server.
[ ] Rollback or restore strategy is documented.
[ ] Tests cover critical schema groups.
[ ] Customer policy versioning is represented.
[ ] Abuse state machine is represented.
[ ] Buyer accounts are separate from customer service rows.
[ ] Buyer action requests are represented.
[ ] Worker policy state is represented.
[ ] Worker blocks are not firewall-only.
[ ] Feature flags are represented but do not bypass phase gates.
[ ] Notification rules are represented without activating Telegram.
[ ] Server profile / preflight history is represented.
[ ] Import staging is represented and cannot directly create production rules.
[ ] Firewall restore/apply history is represented.
[ ] job_runs and scheduler_locks are represented.
[ ] No live firewall apply exists.
[ ] No customer firewall rule is created.
[ ] No NAT redirect is created.
[ ] No proxy data-plane is started.
```

## Next Human Verification

After a Phase 2 patch lands, run repository tests in a development environment first:

```bash
python -m pytest
```

Do not run Alembic migrations on the production server until the migration has been reviewed and a restore plan exists.
