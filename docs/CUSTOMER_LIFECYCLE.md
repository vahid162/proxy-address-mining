# CUSTOMER LIFECYCLE

Status: Phase 5 contract

This document defines the customer lifecycle contract for `proxy-address-mining`.
It is an implementation contract for Phase 5 Customer CRUD in DB Only.

Phase 5 may model customer lifecycle state in PostgreSQL, request DTOs, service validation, and DB-only reports.
It must not activate runtime traffic behavior, timers, firewall rules, NAT redirects, usage collectors, abuse automation, UI, Telegram, or public API binding.

## Goal

Customer CRUD must be future-ready for activation, expiry, renewal, soft delete, reports, UI, buyer reporting, Telegram notifications, and abuse coverage without violating the current DB-only phase gate.

The Phase 5 goal is:

```text
record lifecycle intent safely in PostgreSQL
validate it through services
expose it through DB-only CLI/API contracts
keep all runtime side effects disabled
```

## Phase 5 Boundary

Allowed in Phase 5:

```text
customer lifecycle documentation
schema notes and later reviewed migrations
request/response DTO contracts
service-layer validation
DB-only create/update/renew/disable/delete intent
DB-only reports and previews
event/audit planning or records where schema already supports them
tests that preserve the DB-only gate
```

Forbidden in Phase 5:

```text
customer NAT redirects
customer firewall rules
firewall apply
iptables path
iptables-restore
production customer traffic
usage timers
hash-rate/share collectors
abuse runner automation
block automation
pause automation
worker scanner
worker enforcement
first-connect runtime detection
auto-expire timer
auto-delete timer
systemd timer for customer lifecycle
conntrack/tcpdump lifecycle job
local UI runtime
buyer UI runtime
Telegram bot
public API binding
```

## Activation Modes

Customer activation must use an explicit enum, not an ambiguous boolean.

Allowed activation modes:

```text
immediate
first_connect
```

### `immediate`

The service period starts when the customer is created or renewed.

Expected Phase 5 DB behavior:

```text
activation_mode = immediate
service_days = positive integer
activated_at = created/renewed timestamp
starts_at = activated_at
expires_at = starts_at + service_days
first_connected_at = null unless populated by a future accepted runtime phase
```

This remains DB-only in Phase 5 and must not create traffic reachability.

### `first_connect`

The service period starts after the first valid customer connection in a later accepted runtime phase.

Expected Phase 5 DB behavior:

```text
activation_mode = first_connect
service_days = positive integer
activated_at = null
starts_at = null
expires_at = null
first_connected_at = null
```

Important:

```text
status remains active
```

Do not introduce a `pending_activation` customer status in Phase 5. Pending activation is represented by `activation_mode=first_connect` and `activated_at is null`.

The future first-connect runtime must ignore internal probes, healthchecks, localhost checks, Docker-internal checks, backend-port checks, rejected traffic, v2rayA UI traffic, and invalid scans.
That runtime is not part of Phase 5.

## Expiry Policy

Expiry policy must be represented as lifecycle intent, not as Phase 5 automation.

Recommended fields for the later reviewed Phase 5 schema migration:

```text
customers.activation_mode
customers.service_days
customers.activated_at
customers.first_connected_at
customers.activation_event_id
customers.expired_at
customers.delete_after_expired_days
customers.auto_expire_enabled
customers.auto_delete_enabled
customers.delete_eligible_at
customers.deleted_at
customers.lifecycle_note
```

Phase 5 may store or document these concepts, but must not run lifecycle timers.

### Auto-expire

In Phase 5, `auto_expire_enabled` means DB lifecycle intent only.

Allowed:

```text
list_expiring_customers()
list_expired_customers()
preview_expiry_actions()
DB-only reports
```

Forbidden:

```text
systemd timer that changes active -> expired
automatic expiry job
usage/accounting based expiry automation
firewall changes for expiry
```

### Auto-delete

In Phase 5, `auto_delete_enabled` means DB lifecycle intent only.

Recommended default:

```text
auto_delete_enabled = false
```

Allowed:

