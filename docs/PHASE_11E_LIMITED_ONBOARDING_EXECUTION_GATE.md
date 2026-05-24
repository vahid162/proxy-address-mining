# Phase 11E Limited Onboarding Execution Gate

## Purpose
Validate readiness for a future controlled single real-customer execution PR without onboarding a customer or mutating host/runtime in this PR.

## Prerequisite
farm5 0.1.198 limited-onboarding-gate evidence.

## Input example
`/tmp/phase11-limited-onboarding-gate-0.1.198.json`

## Allowed first limited candidate shape
- key prefix: `limited-btc-`
- lane: `btc`
- public port range: `20101-20120`
- backend target: `172.18.0.3:60010`

## Explicit safety boundary
- this PR does not onboard customer
- this PR does not create DB customer
- this PR does not apply firewall/NAT
- this PR does not authorize production traffic
- this PR does not enable abuse automation
- this PR does not enable UI/Telegram/scheduler/worker enforcement

## Positive decision semantics
`PHASE11E_LIMITED_ONBOARDING_EXECUTION_GATE_READY` means only that the next PR may implement explicit controlled single-customer execution.

## Blocked decision semantics
`BLOCKED` means one or more prerequisites/safety confirmations are missing; no onboarding execution is authorized.

## Required next execution checklist
- create or validate exactly one limited real customer candidate
- ensure no collision with canary port 20001
- ensure no collision with existing customer ports
- generate DB-only customer staging plan
- generate firewall plan/diff only
- require restore point and lock before any future apply
- require rollback/restore-plan artifact
- require restart/container-order evidence
- require live Stratum transcript evidence for the limited customer
- require runtime-path evidence for the limited customer
- require visibility bundle evidence
- require abuse 1h coverage evidence for active customers in enabled lanes
- require operator approval before future execution

## Command example
```bash
mpf production limited-onboarding-execution-gate \
  --expected-version 0.1.199 \
  --farm5-baseline-version 0.1.168 \
  --limited-onboarding-gate-json /tmp/phase11-limited-onboarding-gate-0.1.198.json \
  --candidate-customer-key limited-btc-001 \
  --candidate-lane btc \
  --candidate-public-port 20101 \
  --candidate-backend-target 172.18.0.3:60010 \
  --candidate-description "Phase 11E first limited real customer candidate" \
  --operator "vahid" \
  --reason "Prepare explicit Phase 11E single-customer execution gate after limited onboarding readiness evidence" \
  --operator-confirmed \
  --i-understand-this-does-not-onboard-customer \
  --i-understand-no-firewall-apply-yet \
  --i-understand-no-production-traffic-yet \
  --i-understand-next-pr-must-execute-controlled-single-customer \
  --i-confirm-rollback-plan-required \
  --i-confirm-restart-test-required \
  --i-confirm-abuse-1h-coverage-required \
  --output json
```
