# Phase 11 farm5 0.1.231 Limited Acceptance Decision READY Evidence

Status: recorded farm5 evidence context for the next read-only planning/readiness step. This document does not grant Phase 11 final acceptance or authorize mutation.

## Accepted farm5 Evidence

- GitHub `main` sync completed successfully for `0.1.231`.
- Post-sync test result: `1512 passed`.
- Current phase safety gate: passed.
- `limited-btc-001`: active.
- Preserved `canary-btc-001`: active.
- `firewall_change: no`, `nat_change: no`, `runtime_change: no`, and no job runs.

## Fresh Artifact Gate

- `final_decision = PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS`
- `expected_version = repository_version = 0.1.231`
- `current_phase_gate_ok = true`
- `unknown_mpf_artifacts = []`
- `forbidden_public_runtime_exposure = false`
- `production_gates_remain_closed = true`
- `blockers = []`
- `warnings = ["known_controlled_phase11_artifacts_present"]`
- `sha256 = 3b298863b05f27e178c68cd27f5480c64dca0662e1ed4b250a72fff69d1c5505`

## Limited Acceptance Decision Gate

- Path: `/tmp/phase11-0.1.231-limited-acceptance-decision-gate-20260601T152222Z/phase11-limited-acceptance-decision-gate.json`
- SHA-256: `3d32ed030f05dc37801820565892a049a376aed264445f27e8dfa17e25bc48e0`
- `final_decision = PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY`
- `observation_window_ready = true`
- `final_readiness_planning_ready = true`
- `artifact_gate_passed = true`
- `current_phase_gate_ok = true`
- `limited_acceptance_decision_ready = true`
- `controlled_boundary_package_pr_ready = true`
- `blockers = []`
- `warnings = []`
- `next_required_step = phase11_controlled_boundary_acceptance_package_pr`

Decision manifest:

- Path: `/tmp/phase11-0.1.231-limited-acceptance-decision-gate-20260601T152222Z/manifest.json`
- SHA-256: `0636a9aa13923cb79a0c0e0d11220bfa154be6cf42dbfaeebcbf51640b0933fb`

## Safety Boundary

All mutation, runtime, production, miner, abuse automation, UI, and Telegram flags remain false:

```text
phase11_final_acceptance_allowed = false
production_expansion_allowed = false
miner_traffic_expansion_allowed = false
abuse_automation_allowed = false
ui_allowed = false
telegram_allowed = false
firewall_change = no
nat_change = no
runtime_change = no
```

Phase 11 final acceptance is still not granted. The next step is only the read-only controlled boundary acceptance package PR.
