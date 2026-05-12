# Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define the planned readiness boundary for a **future** live firewall snapshot read gate, without authorizing or implementing any live firewall reads in this step.

## Scope

This step is limited to documentation/test-only planning contracts and regression checks.

## Non-Authorization Statement

This document is planned only, documentation/test-only, and non-authorizing.

It does **not** authorize:

- live firewall read
- `iptables-save`
- live firewall write
- live firewall apply
- live rollback
- live verify
- `iptables-restore`
- real iptables adapter
- subprocess firewall calls
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

## Why Live Snapshot Readiness Exists

A future dedicated apply gate may require trusted live snapshot inputs. This slice defines safety/readiness conditions before any authorization can be proposed.

## Future Live Snapshot Entry Criteria

Before any future live snapshot read can be proposed, all of the following must be evidenced:

- separate accepted gate in `docs/PHASE_STATUS.md`
- explicit operator approval
- time synchronization fixed and evidenced
- `python -m pytest -q` passes
- `bash scripts/verify_current_phase_gate.sh` passes
- `mpf --version` matches repository version
- `mpf phase-status` matches `docs/PHASE_STATUS.md` Current State
- `mpf config validate` OK
- `mpf doctor` OK
- `mpf db status` OK
- `mpf proxy doctor` OK
- backend external exposure = NO
- backend internal reachability = OK
- no customer NAT redirects before gate
- no customer firewall rules before gate
- no MPF/customer firewall references before gate
- `firewall.apply_mode` remains `plan_only` until explicit accepted gate changes it
- `proxy.runtime_activation_allowed` remains `false` until explicit accepted gate changes it
- production traffic remains none
- dry-run/offline snapshot parser tests pass
- clear failure behavior if live snapshot is unavailable
- no fallback to empty snapshot if live read fails
- no fallback to guessed firewall state if live read fails

## Required Preconditions Before Any Future Live Snapshot Read

Any future live snapshot read proposal must be introduced only in a separate, explicitly accepted gate with separate evidence and explicit gate-value updates.

## Operator Approval Requirements

Future authorization proposal must include named operator approvers, dated approvals, and explicit sign-off on boundary constraints.

## Time Synchronization Requirement

Time synchronization must be fixed and evidenced before any future live snapshot read authorization can be proposed.

## Backend Exposure Preconditions

Backend external exposure must remain `NO` and backend internal reachability must remain `OK`.

## Local-only Runtime Preconditions

Runtime exposure must remain local-only under current gate constraints unless a separate accepted gate changes that policy.

## Customer/NAT Preconditions

No customer NAT redirects and no customer firewall rules may exist before future live snapshot read authorization.

## Safety Stop Conditions

Stop and block future authorization proposals if gate values are changed without explicit acceptance evidence, if time sync remains unconfirmed, if backend exposure is unsafe, or if any non-authorized behavior is introduced.

## Required Evidence Before Any Future Authorization

Required evidence must include gate verification outputs, version alignment outputs, doctor/config/db/proxy checks, backend exposure/reachability evidence, no NAT/customer firewall evidence, and production-traffic-none evidence.

## Failure Behavior For Future Live Snapshot Read

- failure to read live snapshot must block apply
- failure must be reported clearly to operator
- failure must not be treated as an empty firewall
- failure must not be treated as a clean firewall
- failure must not silently continue to restore/lock/apply
- no destructive cleanup may run after snapshot failure

## Abuse Invariant Preservation

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed
- abuse automation remains forbidden until Phase 8

## Boundary With Apply Slice 2

Apply Slice 1 only defines future live snapshot readiness.
Apply Slice 2 may later define restore point, lock, and DB apply record readiness.
Apply Slice 1 must not create restore points, acquire locks, or write DB apply records.

## Acceptance Criteria For This Documentation Step

- document exists and is indexed
- status remains planned/documentation-test-only/non-authorizing
- `docs/PHASE_STATUS.md` Current State remains unchanged
- next planned step wording points to Apply Slice 1 readiness boundary
- no live firewall read or `iptables-save` authorization is introduced
- no runtime/firewall/DB mutation behavior is introduced
- abuse invariant remains explicit and unchanged
