# Phase 6-D1 Live-Apply Boundary Contract (Documentation/Test-Only)

## Purpose

This document defines the **Phase 6-D1 live-apply boundary contract** so a future isolated Phase 6-E apply harness can be implemented without guessing.

Phase 6-D1 is **documentation/test-only** work. It preserves the accepted Phase 5 / working Phase 6 gate and does not introduce runtime behavior.

## Current Gate Snapshot

Authoritative source: `docs/PHASE_STATUS.md`.

Required current values remain:

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

## Non-Authorization Statement

Phase 6-D1 is **documentation/test-only** and **does not authorize live apply**.

It also does not authorize live rollback, live verify, live firewall reads/writes, lock acquisition, restore-point writes, or DB apply mutation paths.

## Live Read Boundary

- live firewall reads remain forbidden now.
- future live read may only be introduced after an explicit gate update in `docs/PHASE_STATUS.md`.
- offline snapshot files remain allowed.
- no implicit fallback from offline snapshot input to live read is allowed.

## Live Write Boundary

- live firewall writes remain forbidden now.
- iptables-save remains forbidden now.
- iptables-restore remains forbidden now.
- customer NAT/customer firewall rules remain forbidden now.
- future write path must go through `service -> adapter` only.

## Adapter Boundary

- CLI/API must not call subprocess directly for firewall apply lifecycle.
- service layer owns apply workflow orchestration and safety order.
- firewall adapter owns external firewall interaction.
- repositories own persistence.
- domain DTOs carry plan/apply/verify/rollback reports.

## No-op/Fake Apply Adapter Contract

- allowed for tests only.
- must never mutate host firewall.
- must expose deterministic calls for plan/apply/verify/rollback simulation.
- must prove call ordering without executing external commands.
- must be clearly separate from any real iptables adapter.

## Restore Point Boundary

- no restore point write now.
- future restore point is required before live apply, abuse hard, and manual rollback paths.
- future restore point must include checksum and evidence references.

## Lock Boundary

- no lock acquisition now.
- future apply must acquire scheduler/apply lock before any write step.
- overlapping apply attempts must fail safely.

## Verify Boundary

- no live verify now.
- future verify must compare desired model with accepted live snapshot after apply.
- failed verify must block success and produce rollback guidance.

## Rollback Boundary

- no live rollback now.
- future rollback must use stored restore artifact/snapshot.
- rollback must be audited.
- rollback must not be ad-hoc shell commands.

## Audit/Event Boundary

- future apply, rollback, and verify-failure paths must record event/audit entries.
- current Phase 6-D1 must not write these records.

## Operator Evidence Requirements

Operator evidence for Phase 6-D review must include:

- `mpf phase-status`
- `mpf config validate`
- `mpf doctor`
- `mpf db status`
- `mpf proxy doctor`
- planner output (`mpf firewall plan`, `mpf firewall diff`, related offline reports)
- offline evidence bundle and gate-review output
- explicit confirmation of no MPF/customer firewall refs
- explicit confirmation of no customer NAT redirects
- local-only backend/UI listener checks

## Stop Conditions

Stop and revise immediately if any of the following appears:

- any live firewall read/write
- any subprocess iptables-save/iptables-restore execution
- any customer NAT/customer firewall rule
- any production traffic
- any DB apply write
- any restore point write
- any lock acquisition
- any abuse automation
- backend public exposure
- backend internal reachability failure
- weakening of the abuse 1h requirement

## Future Phase 6-E Entry Criteria

Phase 6-E entry requires all of the following:

- this D1 contract document exists and is tested
- no-op/fake adapter boundaries are defined
- service/adapter/repository ownership is defined
- stop conditions are covered in docs regression tests
- `PHASE_STATUS` gate remains closed for live apply
- server evidence remains clean
- Phase 6-E remains isolated and non-production only

## Abuse Requirement Preservation

The mandatory abuse state machine remains unchanged:

```text
normal -> over_tracking -> over_grace -> hard
```

Required preservation points:

- sustained miner-abuse hardens after about 3600 seconds.
- farms-over alone must not harden.
- worker-over alone must not harden.
- all active customers in enabled lanes must be covered.
- no silent skip is allowed.
- hard uses firewall plan/apply/verify path only after the relevant apply gate.
- current Phase 6-D1 must not implement abuse automation.

## Acceptance Criteria

Phase 6-D1 is acceptable only when:

- this contract remains documentation/test-only.
- it does not authorize live apply.
- live firewall read/write, apply, rollback, and verify remain forbidden.
- iptables-save and iptables-restore remain forbidden now.
- customer NAT and customer firewall rules remain forbidden now.
- gate values in `docs/PHASE_STATUS.md` current state remain unchanged.
- docs regression tests enforce these boundaries.
