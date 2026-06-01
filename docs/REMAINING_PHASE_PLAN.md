

## Current Phase 11E Limited Activation Position (0.1.226 target)

- Farm5 `0.1.225` produced READY decision, execution, and rollback packages with `expected_version=repository_version=0.1.225`.
- `limited-btc-001` remains paused before execution.
- `canary-btc-001` remains active and must be preserved.
- The `0.1.226` target is the gated limited activation execute path, rollback execute path, and post-evidence collector.
- After merge, sync, and tests, the next step is an operator-reviewed controlled activation run followed immediately by post-activation evidence collection.

Any older current-position wording about `0.1.216` or runtime/Stratum evidence collection is historical only; the reviewed limited activation readiness packages are already READY.
# Remaining Phase Plan

Status: planning reference aligned to docs/PHASE_STATUS.md.

Current Position update: farm5 0.1.224 sync/test passed, but the decision package helper failed due to duplicate `config` kwargs. 0.1.225 fixes the CLI wrappers only; after sync, rerun `scripts/phase11e_prepare_limited_activation_decision_package.sh`.

Current Position update: 0.1.224 keeps Phase 11 in planning/readiness, maps `controlled_order_test_performed` into restart/container-order evidence (`post_restart_or_controlled_order_test_performed`), and restores helper `manifest.json` generation.

Current Position update: 0.1.222 farm5 result is source evidence READY and abuse readiness READY, while restart/container-order readiness remained BLOCKED due to missing controlled-order mapping into `post_restart_or_controlled_order_test_performed`.

Current Position update: after 0.1.224 sync/test, rerun the Phase11E helper and inspect restart/container-order readiness plus limited acceptance precheck outputs.

Current Position update (0.1.220): repository version is 0.1.220; 0.1.219 helper fail-closed BLOCKED for missing abuse/restart evidence; 0.1.220 adds source-backed evidence builders; activation still requires explicit later decision PR.


Current Position update (0.1.219): repository version is 0.1.219; runtime path READY; stratum transcript READY; visibility bundle READY at 0.1.218; abuse 1h and restart/container-order readiness still required; limited acceptance decision still required; production/miner traffic remains blocked.
docs/PHASE_STATUS.md remains the authoritative gate. This plan does not open any runtime gate by itself.

## Phase 11E 0.1.229 Target Position

- GitHub `main` before this PR is `0.1.228`.
- The `0.1.229` target is read-only limited activation observation plus limited acceptance review.
- Reported `limited-btc-001` activation and source-backed post-evidence claims must be validated from actual farm5 JSON artifacts and SHA-256 hashes supplied to the helper or CLI.
- Phase 11 final acceptance remains separate. Production expansion remains separate. Abuse automation enable remains separate. UI and Telegram remain later phases.
- This target does not convert historical notes into active authorization and does not open the Current State gates.

## Historical Current Position Notes

The notes below are retained as historical planning context only. The active target is the `Phase 11E 0.1.229 Target Position` section above, and `docs/PHASE_STATUS.md` remains authoritative.

- Current accepted phase is Phase 10.
- Current working phase is Phase 11 Production / Customer Activation Gate planning/readiness.
- Repository version after this PR is 0.1.216.
- post-apply evidence READY is recorded from farm5 0.1.205.
- 20101 controlled NAT/filter primitive artifact exists and is pending runtime-path/Stratum/visibility evidence.
- Runtime-path evidence attempt for 20101 is recorded as BLOCKED due missing ASSURED conntrack signal.
- Forwarder and bridge signals are present/partial.
- after 0.1.216 sync and full pytest, next intended farm5 step is long-lived external Stratum + runtime evidence collection/classification for 20101.
- Next intended farm5 step after sync/test is controlled runtime probe diagnostics and stronger runtime/Stratum evidence collection.
- then Stratum transcript evidence and visibility bundle.
- real customer traffic remains blocked until runtime path evidence, Stratum transcript, visibility bundle, abuse 1h coverage, restart/container-order evidence, and a later explicit acceptance PR.
- production traffic remains none.
- firewall apply remains no.
- customer onboarding remains db_only.
- abuse automation remains no.
- UI remains no.
- Telegram remains no.
- Production/miner traffic remains blocked.
- DB activation remains blocked.
- Abuse 1h and restart/container-order evidence remain required before limited production acceptance.

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


- Phase 11E 0.1.216: use `mpf production current-controlled-artifact-gate` and `scripts/phase11e_collect_runtime_stratum_evidence.sh` for fail-closed evidence collection only (no activation).
Current Position update: 0.1.221 materializes source-backed evidence bundle + artifact gate + abuse/restart readiness chain. If precheck READY, next step is explicit limited activation decision PR. If BLOCKED, next step resolves exact source blockers. Production/miner traffic still blocked.