```text
list_delete_eligible_customers()
preview_delete_actions()
DB-only reports
```

Forbidden:

```text
systemd timer that changes expired -> deleted
automatic delete job
physical DELETE FROM customers
firewall changes for delete
```

## Soft Delete Rule

Customer delete means soft delete.

Required behavior:

```text
status = deleted
deleted_at = now()
```

Forbidden by default:

```sql
DELETE FROM customers
```

Physical deletion may only be introduced later through an explicit retention policy, reviewed cleanup process, restore strategy, and acceptance gate.

Soft delete must preserve customer history, policy history, events, audit, notes, usage history, abuse evidence, and future support context.

## Customer Key

Phase 5 should introduce or preserve a stable customer identifier distinct from mutable display names and ports.

Recommended field:

```text
customers.customer_key
```

Rules:

```text
customer_key is unique
customer_key is stable
customer_key is safe for CLI/API target resolution
customer_key is not a buyer login identity
customer_key does not replace internal numeric id
```

Recommended target resolution order for future CLI/API commands:

```text
customer_key
port
id
name only if unique
```

## Status Model

Do not expand customer status for activation details.

Allowed customer statuses remain:

```text
active
paused
expired
deleted
```

Activation, first-connect, expiry policy, and delete eligibility are separate lifecycle fields.

## Abuse Invariant

Customer lifecycle must preserve mandatory abuse coverage.

Every active customer in every enabled lane must remain evaluatable by the future abuse runner unless a valid abuse exemption exists with reason, expiry, actor, and event/audit record.

Phase 5 must not create an active customer without enough policy state for future abuse evaluation.

Required active-customer policy coverage:

```text
lane_id
current customer policy
miners
farms
maxconn
rate_per_min
burst
abuse_exempt=false by default
```

If abuse exemption is supported in Phase 5, it must require:

```text
abuse_exempt_reason
abuse_exempt_until
abuse_exempt_by
event/audit linkage where supported
```

Silent exclusion from future abuse evaluation is forbidden.

## DB-only Reports and Preview

Phase 5 may add read-only or dry-run lifecycle outputs.

Allowed examples:

```text
mpf customer expiring --within-days 3
mpf customer expired
mpf customer delete-eligible
mpf customer add ... --dry-run
mpf customer renew ... --dry-run
mpf customer delete ... --dry-run
```

Dry-run output must explicitly report:

```text
firewall_change: no
nat_change: no
runtime_change: no
```

## Event and Audit Expectations

Customer lifecycle mutations should be evented and audited where the schema and current phase support it.

Suggested event/action names:

```text
customer.created
customer.updated
customer.policy_changed
customer.renewed
customer.disabled
customer.deleted
customer.ip_pins_changed
customer.lifecycle_policy_changed
```

Mutation records should include:

```text
actor_type
actor_id
action
resource_type
resource_id
before_json
after_json
reason
correlation_id
```

## Phase Placement

```text
Phase 5:
  lifecycle contract, schema/DTO/service validation, DB-only CRUD, DB-only reports, dry-run

Phase 6:
  firewall planner must understand active first-connect customers without starting their service clock

Phase 7:
  usage/accounting may provide accepted traffic evidence for future activation

Phase 8:
  abuse automation evaluates all active eligible customers

Phase 10:
  flow/session evidence can improve first-connect and lifecycle evidence quality

Phase 11+:
  UI/buyer/Telegram surfaces may consume lifecycle reports through service/API boundaries
```

## Acceptance Checklist

Customer lifecycle contract is accepted only when:

```text
activation modes are explicit
first_connect runtime is deferred
status model remains active/paused/expired/deleted
auto-expire timer is forbidden in Phase 5
auto-delete timer is forbidden in Phase 5
delete means soft delete
customer_key is required or clearly represented for Phase 5 work
all active customers remain abuse-evaluable
no firewall/NAT/runtime path is introduced
DB-only reports and dry-run remain non-mutating outside PostgreSQL
```

A patch that starts lifecycle timers, detects first connect through runtime evidence, applies firewall/NAT, or excludes active customers from abuse coverage before the accepted later phase must be rejected.
