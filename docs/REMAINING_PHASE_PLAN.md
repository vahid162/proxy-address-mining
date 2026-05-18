# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main repository version before this PR is 0.1.135.
- Repository version after this PR is 0.1.136.
- latest recorded farm5 sync evidence is 0.1.135.
- Phase 10A/10B/10C backend readiness implementation is done.
- Phase 10D/10E readiness is done.
- Phase 10F runtime worker/scheduler dry-run readiness is done.
- Phase 10 final-acceptance-readiness is introduced.
- Current target is Phase 10 planning/readiness.
- Next target is Phase 10 final acceptance after farm5 0.1.136 sync/test evidence.
- Controlled CLI canary remains Phase 11 after Phase 10 final acceptance.
- No production activation is enabled by this PR.

## Finite Remaining Path

1. Phase 6 Firewall Planner — accepted on farm5
2. Phase 7 Usage + Policy/Reject Accounting — accepted on farm5 as report-only/service-contract/readiness
3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123
4. Phase 9 Check / Report / Diagnostics planning/readiness — accepted
5. Phase 10 report-only planning/readiness foundation — accepted on farm5 evidence chain through 0.1.135
6. Phase 10A/10B/10C Session / Worker Identity / Worker Policy readiness — implemented as backend-readiness and non-authorizing
7. Phase 10D/10E Share Timeline / Collector dry-run readiness — implemented as backend-readiness and non-authorizing
8. Phase 10F Runtime Worker / Scheduler dry-run readiness — introduced in this PR as backend-readiness and non-authorizing
9. Phase 10 final-acceptance-readiness — introduced in this PR as non-authorizing explicit gate
10. Phase 10 final acceptance — future explicit gate, not production activation
11. Phase 11 Production / Customer Activation Gate — future, explicit, controlled CLI canary first, then limited real customer onboarding
12. Phase 12 Worker Policy Enforcement — future, after Phase 10 worker/session evidence and Phase 11 production activation
13. Phase 13 Local UI — future service-layer interface after backend path is accepted
14. Phase 14 Operator UI Actions — future service-layer interface with confirmation and audit
15. Phase 15 Telegram — future notification/read-only/restricted-action interface, last in the roadmap

## Backend-First Principle

The server must become operational through the standard `mpf` CLI and service layer before Telegram or Web UI becomes the operator surface.

The uploaded legacy tgz/scripts are capability references only. They may be used to map command parity and operational expectations, but they must not be copied as the new runtime backend and must not bypass PostgreSQL, service-layer validation, event/audit logging, firewall planning, restore points, or phase gates.

Required post-Phase 10 operational sequence:

```text
Phase 10 accepted
  -> Phase 11 Production / Customer Activation Gate
  -> controlled CLI canary customer
  -> limited real customer onboarding
  -> Phase 12 Worker Policy Enforcement after evidence/adapter support
  -> Phase 13 Local UI
  -> Phase 14 Operator UI Actions
  -> Phase 15 Telegram
```

Production activation is complete only after farm5 evidence proves:

```text
fresh sync/test evidence
restart/container-order safety
controlled firewall apply/verify/rollback path
customer NAT/customer firewall rules through planner only
usage and reject accounting visibility
abuse 1h runtime coverage for all active customers in enabled lanes
manual canary customer success
rollback or restore-plan evidence
```

## Historical Phase 8 Evidence Chain

- 0.1.111 through 0.1.123 evidence chain retained; see docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md.

## Historical/Compatibility Notes

These entries are historical compatibility anchors for older docs/tests/services. They are not current authorization gates and must not be read as active implementation targets.

- read-only iptables-save live snapshot path is explicitly authorized and evidenced.
- must not mutate the host production firewall until an explicit gate opens controlled apply.
- host production firewall mutation is forbidden in the current gate.
- abuse invariant: normal -> over_tracking -> over_grace -> hard.
- abuse invariant must not be weakened.
- farms-over alone must not harden.
- worker-over alone must not harden.
- Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.
- Phase 6 apply-slice materials are historical/reference-only unless a current gate explicitly reopens them.
- Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary
- Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness
- Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness
- Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal
- Phase 7 starts only after Phase 6 final acceptance.
- iptables-restore remains forbidden in the current boundary context.

## Historical Compatibility Anchors

The following strings intentionally preserve prior accepted evidence references and service blocker checks:

```text
Remaining Phase 6 Alignment With Master Roadmap
## Phase 6-E — Isolated Apply Harness
Phase 6-E0 accepted on farm5
Host production firewall mutation remains forbidden
Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review
1. Dedicated Apply Gate Proposal/Review
8. Phase 7 Usage + Policy/Reject Accounting
9. Phase 8 Abuse 1h Core
No-customer runtime execution approval readiness
executed once on farm5 under the accepted controlled boundary
no uncontrolled restore point writes, lock acquisition, or DB apply writes
production traffic remain forbidden
no usage automation
no abuse automation before Phase 8
no UI or Telegram
latest recorded farm5 sync evidence is 0.1.94
latest recorded farm5 sync evidence is 0.1.99
latest recorded farm5 sync evidence is 0.1.100
latest recorded farm5 sync evidence is 0.1.110.
Current target is Phase 8 abuse dry-run evaluator package.
Current target is Phase 8 abuse evidence/reporting contract package.
remaining_plan_state_machine_target_aligned compatibility anchor: Current target is Phase 8 abuse state-machine contract package.
remaining_plan_evidence_reporting_target_aligned compatibility anchor: Current target is Phase 8 abuse evidence/reporting contract package.
Current target is Phase 8 DB-only controlled transition readiness package.
Current target is Phase 8 DB-only controlled transition execution package.
Current target is Phase 8 runtime/worker integration readiness package.
Phase 8 runtime worker dry-run harness — next target
Controlled no-customer runtime execution evidence — current next target.
GitHub main repository version before this PR is 0.1.128. (historical)
Repository version after this PR is 0.1.129. (historical)
0.1.99
```

Current roadmap ordering remains the Finite Remaining Path above. These anchors do not reopen Phase 6, Phase 7, Phase 8, firewall apply, production traffic, abuse automation, worker enforcement, UI, or Telegram.
