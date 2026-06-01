# Phase 11 Farm5 0.1.229 Limited Activation Observation / Review READY Evidence

## Recorded Farm5 Result

Farm5 `0.1.229` sync/test passed. The full pytest run passed with `1482 passed`, and the current phase safety gate passed. This records source-backed READY evidence only; it does not change `docs/PHASE_STATUS.md` Current State.

## Exact Scope

```text
candidate_customer_key: limited-btc-001
lane: btc
public_port: 20101
backend_target: 172.18.0.3:60010
preserved canary: canary-btc-001
```

## Limited Activation Observation

```text
final_decision = PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY
blockers = []
warnings = []
limited-btc-001 active
canary-btc-001 active
canary_preserved = true
db_ok = true
proxy_ok = true
artifact_gate_passed = true
current_phase_gate_ok = true
mutation_performed = false
db_mutation_performed = false
firewall_apply_performed = false
conntrack_flush_performed = false
docker_restart_performed = false
systemd_restart_performed = false
production_traffic_enabled = false
miner_traffic_allowed = false
abuse_automation_enabled = false
phase11_accepted = false
```

DB, proxy, and source evidence were OK. The artifact gate and current phase safety gate passed.

## Limited Activation Acceptance Review

```text
final_decision = PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY
blockers = []
warnings = []
activation_execution_accepted = true
post_activation_evidence_accepted = true
observation_accepted = true
rollback_ready = true
artifact_gate_passed = true
current_phase_gate_ok = true
limited_activation_review_ready = true
phase11_final_acceptance_allowed = false
production_expansion_allowed = false
miner_traffic_expansion_allowed = false
abuse_automation_allowed = false
ui_allowed = false
telegram_allowed = false
```

## Output Hashes

```text
limited-activation-observation.json:
2be853d0cbcb254b296caf31c03076ba86f4f952d68be7ae7dd55f5bdc352858
limited-activation-acceptance-review.json:
9243a5a4daf1e3add318b5ec39f9bd18a51eb765db9bbae3010cd57241605163
manifest.json:
bd85a8b1a636e96b2b842c898872c41e667eaa60f2134084e851f90806c8e0c5
```

## Closed Gates and Next Step

All mutation, firewall, runtime-change, production-traffic, miner-expansion, abuse-automation, UI, and Telegram flags remain false. Phase 11 final acceptance is still not granted. The next safe step is a read-only limited customer observation window and read-only final-readiness planning report, not production expansion.
