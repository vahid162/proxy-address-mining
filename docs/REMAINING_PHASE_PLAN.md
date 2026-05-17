# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main repository version before this PR is 0.1.125.
- Repository version after this PR is 0.1.126.
- latest recorded farm5 sync evidence is 0.1.124.
- Phase 8 final Abuse 1h acceptance readiness/review is done in 0.1.122 and synced/tested on farm5.
- Phase 8 Abuse 1h Core is accepted on farm5 in 0.1.123.
- Current target is Phase 9 Check / Report / Diagnostics planning/readiness.
- This PR introduces the Phase 9 diagnostics bundle report-only package.
- Next target after this PR is farm5 0.1.126 sync/test evidence, then Phase 9 final acceptance readiness.
- Do not fabricate server evidence.
- No production activation is enabled by this PR.
- No production traffic is enabled.
- No firewall apply is enabled.
- No abuse automation runner is enabled.
- No background worker/scheduler/timer is enabled.
- No real production customer evaluation is enabled.
- No production DB execution is enabled.
- No hard/soft firewall block automation is enabled.
- No pause automation is enabled.
- No customer NAT/customer firewall rules, UI, or Telegram is authorized.

## Finite Remaining Path

1. Phase 6 Firewall Planner — accepted on farm5
2. Phase 7 Usage + Policy/Reject Accounting — accepted on farm5 as report-only/service-contract/readiness
3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123
4. Phase 9 Check / Report / Diagnostics planning/readiness — current target
5. Phase 9 diagnostics bundle report-only package — current PR
6. farm5 0.1.126 sync/test evidence, then Phase 9 final acceptance readiness — next target
7. Phase 10 Session / Worker / Policy / Share Timeline — future
8. Phase 11 Local UI + Buyer Read-only — future
9. Phase 12 Operator UI Actions — future
10. Phase 13 Telegram — future
11. Phase 14 Worker Policy Enforcement — future
12. Production / Customer Activation Gate — future, separate, explicit, and not authorized by Phase 8 or Phase 9 readiness acceptance

## Historical Phase 8 Evidence Chain
- 0.1.111 through 0.1.123 evidence chain retained; see docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md.

## Historical/Compatibility Notes

- finite remaining project/Phase 8 plan aligned to PHASE_STATUS.
- read-only iptables-save live snapshot path is explicitly authorized and evidenced.
- must not mutate the host production firewall.
- host production firewall mutation is forbidden.
- abuse invariant: normal -> over_tracking -> over_grace -> hard.
- abuse invariant must not be weakened.
- farms-over alone must not harden.
- worker-over alone must not harden.
- Remaining Phase 6 Alignment With Master Roadmap.
- ## Phase 6-E — Isolated Apply Harness.
- Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review.
- No-customer runtime execution approval readiness.
- executed once on farm5 under the accepted controlled boundary.
- latest recorded farm5 sync evidence is 0.1.94.
- latest recorded farm5 sync evidence is 0.1.99.
- latest recorded farm5 sync evidence is 0.1.100.
- GitHub main repository version before this PR is 0.1.111.
- Current target is Phase 8 abuse evidence/reporting contract package. (historical)
- remaining_plan_state_machine_target_aligned compatibility anchor: Current target is Phase 8 abuse state-machine contract package.
- remaining_plan_evidence_reporting_target_aligned compatibility anchor: Current target is Phase 8 abuse evidence/reporting contract package.

- 1. Dedicated Apply Gate Proposal/Review.
- Phase 6-E0 accepted on farm5.
- Controlled no-customer runtime execution evidence — current next target.
- Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.
- no uncontrolled restore point writes, lock acquisition, or DB apply writes.
- Repository version after this PR is 0.1.112. (historical)
- 8. Phase 7 Usage + Policy/Reject Accounting.
- Host production firewall mutation remains forbidden.
- Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary.
- Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness.
- Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness.
- Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal.
- customer NAT/customer firewall rules.
- production traffic remain forbidden.
- no usage automation.
- no abuse automation before Phase 8.
- no UI or Telegram.
- Next target after this PR is Phase 8 abuse dry-run evaluator package. (historical)
- 9. Phase 8 Abuse 1h Core.
- Phase 7 starts only after Phase 6 final acceptance.
- offline sync may be batched with PR #119 and the next Phase 8 dry-run evaluator PR. (historical)
- No server sync evidence for 0.1.111 or 0.1.112 exists until operator syncs after merge. (historical)
- No Phase 8 runtime automation is enabled by this PR. (historical)

- latest recorded farm5 sync evidence is 0.1.110. (historical compatibility anchor)

- Current target is Phase 8 DB-only controlled transition readiness package. (historical compatibility anchor)

- Current target is Phase 8 DB-only controlled transition execution package. (historical compatibility anchor)


- Current target is Phase 8 runtime/worker integration readiness package. (historical compatibility anchor)

- Phase 8 runtime worker dry-run harness — next target (historical compatibility anchor).

- iptables-restore remains forbidden in this boundary context.
