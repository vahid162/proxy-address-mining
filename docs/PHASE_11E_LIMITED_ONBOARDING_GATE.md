# Phase 11E Limited Onboarding Gate (Design/Readiness Only)

## Purpose
Evaluate readiness to start Phase 11E limited onboarding gate planning only. This is non-mutating and non-authorizing.

## Prerequisite
Phase 11D controlled canary acceptance decision evidence must exist and be accepted.

Input evidence path example:
`/tmp/phase11-canary-acceptance-decision-0.1.197.json`

## Safety boundary
- no real customer onboarding yet
- no production traffic yet
- no firewall/NAT/DB mutation
- no abuse automation
- no UI
- no Telegram
- no scheduler
- no worker enforcement

## Positive decision semantics
`PHASE11E_LIMITED_ONBOARDING_GATE_READY` means only that the next PR may design an explicit execution gate.

## Blocked decision semantics
If any scope/safety/evidence/operator confirmation check fails, decision stays `BLOCKED` and execution remains disallowed.

## Command example
```bash
mpf production limited-onboarding-gate \
  --expected-version 0.1.198 \
  --farm5-baseline-version 0.1.168 \
  --canary-acceptance-decision-json /tmp/phase11-canary-acceptance-decision-0.1.197.json \
  --operator "vahid" \
  --reason "Prepare Phase 11E limited onboarding gate after accepted Phase 11D canary decision" \
  --operator-confirmed \
  --i-understand-no-real-customer-onboarding-yet \
  --i-understand-no-production-traffic-yet \
  --i-understand-phase11e-requires-separate-execution-gate \
  --output json
```
