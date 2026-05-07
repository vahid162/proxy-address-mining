# Phase 2 Server Result

Status: accepted server result

Server:

```text
farm5
```

Phase:

```text
Phase 2 — PostgreSQL + Config + Domain Model
```

## Summary

Phase 2 schema migration was executed and verified on the server.

Only PostgreSQL schema changed.

No production traffic, firewall, Docker data-plane, customer onboarding, abuse automation, UI, Telegram, or import behavior was activated.

## Backup Before Migration

Backup directory:

```text
/var/backups/mpf/phase2-align-20260507T085831Z
```

Recorded artifacts:

```text
mpf-before-phase2.dump
/etc/mpf snapshot
iptables-save.before
ss-lntup.before
docker-ps-a.before
timedatectl.before
db-public-tables.before
mpf-config-safety.before
SHA256SUMS
```

## Migration Command Pattern

Alembic was executed as the system user `mpf` to match local PostgreSQL peer-auth behavior.

Required command pattern:

```bash
sudo -u mpf env PYTHONPATH=/opt/mpf-py-src \
  /opt/mpf-py-src/.venv/bin/alembic \
  -c /opt/mpf-py-src/alembic.ini \
  upgrade head
```

## Verification Result

Accepted checks:

```text
alembic_version = 0001_phase2_initial_schema
public schema table count = 64
required table check passed
missing required table count = 0
runtime tables remain empty
venv CLI checks passed
Docker has no containers
No MPF firewall rules exist
PostgreSQL listens on 127.0.0.1:5432
firewall.apply_mode remains plan_only
no proxy/backend data-plane was started
no production traffic was changed
```

Required tables verified:

```text
abuse_events
abuse_profiles
abuse_states
action_requests
alembic_version
buyer_accounts
buyer_users
config_snapshots
customer_health_snapshots
customer_ip_pins
customer_policies
customers
customer_service_links
feature_flags
firewall_applies
firewall_rules_desired
firewall_rules_live
firewall_snapshots
import_batches
import_staged_customers
import_validation_errors
incident_events
incidents
job_runs
lanes
lane_upstreams
maintenance_windows
notification_rules
plans
plan_versions
preflight_findings
preflight_runs
restore_drills
restore_points
runbook_steps
scheduler_locks
secret_references
server_profiles
service_entitlements
subscriptions
worker_blocks
worker_enforcement_events
worker_identities
worker_policies
```

## Empty Runtime Tables Verified

The following runtime-facing tables were verified empty after migration:

```text
abuse_states = 0
buyer_accounts = 0
customers = 0
firewall_applies = 0
job_runs = 0
lanes = 0
worker_blocks = 0
```

## Still Forbidden After Phase 2

Do not activate yet:

```text
customer CRUD mutation
customer firewall rules
firewall apply
NAT redirects
Docker proxy data-plane
v2rayA / forwarder
usage timers
abuse runner
block/pause automation
local UI
buyer UI
Telegram
production import
worker enforcement
```

## Known Warning

Time synchronization is still not confirmed.

This must be fixed before production traffic, usage accounting, or abuse automation.

## Next Phase

Next working phase:

```text
Phase 3 — CLI + Internal API Foundation
```

Phase 3 must remain read-only / non-traffic-changing until its acceptance gate passes.
