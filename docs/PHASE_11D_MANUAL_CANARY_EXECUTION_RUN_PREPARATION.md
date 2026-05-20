# Phase 11D Operator-reviewed Manual Canary Execution Run Preparation

Status: preparation package, non-authorizing.

This package adds `mpf production canary-execution-run-prep --output json`.
This PR prepares the operator-reviewed execution run only and does **not** execute canary traffic.
This PR does **not** authorize Phase 11D actual execution. Phase 11 remains not accepted.

## Command

- `mpf production canary-execution-run-prep --output json`

## Required Preconditions

- farm5 0.1.149 sync/test evidence is recorded.
- Phase 11D acceptance package evidence is recorded.
- Phase 11D execution gate evidence is recorded.
- farm5 must sync latest main before any future execution.
- future execution must stay one explicit canary.

## Future Operator-reviewed Run Plan

- run the full preflight command chain (version/phase/config/doctor/db/proxy/readiness/canary services/phase gate script).
- review customer DB mutation plan before any future DB write.
- review firewall desired model and human/JSON diff before any future apply.
- create restore point, iptables-save backup, and lock before any future apply.
- verify NAT/usage/reject/session/worker visibility and abuse 1h coverage during the later execution run.

## Evidence Requirements

- before/after snapshots.
- customer row evidence.
- firewall plan and diff evidence.
- restore point and iptables-save backup references.
- lock and verification output.
- canary miner connection and NAT hit proof.
- usage/reject/session/worker visibility proof.
- abuse 1h coverage proof.
- rollback/restore readiness proof.
- final operator verdict.

## Rollback/Restore Requirements

- rollback/restore command references must be prepared before any future dangerous action.
- this package itself is non-mutating and creates no live restore action.

## Abuse 1h Coverage Requirement

- abuse 1h coverage remains required and must include the canary customer in the later execution run.

## Explicit Non-Authorization

- This PR does **not** authorize actual execution.
- Actual execution requires a later farm5 run with explicit operator approval.
- Limited real customer onboarding remains forbidden until canary execution evidence is accepted.
- Phase 11 final acceptance remains later.
