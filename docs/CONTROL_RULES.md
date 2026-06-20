# CONTROL RULES

Status: future architecture contract
Runtime impact: none
Firewall impact: none
Production traffic impact: none
Database migration impact: none in the current phase

This document defines the future control-intent model for `proxy-address-mining`.
It is a contract for humans and AI coding agents so Phase 5 customer CRUD does not create schema, service, or naming dead ends for later block, pause, whitelist, rate-limit, worker, routing, reporting, UI, and automation work.

## Contract boundary

Historical note: this contract was introduced during an earlier phase. Current phase, runtime authorization, and next required step are defined only in `docs/PHASE_STATUS.md`.

This document does **not** authorize runtime controls.

Allowed now:

```text
documentation contracts
future schema contracts
service ownership contracts
phase placement
test expectations that preserve DB-only Phase 5
```

Forbidden now:

```text
runtime block commands
runtime pause commands
firewall planner integration
iptables commands
iptables-restore
NAT redirects
systemd timers
conntrack jobs
tcpdump jobs
worker scanners
worker enforcement
automation
production traffic
```

## Purpose

Control rules represent operator or system intent.

Examples of intent:

```text
block this IP globally
block this IP only for one customer port
pause this customer
pause this customer only for a window
allow only these source IPs
rate-limit this customer later
observe a suspicious worker pattern
notify on a worker policy violation
route or require a worker on a specific port later
```

A control rule is not a firewall rule by itself.
A control rule is not a worker-enforcement action by itself.
A control rule is not automation by itself.

Future services may normalize control intent into firewall desired model, worker policy decisions, notification decisions, or action requests after the relevant phase is accepted.

## Python-first Rule

Control behavior must follow the project service boundary:

```text
CLI / API / future UI / jobs
  -> request DTO / command object
  -> service layer
  -> domain logic
  -> repository
  -> PostgreSQL
  -> event/audit/job record
```

Forbidden:

```text
shell script as business logic
TSV or SQLite production state
ad-hoc iptables mutation
worker policy implemented inside CLI
UI direct table writes
Telegram shell commands
job bypassing service validation
```

Shell may exist only as:

```text
thin wrapper around Python entrypoint
server sync helper
emergency restore helper
diagnostic one-shot commands
operator runbook snippet
```

## Future Generic Intent Model

A future table may be introduced after explicit phase approval:

```text
control_rules
```

Recommended purpose:

```text
Store normalized operator/system control intent for block, pause, whitelist, rate-limit, worker block, worker route, and notify-only behavior.
```

Suggested fields:

```text
id
rule_type
scope_type
lane_id
customer_id
port
ip_cidr
worker_match_type
worker_pattern
target_lane_id
target_port
action
starts_at
expires_at
status
priority
reason
source
created_at
created_by
removed_at
removed_by
metadata_json
correlation_id
```

Recommended `rule_type` values:

```text
block
pause
whitelist
rate_limit
worker_block
worker_route
notify_only
```

Recommended `scope_type` values:

```text
global
lane
customer
port
ip
port_ip
customer_ip
customer_port
customer_port_ip
worker
worker_port
```

Recommended `action` values:

```text
reject
drop
pause
allow
observe
notify
block_port_ip
require_port
kill_session_later
```

Recommended `status` values:

```text
pending
active
expired
removed
disabled
```

This future table must not apply firewall rules by itself.
It stores desired intent only.

## Future Event Model

A future table may be introduced after explicit phase approval:

```text
control_rule_events
```

Suggested fields:

```text
id
control_rule_id
event_type
old_status
new_status
evidence_json
created_at
created_by
correlation_id
```

Recommended `event_type` values:

```text
created
planned
applied
expired
removed
skipped
failed
conflict_detected
```

## Relationship With Existing Blocks and Pauses

The current data model already has domain-specific tables such as:

```text
blocks
pauses
```

These tables are not deprecated by this document.

Current rule:

```text
blocks and pauses remain domain-specific views/services.
control_rules is only a future generic intent model.
firewall planner may consume normalized control intent only in a later accepted phase.
```

Possible future mapping:

```text
global IP block
  -> control_rules(rule_type=block, scope_type=ip)

block IP on a specific port
  -> control_rules(rule_type=block, scope_type=port_ip)

pause whole customer
  -> control_rules(rule_type=pause, scope_type=customer)

pause specific customer port
  -> control_rules(rule_type=pause, scope_type=customer_port)

pause IP on customer port
  -> control_rules(rule_type=pause, scope_type=customer_port_ip)

worker prefix block
  -> control_rules(rule_type=worker_block, scope_type=worker)

require worker on a specific port
  -> control_rules(rule_type=worker_route, scope_type=worker_port)
```

## Abuse Coverage Invariant

Control rules must never weaken the mandatory one-hour abuse requirement.

A future block, pause, whitelist, worker policy, worker route, notification rule, or rate-limit rule must not silently exclude a customer from abuse evaluation.

Required invariant:

```text
all active customers in all enabled lanes remain evaluatable by abuse runner
unless a valid abuse exemption exists with reason, expiry, actor, and event/audit record
```

Farms-over alone must not harden.
Worker-over alone must not harden.
Sustained miner-abuse after about 3600 seconds remains the hardening trigger.

## Phase Placement

### Phase 5 — Customer CRUD in DB Only

Allowed control-rule work:

```text
documentation only
future service ownership notes
validation awareness so customer CRUD does not block future controls
tests that Phase 5 remains DB-only
```

Forbidden control-rule work:

```text
runtime commands
firewall desired model generation
firewall apply
systemd timers
worker observation jobs
conntrack/tcpdump jobs
automation
```

### Phase 6 — Firewall Planner

Control rules may be represented only as desired model planning after explicit phase approval.

Still forbidden unless separately accepted:

```text
ad-hoc iptables mutation
shell-owned firewall state
worker-name enforcement by firewall alone
```

### Phase 7 — Usage and Policy/Reject Accounting

Block and pause reject accounting may be implemented through service-owned policy events.

### Phase 8 — Abuse 1h Core

Abuse hard/unhard must use restore point, policy backup, firewall service, event/audit, and scoped conntrack handling.
Control rules must not bypass this path.

### Phase 10 — Session / Worker / Policy / Share Timeline

Worker evidence and attribution may be collected only with reviewed retention and evidence policy.

### Phase 15 or Later — Worker Enforcement

Worker enforcement may start only after reliable evidence and a suitable Stratum-aware adapter exist.

## Acceptance Criteria for This Contract

This contract is accepted only when:

```text
pytest passes
Phase 5 remains DB-only
no runtime service is added
no timer is added
no firewall/NAT path is added
no TSV/SQLite production state is introduced
control rules are documented as future intent only
worker enforcement remains future-only
abuse 1h coverage is preserved
```

A patch that turns this contract into runtime behavior before the proper phase must be rejected.
