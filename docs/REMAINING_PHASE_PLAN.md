# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Current Position

- Current accepted phase is Phase 10.
- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness.
- Repository version after this PR is 0.1.204.
- 0.1.204 adds a controlled single-customer firewall apply execution path/package (dry-run default).
- Actual server execution still requires farm5 sync/test plus explicit operator execution evidence.
- Production/miner traffic remains blocked until post-apply runtime evidence and later acceptance PR.
- farm5 0.1.200 single-customer DB-only staging evidence is recorded.
- farm5 0.1.201 sync exposed a test isolation issue after real DB-only staging created limited-btc-001.
- farm5 0.1.202 sync/test and firewall plan gate evidence are recorded.
- next intended server step after 0.1.204 sync is rerunning full pytest, then running `mpf production single-customer-firewall-apply-gate` only if tests pass.
- real customer traffic remains blocked until a separate firewall/NAT apply execution PR is merged, synced, tested, and explicitly updates Current State.
- production traffic remains none.
- firewall apply remains no.
- customer onboarding remains db_only.
- abuse automation remains no.
- UI remains no.
- Telegram remains no.

### Historical anchors (non-current)

- 0.1.199 flow pointed to `mpf production limited-onboarding-execution-gate` before this PR.
- customer onboarding remains db_only except future explicit canary run path.
- firewall apply remains no except future explicit single-canary operator-approved run path.
- latest recorded route-safe canary NAT success evidence remains 0.1.164; farm5 0.1.168 sync confirms the controlled canary NAT artifact is still present.
- latest recorded farm5 sync evidence is 0.1.167 (synthetic Stratum canary success evidence recorded).
- GitHub main repository version before this PR is 0.1.168.
- Repository version after this PR is 0.1.197. (historical compatibility anchor)
- Phase 11D manual canary execution gate package is implemented and farm5 evidence is recorded.
- Phase 11D actual execution remains not accepted.
- Phase 11 remains not accepted.

## Finite Remaining Path

1. Phase 6 Firewall Planner — accepted on farm5
2. Phase 7 Usage + Policy/Reject Accounting — accepted on farm5 as report-only/service-contract/readiness
3. Phase 8 Abuse 1h Core — accepted on farm5 in 0.1.123
4. Phase 9 Check / Report / Diagnostics planning/readiness — accepted
5. Phase 10 report-only planning/readiness foundation — accepted on farm5 evidence chain through 0.1.135
6. Phase 10A/10B/10C Session / Worker Identity / Worker Policy readiness — implemented as backend-readiness and non-authorizing
7. Phase 10D/10E Share Timeline / Collector dry-run readiness — implemented as backend-readiness and non-authorizing
8. Phase 10F Runtime Worker / Scheduler dry-run readiness — implemented as backend-readiness and non-authorizing
9. Phase 10 final-acceptance-readiness — implemented as non-authorizing explicit gate
10. Phase 10 final acceptance — accepted, not production activation
11. Phase 11 Production / Customer Activation Gate — current planning/readiness target; explicit controlled CLI canary first, then limited real customer onboarding after evidence
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
latest recorded farm5 sync evidence is 0.1.153.
latest recorded farm5 sync evidence is 0.1.159.
GitHub main repository version before this PR is 0.1.157.
GitHub main repository version before this PR is 0.1.159.
GitHub main repository version before this PR is 0.1.163. (historical route-safe fix PR)
Current blocker before this PR: single_canary_restore_payload_renderer_missing.
Current blocker before this PR: loopback canary DNAT target not route-safe for external PREROUTING traffic. (historical)
single_canary_host_apply_context_not_confirmed
accepted_single_canary_host_apply_execution_missing
Current target is Phase 8 abuse dry-run evaluator package.
Current target is Phase 8 abuse evidence/reporting contract package.
remaining_plan_state_machine_target_aligned compatibility anchor: Current target is Phase 8 abuse state-machine contract package.
remaining_plan_evidence_reporting_target_aligned compatibility anchor: Current target is Phase 8 abuse evidence/reporting contract package.
Current target is Phase 8 DB-only controlled transition readiness package.
Current target is Phase 8 DB-only controlled transition execution package.
Current target is Phase 8 runtime/worker integration readiness package.
Phase 8 runtime worker dry-run harness — next target
Controlled no-customer runtime execution evidence — current next target.
Next target: sync latest main to farm5, run explicit operator-approved single-canary execution once, and collect evidence; if execution blocks, implement the exact missing primitive reported as `accepted_single_canary_host_apply_primitive`.
GitHub main repository version before this PR is 0.1.128. (historical)
Repository version after this PR is 0.1.129. (historical)
0.1.99
```

Current roadmap ordering remains the Finite Remaining Path above. These anchors do not reopen Phase 6, Phase 7, Phase 8, firewall apply, production traffic, abuse automation, worker enforcement, UI, or Telegram.
- Repository version after this PR is 0.1.197.
- After usage evidence capture/validation, next target is `reject_counters_visibility`.

- After 0.1.197 merge/sync, next intended server step is running `mpf production canary-acceptance-decision` on farm5 against `/tmp/phase11-canary-evidence-pack-0.1.195-live` and recording result evidence.
- Phase 11E limited onboarding remains blocked until this Phase 11D canary acceptance decision is executed and recorded on farm5.




0.1.202 planning/readiness: farm5 0.1.201 sync exposed a Phase 11 single-customer staging test isolation issue after real DB-only staging created limited-btc-001; test isolation fix + docs/version-only update, no runtime gate changes.
0.1.201 planning/readiness: recorded farm5 0.1.199 limited-onboarding-execution-gate evidence and added controlled single-customer DB-only staging package.


- docs/PHASE_11E_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTION.md
