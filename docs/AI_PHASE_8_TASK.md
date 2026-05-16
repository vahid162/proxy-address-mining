# AI Phase 8 Task — Abuse 1h Core Planning/Readiness

Phase 8 starts only after Phase 7 acceptance.

Phase 8 is Abuse 1h Core.

Phase 8 starts with planning/readiness only.

Phase 8 must implement the abuse invariant:
normal -> over_tracking -> over_grace -> hard

- farms-over alone must not harden.
- worker-over alone must not harden.
- sustained miner-abuse hardens after about 3600 seconds.
- all active customers in enabled lanes must be covered.
- no silent skip.

Phase 8 must eventually support evidence, audit, and rollback/restore references for hardening decisions.

Phase 8 must not enable production traffic by default.
Phase 8 must not enable firewall apply by default.
Phase 8 must not enable iptables-restore by default.
Phase 8 must not enable customer NAT/customer firewall rules in planning/readiness.
Phase 8 must not enable abuse automation in the first planning/readiness PR.
Phase 8 must not enable hard/soft blocks in the first planning/readiness PR.
Phase 8 must not enable pause automation in the first planning/readiness PR.
Phase 8 must not enable UI or Telegram.
Any future Phase 8 runtime/DB mutation must be behind explicit gates, tests, and fresh farm5 evidence.

## Future Phase 8 work split

1. Phase 8 planning/readiness package
2. Abuse state-machine contract
3. Abuse evidence/reporting contract
4. Abuse dry-run evaluator
5. DB-only controlled transition readiness
6. Runtime/worker integration readiness
7. Final Abuse 1h acceptance


## Current Phase 8 Step — Abuse State-Machine Contract

- This step is report-only/service-contract only.
- It defines the abuse state machine.
- It does not run the abuse runner.
- It does not write abuse_states.
- It does not write abuse_events.
- It does not apply hard/soft blocks.
- It does not apply pause automation.
- It does not mutate firewall rules.
- It does not apply iptables-restore.
- It does not enable customer NAT/customer firewall rules.
- It does not enable production traffic.
- It does not start runtime automation.
- The mandatory state path is normal -> over_tracking -> over_grace -> hard.
- farms-over alone must not harden.
- worker-over alone must not harden.
- sustained miner-abuse hardens after about 3600 seconds.
- all active customers in enabled lanes must be covered.
- no silent skip is allowed.
- runtime implementation remains future-gated and must come in later explicitly gated PRs.

Future path:
1. abuse state-machine contract
2. abuse evidence/reporting contract
3. abuse dry-run evaluator
4. DB-only controlled transition readiness
5. DB-only controlled transition execution
6. runtime/worker integration readiness
7. final Abuse 1h acceptance


## Current Phase 8 Step — Abuse Evidence/Reporting Contract

- report-only/service-contract only
- no live evidence collection
- no DB reads
- no DB writes
- no live conntrack/firewall reads
- no abuse runner
- no hard/soft blocks
- no pause automation
- no runtime automation
- defines future evidence/report DTOs and operator reporting contracts
- missing/stale evidence must be explicit and cannot harden

Future path:
1. abuse state-machine contract — done
2. abuse evidence/reporting contract — current
3. abuse dry-run evaluator
4. DB-only controlled transition readiness
5. DB-only controlled transition execution
6. runtime/worker integration readiness
7. final Abuse 1h acceptance

## Current Phase 8 Step — Abuse Dry-Run Evaluator
- offline dry-run only
- synthetic/in-memory evidence only
- no real customer evaluation
- no live evidence collection
- no DB reads
- no DB writes
- no live conntrack/firewall reads
- no abuse runner
- no hard/soft blocks
- no pause automation
- no runtime automation
- defines pure transition proposal logic
- transition_allowed=false
- hardening_allowed=false
- missing/stale evidence must block hardening
- farms-over alone must not harden
- worker-over alone must not harden
- future path:
  1. abuse state-machine contract — done
  2. abuse evidence/reporting contract — done
  3. abuse dry-run evaluator — current
  4. DB-only controlled transition readiness
  5. runtime/worker integration readiness
  6. final Abuse 1h acceptance


## Current Phase 8 Step — DB-Only Controlled Transition Execution

- report-only readiness only
- no DB connection
- no DB reads
- no DB writes
- no migrations
- no real customer evaluation
- no live evidence collection
- no live conntrack/firewall reads
- no abuse runner
- no hard/soft blocks
- no pause automation
- no runtime automation
- defines transition intent and DB mutation plan contracts
- defines operator approval, audit, restore-reference, and idempotency contracts
- writes_allowed=false
- execution_allowed=false
- missing/stale evidence must block DB transition planning
- farms-over alone must not harden
- worker-over alone must not harden
- future path:
  1. abuse state-machine contract — done
  2. abuse evidence/reporting contract — done
  3. abuse dry-run evaluator — done
  4. DB-only controlled transition readiness — current
  5. DB-only controlled transition execution — future, requires fresh farm5 evidence
  6. runtime/worker integration readiness
  7. final Abuse 1h acceptance


