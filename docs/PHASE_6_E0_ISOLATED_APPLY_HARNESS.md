# Phase 6-E0 Isolated Apply Harness (Planning/Contracts Only)

Status: active Phase 6-E0 contract (isolated/non-production only)

## Purpose

Phase 6-E0 defines isolated harness contracts so future apply workflow ordering can be tested without touching host firewall state, runtime traffic, or production systems.

This step is contract and test only.

## Current Gate Snapshot

Authoritative source: `docs/PHASE_STATUS.md`

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

## Non-Authorization Statement

Phase 6-E0 is isolated/non-production only.

Phase 6-E0 does **not** authorize:

- host production firewall mutation
- live firewall read
- live firewall write
- `iptables-save` execution
- `iptables-restore` execution
- live apply
- live rollback
- live verify
- customer NAT redirects
- customer firewall rules
- DB apply writes
- lock acquisition
- restore point writes

## Harness Scope

Allowed scope in Phase 6-E0:

- pure-data contracts for fake/no-op harness operations
- deterministic call-order simulation in memory only
- failure-injection simulation for apply/verify/rollback ordering tests
- report DTO generation only (no host side effects)

## Fake/No-op Adapter Contract

The harness adapter must be explicitly fake/no-op and isolated from production runtime.

Required properties:

- deterministic output
- in-memory call log only
- no subprocess calls
- no shell command execution
- no iptables command invocation
- no live firewall read/write
- no file writes
- no DB writes

Safety flags must remain false for live/host mutation fields.

## Apply Workflow Ordering Contract

Phase 6-E0 harness apply workflow contract (simulated only):

1. `plan`
2. `apply`
3. `verify`

This sequence must be testable with deterministic call-order evidence.

## Verify Workflow Ordering Contract

Verify remains simulated-only in Phase 6-E0.

- verify may pass and return report-only DTO
- verify may fail by explicit failure-injection input
- verify failure does not authorize live rollback execution

## Rollback Workflow Ordering Contract

Rollback remains simulated-only in Phase 6-E0.

Expected simulated rollback path:

1. `plan`
2. `apply`
3. `verify` (fails via injection)
4. `rollback` guidance/report only

No live rollback execution is authorized.

## Failure Injection Contract

Failure injection is allowed only for deterministic harness simulation.

- apply failure injection
- verify failure injection
- rollback failure injection

Failure injection must not trigger host mutation paths.

## Safety Flags

Harness reports must include safety flags and keep all host-mutation fields false:

```text
live_firewall_read = false
live_firewall_write = false
iptables_save_executed = false
iptables_restore_executed = false
lock_acquired = false
restore_point_written = false
database_write = false
host_firewall_mutated = false
customer_nat_created = false
customer_firewall_rule_created = false
```

## Forbidden Host Interactions

Phase 6-E0 forbids all host firewall and runtime interactions, including:

- reading host firewall state
- writing host firewall state
- executing `iptables-save`
- executing `iptables-restore`
- acquiring apply/rollback locks
- creating restore points
- writing firewall apply rows
- mutating DB apply state

## Abuse Requirement Preservation

Phase 6-E0 must preserve the abuse contract unchanged:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Acceptance Criteria

Phase 6-E0 contract acceptance requires:

- deterministic fake/no-op harness call ordering tests
- explicit non-authorization language for live firewall operations
- explicit prohibition of host mutation and iptables execution
- explicit preservation of abuse 1h requirements
- no CLI apply/rollback/verify enablement
- no runtime behavior change

## Future Phase 6-E1 Entry Criteria

Before entering Phase 6-E1, Phase 6-E0 outputs must show:

- stable harness DTO contracts for plan/apply/verify/rollback simulation
- deterministic ordering and failure-injection tests passing
- safety flags locked to non-mutating values
- documentation alignment in `README.md`, `docs/INDEX.md`, `docs/FIREWALL.md`, `docs/AI_PHASE_6_TASK.md`, and `docs/REMAINING_PHASE_PLAN.md`
- continued `firewall_apply_allowed: no` until a dedicated apply gate is explicitly accepted
