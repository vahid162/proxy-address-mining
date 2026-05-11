# AI Phase 6 Task — Firewall Planner First

Status: active task for Phase 6-A cleanup and planner implementation

This document defines the safe Phase 6-A boundary for AI coding agents.

## Current Gate

Authoritative source:

```text
docs/PHASE_STATUS.md
```

Current state:

```text
accepted phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
working phase: Phase 6 — Firewall Planner
sub-step: Phase 6-A — Repository Cleanup + Firewall Planner Contract and Desired-State Model
production traffic: none
live firewall apply: not allowed
abuse automation: not allowed
```

## Goal

Start Phase 6 safely by cleaning stale repository documentation and implementing planner-first firewall foundations.

Phase 6-A is not a production traffic phase. It is a modeling, planning, diff, and test phase.

## Allowed Work

```text
repository documentation cleanup
phase-gate alignment tests
firewall desired-state domain objects
firewall plan DTOs
firewall diff DTOs
planner service contracts
read-only live-state parser contracts
human-readable plan rendering
JSON plan rendering
dry-run evidence artifacts
planner unit tests
backend exposure classification tests
internal backend reachability classification tests
collision detection tests
orphan/stale MPF object detection tests
```

## Forbidden Work

```text
production customer traffic
customer NAT redirects
customer firewall rules
live firewall apply
live restore execution
usage timers
hash-rate/share collectors
abuse runner automation
block or pause automation
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
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = limited_runtime_local_only
customer_onboarding_allowed = db_only
```

## Planner Boundary

The planner may read config and database state, then produce a desired model and a plan.

It must not mutate live system state in Phase 6-A.

Required planner flow:

```text
load config
load DB state
validate lanes and customers
build desired firewall model
load or accept live snapshot input
compare desired state with live state
produce warnings and errors
render human-readable summary
render stable JSON plan
return non-applyable result when errors exist
```

## Desired Model Scope

The desired model should represent intent, not execute it.

It should include:

```text
backend type
apply mode
tables referenced
chains desired
rules desired
customer coverage
lane backend coverage
accounting coverage intent
backend guard intent
warnings
errors
affected customers
```

## Safety Requirements

Planner errors must block future applyability.

At minimum, Phase 6-A must detect or prepare contracts for:

```text
customer port collision
lane backend port collision
backend public exposure risk
backend internal reachability failure
missing customer coverage
missing accounting coverage
unexpected MPF-owned live object
orphan MPF-owned chain or rule
stale deleted-customer rule
NAT target mismatch
plan with errors is not applyable
```

## Interface Boundary

CLI and API handlers must stay thin.

Required pattern:

```text
CLI/API -> request DTO -> firewall service -> planner/domain -> response DTO
```

Forbidden pattern:

```text
CLI builds firewall rules directly
API builds firewall rules directly
customer service mutates firewall state directly
job bypasses firewall service
```

## Tests Required Before Phase 6-A Acceptance

```text
phase status remains Phase 5 accepted / Phase 6 working
README and INDEX do not point to Phase 5 as current work
planner output has human-readable summary
planner output has JSON representation
plan errors make result not applyable
customer port collision is detected
lane backend collision is detected
backend exposure risk is detected or explicitly represented
internal backend reachability failure is detected or explicitly represented
no runtime apply path is introduced
no customer NAT or firewall rule is created
no usage or abuse automation is introduced
```

## Acceptance Gate

Phase 6-A is accepted only when:

```text
repository cleanup is complete
current phase docs are aligned
planner contracts exist
planner tests pass
dry-run evidence can be generated
no live firewall mutation exists
no production traffic is enabled
limited Phase 4 runtime remains local-only
```

## Next Step After Phase 6-A

Only after Phase 6-A is accepted, continue to deeper planner implementation and then a separate reviewed apply gate.

Do not combine planner cleanup with live apply behavior.
