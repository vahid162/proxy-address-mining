# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main repository version before this PR is 0.1.119.
- Repository version after this PR is 0.1.120.
- latest recorded farm5 sync evidence is 0.1.119.
- Phase 8 runtime/worker integration readiness package is done in 0.1.116 and synced on farm5 in the 0.1.118 batch.
- Phase 8 runtime worker dry-run harness package is done in 0.1.117 and synced on farm5 in the 0.1.118 batch.
- Phase 8 controlled worker pre-acceptance package is done in 0.1.118 and synced on farm5.
- Current target is Phase 8 operator-invoked controlled worker dry-run package.
- Next target after this PR is Phase 8 controlled worker dry-run on farm5, but only after this PR is merged and 0.1.120 is synced/tested on farm5.
- Do not fabricate server evidence.
- No Phase 8 runtime automation is enabled by this PR.
- No abuse runner is enabled.
- No worker/scheduler/timer is enabled.
- No real customer evaluation is enabled.
- No production DB execution is enabled.
- No hard/soft firewall block is enabled.
- No pause automation is enabled.
- No production traffic, firewall apply, iptables-restore, customer NAT/customer firewall rules, UI, or Telegram is authorized.

## Finite Remaining Path

1. Phase 6 Firewall Planner — accepted on farm5
2. Phase 7 Usage + Policy/Reject Accounting — accepted on farm5 as report-only/service-contract/readiness
3. Phase 8 Abuse 1h Core planning/readiness — current
4. Phase 8 abuse state-machine contract — done in 0.1.111
5. Phase 8 abuse evidence/reporting contract — done in 0.1.112
6. Phase 8 abuse dry-run evaluator — done in 0.1.113
7. Phase 8 DB-only controlled transition readiness — done and synced on farm5 in 0.1.114
8. Phase 8 DB-only controlled transition execution — done and synced on farm5 in 0.1.115
9. Phase 8 runtime/worker integration readiness — done in 0.1.116 and synced in the 0.1.118 farm5 batch
10. Phase 8 runtime worker dry-run harness — done in 0.1.117 and synced in the 0.1.118 farm5 batch
11. Phase 8 controlled worker pre-acceptance — done in 0.1.118 and synced on farm5
12. Phase 8 controlled worker dry-run gate preparation — done in 0.1.119 and synced/tested on farm5
13. Phase 8 operator-invoked controlled worker dry-run package — current target in 0.1.120
14. Phase 8 farm5 controlled worker dry-run evidence collection — next after 0.1.120 sync/test
15. Phase 8 final Abuse 1h acceptance — future


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