## Current Phase 8 Step — DB-Only Controlled Transition Execution

- controlled DB-only execution package
- default dry-run
- no runtime automation
- no abuse runner
- no firewall/customer changes
- no production traffic
- manual confirmation required
- idempotency required
- hard transition requires operator approval
- missing/stale evidence blocks execution
- manual unhard future-gated
- future path:
  1. abuse state-machine contract — done
  2. abuse evidence/reporting contract — done
  3. abuse dry-run evaluator — done
  4. DB-only controlled transition readiness — done and synced at 0.1.114
  5. DB-only controlled transition execution — current
  6. runtime/worker integration readiness — future
  7. final Abuse 1h acceptance — future


## Current Phase 8 Step — DB-Only Controlled Transition Readiness
- historical anchor retained for compatibility checks.

## Current Phase 8 Step — Runtime/Worker Integration Readiness

- readiness only
- no worker start
- no scheduler/timer
- no abuse runner
- no real customer evaluation
- no production DB execution
- no firewall/customer mutation
- no hard/soft blocks
- no pause automation
- worker loop contract
- scheduler boundary
- lock/idempotency boundary
- kill switch requirement
- no silent skip

future path:
1. abuse state-machine contract — done
2. abuse evidence/reporting contract — done
3. abuse dry-run evaluator — done
4. DB-only controlled transition readiness — done and synced at 0.1.114
5. DB-only controlled transition execution — done and synced at 0.1.115
6. runtime/worker integration readiness — current
7. runtime worker dry-run harness — future
8. final Abuse 1h acceptance — future


## Current Phase 8 Step — Runtime Worker Dry-Run Harness

- harness only
- synthetic/in-memory items only
- no worker start
- no scheduler/timer
- no abuse runner
- no real customer evaluation
- no production DB execution
- no firewall/customer mutation
- no hard/soft blocks
- no pause automation
- explicit skip reporting
- no-work reporting
- kill switch behavior
- lock/idempotency behavior
- batch limit behavior
- failure-mode behavior

future path:
1. abuse state-machine contract — done
2. abuse evidence/reporting contract — done
3. abuse dry-run evaluator — done
4. DB-only controlled transition readiness — done and synced at 0.1.114
5. DB-only controlled transition execution — done and synced at 0.1.115
6. runtime/worker integration readiness — done in 0.1.116, pending sync if this PR is batched
7. runtime worker dry-run harness — current
8. controlled worker pre-acceptance package — future
9. final Abuse 1h acceptance — future


## Current Phase 8 Step — Controlled Worker Pre-Acceptance

- pre-acceptance only
- no worker start
- no scheduler/timer
- no abuse runner
- no real customer evaluation
- no production DB execution
- no DB reads/writes for worker execution
- no firewall/customer mutation
- no hard/soft blocks
- no pause automation
- fresh farm5 sync required before controlled worker dry-run
- batch sync recommendation for 0.1.116/0.1.117/0.1.118 if report-only
- operator approval required before future controlled worker dry-run
- kill switch required
- lock required
- explicit skip required
- no silent skip required

Future path:
1. abuse state-machine contract — done
2. abuse evidence/reporting contract — done
3. abuse dry-run evaluator — done
4. DB-only controlled transition readiness — done and synced at 0.1.114
5. DB-only controlled transition execution — done and synced at 0.1.115
6. runtime/worker integration readiness — done in 0.1.116, pending batch sync
7. runtime worker dry-run harness — done in 0.1.117, pending batch sync
8. controlled worker pre-acceptance — current
9. farm5 batched sync/evidence package — next
10. controlled worker dry-run on farm5 — future
11. final Abuse 1h acceptance — future


## Current Phase 8 Step — Controlled Worker Dry-Run Gate Preparation

- gate-preparation only
- no worker start
- no scheduler/timer
- no abuse runner
- no real customer evaluation
- no production DB execution
- no DB writes for abuse runtime
- no firewall/customer mutation
- no hard/soft blocks
- no pause automation
- no production traffic
- farm5 0.1.118 batch sync evidence is recorded
- 0.1.119 sync/test evidence is required before any future controlled worker dry-run
- future controlled worker dry-run must be separately invoked by operator
- future controlled worker dry-run must remain limited, explicit, fail-closed, and non-production
- future controlled worker dry-run must report skip/no-work/lock/failure/idempotency outcomes explicitly
- no silent skip is allowed

Future path:
1. abuse state-machine contract — done
2. abuse evidence/reporting contract — done
3. abuse dry-run evaluator — done
4. DB-only controlled transition readiness — done and synced at 0.1.114
5. DB-only controlled transition execution — done and synced at 0.1.115
6. runtime/worker integration readiness — done in 0.1.116 and synced in 0.1.118 batch
7. runtime worker dry-run harness — done in 0.1.117 and synced in 0.1.118 batch
8. controlled worker pre-acceptance — done in 0.1.118 and synced on farm5
9. controlled worker dry-run gate preparation — current
10. controlled worker dry-run on farm5 — future, requires 0.1.119 sync/test evidence
11. final Abuse 1h acceptance — future
