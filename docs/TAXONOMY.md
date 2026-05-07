# TAXONOMY

Status: Draft v1

This document defines the naming and lifecycle taxonomy for events, audit actions, statuses, policy rules, retention, reporting aggregates, and evidence artifacts.

It is a contract for humans and AI coding agents so future phases do not invent incompatible string values or incompatible log shapes.

## 1. Goal

The database already has future-safe columns such as:

```text
event_type
action
subject_type
resource_type
status
severity
data_json
evidence_json
metadata_json
filter_json
limits_json
value_json
correlation_id
```

This document standardizes the values and timing rules that should be used with those fields.

Phase 3 should introduce code-level constants/enums for the core taxonomy without changing the database schema.

Later phases may add optional registry/reference tables if runtime-managed taxonomy becomes necessary, but the first implementation should keep taxonomy in code and documentation.

## 2. Compatibility Rule

Do not break existing data when expanding taxonomy.

Allowed future changes:

```text
- add new enum/constant values
- add new optional JSON keys
- add new optional columns through Alembic migrations
- add new reference tables through Alembic migrations
- add indexes or partitions through reviewed migrations
```

Forbidden compatibility breaks:

```text
- renaming stored event_type values without migration/backfill
- changing the meaning of an existing status silently
- reusing one event_type for a different semantic action
- making existing JSON evidence unreadable by new code
- requiring data-plane activation just to read historical records
```

## 3. Implementation Timing by Phase

### Phase 3 — Foundation taxonomy

Implement or prepare:

```text
mpf/domain/taxonomy.py
```

Minimum contents:

```text
EventSeverity
SubjectType
ActorType
ResourceType
AuditAction
RequestContext
CorrelationId policy
CustomerStatus
JobStatus
AbuseStatus
FirewallApplyStatus
PolicyEventType
WorkerEventType
```

Rules:

```text
- no database migration is required for this foundation step
- no traffic-changing behavior is allowed
- CLI/API/services should import constants instead of hardcoding new strings
- read-only DTOs may include correlation_id/request context fields even if not fully used yet
```

### Before Phase 5 — customer and policy mutation taxonomy

Before Customer CRUD in DB Only starts, define and test:

```text
customer event types
customer audit actions
customer status values
policy change actions
policy change reason vocabulary
actor/request context rules
correlation_id propagation
```

Reason: Phase 5 creates the first production customer/policy mutations and must not create inconsistent event/audit history.

### Before Phase 6 — firewall and restore taxonomy

Before Firewall Planner + Apply/Verify/Rollback starts, define and test:

```text
firewall event types
firewall apply actions
firewall apply statuses
restore point types
plan error codes
verify failure categories
drift categories
backend exposure severity levels
rollback reason taxonomy
```

Reason: firewall apply is a dangerous action and must have consistent restore, verify, rollback, event, and audit semantics.

### Before Phase 7 — retention, aggregation, and accounting taxonomy

Before Usage + Policy/Reject Accounting starts, define:

```text
retention policy for high-volume tables
aggregation policy for reporting tables
counter reset categories
policy/reject event categories
usage source names
report time windows
partitioning decision for large tables
```

Reason: usage, flow, worker, and policy events can grow quickly and must not overload PostgreSQL or produce inconsistent reports.

### Before Phase 8 — abuse taxonomy

Before Abuse 1h Core starts, define and test:

```text
abuse state values
abuse event types
abuse evidence schema
abuse exemption reason rules
manual unhard audit actions
hard/unhard restore point categories
conntrack flush reason taxonomy
farms-over-only non-hardening classification
```

Reason: the one-hour abuse requirement is mandatory for all active customers in all enabled lanes.

### Before Phase 10 — session, worker, and evidence taxonomy

Before Session / Worker / Policy Timeline starts, define:

```text
flow session states
flow event types
worker event types
worker confidence bands
worker identity normalization rules
worker mismatch categories
evidence pack manifest format
evidence artifact reference rules
```

Reason: worker enforcement in later phases must be based on reliable evidence and must not become firewall-only worker blocking.

### Before Phase 11+ — UI, buyer, Telegram, and action taxonomy

Before read-only UI, buyer reporting, UI actions, or Telegram starts, define:

```text
UI request context
operator session/login event taxonomy
buyer-safe event visibility rules
notification event filters
Telegram notification categories
confirmation event/audit taxonomy
allowlist/restricted action taxonomy
```

Reason: future interfaces must use services and must not directly mutate DB/firewall state.

## 4. Naming Rules

Use dotted event and action names.

Recommended format:

```text
<domain>.<object_or_phase>.<verb_or_result>
```

Examples:

```text
customer.created
customer.policy.changed
firewall.plan.created
firewall.apply.succeeded
abuse.state.entered_over_tracking
worker.identity.observed
job.run.failed
backup.created
```

Rules:

```text
- use lowercase
- use dots as namespace separators
- avoid spaces
- avoid ambiguous abbreviations
- never reuse a name for a new meaning
- prefer past-tense results for recorded facts
- prefer imperative verbs for requested actions
```

## 5. Core Subject Types

