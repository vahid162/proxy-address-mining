# PHASE STATUS

## Authority and scope

This file is the only dynamic state and runtime authorization authority for the repository. GitHub repository version, merge state, release notes, and changelog entries are not proof of server deployment or current server state.

Historical release notes, evidence summaries, and prior phase-status narratives are preserved in [`docs/history/PHASE_STATUS_LEGACY_0.1.302.md`](history/PHASE_STATUS_LEGACY_0.1.302.md). Current runtime actions require explicit current authorization in this file plus fresh source-backed evidence and operator review where the active gate requires it.

## Repository state

- Current repository version: `0.1.304`.
- Documentation/state separation is completed by this release.
- No server deployment, runtime mutation, database mutation, firewall mutation, Docker/systemd/conntrack change, customer-state change, abuse execution, worker enforcement, UI, Telegram, or production-traffic change is implied by this repository release.

## Current phase and authorization

The following values are copied from the latest authoritative current-state block in the prior active `docs/PHASE_STATUS.md`; historical conflicting snapshots remain only in the legacy archive.

## Current State

Compatibility heading for current-state parsers. This block is the active current-state assignment block.

```text
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
server_state: farm5 controlled CLI-limited BTC production/customer activation is accepted; Phase 11 operational completion now requires Full CLI Production Operations acceptance before Phase 12 implementation
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled_operator_gated
customer_onboarding_allowed: controlled_cli_limited
proxy_data_plane_allowed: limited_runtime_local_only
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

Full CLI Production Operations is not accepted.

Controlled firewall and abuse boundaries remain operator-gated and do not authorize unrestricted automation, direct mutation, public backend/API exposure, broad production expansion, worker enforcement, UI, Telegram, timers, daemons, or Phase 12 work.

## Next required step

The exact currently authoritative next step copied from the prior active document is:

```text
Next runtime step after sync: rerun `generic-activation-verify` on existing post-apply evidence; if READY, run `generic-activation-first-connect-db` as `sudo -u mpf` using transcript evidence sha256 `3c2857e1da4afe2e69ef12ef079142e277d1659100586ec088d83c69bcbd24ec`; then run `generic-activation-readiness` and the operational gap inventory. Expected `next_required_step`: `final_phase11_operational_completion_acceptance`.
```

GitHub merge does not execute this step. Server work requires offline sync first. Any runtime action still requires the active gate plus fresh evidence and operator review. This PR does not authorize execution.

## Required evidence before runtime action

Before any runtime action, use the current active gate/task documents, fresh source-backed evidence, relevant package/preflight/verify evidence where the active task requires it, and operator approval for controlled runtime work. Do not infer authorization from historical evidence, archived phase-status material, release notes, changelog entries, or GitHub merge state.

## Active task documents

- [`docs/AI_SAFE_RUNTIME_FIRST.md`](AI_SAFE_RUNTIME_FIRST.md)
- [`docs/PRODUCTION_ACTIVATION_GATE.md`](PRODUCTION_ACTIVATION_GATE.md)
- [`docs/BACKEND_PORT_POLICY.md`](BACKEND_PORT_POLICY.md)
- [`docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md`](PHASE_11_OPERATIONAL_COMPLETION_GATE.md)
- [`docs/AI_PHASE_11_TASK.md`](AI_PHASE_11_TASK.md)

These documents are active only to the extent they are consistent with this file and current safety contracts.

## Historical records

- [`docs/history/PHASE_STATUS_LEGACY_0.1.302.md`](history/PHASE_STATUS_LEGACY_0.1.302.md)
- [`CHANGELOG.md`](../CHANGELOG.md)
- [`docs/history/`](history/)

These records are context and audit history only. They cannot authorize runtime work, server mutation, phase advancement, deployment claims, or gate changes.
