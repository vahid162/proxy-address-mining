# PHASE 6-F — MANUAL CANARY GATE DEFINITION

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define the **manual canary gate contract** for a future apply phase without enabling any runtime/live behavior in the current gate.

## Current Gate Snapshot

Authoritative gate source: `docs/PHASE_STATUS.md`.

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

Phase 6-F does **not** authorize:

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

## Manual Canary Gate Definition Scope

Phase 6-F may define only:

- manual canary criteria
- operator approval requirements
- evidence templates
- rollback-readiness checklist
- backend exposure preconditions
- local-only runtime preconditions
- safety assertions and test guards

Explicitly:

- Phase 6-F is **not** canary execution.
- Phase 6-F is **not** host preparation.
- Phase 6-F is **not** live apply.
- Phase 6-F is **not** live firewall inspection.
- Phase 6-F is **not** a permission to run `iptables-save` or `iptables-restore`.

## Required Operator Approval Inputs

Future approval template fields (definition-only in Phase 6-F):

- operator identity
- date/time
- server name
- exact version
- reviewed `PHASE_STATUS`
- reviewed test result
- reviewed rollback plan
- explicit no-production-traffic confirmation
- explicit local-only runtime confirmation
- explicit backend external exposure = NO confirmation
- explicit internal backend reachability = OK confirmation

## Required Evidence Inputs

Future evidence template fields (definition-only in Phase 6-F):

- `mpf --version`
- `mpf phase-status`
- `mpf config validate`
- `mpf doctor`
- `mpf db status`
- `mpf proxy doctor`
- `verify_current_phase_gate.sh`
- `python -m pytest -q`
- listener safety evidence
- backend exposure evidence
- no customer NAT/customer firewall refs evidence
- rollback readiness evidence

## Required Safety Preconditions

Before any future canary execution phase (not in Phase 6-F):

- phase gate must explicitly authorize required behavior
- production traffic must remain disabled unless separately authorized
- backend safety split must be demonstrably preserved
- local-only runtime limitations must be validated
- negative safety assertions must pass in documentation tests

## Rollback Readiness Checklist

Definition-only checklist for future phases:

- rollback operator identified
- rollback decision threshold documented
- rollback validation steps documented
- rollback evidence capture checklist documented

This section is documentation-only in Phase 6-F and must **not** create restore points or rollback files.

## Backend Exposure Preconditions

Future canary gate must require:

- `internal_backend_reachable = OK`
- `external_backend_exposed = NO`

## Local-only Runtime Preconditions

Future canary gate must require confirmation that accepted limited runtime listeners are local-only and that no public backend/UI exposure is introduced.

## Time Synchronization Warning

farm5 time synchronization has previously been reported as not confirmed.
This is not a Phase 6-F documentation/test blocker, but it must be resolved before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Abuse Requirement Preservation

The mandatory abuse invariant remains unchanged:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Negative Safety Assertions

Phase 6-F documentation/tests must keep asserting all of the following remain forbidden now:

- live firewall read/write/apply/rollback/verify
- `iptables-save`/`iptables-restore` execution
- real iptables adapter usage
- DB apply writes, lock acquisition, restore point writes
- customer NAT redirects/customer firewall rules
- production traffic, usage automation, abuse automation
- UI or Telegram activation

## Explicit Future Boundary

Any future canary execution or live apply work requires a separate explicit accepted phase gate update in `docs/PHASE_STATUS.md` with audited evidence. Phase 6-F alone cannot open that gate.

## Acceptance Criteria

Phase 6-F is acceptable only when:

- this document exists and is indexed
- phase documents consistently state Phase 6-E3 accepted / Phase 6-F planned
- Phase 6-F is clearly documented as non-authorizing
- documentation tests confirm no live gate is opened
- abuse 1h invariant remains explicit and unchanged
