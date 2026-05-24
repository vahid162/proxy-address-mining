# Phase 11 farm5 0.1.202 firewall plan gate evidence

- version: 0.1.202
- main/archive commit: e9096446feb42ea1176846d4260bde63892c3c2d

## farm5 sync/test summary
- source synced to /opt/mpf-py-src
- VERSION = 0.1.202
- full pytest: 1206 passed
- doctor/database/proxy OK
- apply_mode: plan_only
- traffic_changes: none
- firewall_mutation: disabled
- abuse_automation: disabled

## DB/customer state
- canary-btc-001 exists on btc port 20001 as the controlled canary artifact
- limited-btc-001 exists
- lane: btc
- port: 20101
- status: paused
- activation_mode: first_connect

## firewall/NAT state
- no firewall/NAT apply for 20101 yet
- existing controlled canary artifact on 20001 remains present
- canary 20001 artifact was not modified

## firewall plan gate command summary
- `mpf production single-customer-firewall-plan-gate ... --output json` executed on farm5 with operator confirmations and safety acknowledgements.

## firewall plan gate decision
- final_decision: PHASE11_SINGLE_CUSTOMER_FIREWALL_PLAN_GATE_READY
- phase11e_firewall_plan_gate_ready: true
- firewall_plan_generated: true
- firewall_apply_allowed: false
- nat_apply_allowed: false
- iptables_restore_authorized: false
- production_traffic_enabled: false
- miner_traffic_allowed: false
- mutation_performed: false
- blockers: []
- warnings: []
- next_required_step: phase11e_firewall_apply_gate_pr

## plan summary
- intended_chain: MPFC_20101
- intended_nat_chain: MPF_NAT_PRE
- intended_public_port: 20101
- intended_backend_target: 172.18.0.3:60010
- intended_customer_key: limited-btc-001
- intended_lane: btc

## explicit safety boundary
- this evidence authorizes building a firewall apply gate only
- it does not authorize firewall/NAT apply
- it does not authorize iptables-restore
- it does not authorize miner traffic
- it does not authorize production traffic
- it does not mark Phase 11 accepted
