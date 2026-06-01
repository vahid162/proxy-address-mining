# Phase 11 farm5 0.1.232 Controlled Boundary Acceptance Package READY Evidence

Status: recorded farm5 evidence context for the next read-only planning/readiness step. This document does not grant Phase 11 final acceptance or authorize mutation.

## Accepted farm5 Evidence

- GitHub `main` sync completed successfully for `0.1.232`.
- Post-sync test result: `1531 passed`.
- The controlled boundary preflight ran read-only.
- `limited-btc-001`: active.
- Preserved `canary-btc-001`: active.
- DB/proxy health is OK and no forbidden public runtime exposure exists.

## Visibility Bundle Input

- Path: `/tmp/phase11e-runtime-stratum-0.1.214-20260525T152651Z/visibility-bundle-0.1.218.json`
- SHA-256: `0cfa19543128954c6774d7ac14646626cd1886ac24895825395fe96612fdc583`
- `final_decision = PHASE11_SINGLE_CUSTOMER_VISIBILITY_BUNDLE_READY`
- `visibility_bundle_ready = true`
- Exact scope: `limited-btc-001` / `btc` / `20101` / `172.18.0.3:60010`
- `blockers = []`
- `warnings = []`

## Limited Acceptance Decision Input

- Path: `/tmp/phase11-0.1.231-limited-acceptance-decision-gate-20260601T152222Z/phase11-limited-acceptance-decision-gate.json`
- SHA-256: `3d32ed030f05dc37801820565892a049a376aed264445f27e8dfa17e25bc48e0`
- `final_decision = PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY`
- `limited_acceptance_decision_ready = true`
- `controlled_boundary_package_pr_ready = true`
- Exact scope: `limited-btc-001` / `btc` / `20101` / `172.18.0.3:60010`
- `blockers = []`
- `warnings = []`

## Fresh Artifact Gate

- `final_decision = PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS`
- `expected_version = repository_version = 0.1.232`
- `current_phase_gate_ok = true`
- `unknown_mpf_artifacts = []`
- `forbidden_public_runtime_exposure = false`
- `production_gates_remain_closed = true`
- `blockers = []`
- `warnings = ["known_controlled_phase11_artifacts_present"]`

## Abuse 1h and Restart/Container-Order Readiness

- Abuse readiness: `final_decision = PHASE11_SINGLE_CUSTOMER_ABUSE_1H_READINESS_READY`.
- `abuse_1h_coverage_ready = true`, `abuse_state_machine_contract_ready = true`, `hard_after_1h_contract_ready = true`.
- Farms-only, worker-only, and missing/stale-evidence hardening remain forbidden by contract.
- Restart/container-order readiness: `final_decision = PHASE11_SINGLE_CUSTOMER_RESTART_CONTAINER_ORDER_READINESS_READY`.
- `restart_container_order_ready = true`, `container_order_contract_ready = true`, `local_only_runtime_ready = true`.
- `backend_public_exposure_blocked = true`, `backend_internal_reachability_ready = true`.

## Controlled Boundary Acceptance Package

- Path: `/tmp/phase11-0.1.232-controlled-boundary-acceptance-package-20260601T181801Z/phase11-controlled-boundary-acceptance-package.json`
- SHA-256: `06f5c33086030d2da5c330c08c47ea36d49cdecd9284b2fcdb6ebe393b7e7271`
- Helper output directory: `/tmp/phase11-0.1.232-controlled-boundary-acceptance-package-20260601T181801Z`
- Preflight directory: `/tmp/phase11-0.1.232-controlled-boundary-preflight-20260601T181801Z`
- Manifest SHA-256: `05e177446951943595ee73b4365fa54409d5c4fde3449f1a388d074c996842fe`
- `final_decision = PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY`
- `limited_acceptance_decision_ready = true`
- `source_evidence_ready = true`
- `artifact_gate_passed = true`
- `abuse_readiness_ready = true`
- `restart_container_order_ready = true`
- `current_phase_gate_ok = true`
- `controlled_boundary_acceptance_package_ready = true`
- `controlled_boundary_acceptance_decision_pr_ready = true`
- `blockers = []`
- `warnings = []`
- `next_required_step = phase11_controlled_boundary_acceptance_decision_pr`

## Source-Bundle Classifier Nuance

The older preflight source-bundle classifier may report `final_decision = BLOCKED` with blocker `limited_btc_001_not_paused`, because that older classifier still expects the pre-activation paused state. This is not a blocker for the controlled boundary acceptance package. The controlled-boundary service correctly validates the currently accepted limited scope as active: `limited-btc-001` is active, preserved `canary-btc-001` is active, DB/proxy health is OK, and no forbidden public runtime exposure exists. The controlled boundary package is therefore READY.

## Safety Boundary

All mutation, runtime, production, miner, abuse automation, UI, and Telegram flags remain false:

```text
phase11_final_acceptance_allowed = false
production_expansion_allowed = false
miner_traffic_expansion_allowed = false
abuse_automation_allowed = false
ui_allowed = false
telegram_allowed = false
mutation_performed = false
db_mutation_performed = false
firewall_apply_performed = false
docker_restart_performed = false
systemd_restart_performed = false
phase11_accepted = false
```

Phase 11 final acceptance is still not granted. The next step is only the read-only controlled boundary acceptance decision PR.
