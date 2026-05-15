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
