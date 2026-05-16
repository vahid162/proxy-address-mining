# Phase 8 Final Acceptance Readiness Review

## Status
- Readiness review only.
- Phase 8 is not accepted by this document.
- No runtime gate is opened.
- No production traffic is enabled.
- No firewall/customer/DB mutation is authorized.

## Evidence Covered
- abuse state-machine contract (0.1.111)
- abuse evidence/reporting contract (0.1.112)
- abuse dry-run evaluator (0.1.113)
- DB-only controlled transition readiness (0.1.114)
- DB-only controlled transition execution (0.1.115)
- runtime/worker integration readiness (0.1.116)
- runtime worker dry-run harness (0.1.117)
- controlled worker pre-acceptance (0.1.118)
- controlled worker dry-run gate preparation (0.1.119)
- operator-invoked controlled worker dry-run package (0.1.120)
- farm5 dry-run evidence collection preparation (0.1.121)
- farm5 0.1.121 sync evidence
- farm5 controlled worker dry-run evidence

## Abuse 1h Invariant
normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone does not harden
- worker-over alone does not harden
- missing evidence does not harden
- stale evidence does not harden
- DB failure does not harden
- firewall failure does not harden
- all active customers in enabled lanes must be covered
- explicit skip is required
- no silent skip is allowed

## Non-Authorization
Does not authorize: background worker, scheduler, timer, abuse runner, real customer evaluation, production DB execution, DB writes, firewall apply, iptables-restore, customer NAT/rules, customer policy mutation, hard/soft block, pause automation, UI, Telegram, production traffic.

## Next Step
Next step is a separate Phase 8 final acceptance PR after this PR is merged and 0.1.122 is synced/tested on farm5.
