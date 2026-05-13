# Remaining Phase Plan

Status: planning reference aligned to `docs/PHASE_STATUS.md`.

`docs/PHASE_STATUS.md` remains the authoritative gate. This plan does not open any runtime gate by itself.

## Phase 6-D — Documentation Alignment + Live Apply Boundary

Phase 6-D remains documentation/test-only and does not open the apply gate.

- **Phase 6-D1 contract:** `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md` defines live-apply boundaries, non-authorization rules, stop conditions, and Phase 6-E entry criteria for isolated/non-production planning only.
- **Phase 6-D1 accepted on farm5:** recorded in `docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md`.

### Purpose
- Align all phase docs after Phase 6-C acceptance.
- Define exact future live-apply boundaries without enabling them now.

### Allowed Scope
- documentation/test-only updates aligned with `docs/PHASE_STATUS.md`
- align `README.md`, `AGENTS.md`, `docs/AI_PHASE_6_TASK.md`, `docs/INDEX.md`, and `docs/ROADMAP.md`
- define exact future live read boundary
- define exact future live write boundary
- define when `iptables-save` may become allowed (future accepted gate only)
- define when `iptables-restore` may become allowed (future accepted gate only)
- define stop conditions and operator evidence requirements
- define fake/no-op apply adapter contracts
- define restore/lock/verify/rollback contracts
- add docs regression tests and non-mutating service-boundary tests only if needed

### Forbidden Scope
- subprocess `iptables-save`
- subprocess `iptables-restore`
- live firewall read
- live firewall write
- lock acquisition
- restore point write
- DB apply write
- customer NAT rules
- customer firewall rules
- production traffic
- abuse automation

### Acceptance Criteria
- stale step wording removed from core docs
- docs explicitly state Phase 6-C accepted as offline readiness/review only
- docs explicitly state next safe step is Phase 6-D0 / Phase 6-D documentation/test-only
- tests prove live apply and runtime mutation remain forbidden

### Safety Notes
- no apply gate is opened in this phase
- `firewall_apply_allowed` must stay `no`

### Server Verification Expectations
- documentation/test evidence only
- no host firewall mutation or runtime traffic changes

## Phase 6-E — Isolated Apply Harness

- Reference: `docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md`
- Phase 6-E0 accepted on farm5 via `docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md`.
- Phase 6-E1 contract reference: `docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md`.
- Phase 6-E1 accepted on farm5 via `docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md`.
- Phase 6-E2 contract reference: `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md`.
- Phase 6-E2 is accepted.
- Phase 6-E3 is accepted as isolated/non-production evidence review / non-authorizing gate checklist only.
- Phase 6-F is accepted as manual canary gate definition only, documentation/test-only and non-authorizing.
- Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review is accepted as documentation/test-only and non-authorizing. Future dedicated apply gate remains not accepted and not authorized.
- No live apply/read/write, `iptables-save`, `iptables-restore`, real adapters, DB writes, locks, restore points, NAT, or customer firewall rules are allowed.
- Host production firewall mutation remains forbidden.

Purpose: design and validate isolated, non-production apply harness contracts.

Allowed scope: harness design docs, fake adapter tests, isolated fixture-driven validation.

Forbidden scope: host production firewall mutation is forbidden; no production host live apply.

Acceptance criteria: reproducible harness contract outputs and safety proofs.

Safety notes: no production gate change; no runtime customer traffic.

Server verification expectations: isolated evidence only, no production firewall mutation.

## Phase 6-F — Manual Canary Gate Definition
Purpose: operator-reviewed canary gate definition before controlled apply.

Allowed scope: canary checklist docs, operator approval/evidence templates, dry-run-only checks.

Forbidden scope: unattended apply, automation-led apply, production rollout.

Acceptance criteria: explicit manual go/no-go criteria with rollback readiness evidence.

Safety notes: human review mandatory.

Server verification expectations: manual evidence bundle only.

## Phase 6-G — Controlled Live Apply
Purpose: limited, explicitly gated live apply after prior acceptance steps.

Allowed scope: only accepted, audited, service-boundary apply path.

Forbidden scope: ad-hoc firewall mutation, interface-direct shell apply.

Acceptance criteria: apply/verify/rollback lifecycle evidence and audit trail.

Safety notes: restore points and lock discipline required.

Server verification expectations: canary then controlled expansion with documented outcomes.

## Phase 7 — Usage + Policy/Reject Accounting
Purpose: add usage/accounting foundations through service-layer contracts.

Allowed scope: structured accounting models, policy/reject counters, retention-aware reporting contracts.

Forbidden scope: traffic mutation unrelated to approved scope, bypassing service boundary.

Acceptance criteria: tested accounting contracts and auditability.

Safety notes: phase order must not bypass abuse prerequisites.

Server verification expectations: metric correctness checks and gate-safe rollout evidence.

## Phase 8 — Abuse 1h Core
Purpose: implement core abuse state machine and evidence path.

Allowed scope: `normal -> over_tracking -> over_grace -> hard`, full active-customer coverage in enabled lanes, exemptions with reason/expiry.

Forbidden scope: weakening abuse invariants.

Acceptance criteria: sustained miner-abuse hardens after about 3600 seconds; farms-over alone must not harden; worker-over alone must not harden; no silent skip.

Safety notes: this abuse 1h invariant is mandatory and must not be weakened.

Server verification expectations: auditable hard/unhard evidence with coverage proofs.