Allowed initial `subject_type` values:

```text
system
server
config
lane
customer
customer_policy
customer_ip_pin
buyer_account
buyer_user
action_request
firewall
firewall_apply
firewall_snapshot
restore_point
usage
policy_event
flow_session
worker
worker_policy
worker_block
abuse
job
scheduler_lock
block
pause
backup
notification
incident
runbook
import_batch
feature_flag
secret_reference
maintenance_window
```

Do not add a new subject type when an existing one clearly applies.

## 6. Event Severity

Allowed severity values:

```text
debug
info
notice
warning
error
critical
```

Guidance:

```text
debug     internal detail, normally hidden from operator summaries
info      normal expected event
notice    important but not degraded
warning   degraded or suspicious condition requiring attention
error     operation failed or customer impact possible
critical  safety, exposure, data loss, or production-impacting event
```

Backend exposure, failed firewall verify, missing accounting rules for active customers, or abuse automation coverage gaps must be at least `critical` once the relevant phase is active.

## 7. Actor Types

Allowed initial `actor_type` values:

```text
operator
buyer_user
api_token
job
system
telegram_bot
ui
internal_api
migration
importer
```

Rules:

```text
- mutation audit must include actor_type and actor_id where available
- system-generated actions must still use an actor_type
- unknown actors are not acceptable for dangerous actions
- future UI/API/Telegram actions must preserve source context
```

## 8. Request Context

Services that can mutate state in later phases should accept a request context object, even when Phase 3 remains read-only.

Recommended fields:

```text
correlation_id
actor_type
actor_id
source_interface
source_ip
user_agent
request_id
reason
confirmed
```

Rules:

```text
- correlation_id links events, audit_log, job_runs, firewall_applies, notifications, and restore_points
- reason is required for dangerous actions
- confirmed=true is required for explicitly confirmed dangerous actions in later UI/CLI phases
```

## 9. Customer and Policy Taxonomy

Customer statuses:

```text
active
paused
expired
deleted
suspended
pending
```

Customer event types:

```text
customer.created
customer.updated
customer.deleted
customer.renewed
customer.expired
customer.paused
customer.unpaused
customer.ip_pins.changed
customer.status.changed
```

Policy audit actions:

```text
customer_policy.created
customer_policy.changed
customer_policy.override.created
customer_policy.override.expired
customer_policy.abuse_exempt.created
customer_policy.abuse_exempt.expired
customer_policy.restored
```

Policy reason categories:

```text
operator_request
renewal
support_fix
abuse_hard
abuse_unhard
imported
rollback
maintenance
buyer_request_reviewed
```

## 10. Firewall, Restore, and Backup Taxonomy

Firewall event types:

```text
firewall.plan.created
firewall.plan.failed
firewall.diff.created
firewall.apply.started
firewall.apply.succeeded
firewall.apply.failed
firewall.verify.started
firewall.verify.succeeded
firewall.verify.failed
firewall.rollback.started
firewall.rollback.succeeded
firewall.rollback.failed
firewall.drift.detected
firewall.backend_exposure.detected
```

Firewall apply actions:

```text
plan
apply
verify
rollback
restore
```

Firewall statuses:

```text
planned
running
applied
verified
failed
rolled_back
degraded
blocked
```

Restore point types:

```text
firewall
abuse
policy
backup
migration
bulk_change
config
import
```

Backup event types:

```text
backup.created
backup.verified
backup.failed
backup.restore_plan.created
backup.restore.started
backup.restore.succeeded
backup.restore.failed
restore_drill.succeeded
restore_drill.failed
```

Plan error categories:

```text
port_collision
lane_collision
backend_exposure
orphan_chain
drift_detected
missing_customer_policy
missing_lane
invalid_apply_mode
unsafe_public_binding
```

## 11. Usage, Policy, and Accounting Taxonomy

Usage source names:

```text
iptables_counters
conntrack_snapshot
policy_counter_snapshot
manual_probe
imported
```

Policy/reject event types:

```text
connlimit_reject
hashlimit_reject
pause_reject
block_reject
whitelist_reject
backend_guard_reject
unknown_reject
```

Counter reset categories:

```text
firewall_reload
counter_wrap
chain_recreated
snapshot_gap
unknown_reset
```

Standard report windows:

```text
1h
6h
1d
7d
30d
custom
```

## 12. Abuse Taxonomy

Abuse states:

```text
normal
over_tracking
over_grace
hard
exempt_until
disabled_manual
```

Canonical active state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Abuse event types:

```text
abuse.state.entered_normal
abuse.state.entered_over_tracking
abuse.state.entered_over_grace
abuse.hard.started
abuse.hard.applied
abuse.hard.failed
abuse.manual_unhard.started
abuse.manual_unhard.applied
abuse.manual_unhard.failed
abuse.exemption.created
abuse.exemption.expired
abuse.coverage.missing_customer
abuse.farms_over.observed
abuse.miners_over.observed
```

Abuse evidence schema should include, when available:

