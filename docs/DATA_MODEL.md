# DATA MODEL

Status: Draft v1

This document defines the PostgreSQL data model contract for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

## Goal

PostgreSQL is the source of truth for customer state, policy state, firewall desired state, abuse state, usage, events, jobs, and restore metadata.

Flat files and SQLite are not production sources of truth.

Allowed non-primary uses:

- import from old scripts
- export/debug artifacts
- temporary migration tooling
- backup artifacts
- generated firewall restore files

## Database Principles

- Use PostgreSQL locally.
- Use migrations for every schema change.
- Use typed models in Python.
- Do not store production state in scattered files.
- Do not allow UI/Telegram/CLI to directly mutate tables.
- All mutations go through services/repositories.
- Every dangerous mutation creates event/audit records.
- Every destructive or risky action creates a restore point.
- Buyer accounts are separate from customer service/port records.
- Worker block policy is not a firewall-only concept.

## Migration Tooling

Recommended:

```text
SQLAlchemy
Alembic
PostgreSQL
```

Required migration behavior:

- migrations are versioned
- upgrade path is tested
- downgrade or restore strategy exists for risky changes
- schema version is visible through CLI
- migrations do not run implicitly inside unrelated commands

Required commands:

```bash
mpf db status
mpf db ping
mpf db migrate
mpf db revision
```

## Naming Rules

Use plural table names.

Use timestamps with timezone where practical.

Recommended common columns:

```text
id
created_at
updated_at
created_by
updated_by
```

Use explicit status enums, not ambiguous booleans, for lifecycle objects.

## Core Tables

Minimum v1 table groups:

```text
configuration / metadata:
  schema_migrations
  settings
  operators
  api_tokens

lanes and customers:
  lanes
  lane_upstreams
  customers
  customer_policies
  customer_ip_pins

future buyer boundary:
  buyer_accounts
  buyer_users
  customer_service_links
  customer_service_permissions
  action_requests

operations:
  events
  audit_log
  notes

firewall:
  firewall_applies
  firewall_snapshots
  firewall_rules_desired
  firewall_rules_live
  restore_points

usage and observability:
  usage_samples
  policy_events
  flow_sessions
  flow_events
  worker_events
  customer_workers
  worker_identities
  worker_policies
  worker_blocks
  worker_enforcement_events

abuse:
  abuse_states
  abuse_events

jobs:
  job_runs
  scheduler_locks

controls:
  blocks
  pauses

notifications:
  notifications
  notification_targets

backup:
  backups
```

## Customers and Buyer Accounts

### `customers`

Purpose: stable customer service identity and port assignment.

Important: this table is not a human login account. A customer row represents a mining service/port allocation.

Required fields:

```text
id
lane_id
name
port
status                  active / paused / expired / deleted
starts_at
expires_at
created_at
updated_at
created_by
updated_by
```

Constraints:

- `port` unique among non-deleted customers.
- `name` should be unique or scoped clearly.
- `lane_id` required.

Status behavior:

```text
active   -> normal forwarding if policy permits
paused   -> reject/pause behavior
expired  -> no normal forwarding unless explicit grace policy exists
deleted  -> removed from desired firewall model after safe deletion
```

### `buyer_accounts`

Purpose: future buyer/customer account boundary for a buyer-facing panel.

Required fields:

```text
id
account_key             unique stable account reference
display_name
status                  active / suspended / closed
notes
created_at
updated_at
```

Rules:

- Buyer accounts must not be stored inside `customers`.
- A buyer account can own zero or more customer service records through `customer_service_links`.
- Buyer UI must be read-only first.

### `buyer_users`

Purpose: future login identities under a buyer account.

Required fields:

```text
id
buyer_account_id
email
display_name
password_hash           nullable until auth is implemented
status
last_login_at
created_at
updated_at
```

Rules:

- Do not implement public login until the UI/auth phase.
- Store hashes only. Never store raw passwords.

### `customer_service_links`

Purpose: link buyer accounts to customer service/port records.

Required fields:

```text
id
buyer_account_id
customer_id
status
starts_at
ends_at
created_at
created_by
reason
```

### `customer_service_permissions`

Purpose: lightweight future permissions for buyer-visible services.

Required fields:

```text
id
buyer_user_id
customer_id
scope                   view_report / view_usage / request_action, later
enabled
created_at
created_by
```

This is intentionally not a heavy enterprise RBAC system.

### `action_requests`

Purpose: future request/approval queue for buyer-safe actions.

Required fields:

