# Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define Phase 6-G as planning-only pre-apply review scope for a future controlled live apply gate, without authorizing any live behavior in the current gate.

## Current Gate Snapshot

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

Phase 6-G does not authorize:

- live firewall read
- live firewall write
- live firewall apply
- live rollback
- live verify
- iptables-save
- iptables-restore
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

## Controlled Live Apply Gate Planning Scope

Phase 6-G may define only:

- future controlled live apply prerequisites
- final operator approval requirements
- evidence templates
- rollback readiness requirements
- verify readiness requirements
- pre-apply review criteria
- backend exposure preconditions
- local-only runtime preconditions
- stop conditions
- safety assertions and test guards

Phase 6-G is not live apply.
Phase 6-G is not canary execution.
Phase 6-G is not host preparation.
Phase 6-G is not live firewall inspection.
Phase 6-G is not permission to run iptables-save.
Phase 6-G is not permission to run iptables-restore.
Phase 6-G is not permission to acquire locks.
Phase 6-G is not permission to write restore points.
Phase 6-G is not permission to write DB apply records.

## Pre-Apply Review Scope

Phase 6-G pre-apply review is documentation/test-only criteria planning and evidence-structure planning. It is not runtime behavior, not CLI/runtime apply behavior, and not any live firewall interaction.

## Required Operator Approval Template

Future template fields only:

- operator identity
- date/time
- server name
- exact version
- reviewed PHASE_STATUS
- reviewed test result
- reviewed pre-apply review
- reviewed rollback readiness
- reviewed verify readiness
- explicit no-production-traffic confirmation
- explicit local-only runtime confirmation
- explicit backend external exposure = NO confirmation
- explicit internal backend reachability = OK confirmation
- explicit abuse automation remains disabled confirmation
- explicit firewall_apply_allowed remains no confirmation

## Required Evidence Template

Future template fields only:

- mpf --version
- mpf phase-status
- mpf config validate
- mpf doctor
- mpf db status
- mpf proxy doctor
- verify_current_phase_gate.sh
- python -m pytest -q
- listener safety evidence
- backend exposure evidence
- no customer NAT/customer firewall refs evidence
- no live apply evidence
- no iptables-save/iptables-restore execution evidence
- rollback readiness evidence
- verify readiness evidence

## Required Safety Preconditions

- PHASE_STATUS current state remains unchanged.
- firewall.apply_mode remains plan_only.
- proxy runtime remains limited_runtime_local_only.
- no production customer traffic is active.
- backend external exposure remains NO.
- internal backend reachability remains OK.

## Required Rollback Readiness Template

Documentation-only template for future review readiness. It must not create restore points or rollback files in Phase 6-G.

## Required Verify Readiness Template

Documentation-only template for future verification readiness. It must not run live verify in Phase 6-G.

## Backend Exposure Preconditions

- external_backend_exposed = NO
- internal_backend_reachable = OK

## Local-only Runtime Preconditions

- accepted runtime listeners remain local-only
- no customer/public listener exposure is allowed
- no customer NAT redirects and no customer firewall rules

## Time Synchronization Warning

farm5 time synchronization has previously been reported as not confirmed.
This is not a Phase 6-G documentation/test blocker, but it must be resolved before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Abuse Requirement Preservation

- normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Negative Safety Assertions

Phase 6-G must not enable or imply authorization for live apply, live firewall inspection, live mutation, host firewall mutation, DB apply writes, locks, restore points, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

## Explicit Future Boundary

Live apply remains forbidden until a dedicated apply gate is explicitly accepted with separate acceptance evidence.

## Acceptance Criteria

- Phase 6-G is documented as planned only.
- Phase 6-G is documentation/test-only and non-authorizing.
- Current State gate values remain unchanged.
- No live behavior is introduced.
- Non-authorization statements remain explicit and test-guarded.
