# Phase 11D Farm5 Manual Canary Execution Runbook

## Prerequisites
- Sync latest `main` on farm5.
- Confirm version is `0.1.156`.
- Do **not** onboard real customers.

## Preflight
- `python -m pytest -q`
- `bash scripts/verify_current_phase_gate.sh`
- `mpf phase-status`
- `mpf doctor`
- `mpf db status`
- `mpf proxy doctor`

## Plan mode (default)
- `mpf production manual-canary-execute --output json > canary-plan.json`

## Execute mode (single explicit canary only)
```bash
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.156 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11D single canary execution on farm5" \
  --output json > canary-execute.json
```

## Evidence to collect
- `canary-plan.json`
- `canary-execute.json`
- `mpf doctor`, `mpf phase-status`, `mpf db status`, `mpf proxy doctor`
- listener/NAT/firewall status outputs required by reviewer.

## Failure / rollback
- Stop immediately on `BLOCKED` or `EXECUTION_FAILED`.
- Use restore/backup references in JSON output.
- Send failure evidence for review before any new attempt.

## Safety reminders
- Phase 11 remains unaccepted until evidence is reviewed and accepted.
- Limited real customer onboarding remains forbidden until canary evidence is accepted.


> Note: This command is a readiness contract and is expected to return BLOCKED when real production execution adapters are not wired yet.


## Phase 11E adapter wiring note
- Execute mode is now wired to production service-layer adapters.
- Actual execution remains BLOCKED until `missing_real_firewall_apply_adapter` is implemented through an accepted service-layer apply boundary.
- Do **not** run real customer onboarding.
