# Phase 11 Farm5 0.1.230 Observation Window / Final-readiness READY Evidence

## Recorded Farm5 Result

Farm5 `0.1.230` sync to GitHub main completed successfully. The full pytest run passed with `1495 passed`, and the current phase safety gate passed. This records source-backed READY evidence only; it does not change `docs/PHASE_STATUS.md` Current State and does not grant Phase 11 final acceptance.

## Exact Scope

```text
candidate_customer_key: limited-btc-001
lane: btc
public_port: 20101
backend_target: 172.18.0.3:60010
preserved canary: canary-btc-001
```

## Fresh Controlled Artifact Gate

```text
component = phase11_current_controlled_artifact_gate
expected_version = 0.1.230
repository_version = 0.1.230
final_decision = PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS
current_phase_gate_ok = true
unknown_mpf_artifacts = []
forbidden_public_runtime_exposure = false
production_gates_remain_closed = true
blockers = []
warnings = ["known_controlled_phase11_artifacts_present"]
sha256 = 92e8d5a9dd4da77ee953ad4fce2567b2a3c1989e68f010f0f950f0ac0fbf0af8
```

## Observation Window READY

```text
path = /tmp/phase11e-0.1.230-observation-final-readiness-20260601T132436Z/limited-customer-observation-window.json
sha256 = f9bdf39c0f100ef922e11a6ce25ae74ff31410b4035378d8cb72508c0a151436
final_decision = PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY
samples_collected = 3
sample_interval_seconds = 30
min_samples = 3
limited-btc-001 active in all 3 samples
canary-btc-001 active in all 3 samples
canary_preserved = true
db_ok = true
proxy_ok = true
doctor_ok = true
artifact_gate_passed = true
current_phase_gate_ok = true
production_gates_remain_closed = true
unknown_mpf_artifacts = []
forbidden_public_runtime_exposure = false
blockers = []
warnings = []
```

All mutation/runtime/production/miner/abuse/UI/Telegram flags were false.

## Final-readiness Planning READY

```text
path = /tmp/phase11e-0.1.230-observation-final-readiness-20260601T132436Z/phase11-final-acceptance-readiness-planning.json
sha256 = 4f4fabc1597b1af9ca33621fc0b109fada32be547fd9a0b9441d3a90da0c3580
final_decision = PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY
limited_customer_observation_window_ready = true
limited_activation_review_ready = true
rollback_ready = true
artifact_gate_passed = true
current_phase_gate_ok = true
phase11_final_acceptance_pr_ready = true
phase11_final_acceptance_allowed = false
production_expansion_allowed = false
miner_traffic_expansion_allowed = false
abuse_automation_allowed = false
ui_allowed = false
telegram_allowed = false
blockers = []
warnings = []
next_required_step = explicit_phase11_limited_acceptance_decision_pr
```

## Manifest

```text
path = /tmp/phase11e-0.1.230-observation-final-readiness-20260601T132436Z/manifest.json
sha256 = b547993870f749d72cf9fc5586189733458af8584000685eef9daecbe1dc716b
```

## Closed Gates and Next Step

Phase 11 final acceptance is still not granted. Production expansion, miner traffic expansion, abuse automation, UI, Telegram, DB mutation, firewall apply, conntrack flush, Docker restart, and systemd restart remain closed. The next required step is `explicit_phase11_limited_acceptance_decision_pr`, not activation or expansion.
