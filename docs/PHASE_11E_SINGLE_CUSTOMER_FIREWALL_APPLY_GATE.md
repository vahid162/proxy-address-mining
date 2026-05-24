# Phase 11E single-customer firewall apply gate

Purpose: non-mutating apply-gate package readiness report only.

## prerequisite
- farm5 0.1.202 sync/test evidence
- farm5 0.1.202 single-customer firewall plan gate evidence

## candidate
- limited-btc-001 / btc / 20101 / 172.18.0.3:60010

## hard safety boundary
- apply-gate package only
- no firewall apply
- no NAT apply
- no iptables-restore
- no production traffic
- no miner traffic
- no abuse automation
- no UI
- no Telegram
- no scheduler
- no worker enforcement

## required pre-apply artifacts
- pre-apply iptables-save
- restore point
- operator lock
- rollback artifact
- canary 20001 preservation check
- exact 20101 plan summary/hash

## required future post-apply evidence
- post-apply iptables-save
- MPFC_20101 exists
- DNAT 20101 -> 172.18.0.3:60010 exists
- canary 20001 still exists
- runtime path evidence for 20101
- Stratum transcript evidence for 20101
- visibility bundle evidence
- rollback readiness evidence
- abuse 1h coverage evidence before customer traffic
- restart/container-order evidence before limited production acceptance


## live snapshot safety checks
- The apply gate verifies the existing 20001 controlled canary artifact read-only.
- It must not modify or remove the 20001 canary artifact.
- It must block if 20101 is already live before the future apply execution PR.
- It must block if live snapshot read is not authorized by PHASE_STATUS.

## expected positive output
- `final_decision: PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_GATE_READY`
- `phase11e_firewall_apply_gate_ready: true`
- `apply_gate_package_generated: true`
- all apply/traffic/authorization flags remain `false`

## expected blocked output
- `final_decision: BLOCKED`
- `phase11e_firewall_apply_gate_ready: false`
- `apply_gate_package_generated: false`
- blockers populated

## command example
```bash
mpf production single-customer-firewall-apply-gate \
  --expected-version 0.1.203 \
  --farm5-baseline-version 0.1.168 \
  --firewall-plan-gate-json /tmp/phase11-single-customer-firewall-plan-gate-0.1.202.json \
  --candidate-customer-key limited-btc-001 \
  --candidate-lane btc \
  --candidate-public-port 20101 \
  --candidate-backend-target 172.18.0.3:60010 \
  --operator "vahid" \
  --reason "Prepare Phase 11E single-customer firewall apply gate after 0.1.202 plan evidence" \
  --operator-confirmed \
  --i-understand-apply-gate-only \
  --i-understand-no-firewall-apply-in-this-pr \
  --i-understand-no-nat-apply-in-this-pr \
  --i-understand-no-iptables-restore-in-this-pr \
  --i-understand-no-production-traffic \
  --i-understand-no-miner-traffic-yet \
  --i-confirm-limited-single-customer-scope \
  --i-confirm-restore-point-required-before-apply \
  --i-confirm-operator-lock-required-before-apply \
  --i-confirm-rollback-artifact-required-before-apply \
  --i-confirm-pre-apply-snapshot-required-before-apply \
  --i-confirm-post-apply-verification-required \
  --i-confirm-runtime-path-evidence-required-after-apply \
  --i-confirm-abuse-1h-evidence-required-before-customer-traffic \
  --i-confirm-restart-container-order-evidence-required-before-customer-traffic \
  --collect-live \
  --output json
```
