# Phase 11 farm5 0.1.279 lifecycle execution evidence

This document records the farm5 controlled DB-only production customer lifecycle execution evidence for Phase 11 operational completion item 2.

## Scope

```text
repository_version: 0.1.279
server: farm5
evidence_collected_at_utc: 2026-06-16T09:21:49Z
operator_user: mpf
operator_command_prefix: sudo -u mpf /usr/local/bin/mpf
target_customer_key: limited-btc-001
target_lane: btc
target_port: 20101
package_id: phase11-lifecycle-7af897db-9e7e-4748-b4ea-f6c65c587cd2
package_sha256: b347840ed55cb79fa766e3f04b477807f7a2ef777081893eeb41c4e3345bfe18
correlation_id: 14d5d96c-861f-4b45-b9af-c5a32d38d70e
backup_id: 6
restore_point_id: 7
event_id: 21
audit_id: 21
backup_path: /var/backups/mpf/phase11-lifecycle-execution/14d5d96c-861f-4b45-b9af-c5a32d38d70e.json
backup_sha256: 3914d7500469d2acbbff0dafdf699e7e52cead28ea3dbd2db369c6f595313c6c
```

## Gate state before execution

```text
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
customer_onboarding_allowed: controlled_cli_limited
proxy_data_plane_allowed: limited_runtime_local_only
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
```

## Package and preflight

```text
package_final_decision: PACKAGE_READY
package_blockers: []
preflight_final_decision: PREFLIGHT_READY
preflight_blockers: []
operator_context.effective_user: mpf
mutation_performed_before_execute: false
db_mutation_performed_before_execute: false
firewall_apply_performed_before_execute: false
conntrack_flush_performed_before_execute: false
docker_restart_performed_before_execute: false
systemd_restart_performed_before_execute: false
phase12_start_allowed_before_execute: false
```

## Execute result

```text
final_decision: PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_RECORDED
mutation_performed: true
db_mutation_performed: true
firewall_apply_performed: false
conntrack_flush_performed: false
docker_restart_performed: false
systemd_restart_performed: false
phase12_start_allowed: false
```

The execution created the intended DB-backed evidence records and backup artifact:

```text
audit_log: 20 -> 21
backups: 5 -> 6
events: 20 -> 21
restore_points: 6 -> 7
job_runs: 0 -> 0
```

The target customer remained active on the exact BTC port:

```text
customer_id: 3
customer_key: limited-btc-001
lane: btc
port: 20101
status: active
service_days: null
updated_by: vahid/farm5-phase11-0.1.279
```

## Verify result

```text
final_decision: PRODUCTION_CUSTOMER_LIFECYCLE_EXECUTION_EVIDENCE_READY
verify_blockers: []
verify_mutation_performed: false
verify_db_mutation_performed: false
verify_firewall_apply_performed: false
verify_conntrack_flush_performed: false
verify_docker_restart_performed: false
verify_systemd_restart_performed: false
verify_phase12_start_allowed: false
```

## Final local safety recheck

```text
phase12_start_allowed: no
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
proxy_status: OK
```

## Acceptance impact

This evidence advances only Phase 11 operational completion item 2:

```text
production_customer_lifecycle_execution: READY
```

The remaining Phase 11 operational completion surfaces still require their own farm5 evidence. Full CLI Production Operations remains not accepted, and `production_traffic` plus `customer_onboarding_allowed` remain `controlled_cli_limited`.
