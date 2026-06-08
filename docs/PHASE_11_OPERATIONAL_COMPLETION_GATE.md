Phase 11 operational completion 0.1.248 note: farm5 0.1.247 post-sync evidence distinguishes healthy runtime container/listener persistence from unresolved controlled customer firewall artifact persistence. The current next implementation step is `implement_controlled_artifact_reapply_execute_package`; restart/autostart proof and Full CLI Production Operations remain unaccepted, and Phase 12/worker enforcement/UI/Telegram remain blocked.
Phase 11 operational completion 0.1.247 note: the active step is `fix_restart_autostart_persistence_gap`. The repository now provides controlled repair planning/package/evidence tooling for the post-reboot persistence blockers (`unhealthy_container:mpf-v2raya-socks-bridge` and `post_reboot_known_controlled_phase11_artifacts_absent`) while keeping `restart_autostart_proof=missing_or_partial` until farm5 post-fix evidence proves recovery. `unknown_mpf_artifacts` remained `[]`, public backend exposure remained false, Phase 12, worker enforcement, UI, and Telegram remain blocked, and `full_cli_production_operations` remains not accepted.

# Phase 11 operational completion — Full CLI Production Operations Gate


Phase 11 operational completion 0.1.246 note: farm5 0.1.245 post-reboot evidence discovered that runtime containers partially returned, `mpf-v2raya-socks-bridge` was missing from the expected runtime container set, and controlled Phase 11 firewall artifacts were absent after reboot. Restart/autostart proof remains blocked as `missing_or_partial` until the persistence gap is fixed; `next_required_step` remains `fix_restart_autostart_persistence_gap`.

Phase 11 operational completion 0.1.245 note: restart/autostart proof now has a real read-only service/CLI/helper surface, but remains missing_or_partial until farm5 source-backed restart/autostart evidence is collected; all other Full CLI Production Operations items remain missing_or_partial and Phase 12 remains blocked.

## Gate Meaning

`Phase 11 operational completion — Full CLI Production Operations` is the active post-acceptance completion gate after the accepted Phase 11 controlled CLI-limited BTC boundary and before Phase 12 Worker Policy Enforcement. This is not a new phase: Phase 11 remains accepted for the controlled BTC boundary, and the current working phase stays under Phase 11 operational completion.

Phase 12 implementation must not start until a final Phase 11 operational completion acceptance PR records Full CLI Production Operations as accepted.

## Required Full CLI Production Operations Acceptance Scope

Final acceptance must prove all of these operational surfaces through CLI/service-layer workflows and farm5 evidence:

1. restart/autostart proof;
2. production customer lifecycle CLI execution;
3. production firewall plan/apply/verify/rollback for real customer ports;
4. production onboarding flow through CLI;
5. production usage/report/check evidence;
6. production abuse runner for all active customers in all enabled lanes;
7. pause/block/expire-run operational controls;
8. backup/restore drill;
9. final acceptance that sets `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`.

## Final Acceptance Criteria

```text
restart_autostart_proof: READY
production_customer_lifecycle_execution: READY
production_firewall_apply_verify_rollback: READY
production_onboarding_flow: READY
production_usage_report_check_evidence: READY
production_abuse_runner: READY
production_controls_pause_block_expire: READY
backup_restore_drill: READY
full_cli_production_operations: READY
unknown_mpf_artifacts: []
forbidden_public_runtime_exposure: false
production_traffic: cli_production
customer_onboarding_allowed: cli_production
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: yes only after final acceptance
```

## Current Fail-Closed Position

Until every acceptance criterion is evidenced and a final acceptance PR explicitly advances the gate:

```text
phase12_start_allowed: no
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
production_traffic: controlled_cli_limited
customer_onboarding_allowed: controlled_cli_limited
```

No worker enforcement, UI, Telegram, buyer panel, public API, public backend exposure, direct/ad-hoc DB or firewall mutation, firewall changes outside the service-layer planner/apply/verify path, or abuse hard outside the official restore/backup/firewall/conntrack/audit path is authorized by this document.

## Progress Update (0.1.246)

- farm5 0.1.245 post-reboot evidence found a restart/autostart persistence blocker: runtime containers only partially returned after reboot.
- `mpf-v2raya-socks-bridge` was missing from the expected runtime container set while the local-only v2rayA UI and BTC backend listeners were visible.
- The current controlled artifact gate reported no unknown MPF artifacts, but known controlled Phase 11 firewall customer artifacts were absent after reboot.
- Restart/autostart proof stays `missing_or_partial`; the next required step is `implement_controlled_artifact_reapply_execute_package`, not Phase 12 or Full CLI Production Operations acceptance.


0.1.251 controlled runtime-forward note: the source-backed controlled artifact renderer, schema-faithful metadata wiring, and production adapters are implemented, but the filter packet path remains fail-closed until source-backed farm5 evidence proves the correct hook for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`. No farm5 mutation was performed, no live `iptables-restore` was executed during PR development or CI, and no READY farm5 package has been collected. Progression is now `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`. The exact next step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; server sync is allowed only for read-only package/evidence collection first, and controlled execution requires separate package review. `restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

0.1.251 controlled filter packet-path evidence note: static packet-path collection and offline verification capability is implemented for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`; no farm5 packet-path evidence was collected by this PR, no runtime packet was observed, no hook was proven on farm5 during PR development, and no firewall, Docker, systemd, conntrack, PostgreSQL, customer, policy, block, pause, or abuse mutation occurred. Controlled artifact package generation remains blocked by `controlled_filter_packet_path_unresolved`; artifact graph binding and production execution remain unavailable; post-DNAT hook and match semantics require a future reviewed binding PR after a source-backed farm5 bundle. Current progression flags are `read_only_reapply_foundation_implemented=true`, `controlled_filter_packet_path_evidence_capability_implemented=true`, `controlled_filter_packet_path_evidence_ready=false`, `controlled_filter_packet_path_verified=false`, `artifact_graph_binding_ready=false`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`; `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`. The next required step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; a future READY bundle recommends `review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph`, not execution. `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.
