0.1.279 lifecycle execution hardening note: farm5 evidence proves `mpf` is the correct controlled lifecycle execution user (`sudo -u mpf /usr/local/bin/mpf ...`). Packages now include operator_context, preflight blocks non-mpf execute context and unwritable backup roots, execute re-runs preflight and reports controlled JSON errors/orphan backup artifacts, and verify fails closed as JSON for missing/invalid evidence, missing/corrupt backups, missing DB rows, and correlation mismatches. Controlled lifecycle execute was not run by this PR; production_traffic and customer_onboarding_allowed remain controlled_cli_limited, backup_restore_drill and Full CLI Production Operations remain not ready, and Phase 12/worker/UI/Telegram remain closed.
Phase 11 completion is now a 10-item matrix: items 1-8 remain the previous operational surfaces, item 9 is production generic real-customer activation, and item 10 is final acceptance. Final acceptance remains the last gate and must set `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`. Generic Real-Customer Activation is required before final acceptance; this does not authorize uncontrolled production expansion, Phase 12, worker enforcement, UI, Telegram, timers, or daemons. Until final acceptance, production_traffic and customer_onboarding_allowed remain controlled_cli_limited.


0.1.276 restart/autostart strict JSON evidence note: farm5 0.1.275 evidence at `/tmp/phase11-restart-autostart-proof-0.1.275-20260615T190637Z` proved the controlled artifact gate passed with backend target `172.18.0.2:60010`, unknown_mpf_artifacts=[], duplicate_nat_redirect_count=0, forbidden_public_runtime_exposure=false, production gates closed, and the restart/autostart proof payload READY, but `proof-report.json` was not strict JSON because shell provenance comments preceded the JSON object. This release keeps JSON captures strict, moves provenance to sidecar metadata, propagates the supplied evidence directory through post-cleanup summary/gap inventory, fails closed on malformed JSON evidence, and adds a read-only production customer lifecycle execution readiness package. Phase 11 operational completion remains not accepted; production_traffic and customer_onboarding_allowed remain controlled_cli_limited; Phase 12, worker enforcement, UI, and Telegram remain closed. Next runtime step: production customer lifecycle execution.


0.1.267 controlled execute recovery note: farm5 0.1.266 proved guarded execute reached `iptables-restore --test --noflush` and `iptables-restore --noflush` with `apply_succeeded=true`, but post-apply verification failed closed because the current artifact gate used a narrower allowlist than the official controlled artifact taxonomy and did not carry the resolved backend target consistently. The immediate recovery used a manually reviewed exact-inverse rollback from the package rollback_plan; rollback test passed, rollback apply succeeded, and the post-rollback gate returned `PASS_NO_CUSTOMER_ARTIFACTS` with MPF/proxy doctors OK and production gates still closed. Before any new execute, taxonomy/gate/post-verify alignment and the reviewed exact-inverse rollback executor path are required.
0.1.265 controlled reapply execute structure-stable snapshot hash note: farm5 0.1.264 evidence showed backend identity drift was fixed (`canonical_backend_binding_identity_match=true`, hard/informational mismatches empty, and package placeholder metadata ignored), fresh packet-path evidence was READY, the live-ready package was READY, and execute-preflight was READY. Guarded execute then failed safely before mutation with `final_decision=FAILED_PRE_APPLY` due only to raw `execution_precondition_fingerprint_drift`, `iptables_snapshot_drift`, and `ip6tables_snapshot_drift`; `firewall_mutation_performed=false`, `iptables_restore_invoked=false`, `restore_test_invoked=false`, `apply_invoked=false`, `partial_apply_possible=false`, and `rollback_required=false`. The package/live backend target fingerprints matched, the live plan remained `CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY`, and `live_plan_blockers=[]`. Current next_required_step: implement structure-stable firewall snapshot hashes for the controlled execute drift gate, then offline sync 0.1.265 to farm5, regenerate fresh packet-path evidence, build a READY live-ready package, pass execute-preflight, and run guarded execute only if real structure drift and all other hard safety checks remain clear. production_traffic and customer_onboarding_allowed remain controlled_cli_limited; restart_autostart_proof and Full CLI Production Operations remain missing_or_partial/unaccepted; Phase 12, worker enforcement, UI, Telegram, timers, daemons, direct Docker/systemd/conntrack mutation, customer/policy/abuse mutation, public backend exposure, and unrestricted production remain blocked.

0.1.264 controlled reapply execute placeholder metadata note: farm5 0.1.263 fresh packet-path evidence was READY, the live-ready package was READY, and execute-preflight was READY with blockers=[]. Guarded execute then failed safely before any restore test, apply, or firewall mutation with final_decision=FAILED_PRE_APPLY because canonical execute identity still treated package-bound placeholder backend metadata (`network_id=verified_packet_path_bundle`, `endpoint_id=verified_packet_path_endpoint`, `compose_project=None`, and `tcp_connect_ok=None`) as hard identity against real Docker runtime metadata. Version 0.1.264 ignores those known package placeholder metadata differences in canonical_backend_binding_identity_match while keeping them visible as informational diagnostics and preserving hard fail-closed checks for IP, port, container, running/health, public exposure, verified filter packet path, and controlled artifact graph binding mode. Current next_required_step: fix canonical execute identity to ignore package placeholder backend metadata while preserving hard safety identity checks, then offline sync 0.1.264 to farm5, regenerate fresh packet-path evidence, build a READY live-ready package, pass execute-preflight, and run guarded execute only if blockers=[]. production_traffic and customer_onboarding_allowed remain controlled_cli_limited; restart_autostart_proof and Full CLI Production Operations remain missing_or_partial/unaccepted; Phase 12, worker enforcement, UI, Telegram, timers, daemons, direct Docker/systemd/conntrack mutation, customer/policy/abuse mutation, public backend exposure, and unrestricted production remain blocked.