## Phase 9 — Check / Report / Diagnostics
Purpose: richer operator diagnostics/report surfaces.

Allowed scope: read/report tooling via service layer.

Forbidden scope: hidden state mutation from diagnostic paths.

Acceptance criteria: deterministic reports and safety regression coverage.

Safety notes: diagnostics must not bypass gates.

Server verification expectations: report reproducibility evidence.

## Phase 10 — Session / Worker / Policy / Share Timeline
Purpose: structured timeline/evidence layers for sessions/workers/shares.

Allowed scope: evidence schema/services, retention-aware aggregation boundaries.

Forbidden scope: unbounded raw collection without retention policy.

Acceptance criteria: tested timeline contracts and worker identity safeguards.

Safety notes: worker name alone is not guaranteed physical identity.

Server verification expectations: storage and retention conformance evidence.

## Phase 11 — Local UI + Buyer Read-only
Purpose: local-only UI and buyer read-only visibility.

Allowed scope: local bind UI, read-only buyer-facing views.

Forbidden scope: public exposure or direct mutating buyer controls.

Acceptance criteria: local-only binding and read-only enforcement tests.

Safety notes: buyer accounts remain separate from customer service rows.

Server verification expectations: bind/exposure checks and permission tests.

## Phase 12 — Operator UI Actions
Purpose: controlled operator actions through audited UI workflows.

Allowed scope: reviewed operator actions via service APIs.

Forbidden scope: UI direct DB/firewall mutation bypassing services.

Acceptance criteria: audit/event coverage for each action.

Safety notes: risky operations require restore/evidence pathways.

Server verification expectations: action-to-audit traceability checks.

## Phase 13 — Telegram
Purpose: staged Telegram integration.

Allowed scope: notification-first integration.

Forbidden scope: direct shell command execution from Telegram flows.

Acceptance criteria: notification contracts and safety tests.

Safety notes: no privileged command execution path.

Server verification expectations: token/secret handling and boundary checks.

## Phase 14 — Worker Policy Enforcement
Purpose: implement worker-policy enforcement boundary.

Allowed scope: worker policy service + enforcement adapter with evidence/audit.

Forbidden scope: firewall-only worker blocking model.

Acceptance criteria: tested worker-policy lifecycle and enforcement traceability.

Safety notes: maintain separation between worker identity evidence and firewall policy.

Server verification expectations: controlled enforcement evidence with rollback readiness.

Phase 6-E0 must not mutate the host production firewall.


Phase 6-E1 must remain fake/no-op, isolated/non-production, and must not mutate the host production firewall.
Phase 6-E1 allows no live read/write, no iptables-save, no iptables-restore, no real iptables adapter, no DB apply writes, no locks, and no restore points.


Phase 6-F is accepted as manual canary gate definition only, documentation/test-only and non-authorizing.
Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review is accepted as documentation/test-only and non-authorizing. Future dedicated apply gate remains not accepted and not authorized.
Phase 6-G is controlled live apply gate planning / pre-apply review only.
Phase 6-G does not authorize live apply/read/write, iptables-save, iptables-restore, real adapters, DB writes, locks, restore points, NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.


Phase 6-G is accepted as planning/pre-apply review only (documentation/test-only, non-authorizing).
Apply Slice 1 is already documented as a planned documentation/test-only boundary and is not accepted by server evidence unless explicitly recorded elsewhere.
Apply Slice 3 is documented as planned documentation/test-only controlled no-customer harness contract, not accepted by server evidence yet, and not authorized. Next planned implementation sub-step is Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal (planned, documentation/test-only, non-authorizing).
Future dedicated apply gate remains not accepted and not authorized.


Phase 6-H is accepted as documentation/test-only and non-authorizing. Future dedicated Phase 6 apply gate remains not accepted and not authorized. No live apply/read/write, iptables-save, iptables-restore, real adapters, DB writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram are allowed.


## Remaining Phase 6 Alignment With Master Roadmap

Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.
They do not change the master roadmap phase ordering.
After Phase 6 final acceptance, execution must return to the master roadmap sequence:

- Phase 7 remains **Usage + Policy/Reject Accounting**.
- Phase 8 remains **Abuse 1h Core**.
- Abuse automation must not start before Phase 8.

No further documentation-only Phase 6 sub-step should be added unless it closes a concrete blocker for the dedicated apply gate path and Phase 6 final acceptance.

### Finite Remaining Phase 6 Implementation Slices

A. **Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary**
- server-synced and accepted only as documentation/test-only readiness boundary
- not authorized
- no live snapshot read now
- no `iptables-save` now
- no subprocess firewall calls now
- no real adapter now
- no DB writes now
- no restore point or lock now

B. **Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness**
- server-synced and accepted only as documentation/test-only readiness boundary
- not authorized
- no restore point writes now
- no lock acquisition now
- no DB apply writes now
- no migrations now
- no live firewall read/write/apply now
- no iptables-save or iptables-restore now
- no real adapters or subprocess firewall calls now

C. **Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness**
- next planned sub-step
- planned only, documentation/test-only, non-authorizing
- isolated/non-production only
- must not authorize no-customer apply or real runtime apply
- no customer NAT, no customer firewall rules, no production traffic

D. **Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal**
- planned only
- requires time synchronization fixed and evidenced
- requires separate `docs/PHASE_STATUS.md` update and server evidence before any authorization

Phase 6 final acceptance is allowed only after apply/verify/rollback safety is proven.
Phase 7 starts only after Phase 6 final acceptance.
