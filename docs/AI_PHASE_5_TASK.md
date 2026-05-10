# AI Phase 5 Task — Customer CRUD in DB Only

Status: active task for Phase 5 planning and implementation

This document defines the Phase 5 boundary for AI coding agents.

Phase 5 is limited to customer CRUD in PostgreSQL only. It must not create customer NAT redirects, customer firewall rules, production traffic, usage timers, abuse automation, UI, Telegram, or public API exposure.

## Required Reading

Read before changing code, tests, scripts, docs, migrations, services, or interfaces:

1. `AGENTS.md`
2. `README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`
6. `docs/ROADMAP.md`
7. `docs/SAFETY.md`
8. `docs/DATA_MODEL.md`
9. `docs/TAXONOMY.md`
10. `docs/FIREWALL.md`
11. `docs/ABUSE.md`
12. `docs/CUSTOMER_LIFECYCLE.md`
13. `docs/CONTROL_RULES.md`
14. `docs/WORKER_POLICY.md`
15. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`

If documents conflict, follow the stricter safety rule and update documentation before implementing code.

## Current Boundary

Accepted phase:

```text
Phase 4 Runtime Activation — Limited Proxy Runtime Startup accepted on farm5
```

Working phase:

```text
Phase 5 — Customer CRUD in DB Only
```

## Goal

Implement safe customer CRUD against PostgreSQL through domain/service/repository boundaries.

Phase 5 may create or update customer records in the database only. It must not connect those records to live traffic yet.

## Phase 5 Contract Clarification

Phase 5 may refine architecture contracts for later controls, worker policy, customer lifecycle, routing, reporting, UI, and automation **only as documentation and tests that preserve the DB-only gate**.

Allowed contract-only work:

```text
customer lifecycle documentation
activation-mode documentation
expiry/soft-delete documentation
control-rule intent documentation
worker policy boundary documentation
future schema notes without migration
service ownership notes
phase placement notes
tests that the project remains Phase 5 DB-only
```

Forbidden contract work:

```text
control_rules migration without explicit phase approval
worker_routing_rules migration without explicit phase approval
customer lifecycle timer
auto-expire runtime
auto-delete runtime
first-connect runtime detection
runtime block command
runtime pause command
worker scanner
worker guard
firewall planner integration
systemd timer
conntrack/tcpdump job
iptables path
production import
```

Customer CRUD implementation must not hardcode assumptions that future block, pause, whitelist, lifecycle policy, worker policy, or control intent cannot exist.

It must also not implement those future controls prematurely.

## Allowed Work

```text
customer request/response DTOs
customer domain validation
customer lifecycle DTO/validation contracts
customer repository methods
customer service methods
DB-only CLI/API command contracts
DB-only lifecycle reports and previews
port collision validation against DB/config
lane validation against enabled lanes
customer status transitions in DB
expiry field validation
customer_key planning and validation
read-only and DB-only tests
migration-safe schema usage
future audit/event hooks or event records if already supported by schema
future-control awareness that does not create runtime behavior
```

## Forbidden Work

```text
customer NAT redirects
customer firewall rules
firewall apply
iptables-restore
production traffic enablement
usage timers
hash-rate/share collectors
abuse runner automation
block/pause automation
customer lifecycle timers
auto-expire job
auto-delete job
first-connect runtime detector
conntrack/tcpdump lifecycle job
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
worker routing enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