0.1.263 controlled reapply execute binding note: farm5 0.1.262 reached READY live-ready package and READY execute-preflight, then guarded execute failed pre-apply before any restore test or firewall mutation because execute-time backend binding/drift comparison treated raw backend fingerprint/source shape differences as broad drift and buried the root cause under secondary blockers. Version 0.1.263 canonicalizes execute-time backend binding identity comparison, preserves fail-closed behavior for real backend identity drift/public exposure/unhealthy backend/gate failures, and records compact FAILED_PRE_APPLY diagnostics. Current next_required_step: offline sync 0.1.263 to farm5, regenerate/review the live-ready controlled artifact reapply package if needed, run fresh execute-preflight, then run guarded controlled artifact reapply execute only if all gates remain READY and blockers=[]. production_traffic and customer_onboarding_allowed remain controlled_cli_limited; restart_autostart_proof and Full CLI Production Operations remain missing_or_partial/unaccepted; Phase 12, worker enforcement, UI, Telegram, timers, daemons, Docker/systemd/conntrack mutation, customer/policy/abuse mutation, and unrestricted production remain blocked.

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
9. production generic real-customer activation (`production_generic_real_customer_activation`);
10. final acceptance that sets `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`.

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
production_generic_real_customer_activation: READY
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


## 0.1.253 verified binding/package evidence update

A source-backed 0.1.252 farm5 packet-path READY bundle may now be consumed by `mpf production verified-filter-hook-binding-plan` to bind the verified `DOCKER-USER` / `FORWARD` / `post_dnat_forward_filter` hook to explicit Phase 11 controlled artifact graph semantics. `mpf production controlled-artifact-reapply-package-plan` and `mpf production controlled-artifact-reapply-package-verify` generate and verify package evidence only. Execution remains blocked: `production_execution_available=false`, `iptables_restore_invocation_allowed=false`, `runtime_packet_observed=false`, `post_apply_runtime_verified=false`, `restart_autostart_proof=missing_or_partial`, `full_cli_production_operations=missing_or_partial`, and Phase 12/worker/UI/Telegram remain blocked.


## 0.1.256 Phase 11 live-ready controlled artifact reapply readiness package

- Adds `mpf production controlled-artifact-reapply-readiness --output json` and `scripts/phase11_controlled_artifact_reapply.sh --readiness` as an operator-reviewable live-ready readiness/package review surface only.
- This does not execute `iptables-restore`, does not apply firewall changes, does not call controlled artifact execute, and does not mutate DB, firewall, Docker, systemd, conntrack, customer, abuse, or policy state.
- `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`; production traffic and onboarding remain `controlled_cli_limited`.
- Phase 12, worker enforcement, UI, Telegram, timers, daemons, public backend/API, and unrestricted production remain closed.
- When readiness is READY, the next required step becomes `sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5`; otherwise it remains `prepare_live_ready_controlled_artifact_reapply_package`.


## 0.1.257 Phase 11 live-ready verified packet-path reapply package

This update creates a live-ready package/review artifact from the verified packet-path/filter-hook binding. It still does not execute `iptables-restore`, does not apply firewall changes, does not accept restart/autostart proof, and does not accept Full CLI Production Operations. Phase 12, worker enforcement, UI, Telegram, timers, daemons, public backend/API, and unrestricted production remain closed; production traffic and customer onboarding remain `controlled_cli_limited`.


## 0.1.266 Phase 11 controlled reapply audit dependency hardening

Farm5 0.1.265 moved past the prior structure-stable raw snapshot drift blockers: fresh packet-path evidence, live-ready package, and execute-preflight were READY. Guarded execute then failed safely before any `iptables-restore --test` or apply because operational audit metadata used direct local-peer PostgreSQL as root (`postgresql:///mpf`) and hit `role "root" does not exist`. A retry backup directory was already created with `iptables-save.txt`, `ip6tables-save.txt`, `package.json`, `payload.restore`, `rollback-plan.json`, and `manifest.sha256.json`, while `firewall_applies` remained unchanged. No restore test, apply, partial apply, rollback, or public exposure occurred; production gates stayed closed.

Next required step: harden audit metadata local-peer root writes, make backup attempts retry-safe, and expose stage-specific pre-apply dependency evidence before re-running farm5 controlled execute.

## Progress Update (0.1.278)

Adds controlled exact-scope DB-only lifecycle execution evidence for `limited-btc-001` / `btc` / `20101`. Valid verifier evidence advances production customer lifecycle execution item #2 by proving audit/event path availability and a linked backup/restore point requirement, while `backup_restore_drill`, final Full CLI Production Operations acceptance, `cli_production` traffic/onboarding, Phase 12, worker enforcement, UI, and Telegram remain closed.

### 0.1.282 Read-only firewall completion evidence bundle note

0.1.282 adds a standardized read-only Phase 11 firewall completion evidence bundle/preflight builder and verifier. It records manifest and SHA256SUMS evidence for backend target, read-only firewall snapshots, current controlled artifact gate, target-aware reapply diagnostics, and firewall completion readiness. This release performs no firewall apply, no `iptables-restore`, no rollback apply, no DB mutation, no Docker/systemd restart, no conntrack flush, no abuse execute, and no Phase 12 opening. Full CLI Production Operations remains not accepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`, and the next farm5 step is to sync 0.1.282, run the read-only firewall completion evidence collector, then run the operational surfaces collector with `MPF_FIREWALL_COMPLETION_EVIDENCE_DIR=<bundle-dir>` and verify only evidence/preflight moved forward while mutation and Phase 12 flags remain false.
