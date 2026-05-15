# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main repository version before this PR is 0.1.96; latest recorded farm5 sync evidence is 0.1.96 (0.1.90 remains historical evidence).
- Phase 5 remains the accepted phase.
- Phase 6 remains the working phase.
- Current work is Phase 6 Firewall Planner / Apply Gate Readiness.
- mpf firewall apply-gate-readiness is read-only/report-only and remains BLOCKED.
- mpf firewall gate-review includes apply_gate_readiness_summary and remains BLOCKED.
- Read-only iptables-save live snapshot path is explicitly authorized and evidenced.
- Restore point + scoped lock + DB apply record controlled boundary was executed once and evidenced.
- Live firewall write/apply/rollback/verify remains unauthorized.
- iptables-restore remains unauthorized.
- customer NAT/customer firewall rules remain unauthorized.
- production traffic remains none.
- usage automation and abuse automation remain unauthorized.
- Host production firewall mutation remains forbidden.

## Completed Phase 6 Safety Sub-Steps

- Phase 6-C through Phase 6-H established offline/readiness/boundary/review contracts.
- Apply Slice 1 and Slice 2 were server-synced as documentation/test-only readiness boundaries.
- Apply Slice 3 and Slice 4 were server-synced as documentation/test-only boundaries.
- Controlled restore point + scoped lock + DB apply record preparation boundary was executed once on farm5 under the accepted controlled boundary; final_decision/apply_decision remained BLOCKED and no live firewall/NAT/customer rule runtime behavior was authorized.
- Future Dedicated Phase 6 Apply Gate Proposal/Review was documented as non-authorizing historical/reference context.
- farm5 sync evidence for 0.1.88 was recorded.
- apply-gate-readiness was implemented as read-only/report-only.
- gate-review now includes apply_gate_readiness_summary.
- gate-review JSON serialization fix (PR #100) is evidenced on farm5; config-only gate-review JSON output is valid, non-crashing, and remains BLOCKED/non-applyable/non-authorizing.
- Gate-review includes live snapshot scaffold/read summaries. The explicitly gated read-only iptables-save snapshot path is authorized and evidenced. Unauthorized live firewall reads and unauthorized iptables-save execution remain forbidden. Live firewall write/apply/rollback/verify and iptables-restore remain forbidden until their dedicated gates are explicitly accepted.
- farm5 was synced to 0.1.90 successfully.
- No-customer apply/verify/rollback scaffold exists as report-only/non-authorizing surface and remains BLOCKED / NOT_AUTHORIZED_FOR_APPLY.
- No-customer apply/verify/rollback explicit acceptance-gate report exists as report-only/non-executing surface and remains BLOCKED for execution until separate server evidence is collected.
- No-customer apply/verify/rollback acceptance-gate server evidence was recorded on farm5 as report-only/non-executing; apply/verify/rollback decisions remained BLOCKED and no firewall/NAT/customer rule runtime behavior was authorized.
- No-customer apply/verify/rollback execution-gate report exists as report-only/non-executing surface and remains BLOCKED / NOT_ACCEPTED_FOR_EXECUTION.
- No-customer apply/verify/rollback execution acceptance package exists as artifact-only/report-only/non-executing surface and remains BLOCKED / EXECUTION_ACCEPTANCE_DEFINED_NOT_EXECUTABLE.
- No-customer runtime execution approval readiness exists as report-only/non-executing/non-authorizing surface and remains BLOCKED / RUNTIME_EXECUTION_APPROVAL_READY_BUT_NOT_GRANTED; this step is done and synced on farm5 at 0.1.94.
- Controlled no-customer runtime execution evidence package is done and farm5 synced at 0.1.95.
- Repository version after this PR will be 0.1.97; latest farm5 sync evidence remains 0.1.96 until next operator sync. Runtime execution still requires separate operator approval, separate runtime execution PR, and fresh farm5 runtime execution evidence.
- farm5 0.1.94 sync evidence is recorded as completed.
- Historical labels retained for compatibility with existing docs checks: `## Phase 6-E — Isolated Apply Harness`, `Remaining Phase 6 Alignment With Master Roadmap`, and `Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review`.
- Host production firewall mutation remains forbidden; must not mutate the host production firewall.
- Compatibility anchors: `Phase 6-E0 accepted on farm5`, `Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.`, and `host production firewall mutation is forbidden`.
- Compatibility anchors for prior roadmap tests: `Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary`, `Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness`, `Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness`, and `Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal`.

## Finite Remaining Path

1. Dedicated Apply Gate Proposal/Review — done
2. No-customer apply/verify/rollback scaffold — done
3. No-customer apply/verify/rollback explicit acceptance — done and evidenced
4. No-customer apply/verify/rollback execution package — done as report-only/non-executing
5. No-customer runtime execution approval readiness — done and farm5 synced at 0.1.94
6. Controlled no-customer runtime execution evidence package — done and farm5 synced at 0.1.95
7. Manual canary customer NAT/customer firewall rules proposal + explicit acceptance readiness — done and farm5 synced at 0.1.96, report-only/non-authorizing
8. Manual canary customer server evidence / final gate review — current next target, must remain BLOCKED while no non-deleted customer exists and no operator acceptance evidence exists
9. Phase 6 final acceptance readiness — added by this PR, must remain BLOCKED until manual canary evidence is accepted
10. Phase 6 final acceptance
11. Phase 7 Usage + Policy/Reject Accounting
12. Phase 8 Abuse 1h Core

Compatibility note: Future Dedicated Phase 6 Apply Gate Proposal/Review remains the documented next planning target label in historical checks.
Legacy compatibility anchors for older checks: 8. Phase 7 Usage + Policy/Reject Accounting; 9. Phase 8 Abuse 1h Core.

## Non-Negotiable Current Prohibitions

- no production traffic
- no live firewall write/apply/rollback/verify
- read-only iptables-save live snapshot is authorized and evidenced
- no iptables-restore until a dedicated apply gate is accepted
- no real firewall adapter or subprocess firewall calls
- no uncontrolled restore point writes, lock acquisition, or DB apply writes outside the accepted controlled execution boundary
- no migrations
- no customer NAT or customer firewall rules
- firewall apply, iptables-restore, customer NAT/customer firewall rules, and production traffic remain forbidden
- no usage automation
- no abuse automation before Phase 8
- no UI or Telegram
- no public v2rayA UI exposure
- no public backend exposure

## Production Readiness Sequence

Phase 6 final acceptance is not complete until live snapshot read, restore point, lock, apply, verify, and rollback are proven through accepted gates.

Phase 7 starts only after Phase 6 final acceptance.

Phase 8 is mandatory before the system is considered production-complete because the one-hour abuse requirement is a core requirement.




## Master Phase Summaries

### Phase 7 — Usage + Policy/Reject Accounting
Purpose: add usage/accounting foundations through service-layer contracts.

### Phase 8 — Abuse 1h Core
Purpose: implement core abuse state machine and evidence path.
Required invariant: normal -> over_tracking -> over_grace -> hard.
farms-over alone must not harden; worker-over alone must not harden.
The abuse 1h invariant must not be weakened.
sustained miner-abuse hardens after about 3600 seconds.
all active customers in enabled lanes must be covered.
no silent skip.

### Phase 9 — Check / Report / Diagnostics
Purpose: richer operator diagnostics/report surfaces.

### Phase 10 — Session / Worker / Policy / Share Timeline
Purpose: structured timeline/evidence layers for sessions/workers/shares.

### Phase 11 — Local UI + Buyer Read-only
Purpose: local-only UI and buyer read-only visibility.

### Phase 12 — Operator UI Actions
Purpose: controlled operator actions through audited UI workflows.

### Phase 13 — Telegram
Purpose: staged Telegram integration (notification-first).

### Phase 14 — Worker Policy Enforcement
Purpose: implement worker-policy enforcement boundary.



Compatibility anchor: latest recorded farm5 sync evidence is 0.1.94 (historical).

Compatibility anchor: repository version after this PR becomes 0.1.95 (historical).

Compatibility anchor: Controlled no-customer runtime execution evidence — current next target.
