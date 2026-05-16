# Phase 8 Final Acceptance Evidence

## Status

- Phase 8 Abuse 1h Core is accepted on farm5 by this PR.
- This is not production activation.
- This does not open firewall apply.
- This does not open production traffic.
- This does not start abuse automation.
- This does not start background worker/scheduler/timer.
- This does not authorize customer NAT/customer firewall rules.
- This does not authorize production DB execution.
- This does not authorize hard/soft block automation.
- This does not authorize pause automation.
- This does not authorize UI or Telegram.

## Evidence Chain

- 0.1.111 — abuse state-machine contract
- 0.1.112 — abuse evidence/reporting contract
- 0.1.113 — abuse dry-run evaluator
- 0.1.114 — DB-only controlled transition readiness
- 0.1.115 — DB-only controlled transition execution
- 0.1.116 — runtime/worker integration readiness
- 0.1.117 — runtime worker dry-run harness
- 0.1.118 — controlled worker pre-acceptance
- 0.1.119 — controlled worker dry-run gate preparation
- 0.1.120 — operator-invoked controlled worker dry-run package
- 0.1.121 — farm5 controlled worker dry-run evidence collection preparation
- 0.1.122 — final acceptance readiness/review and server sync/test evidence
- 0.1.123 — Phase 8 final acceptance

## Abuse 1h Core Acceptance Criteria

- normal -> over_tracking -> over_grace -> hard state path is preserved.
- sustained miner-abuse hardens only after about 3600 seconds.
- farms-over alone does not harden.
- worker-over alone does not harden.
- missing evidence does not harden.
- stale evidence does not harden.
- DB failure does not harden.
- firewall failure does not harden.
- explicit skip is required.
- no silent skip is allowed.
- all active customers in enabled lanes must be covered.
- dry-run evidence was synthetic/report-only and had no side effects.
- all dangerous authorization flags remained false.

## Accepted Boundary

Phase 8 acceptance means the Abuse 1h Core design, contracts, reports, evidence, dry-run path, and readiness chain are accepted on farm5.

Phase 8 acceptance does not mean live automation is enabled.

## Next Phase

Phase 9 — Check / Report / Diagnostics planning/readiness.

Phase 9 must start as report-only/readiness.
It must not enable production traffic, firewall apply, customer NAT/customer firewall rules, abuse automation, UI, Telegram, or production customer onboarding.
