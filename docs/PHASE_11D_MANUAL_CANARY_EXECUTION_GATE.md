# Phase 11D Manual Canary Execution Gate

Status: planned/packaged, non-authorizing.

This package adds `mpf production canary-execution-gate --output json` to evaluate whether a *future* manual canary execution run may be considered.

This PR does **not** authorize execution, does **not** run canary traffic, and does **not** mutate DB/firewall/NAT/runtime.
Phase 11 remains not accepted.

## Command

- `mpf production canary-execution-gate --output json`

## Required preconditions

- farm5 sync evidence remains at 0.1.147 and must be refreshed after merge.
- farm5 must sync latest GitHub main before any later execution.
- exactly one explicit canary only in later run.
- backup/restore/rollback references must be reviewed.
- abuse 1h coverage checks must remain required.

## Future execution checklist

- run: `mpf --version`, `mpf phase-status`, `mpf config validate`, `mpf doctor`, `mpf db status`, `mpf proxy doctor`
- run: readiness/canary-plan/activation-harness/canary-acceptance/canary-execution-gate reports
- verify no customer NAT/rules baseline and local-only listeners baseline
- prepare restore point + backup + rollback plan before any future apply

## Forbidden actions in this PR

- no manual canary execution
- no production traffic
- no firewall apply or `iptables-restore`
- no customer DB mutation
- no customer NAT/customer firewall rules
- no abuse automation/UI/Telegram