```text
customer_id
lane_id
port
miners
farms
maxconn
current_hot
current_unique_ips
current_unique_workers
first_seen_over
last_seen_over
duration_sec
sample_window_sec
source
confidence
```

Hardening must never be triggered by farms-over alone.

## 13. Flow, Worker, and Evidence Taxonomy

Flow session states:

```text
new
active
idle
closed
expired
unknown
```

Flow event types:

```text
flow.session.started
flow.session.updated
flow.session.closed
flow.session.expired
flow.session.reconciled
```

Worker event types:

```text
worker.authorize.observed
worker.submit.observed
worker.identity.observed
worker.identity.mismatch
worker.policy.reported
worker.policy.block_detected
worker.enforcement.blocked
worker.enforcement.rejected
worker.enforcement.failed
```

Worker confidence bands:

```text
0-39   low
40-69  medium
70-89  high
90-100 confirmed
```

Evidence artifact references should use a stable manifest shape:

```text
artifact_type
path
checksum
size_bytes
created_at
source
metadata_json
```

Allowed artifact types:

```text
iptables_save
conntrack_snapshot
tcpdump_sample
worker_capture
report_json
report_text
config_snapshot
db_dump
firewall_plan
```

A future `evidence_artifacts` table may be added if large forensic artifacts become common. Until then, store small evidence in `evidence_json` and large artifacts as paths/checksums in metadata.

## 14. Jobs and Scheduler Taxonomy

Job statuses:

```text
running
succeeded
failed
degraded
skipped
cancelled
```

Job event types:

```text
job.started
job.succeeded
job.failed
job.degraded
job.skipped
job.lock.acquired
job.lock.failed
job.lock.released
```

Scheduler lock names should be stable:

```text
usage_snapshot
abuse_runner
block_expiry
pause_sync
backup_runner
firewall_apply
session_reconcile
worker_capture
```

## 15. Blocks and Pauses Taxonomy

Block scopes:

```text
global_ip
customer_ip
port_ip
lane_ip
```

Block event types:

```text
block.created
block.expired
block.removed
block.rejected_connection
```

Pause event types:

```text
pause.created
pause.expired
pause.removed
pause.rejected_connection
```

Block/pause statuses:

```text
active
expired
removed
pending
failed
```

## 16. UI, Buyer, Telegram, and Notification Taxonomy

Buyer-safe event visibility:

```text
public_to_buyer
operator_only
security_sensitive
internal_only
```

Action request statuses:

```text
pending
approved
rejected
executed
cancelled
expired
failed
```

Action request event types:

```text
action_request.created
action_request.approved
action_request.rejected
action_request.executed
action_request.cancelled
action_request.failed
```

Notification statuses:

```text
pending
sent
failed
skipped
throttled
```

Notification event types:

```text
notification.queued
notification.sent
notification.failed
notification.skipped
notification.throttled
```

Telegram action taxonomy must not be implemented before the Telegram action phase and must require allowlist, confirmation, service-layer routing, event/audit, and restore points where dangerous.

## 17. Retention and Partitioning Strategy

Before Phase 7, define concrete retention values for high-volume tables.

Initial policy recommendation:

```text
usage_samples: raw 90 days, aggregate longer
policy_events: raw 180 days, aggregate longer
flow_sessions: raw 30-90 days depending volume
flow_events: raw 30-90 days depending volume
worker_events: raw 90 days, aggregate longer
notifications: 90 days
job_runs: 180 days
audit_log: long-term, operator-defined
firewall_snapshots: keep according to backup/restore policy
backups: keep according to storage capacity and restore policy
```

Partitioning review is required before enabling high-volume usage/session/worker collection in production.

Partition candidates:

```text
usage_samples by sampled_at
policy_events by seen_at
flow_sessions by last_seen_at or started_at
flow_events by created_at
worker_events by seen_at
notifications by created_at
```

## 18. Aggregate Reporting Tables

Do not add aggregate tables until raw collection semantics are stable.

Potential future aggregates:

```text
customer_hourly_usage
customer_daily_usage
customer_policy_daily_summary
customer_worker_daily_summary
abuse_daily_summary
lane_daily_summary
buyer_service_daily_summary
```

Aggregate table creation should happen after Phase 7 data quality is proven and before report performance becomes a bottleneck.

## 19. Code Placement Rule

Phase 3 should create the code home for taxonomy:

```text
mpf/domain/taxonomy.py
```

Guidelines:

```text
- use StrEnum where practical
- keep names stable
- test representative values
- services import taxonomy constants
- interfaces do not invent event/action/status strings
- adapters do not invent business event strings
```

Optional future registry tables may be considered only after taxonomy values need runtime management.

## 20. Stop Conditions

Stop and review if any implementation:

```text
- hardcodes a new mutation event type outside taxonomy
- introduces customer mutation before customer audit taxonomy exists
- introduces firewall apply before firewall/restore taxonomy exists
- starts usage/worker/session collection before retention is defined
- starts abuse automation before abuse evidence taxonomy is defined
- exposes UI/Telegram action before actor/request context is defined
- uses worker block as firewall-only IP blocking
- stores large forensic artifacts only as untracked files without checksum/reference
```
