# Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define the documentation/test-only entry criteria and authorization boundary that must be satisfied before any later, separate PR may even propose a dedicated live firewall apply gate.

## Current Gate Snapshot

Authoritative source:

```text
docs/PHASE_STATUS.md
```

Current state remains:

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

Phase 6-H is planned only, documentation/test-only, and non-authorizing.

Phase 6-H does **not** authorize:

- live firewall read
- live firewall write
- live firewall apply
- live rollback
- live verify
- `iptables-save`
- `iptables-restore`
- real iptables adapter
- DB apply writes
- lock acquisition
- restore point writes
- customer NAT redirects
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram

## Dedicated Apply Gate Entry Criteria

Before any later separate PR may propose a dedicated apply gate, all of the following must be true and evidenced:

- `docs/PHASE_STATUS.md` Current State is explicitly changed by a separate accepted gate.
- Farm/runtime time synchronization is fixed and evidenced.
- `python -m pytest -q` passes.
- `bash scripts/verify_current_phase_gate.sh` passes.
- `mpf config validate` reports OK.
- `mpf doctor` reports OK.
- `mpf db status` reports OK.
- `mpf proxy doctor` reports OK.
- backend external exposure = NO.
- backend internal reachability = OK.
- no customer NAT redirects exist before the dedicated apply gate.
- no customer firewall rules exist before the dedicated apply gate.
- `firewall.apply_mode` remains `plan_only` until an explicit accepted gate changes it.
- `proxy.runtime_activation_allowed` remains `false` until an explicit accepted gate changes it.
- no production customer traffic is active.
- rollback readiness has explicit evidence.
- verify readiness has explicit evidence.
- restore point readiness has explicit evidence.
- lock readiness has explicit evidence.
- operator approval template is completed.
- manual rollback runbook exists.
- stop conditions are reviewed.

## Required Preconditions Before Any Future Apply Gate

Any future dedicated apply gate proposal must be a separate, explicitly accepted step with separate server evidence and explicit gate-value updates in `docs/PHASE_STATUS.md`.

## Time Synchronization Blocker

Farm5 time synchronization has previously been reported as not confirmed.

This blocker must be resolved and evidenced before any dedicated live apply gate, production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Operator Approval Requirements

A dedicated apply gate proposal must include a completed operator approval template with named approvers, dated approvals, scope boundary, rollback contact, and explicit sign-off that current non-authorizing constraints are understood.

## Required Evidence Before Any Future Apply Gate

Minimum evidence set must include:

- synced repository version and runtime version evidence
- full command outputs for pytest and gate verification commands
- backend exposure/reachability evidence
- explicit no-customer-NAT/no-customer-firewall-rules evidence
- explicit production-traffic-none evidence
- explicit gate-flag evidence (`firewall_apply_allowed=no`, `abuse_automation_allowed=no` until changed by accepted gate)

## Rollback Readiness Entry Criteria

Before proposing any dedicated apply gate, rollback readiness evidence must prove manual rollback runbook availability, explicit rollback decision points, and tested rollback artifact expectations from operator-provided snapshots.

## Verify Readiness Entry Criteria

Before proposing any dedicated apply gate, verify readiness evidence must prove deterministic post-action verification expectations, failure classification, and operator-visible verify outcomes.

## Restore Point Readiness Entry Criteria

Before proposing any dedicated apply gate, restore point readiness evidence must prove restore point contract completeness, required metadata, and operator review requirements.

## Lock Readiness Entry Criteria

Before proposing any dedicated apply gate, lock readiness evidence must prove lock scope definition, overlap prevention strategy, timeout/failure behavior, and operator unlock/runbook safety notes.

## Backend Exposure Preconditions

The dedicated apply gate cannot be proposed if backend direct external/public exposure exists. Internal backend reachability must remain healthy and independently verified.

## Local-only Runtime Preconditions

Accepted runtime listeners must remain local-only under current gate constraints until a separate accepted gate explicitly changes runtime exposure policy.

## Customer/NAT Preconditions

No customer NAT redirects and no customer firewall rules may exist before the dedicated apply gate proposal. Dedicated apply gate planning must not pre-create runtime customer traffic paths.

## Database Preconditions

No DB apply writes are authorized by Phase 6-H. Any future dedicated apply gate proposal must clearly separate documentation/test-only readiness evidence from runtime mutation authorization.

## Abuse Invariant Preservation

The abuse invariant remains mandatory and unchanged:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Stop Conditions

Stop and block any dedicated apply gate proposal if any of the following is true:

- gate values are changed without separate accepted authorization evidence
- time synchronization remains unconfirmed
- backend exposure is unsafe or internal reachability is broken
- customer NAT redirects/customer firewall rules are introduced before authorization
- production traffic is active before explicit acceptance
- non-authorized behaviors are introduced (live read/write/apply/rollback/verify, `iptables-save`, `iptables-restore`, real adapters, DB apply writes, locks, restore point writes)

## Explicit Future Boundary

Live apply remains forbidden until a later dedicated apply gate is explicitly accepted with separate server evidence.

This Phase 6-H document is not that gate.

## Acceptance Criteria For This Documentation Step

- document exists and is indexed
- wording clearly marks Phase 6-H as planned, documentation/test-only, non-authorizing
- no current gate authorization is changed
- no live/runtime/firewall/database mutation behavior is introduced
- abuse invariant and time synchronization blocker remain explicit