```text
id
requester_type          buyer / operator / system
requester_id
action_type             renew_request / unpause_request / support_request / ip_change_request, later
target_type
target_id
status                  pending / approved / rejected / executed / cancelled
payload_json
created_at
reviewed_by
reviewed_at
review_reason
```

Rules:

- Buyer UI should create requests, not directly mutate customers, firewall, abuse, blocks, pauses, or policies.
- Dangerous requests must require operator review and event/audit in later phases.

## Customer Policies

### `customer_policies`

Purpose: versioned customer policy.

Required fields:

```text
id
customer_id
version
is_current
miners
farms
maxconn
rate_per_min
burst
ips_mode                any / whitelist
abuse_exempt            bool
abuse_exempt_reason
abuse_exempt_until
abuse_exempt_by
created_at
created_by
reason
```

Rules:

- Policy updates create a new version.
- Do not overwrite policy history.
- Hard/unhard must preserve enough policy history to restore safely.
- Abuse exemption requires reason and expiry.

### `customer_ip_pins`

Purpose: optional whitelist/source IP control.

Required fields:

```text
id
customer_id
ip_cidr
enabled
created_at
created_by
reason
```

## Lanes

### `lanes`

Purpose: enabled coin/proxy lanes.

Required fields:

```text
id
name                    unique, e.g. btc
enabled                 bool
backend_port            integer, unique among enabled lanes
chain_prefix            text
protocol                text, e.g. stratum
created_at
updated_at
```

Rules:

- BTC lane uses backend `60010`.
- Additional coins must be added as lanes.
- Do not clone command trees per coin.

### `lane_upstreams`

Purpose: mining pool endpoints per lane.

Required fields:

```text
id
lane_id
host
port
priority
enabled
created_at
updated_at
```

## Worker Policy and Enforcement Boundary

Worker names are Stratum-layer identities. Firewall rules can block IPs and ports, but cannot reliably understand a worker name by themselves.

### `worker_identities`

Purpose: observed and normalized worker identities.

Required fields:

```text
id
customer_id
worker_name
normalized_worker_name
first_seen_at
last_seen_at
status
```

### `worker_policies`

Purpose: future worker policy mode per customer.

Required fields:

```text
id
customer_id
mode                    allow_all / block_list / allow_list
created_at
created_by
reason
```

### `worker_blocks`

Purpose: future worker block rules.

Required fields:

```text
id
customer_id
worker_name
match_type              exact / prefix / regex
reason
starts_at
expires_at
status                  active / expired / removed
created_at
created_by
removed_at
removed_by
```

### `worker_enforcement_events`

Purpose: evidence/audit trail for worker enforcement decisions.

Required fields:

```text
id
customer_id
worker_name
src_ip
action                  observed / blocked / rejected / killed_session
adapter                 detection_only / stratum_proxy / manual, later
evidence_json
created_at
created_by
```

Rules:

- Worker blocking is not accepted as firewall-only.
- Strict worker enforcement requires future Stratum-aware data-plane support.
- Detection-only worker actions must record confidence and evidence.

## Events and Audit

### `events`

Purpose: structured operational event stream.

Required fields:

```text
id
event_type
severity                info / warning / error / critical
subject_type            customer / firewall / abuse / job / backup / system / lane / block / pause
subject_id
message
data_json
created_at
created_by
correlation_id
```

Events are for operator-visible history and reporting.

### `audit_log`

Purpose: security and mutation audit.

Required fields:

```text
id
actor_type              operator / job / system / api_token
actor_id
action
resource_type
resource_id
before_json
after_json
reason
created_at
correlation_id
```

Audit is required for dangerous actions.

### `notes`

Purpose: operator notes attached to customer/IP/general objects.

Required fields:

```text
id
subject_type
subject_key
message
created_at
created_by
```

## Firewall Tables

### `firewall_applies`

Purpose: each firewall apply/rollback record.

Required fields:

```text
id
action                  apply / rollback / verify
status                  planned / applied / failed / rolled_back
apply_mode
backend
restore_point_id
snapshot_before_id
snapshot_after_id
plan_json
summary
started_at
finished_at
created_by
error_message
correlation_id
```

### `firewall_snapshots`

Purpose: stored live firewall snapshots.

Required fields:

```text
id
backend
iptables_save_text
checksum
created_at
created_by
reason
```

### `firewall_rules_desired`

Purpose: optional materialized desired firewall model for diff/debug.

Required fields:

```text
id
apply_id
customer_id
lane_id
table_name
chain_name
rule_key
rule_text
rule_json
created_at
```

### `firewall_rules_live`

Purpose: optional parsed live firewall model for diff/debug.

