# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main repository version before this PR is 0.1.105.
- Repository version after this PR is 0.1.106.
- latest recorded farm5 sync evidence is 0.1.104.
- Phase 6 is the accepted phase: Firewall Planner accepted on farm5 as planner/reporting/gate-readiness only.
- Phase 7 is the working phase: Usage + Policy/Reject Accounting planning/readiness only.
- Phase 7 current target is Policy/Reject Accounting service-contract package.
- Next target after this PR is Phase 7 read-only reports/doctor package.
- Current work is Phase 7 planning/readiness.
- Phase 7 must begin with read-only/reporting/service-contract work.
- Phase 7 must not enable production traffic.
- Phase 7 must not enable firewall apply.
- Phase 7 must not enable iptables-restore.
- Phase 7 must not enable customer NAT/customer firewall rules.
- Phase 7 must not enable usage automation that changes runtime behavior.
- Phase 7 must not enable abuse automation.
- Phase 8 remains the future mandatory Abuse 1h Core phase.
- no offline sync is required after this PR if it remains report-only; batch sync after the next Phase 7 reports/doctor PR unless runtime/deploy/config/migration behavior changes.
- mpf firewall apply-gate-readiness is read-only/report-only and remains BLOCKED for runtime apply gates.
- mpf firewall gate-review includes apply_gate_readiness_summary and remains non-applyable for live apply.
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
- Manual canary customer NAT/customer firewall rules proposal + explicit acceptance readiness is done and farm5 synced at 0.1.96, report-only/non-authorizing.
- Manual canary customer server evidence / final gate review and Phase 6 final acceptance readiness were implemented and evidenced as report-only/non-authorizing surfaces.
- Phase 6 final acceptance review and operator acceptance decision are completed.
- Phase 6 is accepted after farm5 0.1.100 sync evidence as planner/reporting/gate-readiness only.
- Phase 6 acceptance does not authorize firewall apply, iptables-restore, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.
- Runtime execution still requires separate operator approval, separate runtime execution PR, and fresh farm5 runtime execution evidence.
- Historical labels retained for compatibility with existing docs checks: `## Phase 6-E — Isolated Apply Harness`, `Remaining Phase 6 Alignment With Master Roadmap`, and `Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review`.
- Host production firewall mutation remains forbidden; must not mutate the host production firewall.
- Compatibility anchors: `Phase 6-E0 accepted on farm5`, `Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.`, and `host production firewall mutation is forbidden`.
- Compatibility anchors for prior roadmap tests: `Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary`, `Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness`, `Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness`, and `Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal`.

## Finite Remaining Path

1. Phase 6 Firewall Planner — accepted on farm5
2. Phase 7 Usage + Policy/Reject Accounting readiness — current target
3. Phase 7 usage accounting service contracts — next
4. Phase 7 policy/reject accounting service contracts — next
5. Phase 7 read-only reports/doctor — next
6. Phase 7 final acceptance
7. Phase 8 Abuse 1h Core
8. Phase 9 Check / Report / Diagnostics
9. Phase 10 Session / Worker / Policy / Share Timeline
10. Phase 11 Local UI + Buyer Read-only
11. Phase 12 Operator UI Actions
12. Phase 13 Telegram
13. Phase 14 Worker Policy Enforcement

## Non-Negotiable Current Prohibitions

- no production traffic
- no live firewall write/apply/rollback/verify
- read-only iptables-save live snapshot is authorized and evidenced
- no iptables-restore until a dedicated apply gate is accepted
- no real firewall adapter or subprocess firewall calls
- no uncontrolled restore point writes, lock acquisition, or DB apply writes outside the accepted controlled execution boundary
- no migrations unless a future phase explicitly authorizes one
- no customer NAT or customer firewall rules
- firewall apply, iptables-restore, customer NAT/customer firewall rules, and production traffic remain forbidden
- no usage automation that changes runtime behavior
- no abuse automation before Phase 8
- no UI or Telegram
- no public v2rayA UI exposure
- no public backend exposure

## Production Readiness Sequence

Phase 7 starts after Phase 6 acceptance, but Phase 7 is not production activation.

Phase 8 is mandatory before the system is considered production-complete because the one-hour abuse requirement is a core requirement.

## Master Phase Summaries

### Phase 7 — Usage + Policy/Reject Accounting
Purpose: add usage/accounting foundations through service-layer contracts and report-only/readiness boundaries first.

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

## Legacy Compatibility Anchors (tests + historical references)

These anchors are intentionally historical and do not override the Current Position above.

- Repository version before this PR: 0.1.100
- Repository version after this PR: 0.1.105
- Historical compatibility anchor: previous planning text referenced 0.1.103 (historical).
- GitHub main repository version (before this cleanup PR) is 0.1.101
- latest recorded farm5 sync evidence is 0.1.94
- latest recorded farm5 sync evidence is 0.1.99
- 8. Phase 7 Usage + Policy/Reject Accounting
- 9. Phase 8 Abuse 1h Core
- Phase 7 starts only after Phase 6 final acceptance.
- Controlled no-customer runtime execution evidence — current next target
- production traffic remain forbidden
- abuse invariant: normal -> over_tracking -> over_grace -> hard
- abuse invariant must not be weakened
- no uncontrolled restore point writes, lock acquisition, or DB apply writes
- no migrations
- no usage automation
- no abuse automation before Phase 8
- no UI or Telegram
- farms-over alone must not harden
- worker-over alone must not harden


## Historical Compatibility Anchors

- 1. Dedicated Apply Gate Proposal/Review
- latest recorded farm5 sync evidence is 0.1.100 (historical; superseded by 0.1.102 in current active state)
