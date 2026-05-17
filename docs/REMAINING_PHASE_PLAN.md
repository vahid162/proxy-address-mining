# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main repository version before this PR is 0.1.129.
- Repository version after this PR is 0.1.130.
- latest recorded farm5 sync evidence is 0.1.128.
- Phase 8 final Abuse 1h acceptance readiness/review is done in 0.1.122 and synced/tested on farm5.
- Phase 8 Abuse 1h Core is accepted on farm5 in 0.1.123.
- Phase 9 Check / Report / Diagnostics is accepted on farm5.
- Current target is Phase 10 planning/readiness.
- Phase 10 remains Session / Worker / Policy / Share Timeline planning/readiness and does not by itself open production traffic.
- This PR clarifies the backend-first remaining roadmap after Phase 10.
- Next required operator evidence is farm5 0.1.129 sync/test before Phase 10 implementation PRs.
- Do not fabricate server evidence.
- No production activation is enabled by this PR.
- No production traffic is enabled.
- No firewall apply is enabled.
- No abuse automation runner is enabled.
- No background worker/scheduler/timer is enabled.
- No worker policy enforcement is enabled.
- No real production customer evaluation is enabled.
- No production DB execution is enabled.
- No hard/soft firewall block automation is enabled.
- No pause automation is enabled.
- No customer NAT/customer firewall rules, UI, or Telegram is authorized.

## Finite Remaining Path

1. Phase 6 Firewall Planner — accepted on farm5
2. Phase 7 Usage + Policy/Reject Accounting — accepted on farm5 as report-only/service-contract/readiness
3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123
4. Phase 9 Check / Report / Diagnostics planning/readiness — accepted
5. Phase 10 report-only planning/readiness foundation — repository version 0.1.129, pending fresh farm5 0.1.129 sync/test evidence
6. farm5 0.1.129 sync/test evidence before Phase 10 implementation PRs — next required operator evidence
7. Phase 10 Session / Worker / Policy / Share Timeline — active backend-readiness work
8. Phase 11 Production / Customer Activation Gate — future, explicit, controlled CLI canary first, then limited real customer onboarding
9. Phase 12 Worker Policy Enforcement — future, after Phase 10 worker/session evidence and Phase 11 production activation
10. Phase 13 Local UI — future service-layer interface after backend path is accepted
11. Phase 14 Operator UI Actions — future service-layer interface with confirmation and audit
12. Phase 15 Telegram — future notification/read-only/restricted-action interface, last in the roadmap

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