Required fields:

```text
id
snapshot_id
table_name
chain_name
rule_key
rule_text
rule_json
created_at
```

### `restore_points`

Purpose: restore metadata before dangerous actions.

Required fields:

```text
id
restore_type            firewall / abuse / policy / backup / migration / bulk_change
subject_type
subject_id
snapshot_id
backup_id
metadata_json
created_at
created_by
reason
checksum
```

Rules:

- Required before firewall apply.
- Required before abuse hard/unhard.
- Required before bulk policy changes.
- Restore must be testable.

## Usage and Observability

### `usage_samples`

Purpose: periodic customer counter snapshots.

Required fields:

```text
id
customer_id
lane_id
port
bytes_in
bytes_out
packets_in
packets_out
connlimit_rejects
hashlimit_rejects
pause_rejects
block_rejects
sampled_at
source
```

Rules:

- Deltas are calculated from ordered snapshots.
- Counter resets must be detected.

### `policy_events`

Purpose: reject/policy events derived from firewall counters or logs.

Required fields:

```text
id
customer_id
lane_id
port
src_ip
event_type              connlimit_reject / hashlimit_reject / pause_reject / block_reject / whitelist_reject
counter_delta
evidence_json
seen_at
created_at
```

### `flow_sessions`

Purpose: active and recent connection/session ledger.

Required fields:

```text
id
customer_id
lane_id
port
src_ip
src_port
dst_ip
dst_port
protocol
state
started_at
last_seen_at
ended_at
evidence_json
```

### `flow_events`

Purpose: session timeline events.

Required fields:

```text
id
flow_session_id
customer_id
event_type
message
data_json
created_at
```

### `worker_events`

Purpose: observed mining worker activity.

Required fields:

```text
id
customer_id
lane_id
port
src_ip
worker_name
event_type              authorize / submit / observed / mismatch
confidence
seen_at
evidence_json
```

### `customer_workers`

Purpose: latest known worker mapping per customer.

Required fields:

```text
id
customer_id
worker_name
first_seen_at
last_seen_at
last_src_ip
seen_count
status
```

## Abuse Tables

### `abuse_states`

Purpose: current abuse state per customer.

Required fields:

```text
customer_id             primary key
status                  normal / over_tracking / over_grace / hard
current_hot
current_unique_ips
current_unique_workers
first_seen_over
last_seen_over
last_recovery_at
hard_applied_at
policy_backup_id
restore_point_id
last_event_id
updated_at
```

Rules:

- One row per customer.
- Every active customer must be evaluatable.
- Hard/unhard must be evented and audited.

### `abuse_events`

Purpose: abuse-specific event timeline.

Required fields:

```text
id
customer_id
old_status
new_status
event_type
evidence_json
policy_backup_id
restore_point_id
created_at
created_by
```

## Jobs

### `job_runs`

Purpose: status of recurring and manual jobs.

Required fields:

```text
id
job_name
status                  running / succeeded / failed / degraded
started_at
finished_at
duration_ms
affected_count
error_message
data_json
correlation_id
```

Every systemd timer job must write a row.

### `scheduler_locks`

Purpose: DB-backed job locks.

Required fields:

```text
lock_name               primary key
owner
acquired_at
expires_at
metadata_json
```

Locks required for:

- abuse runner
- usage snapshot
- firewall apply
- backup
- block expiry
- pause sync

## Blocks and Pauses

### `blocks`

Purpose: global or customer-scoped IP/port blocks.

Required fields:

```text
id
scope                   global_ip / customer_ip / port_ip
customer_id
ip_cidr
port
reason
starts_at
expires_at
status                  active / expired / removed
created_at
created_by
removed_at
removed_by
```

IP/port blocks are separate from worker blocks.

### `pauses`

Purpose: temporary customer pause.

Required fields:

```text
id
customer_id
reason
starts_at
expires_at
status                  active / expired / removed
created_at
created_by
removed_at
removed_by
```

## Operators and API Tokens

### `operators`

Purpose: local operator identity for audit/UI/API.

Required fields:

```text
id
username
display_name
role
active
created_at
updated_at
```

### `api_tokens`

Purpose: future local API/UI/Telegram tokens.

Required fields:

```text
id
operator_id
name
token_hash
scopes
last_used_at
expires_at
revoked_at
created_at
```

Rules:

- Store token hashes only.
- Never store raw tokens after creation.

## Notifications

### `notification_targets`

Purpose: configured notification outputs.

Required fields:

```text
id
type                    telegram / local_log / webhook
name
enabled
config_json             no raw secrets
created_at
updated_at
```

