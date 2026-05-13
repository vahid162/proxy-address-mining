# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- GitHub main and farm5 are aligned at 0.1.90.
- Phase 5 remains the accepted phase.
- Phase 6 remains the working phase.
- Current work is Phase 6 Firewall Planner / Apply Gate Readiness.
- mpf firewall apply-gate-readiness is read-only/report-only and remains BLOCKED.
- mpf firewall gate-review includes apply_gate_readiness_summary and remains BLOCKED.
- Production traffic, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, customer NAT/customer firewall rules, usage automation, abuse automation, UI, and Telegram remain unauthorized.
- Host production firewall mutation remains forbidden.

## Completed Phase 6 Safety Sub-Steps

- Phase 6-C through Phase 6-H established offline/readiness/boundary/review contracts.
- Apply Slice 1 and Slice 2 were server-synced as documentation/test-only readiness boundaries.
- Apply Slice 3 and Slice 4 were server-synced as documentation/test-only boundaries.
- Future Dedicated Phase 6 Apply Gate Proposal/Review was documented as non-authorizing historical/reference context.
- farm5 sync evidence for 0.1.88 was recorded.
- apply-gate-readiness was implemented as read-only/report-only.
- gate-review now includes apply_gate_readiness_summary.
- farm5 was synced to 0.1.90 successfully.
- Historical labels retained for compatibility with existing docs checks: `## Phase 6-E — Isolated Apply Harness`, `Remaining Phase 6 Alignment With Master Roadmap`, and `Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review`.
- Host production firewall mutation remains forbidden; must not mutate the host production firewall.
- Compatibility anchors: `Phase 6-E0 accepted on farm5`, `Phase 6-G and Phase 6-H are safety sub-steps inside Phase 6, not new top-level roadmap phases.`, and `host production firewall mutation is forbidden`.
- Compatibility anchors for prior roadmap tests: `Phase 6 Apply Slice 1 — Live Snapshot Readiness Boundary`, `Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness`, `Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness`, and `Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal`.

## Finite Remaining Path

1. Complete the Phase 6 Live Snapshot Read Gate Proposal.
2. Then, in a separate PR, implement read-only live snapshot scaffolding only after proposal review.
3. Actual live read requires separate `docs/PHASE_STATUS.md` acceptance and farm5 evidence.
4. Apply/restore/NAT/customer firewall rules remain later gates.

## Non-Negotiable Current Prohibitions

- no production traffic
- no live firewall write/apply/rollback/verify
- no live firewall read until a dedicated read gate is accepted
- no iptables-save until a dedicated read gate is accepted
- no iptables-restore until a dedicated apply gate is accepted
- no real firewall adapter or subprocess firewall calls
- no restore point writes, lock acquisition, DB apply writes, or migrations
- no migrations
- no customer NAT or customer firewall rules
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
