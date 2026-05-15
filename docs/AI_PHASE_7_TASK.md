# AI Phase 7 Task — Usage + Policy/Reject Accounting

Status: planning/readiness only; report-only and non-authorizing. `docs/PHASE_STATUS.md` remains authoritative.

- Current repository before this PR: 0.1.105
- Repository after this PR: 0.1.106
- Latest recorded farm5 sync evidence: 0.1.104
- Phase 7 starts only after Phase 6 is accepted.
- Phase 7 begins with read-only/reporting/service-contract work.

## Mandatory Runtime Prohibitions (Phase 7)

- Phase 7 must not enable production traffic.
- Phase 7 must not enable firewall apply.
- Phase 7 must not enable iptables-restore.
- Phase 7 must not enable customer NAT/customer firewall rules.
- Phase 7 must not enable usage automation.
- Phase 7 must not enable usage collectors.
- Phase 7 must not enable policy/reject collectors.
- Phase 7 must not enable abuse automation.
- Phase 7 must not implement hard/soft blocks.
- Phase 7 must not enable pause automation.

Phase 8 remains the future abuse 1h core phase.

## Phase 7 Planned Work Split

1. readiness package
2. usage accounting service contracts
3. policy/reject accounting service contracts
4. read-only reports/doctor
5. Phase 7 acceptance

## Abuse Invariant (Mandatory, Unchanged)

- normal -> over_tracking -> over_grace -> hard
- farms-over alone must not harden
- worker-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- all active customers in enabled lanes must be covered
- no silent skip


## Current Phase 7 Step — Usage Accounting Contract

- This step is report-only/service-contract only.
- It defines usage sample, delta, windows, and doctor contracts.
- It does not enable collectors.
- It does not enable timers.
- It does not read live firewall counters.
- It does not write usage_samples.
- It does not write policy_events.
- It does not enable production traffic.
- It does not enable abuse automation.
- Phase 8 remains future-only.


## Current Phase 7 Step — Policy/Reject Accounting Contract

- This step is report-only/service-contract only.
- It defines policy/reject event semantics.
- It defines connlimit/hashlimit/pause/block reject categories.
- It defines explainability rules for rejects.
- It does not enable collectors.
- It does not read live firewall counters.
- It does not write policy_events.
- It does not write usage_samples.
- It does not enable firewall apply.
- It does not enable customer NAT/customer firewall rules.
- It does not enable abuse automation.
- Phase 8 remains future-only.