### `notifications`

Purpose: notification delivery queue/history.

Required fields:

```text
id
target_id
event_id
status                  pending / sent / failed / skipped
attempt_count
last_error
created_at
sent_at
```

Telegram starts as notification-only.

## Backups

### `backups`

Purpose: backup metadata.

Required fields:

```text
id
backup_type             db / config / firewall / full
path
checksum
status                  created / failed / verified / restored
created_at
created_by
verified_at
error_message
metadata_json
```

Rules:

- Backup is not accepted until restore is tested.
- Restore test should be recorded.

## Relationships and Ownership

Service ownership:

```text
customer_service owns customers/customer_policies/customer_ip_pins
buyer_service owns buyer_accounts/buyer_users/customer_service_links/customer_service_permissions/action_requests
worker_policy_service owns worker_identities/worker_policies/worker_blocks/worker_enforcement_events
firewall_service owns firewall_* and restore_points for firewall operations
abuse_service owns abuse_states/abuse_events and calls firewall_service for hard/unhard
usage_service owns usage_samples/policy_events
job_service owns job_runs/scheduler_locks
backup_service owns backups and restore metadata
notification_service owns notifications/notification_targets
```

No interface owns tables directly.

## Index Requirements

Recommended indexes:

```text
customers(port)
customers(status)
customers(lane_id, status)
customer_policies(customer_id, is_current)
buyer_accounts(account_key)
buyer_users(buyer_account_id, email)
customer_service_links(buyer_account_id, status)
action_requests(status, created_at)
usage_samples(customer_id, sampled_at)
policy_events(customer_id, seen_at)
flow_sessions(customer_id, last_seen_at)
worker_events(customer_id, seen_at)
worker_identities(customer_id, status)
worker_blocks(customer_id, status)
worker_enforcement_events(customer_id, created_at)
abuse_states(status)
events(subject_type, subject_id, created_at)
audit_log(resource_type, resource_id, created_at)
job_runs(job_name, started_at)
blocks(status, expires_at)
pauses(status, expires_at)
```

## Retention

Retention policy must be explicit for large tables:

- usage_samples
- policy_events
- flow_sessions
- flow_events
- worker_events
- worker_enforcement_events
- notifications
- job_runs
- application logs outside DB

Default retention should be conservative but finite.

## Import From Old System

Old system import must be explicit and auditable.

Recommended import mode:

```text
read old files/dbs
  -> validate
  -> stage import
  -> show summary
  -> operator confirms
  -> write through services/repositories
  -> create event/audit
```

Imported customers must not bypass abuse coverage.

Imported policy must not directly create live firewall rules until planner/apply is run.

## API-First Boundary

Repositories expose persistence operations.
Services own business logic.
Interfaces call services.

Forbidden:

```text
CLI directly updates customers
UI directly updates customer_policies
buyer UI directly updates customer_policies
buyer UI directly triggers firewall/apply/abuse/block/pause
UI directly updates abuse_states
Telegram directly inserts blocks
job directly edits abuse_states without abuse_service
firewall adapter writes customer policy
worker block implemented as firewall-only IP block
```

Allowed:

```text
CLI -> customer_service.add_customer() -> repositories -> event/audit
abuse job -> abuse_service.run_scan() -> repositories + firewall_service
UI -> report_service.get_customer_report()
buyer UI -> buyer_report_service.get_service_report()
buyer UI -> action_request_service.create_request()
worker policy service -> worker enforcement adapter, later
```

## Tests Required

Minimum tests:

- migration upgrade works
- migration downgrade or restore strategy documented
- config seed creates BTC lane
- customer port unique constraint works
- current policy uniqueness works
- abuse state row exists or is created for active customer
- hard action references restore point and policy backup
- job run records success/failure
- API tokens store hashes only
- buyer accounts remain separate from customer service records
- worker blocks are not modeled as firewall-only IP blocks
- import does not bypass service validation

## Acceptance Checklist

Data model is accepted only when:

- PostgreSQL is source of truth
- migrations are present
- BTC lane with backend 60010 is representable
- customer policy is versioned
- abuse state machine is representable
- firewall restore/apply history is representable
- job runs and locks are representable
- event/audit is mandatory for mutations
- future buyer UI needs are represented without mixing buyer accounts with customer service rows
- future worker block needs are represented without pretending firewall can block worker names alone
- UI/API/Telegram future needs are represented without direct table writes
- tests cover constraints and critical relationships

A patch that reintroduces TSV/SQLite as production source of truth must be rejected.
