# Phase 11E Single-Customer DB-Only Staging

## Purpose
Provide a controlled package to plan and optionally execute DB-only staging for exactly one limited candidate customer (`limited-btc-001`) after the accepted farm5 `0.1.199` limited-onboarding-execution-gate evidence.

## Prerequisite
- farm5 `0.1.199` limited-onboarding-execution-gate evidence must already be recorded.

## Candidate Scope (fixed for first package)
- `candidate_customer_key`: `limited-btc-001`
- `candidate_lane`: `btc`
- `candidate_public_port`: `20101`
- `candidate_backend_target`: `172.18.0.3:60010`

## Allowed Modes
- `plan`
- `execute-db-only`

## Safety Boundary (hard)
- DB-only staging at most
- no firewall apply
- no NAT apply
- no production traffic
- no live customer traffic
- no abuse automation
- no UI
- no Telegram
- no scheduler
- no worker enforcement

## Expected plan output
- `final_decision`: `PHASE11_SINGLE_CUSTOMER_STAGING_PLAN_READY`
- `mode`: `plan`
- `phase11e_single_customer_staging_ready`: `true`
- `phase11e_db_staging_allowed`: `false`
- `customer_created`: `false`
- `db_mutation_performed`: `false`
- `firewall_mutation_performed`: `false`
- `nat_mutation_performed`: `false`
- `production_traffic_enabled`: `false`
- `next_required_step`: `run_execute_db_only_staging_on_farm5`

## Expected execute-db-only output
- `final_decision`: `PHASE11_SINGLE_CUSTOMER_DB_STAGING_EXECUTED`
- `mode`: `execute-db-only`
- `phase11e_db_staging_allowed`: `true`
- `customer_created`: `true` OR exact-existing-idempotent
- `db_mutation_performed`: `true` if created else `false`
- `firewall_mutation_performed`: `false`
- `nat_mutation_performed`: `false`
- `production_traffic_enabled`: `false`
- `limited_onboarding_allowed`: `false`
- `next_required_step`: `phase11e_firewall_plan_gate_pr`

## Rollback note
DB-created limited customer must be removable/markable through accepted customer lifecycle path in a later rollback/evidence step if needed.

## Command example (plan)
```bash
mpf production single-customer-staging \
  --expected-version 0.1.200 \
  --farm5-baseline-version 0.1.168 \
  --execution-gate-json /tmp/phase11-limited-onboarding-execution-gate-0.1.199.json \
  --candidate-customer-key limited-btc-001 \
  --candidate-lane btc \
  --candidate-public-port 20101 \
  --candidate-backend-target 172.18.0.3:60010 \
  --candidate-description "Phase 11E first limited real customer candidate" \
  --mode plan \
  --operator "vahid" \
  --reason "Plan Phase 11E DB-only single-customer staging after execution-gate readiness" \
  --operator-confirmed \
  --i-understand-db-only-staging \
  --i-understand-no-firewall-apply \
  --i-understand-no-nat-apply \
  --i-understand-no-production-traffic \
  --i-understand-single-customer-limit \
  --i-confirm-port-not-live-until-firewall-gate \
  --i-confirm-rollback-plan-required \
  --i-confirm-restart-test-required-before-traffic \
  --i-confirm-abuse-1h-required-before-traffic \
  --output json
```

## Command example (execute-db-only)
```bash
mpf production single-customer-staging \
  --expected-version 0.1.200 \
  --farm5-baseline-version 0.1.168 \
  --execution-gate-json /tmp/phase11-limited-onboarding-execution-gate-0.1.199.json \
  --candidate-customer-key limited-btc-001 \
  --candidate-lane btc \
  --candidate-public-port 20101 \
  --candidate-backend-target 172.18.0.3:60010 \
  --candidate-description "Phase 11E first limited real customer candidate" \
  --mode execute-db-only \
  --operator "vahid" \
  --reason "Execute DB-only staging for Phase 11E first limited customer; no firewall/NAT/traffic" \
  --operator-confirmed \
  --i-understand-db-only-staging \
  --i-understand-no-firewall-apply \
  --i-understand-no-nat-apply \
  --i-understand-no-production-traffic \
  --i-understand-single-customer-limit \
  --i-confirm-port-not-live-until-firewall-gate \
  --i-confirm-rollback-plan-required \
  --i-confirm-restart-test-required-before-traffic \
  --i-confirm-abuse-1h-required-before-traffic \
  --output json
```
