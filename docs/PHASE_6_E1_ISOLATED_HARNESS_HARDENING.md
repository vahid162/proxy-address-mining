# Phase 6-E1 — Isolated Harness Contract Hardening

## Purpose
Phase 6-E1 is isolated/non-production only. It hardens fake/no-op harness contracts and tests without enabling runtime mutations.

## Current Gate Snapshot
- accepted phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
- working phase: Phase 6 — Firewall Planner
- firewall_apply_allowed: no
- production_traffic: none
- abuse_automation_allowed: no

## Non-Authorization Statement
Phase 6-E1 does not authorize host production firewall mutation, live firewall read/write, `iptables-save`, `iptables-restore`, real iptables adapters, live apply/rollback/verify, DB apply writes, lock acquisition, restore point writes, customer NAT rules, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

## E0 Accepted Baseline
Phase 6-E0 accepted isolated apply harness contracts on farm5 and preserved all non-authorization safety gates.

## E1 Hardening Scope
- tighten fake/no-op harness DTO and reporting contracts
- deterministic in-memory operation ordering
- failure injection coverage for plan/apply/verify/rollback
- regression guards that prove no host mutation behavior

## Harness Operation Contract
Harness operations are report-only simulation steps: `plan`, `apply`, `verify`, `rollback`.

## Harness Safety Flags Contract
The following flags must remain false:
- `live_firewall_read`
- `live_firewall_write`
- `iptables_save_executed`
- `iptables_restore_executed`
- `lock_acquired`
- `restore_point_written`
- `database_write`
- `host_firewall_mutated`
- `customer_nat_created`
- `customer_firewall_rule_created`

## Harness Workflow Report Contract
Workflow reports are deterministic DTOs only and include call order, operation results, and safety flags.

## Failure Injection Matrix
Supported in-memory failure injection: `plan`, `apply`, `verify`, `rollback`. No DB/files/subprocess/firewall reads are allowed.

## Negative Safety Assertions
Any change that enables live firewall mutation behavior in E1 must be rejected.

## Repository Scan Guards
Scan source/runtime files only for forbidden runtime terms; documentation tests may mention terms only as prohibited/non-authorized behavior.

## Forbidden Host Interactions
No subprocess firewall calls, no real iptables adapter, no lock acquisition, no restore point writes, no DB apply writes.

## Abuse Requirement Preservation
Abuse invariant remains mandatory:
- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Acceptance Criteria
- isolated/non-production-only hardening completed
- tests prove fake/no-op and no host mutation behavior
- no live apply gate opened

## Future Phase 6-E2 Entry Criteria
Phase 6-E2 may proceed only after E1 hardening tests are stable and non-authorization gates remain unchanged.
