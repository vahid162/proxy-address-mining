# Phase 11 Controlled Artifact Reapply Runbook (0.1.251)

Version `0.1.251` implements controlled artifact reapply source-backed renderer and production adapter surfaces for exactly the accepted BTC customers `canary-btc-001:20001` and `limited-btc-001:20101`.

No farm5 mutation was performed by this PR. Package generation is read-only, and this version must not produce a READY package in production until source-backed farm5 evidence proves the controlled filter packet path. Server sync for READY package collection must wait until `controlled_filter_packet_path_unresolved` is resolved with evidence.

## Read-only shape and evidence collection

```bash
mpf production controlled-backend-target --output json
mpf production controlled-artifact-reapply-plan --output json
mpf production controlled-artifact-reapply-package --output json
mpf production controlled-artifact-reapply-verify --package-json <package.json> --output json
scripts/phase11_controlled_artifact_reapply.sh --package --out-dir <evidence-dir>
```

The verify command builds a fresh read-only live plan and compares it with the supplied package; while `controlled_filter_packet_path_unresolved` remains present, verification must return a blocked decision. Local or CI environments without source-backed Docker, PostgreSQL, listener, and firewall evidence must fail closed and must not fabricate a historical backend target or READY execution package.

## Execution boundary

Public production execution intentionally fails closed before any `iptables-restore` invocation until the filter packet path is proven and real live preflight, OS lock, non-empty firewall backup, PostgreSQL operational metadata, exact rollback-plan, and post-apply verification gates all pass. The command still validates package file hash, canonical content hash, scope, version, hostname, phase gates, payload safety, and rollback metadata before reporting blockers.

The execution path must not restart Docker, call systemd, flush conntrack, mutate customer/policy/abuse/block/pause state, enable timers/daemons, broaden the two-customer scope, or mark restart/autostart proof READY.

## Current progression

The next step before execution is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`. Current flags are `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`.

`restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, and timer/daemon automation remain blocked.


0.1.251 controlled runtime-forward note: the source-backed controlled artifact renderer, schema-faithful metadata wiring, and production adapters are implemented, but the filter packet path remains fail-closed until source-backed farm5 evidence proves the correct hook for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`. No farm5 mutation was performed, no live `iptables-restore` was executed during PR development or CI, and no READY farm5 package has been collected. Progression is now `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`. The exact next step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; server sync is allowed only for read-only package/evidence collection first, and controlled execution requires separate package review. `restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

0.1.251 controlled filter packet-path evidence note: static packet-path collection and offline verification capability is implemented for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`; no farm5 packet-path evidence was collected by this PR, no runtime packet was observed, no hook was proven on farm5 during PR development, and no firewall, Docker, systemd, conntrack, PostgreSQL, customer, policy, block, pause, or abuse mutation occurred. Controlled artifact package generation remains blocked by `controlled_filter_packet_path_unresolved`; artifact graph binding and production execution remain unavailable; post-DNAT hook and match semantics require a future reviewed binding PR after a source-backed farm5 bundle. Current progression flags are `read_only_reapply_foundation_implemented=true`, `controlled_filter_packet_path_evidence_capability_implemented=true`, `controlled_filter_packet_path_evidence_ready=false`, `controlled_filter_packet_path_verified=false`, `artifact_graph_binding_ready=false`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`; `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`. The next required step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; a future READY bundle recommends `review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph`, not execution. `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.


## 0.1.253 verified binding/package evidence update

A source-backed 0.1.252 farm5 packet-path READY bundle may now be consumed by `mpf production verified-filter-hook-binding-plan` to bind the verified `DOCKER-USER` / `FORWARD` / `post_dnat_forward_filter` hook to explicit Phase 11 controlled artifact graph semantics. `mpf production controlled-artifact-reapply-package-plan` and `mpf production controlled-artifact-reapply-package-verify` generate and verify package evidence only. Execution remains blocked: `production_execution_available=false`, `iptables_restore_invocation_allowed=false`, `runtime_packet_observed=false`, `post_apply_runtime_verified=false`, `restart_autostart_proof=missing_or_partial`, `full_cli_production_operations=missing_or_partial`, and Phase 12/worker/UI/Telegram remain blocked.


## 0.1.256 Phase 11 live-ready controlled artifact reapply readiness package

- Adds `mpf production controlled-artifact-reapply-readiness --output json` and `scripts/phase11_controlled_artifact_reapply.sh --readiness` as an operator-reviewable live-ready readiness/package review surface only.
- This does not execute `iptables-restore`, does not apply firewall changes, does not call controlled artifact execute, and does not mutate DB, firewall, Docker, systemd, conntrack, customer, abuse, or policy state.
- `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`; production traffic and onboarding remain `controlled_cli_limited`.
- Phase 12, worker enforcement, UI, Telegram, timers, daemons, public backend/API, and unrestricted production remain closed.
- When readiness is READY, the next required step becomes `sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5`; otherwise it remains `prepare_live_ready_controlled_artifact_reapply_package`.
