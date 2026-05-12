# Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning

Status: planned, isolated/non-production only, non-authorizing

## Purpose

Phase 6-E2 defines a deterministic, complete, and reviewable evidence package contract for isolated harness behavior and boundary planning only.

This phase is documentation/test-only and does not introduce runtime behavior.

## Current Gate Snapshot

Authoritative gate: `docs/PHASE_STATUS.md`

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
current_phase6_step: Phase 6-E1 accepted (isolated/non-production harness contract hardening); next planned step: Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning, isolated/non-production only
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

## Non-Authorization Statement

Phase 6-E2 does not authorize host production firewall mutation.

Phase 6-E2 does not authorize live firewall read/write.

Phase 6-E2 does not authorize `iptables-save` or `iptables-restore`.

Phase 6-E2 does not authorize real iptables adapters.

Phase 6-E2 does not authorize live apply/rollback/verify.

Phase 6-E2 does not authorize DB apply writes.

Phase 6-E2 does not authorize lock acquisition.

Phase 6-E2 does not authorize restore point writes.

Phase 6-E2 does not authorize customer NAT redirects or customer firewall rules.

Phase 6-E2 does not authorize production traffic.

Phase 6-E2 does not authorize usage automation, abuse automation, UI, or Telegram.

## E1 Accepted Baseline

Phase 6-E1 is accepted as isolated/non-production harness contract hardening only.

Phase 6-E2 starts from that baseline and remains non-authorizing.

## E2 Scope

Phase 6-E2 scope is evidence package / boundary planning only.

Allowed outputs are report/documentation-only contracts and tests that prove boundary preservation.

## Evidence Package Contract

In Phase 6-E2, the evidence package contract is report/documentation-only.

The contract must be deterministic and reviewable, and it must not require filesystem writes, DB writes, lock acquisition, live firewall reads, live firewall writes, `iptables-save`, or `iptables-restore`.

## Required Evidence Sections

Every Phase 6-E2 evidence package definition must include these sections:

- phase gate snapshot
- version/source reference
- harness workflow evidence
- operation call order evidence
- failure injection evidence
- safety flags evidence
- no-subprocess/no-iptables evidence
- no DB write evidence
- no lock/restore point evidence
- no NAT/customer firewall evidence
- proxy/runtime local-only evidence
- abuse invariant evidence
- next-step non-authorization statement

## Harness Operation Evidence

Harness operation evidence must document deterministic call order and explicit non-apply boundaries.

The evidence must remain isolated/non-production only.

## Safety Flag Evidence

Safety flags must explicitly remain false for live mutation paths, including live firewall read/write, apply/rollback/verify, lock acquisition, restore point writes, and DB apply writes.

## Failure Injection Evidence

Failure injection evidence must demonstrate boundary-preserving behavior under representative error paths without enabling live host interactions.

## Negative Safety Assertions

Phase 6-E2 evidence must include explicit assertions that no runtime/firewall/DB mutation authorization was introduced.

## Boundary Planning Rules

Boundary planning must preserve Phase 5 accepted / Phase 6 working gate and keep live apply forbidden until a dedicated apply gate is explicitly accepted.

## Forbidden Host Interactions

The following remain forbidden in Phase 6-E2:

- host production firewall mutation
- live firewall read
- live firewall write
- `iptables-save` execution
- `iptables-restore` execution
- subprocess firewall calls
- real iptables adapter usage
- live apply, live rollback, live verify
- DB apply mutation writes
- lock acquisition
- restore point writes
- customer NAT redirects
- customer firewall rules
- production customer traffic

## Abuse Requirement Preservation

The mandatory abuse invariant remains unchanged:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Acceptance Criteria

Phase 6-E2 acceptance (future) requires that evidence package contracts and tests are deterministic, complete, reviewable, and non-authorizing while preserving all current safety gates.

Phase 6-E2 is not accepted by this document.

## Future Phase 6-E3 Entry Criteria

Before entering Phase 6-E3, reviewers must confirm that Phase 6-E2 outputs stayed isolated/non-production only, remained report/documentation-only, and did not introduce any live firewall/runtime/DB mutation behavior.
