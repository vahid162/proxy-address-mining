# AI Phase 6 Task — Firewall Planner + Offline Apply Contracts

Status: active task for Phase 6-D0 / Phase 6-D documentation/test-only live-apply boundary review

This document defines the safe Phase 6 boundary for AI coding agents.

## Current Gate

Authoritative source:

```text
docs/PHASE_STATUS.md
```

Current state:

```text
accepted phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
working phase: Phase 6 — Firewall Planner
current sub-step: Phase 6-C accepted (offline apply-gate readiness/review only); next safe step: Phase 6-D0 / Phase 6-D documentation/test-only live-apply boundary review
production traffic: none
live firewall apply: not allowed
abuse automation: not allowed
customer onboarding: db_only
proxy data plane: limited_runtime_local_only
UI: not allowed
Telegram: not allowed
```

## Purpose

Phase 6 builds the firewall planner and the apply/rollback safety contract without enabling production traffic or live firewall mutation.

Completed Phase 6-A work established:

```text
firewall desired-state model
planner/diff DTOs
human and JSON dry-run output
offline snapshot parser
offline file-backed diff
planner-only firewall doctor
```

Phase 6-C accepted work (historical reference) included:

```text
offline restore payload artifacts
offline apply-readiness contracts
offline apply package reports
offline rollback artifacts from explicit snapshot files
offline preflight inspection/failure matrix
safety regression tests
```

Phase 6-B is still not a production traffic phase.

## Allowed Work Now

```text
repository/documentation cleanup that preserves the current gate
firewall desired-model refinement
firewall planner/diff refinement
human-readable and JSON plan/report output
offline parser and file-backed snapshot fixtures
offline restore payload rendering as artifact only
offline apply-readiness contract modeling
offline apply package reporting
offline rollback artifact rendering from explicit operator-provided snapshot files
offline preflight reporting
planner, contract, package, rollback, and preflight tests
safety regression tests proving no live firewall side effects
proxy/backend safety checks that preserve internal reachability + external non-exposure contracts
```

## Forbidden Work Now

Do not implement, run, or activate:

```text
production customer traffic
customer NAT redirects
customer firewall rules
live firewall apply
live firewall rollback
live firewall verify
iptables-save execution
iptables-restore execution
conntrack flush
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

Live firewall apply remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.

## Required Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = limited_runtime_local_only
customer_onboarding_allowed = db_only
ui_allowed = no
telegram_allowed = no
```

Any patch that bypasses these invariants or introduces traffic-changing behavior before the correct accepted phase must be rejected.

## Planner Boundary

Allowed planner flow:

```text
load config
load DB state through read-only repository paths
validate lanes and customers
build desired firewall model
accept explicit offline snapshot input when requested
compare desired state with offline snapshot state
produce warnings and errors
render human-readable summary
render stable JSON plan/report
return non-applyable result when errors exist
```

Forbidden planner flow:

```text
execute iptables-save automatically
execute iptables-restore
read live firewall state implicitly
mutate firewall/NAT/runtime state
write DB rows from planner/report commands
write filesystem artifacts from inspection commands
silently fall back from DB-backed input to config-only input
produce misleading empty plans when DB read failed
```

## Offline Apply Contract Boundary

Phase 6-B artifacts may describe future apply behavior, but they must not perform it.

Allowed contract outputs:

```text
restore payload text/artifact displayed to operator
apply-readiness contract
apply package report
rollback artifact rendered from explicit offline snapshot file
preflight report combining planner, restore, readiness, package, and optional rollback status
```

Required safety flags must remain false before explicit apply gate acceptance:

```text
live_firewall_read = false
live_firewall_write = false
iptables_save_executed = false
iptables_restore_executed = false
lock_acquired = false
restore_point_written = false
rollback_written = false
database_write = false
filesystem_write = false
```

## Desired Model Scope

The desired model represents intent only. It may include:

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

It must not create live chains, live rules, or live NAT redirects.

## Safety Requirements

Planner and contract errors must block future applyability.

At minimum, Phase 6 must detect or represent:

```text
customer port collision
lane backend port collision
customer/backend port collision
backend public exposure risk
backend internal reachability failure
missing customer coverage
missing accounting coverage
unexpected MPF-owned live object in offline snapshot
orphan MPF-owned chain or rule in offline snapshot
stale deleted-customer rule in offline snapshot
NAT target mismatch in offline snapshot
plan with errors is not applyable
live apply remains blocked by current phase gate
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

## Tests Required Before Advancing Beyond Phase 6-B

```text
phase status remains Phase 5 accepted / Phase 6 working
current docs identify Phase 6-B as contract/artifact/preflight work, not stale Phase 6-A-only work
planner output has human-readable summary
planner output has JSON representation
plan errors make result not applyable
customer port collision is detected
lane backend collision is detected
customer/backend port collision is detected
backend exposure risk is detected or explicitly represented
internal backend reachability failure is detected or explicitly represented
offline snapshot parser remains file-backed and explicit
restore payload renderer is artifact-only
apply-readiness contract is non-applyable while current gate forbids live apply
rollback artifact renderer uses explicit snapshot input only
preflight final verdict remains BLOCKED while live apply is forbidden
no runtime apply path is introduced
no iptables-save execution is introduced
no iptables-restore execution is introduced
no customer NAT or firewall rule is created
no usage or abuse automation is introduced
```

## Acceptance Gate For Any Future Live Apply Slice

A later live apply slice may be considered only after an explicit gate update and separate review. Before that, the project must have:

```text
planner accepted
restore point contract accepted
lock contract accepted
verify contract accepted
rollback contract accepted
preflight accepted
canary/manual/isolated validation plan accepted
server time synchronization fixed before production-dependent jobs
```

Do not combine planner/offline contract work with live apply behavior.


Phase 6-C closure is documentation/test-only and live apply remains forbidden.


Next safe work now is Phase 6-D0 / Phase 6-D documentation/test-only live-apply boundary review.
No `mpf firewall apply`, `mpf firewall rollback`, or live `verify` may be enabled in this step.
No `iptables-save` or `iptables-restore` execution is authorized in this step.
