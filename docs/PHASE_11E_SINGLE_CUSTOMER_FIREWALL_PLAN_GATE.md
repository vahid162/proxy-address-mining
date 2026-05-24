# Phase 11E single-customer firewall plan gate

## Purpose
Validate DB-staged limited customer scope and produce a non-mutating firewall/NAT plan summary for review only.

## Prerequisite
farm5 0.1.200 single-customer DB-only staging evidence recorded.

## Candidate
`limited-btc-001 / btc / 20101 / 172.18.0.3:60010`

## Safety boundary
- plan/diff only
- no firewall apply
- no NAT apply
- no iptables-restore authorization
- no production traffic
- no miner traffic
- no abuse automation
- no UI
- no Telegram
- no scheduler
- no worker enforcement

## Expected positive output
`final_decision: PHASE11_SINGLE_CUSTOMER_FIREWALL_PLAN_GATE_READY` with plan generated and all apply/traffic flags false.

## Expected blocked output
`final_decision: BLOCKED`, plan not generated, blockers populated, and all apply/traffic flags false.

## Required next apply prerequisites
- restore point
- lock
- rollback artifact
- pre-apply iptables-save
- post-apply verification
- runtime path evidence for 20101
- visibility bundle evidence
- abuse 1h coverage evidence
- restart/container-order evidence

## Command example
```bash
mpf production single-customer-firewall-plan-gate \
  --expected-version 0.1.201 \
  --farm5-baseline-version 0.1.168 \
  --staging-execute-json /tmp/phase11-single-customer-staging-execute-db-only-0.1.200.as-mpf.json \
  --candidate-customer-key limited-btc-001 \
  --candidate-lane btc \
  --candidate-public-port 20101 \
  --candidate-backend-target 172.18.0.3:60010 \
  --operator "vahid" \
  --reason "Generate Phase 11E single-customer firewall/NAT plan gate after DB-only staging evidence" \
  --operator-confirmed \
  --i-understand-plan-only \
  --i-understand-no-firewall-apply \
  --i-understand-no-nat-apply \
  --i-understand-no-production-traffic \
  --i-understand-no-miner-traffic-yet \
  --i-confirm-restore-point-required-before-apply \
  --i-confirm-lock-required-before-apply \
  --i-confirm-rollback-plan-required-before-apply \
  --i-confirm-restart-test-required-before-traffic \
  --i-confirm-abuse-1h-required-before-traffic \
  --output json
```
