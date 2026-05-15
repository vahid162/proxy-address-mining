# AI Phase 7 Task — Usage + Policy/Reject Accounting (Planning/Readiness Only)

Status: planning-only/readiness-only guidance. `docs/PHASE_STATUS.md` remains authoritative.

- Phase 7 is Usage + Policy/Reject Accounting.
- Phase 7 starts only after Phase 6 is accepted.
- Phase 7 begins with read-only/reporting/service-contract work.
- Phase 7 must not enable production traffic.
- Phase 7 must not enable firewall apply.
- Phase 7 must not enable iptables-restore.
- Phase 7 must not enable customer NAT/customer firewall rules.
- Phase 7 must not enable abuse automation.
- Phase 7 must not implement hard/soft blocks.
- Phase 8 remains the abuse 1h core phase.

Abuse invariant remains mandatory:

- normal -> over_tracking -> over_grace -> hard
- farms-over alone must not harden
- worker-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- all active customers in enabled lanes must be covered
- no silent skip
