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
12. `docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md`

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

## Allowed Work

```text
customer request/response DTOs
customer domain validation
customer repository methods
customer service methods
DB-only CLI/API command contracts
port collision validation against DB/config
lane validation against enabled lanes
customer status transitions in DB
expiry field validation
read-only and DB-only tests
migration-safe schema usage
future audit/event hooks or event records if already supported by schema
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
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
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

## Customer Validation Requirements

Customer create/update logic must validate:

```text
lane exists and is enabled
customer port is valid TCP port
customer port does not collide with reserved backend/UI ports
customer port does not collide with another active customer in the same lane
status is from the accepted taxonomy
expiry fields are parseable and timezone-safe
notes/labels are bounded and safe for logs/UI
```

Reserved ports include at least:

```text
2015  # v2rayA host/operator UI
60010 # BTC backend
60015 # future ZEC backend
60020 # future LTC backend
```

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
```

## Required Tests

Minimum tests:

```text
create customer in DB only
list customer after create
update mutable fields in DB only
disable customer in DB only
reject duplicate active port per lane
reject reserved backend/UI ports
reject unknown lane
reject disabled lane unless explicitly allowed by a reviewed rule
verify no firewall apply code path is called
verify no NAT/firewall scripts are introduced
verify phase-status remains Phase 5 DB-only
```

## Acceptance Gate

Phase 5 is accepted only when:

```text
pytest passes
customer CRUD is DB-only
no firewall/NAT/customer traffic mutation exists
no usage or abuse automation exists
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
UI or Telegram runtime
public API binding
public backend/UI exposure
bypassing service/repository boundaries
```
