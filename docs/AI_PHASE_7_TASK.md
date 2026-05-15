# AI Phase 7 Task — Usage + Policy/Reject Accounting

Status: planning/readiness only; report-only and non-authorizing. `docs/PHASE_STATUS.md` remains authoritative.

- Current repository before this PR: 0.1.102
- Repository after this PR: 0.1.103
- Latest recorded farm5 sync evidence: 0.1.102
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