## Required Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
proxy_data_plane_allowed = limited_runtime_local_only
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
```

Customer records created in Phase 5 must remain DB-only and must not receive live firewall/NAT reachability.

## Customer Lifecycle Requirements

Phase 5 must follow `docs/CUSTOMER_LIFECYCLE.md`.

Required lifecycle contract:

```text
activation_mode = immediate | first_connect
first_connect runtime detection is future-only
status remains active/paused/expired/deleted
delete means soft delete
auto_expire is DB intent/reporting only in Phase 5
auto_delete is DB intent/reporting only in Phase 5
customer_key is the stable operator/API target identifier
```

`first_connect` customers remain `status=active` while activation is pending. Do not introduce a `pending_activation` status in Phase 5.

Soft delete means:

```text
status = deleted
deleted_at = now()
```

Physical deletion of customer rows is forbidden in Phase 5.

Allowed lifecycle reports and previews:

```text
list_expiring_customers()
list_expired_customers()
list_delete_eligible_customers()
preview_expiry_actions()
preview_delete_actions()
dry-run create/update/renew/disable/delete outputs
```

Forbidden lifecycle runtime:

```text
systemd timer that expires customers
systemd timer that deletes customers
first-connect detector using conntrack/tcpdump/firewall/usage evidence
firewall changes caused by lifecycle state
NAT changes caused by lifecycle state
```

Dry-run output for customer lifecycle actions must explicitly show:

```text
firewall_change: no
nat_change: no
runtime_change: no
```

## Customer Validation Requirements

Customer create/update logic must validate:

```text
lane exists and is enabled
customer port is valid TCP port
customer port does not collide with reserved backend/UI ports
customer port does not collide with another active/non-deleted customer
customer_key is stable and unique when present
status is from the accepted taxonomy
activation_mode is immediate or first_connect
service_days is positive when lifecycle duration is used
expiry fields are parseable and timezone-safe
notes/labels/reasons are bounded and safe for logs/UI
miners/farms/maxconn/rate_per_min/burst are positive
maxconn is not lower than miners unless a reviewed rule explicitly allows it
IP whitelist entries are valid IP/CIDR values
```

Reserved ports include at least:

```text
2015  # v2rayA host/operator UI
60010 # BTC backend
60015 # future ZEC backend
60020 # future LTC backend
```

Future control-rule awareness means Phase 5 validation should avoid naming or schema choices that prevent later customer-scoped block, pause, whitelist, worker policy, lifecycle, or action-request support.

## Required Service Boundary

Interfaces must call services, not direct database or firewall operations:

```text
CLI/API -> request DTO -> customer service -> repository -> database
```

Forbidden:

```text
CLI directly writes DB
API directly writes DB
service directly runs iptables
customer CRUD creates Docker or firewall state
customer CRUD activates lifecycle timers
customer CRUD activates control rules
customer CRUD activates worker policy
```

## Abuse Invariant

Customer CRUD and future control/lifecycle contracts must preserve the mandatory abuse requirement:

```text
all active customers in all enabled lanes remain evaluatable by abuse runner
unless a valid abuse exemption exists with reason, expiry, actor, and event/audit record
```

Phase 5 must not introduce any path that silently excludes active customers from future abuse evaluation.

Every active customer created in Phase 5 must have enough current policy state for future abuse evaluation:

```text
lane_id
current policy
miners
farms
maxconn
rate_per_min
burst
abuse_exempt=false by default
```

## Required Tests

Minimum tests:

```text
create customer in DB only
list customer after create
update mutable fields in DB only
disable customer in DB only
soft-delete customer in DB only
first_connect is documented as future-only runtime
first_connect does not create pending_activation status
auto-expire timer is forbidden in Phase 5
auto-delete timer is forbidden in Phase 5
delete is soft-delete, not physical delete
customer_key is documented and guarded
reject duplicate active/non-deleted port
reject reserved backend/UI ports
reject unknown lane
reject disabled lane unless explicitly allowed by a reviewed rule
verify no firewall apply code path is called
verify no NAT/firewall scripts are introduced
verify no lifecycle timer is introduced
verify no block/pause/worker runtime is introduced
verify phase-status remains Phase 5 DB-only
```

## Acceptance Gate

Phase 5 is accepted only when:

```text
pytest passes
customer CRUD is DB-only
customer lifecycle contract is DB-only
no firewall/NAT/customer traffic mutation exists
no usage or abuse automation exists
no lifecycle timer exists
no block/pause/worker runtime exists
server sync evidence is reviewed
customer CRUD evidence shows DB rows only
runtime proxy remains limited local-only
```

## Stop Conditions

Stop and revise if a patch introduces:

```text
traffic-changing behavior
firewall apply
NAT redirects
customer live port reachability
usage timers
abuse automation
customer lifecycle timer
auto-expire runtime
auto-delete runtime
first-connect runtime detection
block/pause automation
worker scanner
worker enforcement
worker routing enforcement
UI or Telegram runtime
public API binding
public backend/UI exposure
bypassing service/repository boundaries
```
