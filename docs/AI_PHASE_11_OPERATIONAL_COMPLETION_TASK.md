0.1.269 controlled post-apply semantic classification note: fixes the 0.1.268 post-apply verification mismatch by comparing official Phase 11 controlled artifacts with semantic/canonical forms for iptables-save normalizations (`-m tcp`, connlimit saddr, hashlimit rate/expiry) while preserving exact package payload hash behavior before apply. Farm5 is safe after the official rollback returned PASS_NO_CUSTOMER_ARTIFACTS; after sync, rerun read-only/package/preflight before any guarded execute. AI PR creation is hardened through scripts/create_runtime_first_pr.sh only.



0.1.268 controlled post-apply verification note: fixes the Phase 11 controlled artifact reapply verification chain by deriving/propagating `expected_backend_target` from the reviewed package backend target, normalizing live `iptables-save` colon chain declarations against restore-payload `-N` declarations, and verifying exact post-apply controlled artifacts without treating expected live MPF artifacts as unknown. Do not rerun the 0.1.267 execute path. After offline sync to farm5, run only read-only/package/preflight first; guarded execute is allowed only after 0.1.268 tests and fresh READY evidence.
0.1.267 controlled execute recovery note: farm5 0.1.266 proved guarded execute reached `iptables-restore --test --noflush` and `iptables-restore --noflush` with `apply_succeeded=true`, but post-apply verification failed closed because the current artifact gate used a narrower allowlist than the official controlled artifact taxonomy and did not carry the resolved backend target consistently. The immediate recovery used a manually reviewed exact-inverse rollback from the package rollback_plan; rollback test passed, rollback apply succeeded, and the post-rollback gate returned `PASS_NO_CUSTOMER_ARTIFACTS` with MPF/proxy doctors OK and production gates still closed. Before any new execute, taxonomy/gate/post-verify alignment and the reviewed exact-inverse rollback executor path are required.
0.1.265 controlled reapply execute structure-stable snapshot hash note: farm5 0.1.264 evidence showed backend identity drift was fixed (`canonical_backend_binding_identity_match=true`, hard/informational mismatches empty, and package placeholder metadata ignored), fresh packet-path evidence was READY, the live-ready package was READY, and execute-preflight was READY. Guarded execute then failed safely before mutation with `final_decision=FAILED_PRE_APPLY` due only to raw `execution_precondition_fingerprint_drift`, `iptables_snapshot_drift`, and `ip6tables_snapshot_drift`; `firewall_mutation_performed=false`, `iptables_restore_invoked=false`, `restore_test_invoked=false`, `apply_invoked=false`, `partial_apply_possible=false`, and `rollback_required=false`. The package/live backend target fingerprints matched, the live plan remained `CONTROLLED_ARTIFACT_REAPPLY_PACKAGE_READY`, and `live_plan_blockers=[]`. Current next_required_step: implement structure-stable firewall snapshot hashes for the controlled execute drift gate, then offline sync 0.1.265 to farm5, regenerate fresh packet-path evidence, build a READY live-ready package, pass execute-preflight, and run guarded execute only if real structure drift and all other hard safety checks remain clear. production_traffic and customer_onboarding_allowed remain controlled_cli_limited; restart_autostart_proof and Full CLI Production Operations remain missing_or_partial/unaccepted; Phase 12, worker enforcement, UI, Telegram, timers, daemons, direct Docker/systemd/conntrack mutation, customer/policy/abuse mutation, public backend exposure, and unrestricted production remain blocked.

0.1.264 controlled reapply execute placeholder metadata note: farm5 0.1.263 fresh packet-path evidence was READY, the live-ready package was READY, and execute-preflight was READY with blockers=[]. Guarded execute then failed safely before any restore test, apply, or firewall mutation with final_decision=FAILED_PRE_APPLY because canonical execute identity still treated package-bound placeholder backend metadata (`network_id=verified_packet_path_bundle`, `endpoint_id=verified_packet_path_endpoint`, `compose_project=None`, and `tcp_connect_ok=None`) as hard identity against real Docker runtime metadata. Version 0.1.264 ignores those known package placeholder metadata differences in canonical_backend_binding_identity_match while keeping them visible as informational diagnostics and preserving hard fail-closed checks for IP, port, container, running/health, public exposure, verified filter packet path, and controlled artifact graph binding mode. Current next_required_step: fix canonical execute identity to ignore package placeholder backend metadata while preserving hard safety identity checks, then offline sync 0.1.264 to farm5, regenerate fresh packet-path evidence, build a READY live-ready package, pass execute-preflight, and run guarded execute only if blockers=[]. production_traffic and customer_onboarding_allowed remain controlled_cli_limited; restart_autostart_proof and Full CLI Production Operations remain missing_or_partial/unaccepted; Phase 12, worker enforcement, UI, Telegram, timers, daemons, direct Docker/systemd/conntrack mutation, customer/policy/abuse mutation, public backend exposure, and unrestricted production remain blocked.

0.1.263 controlled reapply execute binding note: farm5 0.1.262 reached READY live-ready package and READY execute-preflight, then guarded execute failed pre-apply before any restore test or firewall mutation because execute-time backend binding/drift comparison treated raw backend fingerprint/source shape differences as broad drift and buried the root cause under secondary blockers. Version 0.1.263 canonicalizes execute-time backend binding identity comparison, preserves fail-closed behavior for real backend identity drift/public exposure/unhealthy backend/gate failures, and records compact FAILED_PRE_APPLY diagnostics. Current next_required_step: offline sync 0.1.263 to farm5, regenerate/review the live-ready controlled artifact reapply package if needed, run fresh execute-preflight, then run guarded controlled artifact reapply execute only if all gates remain READY and blockers=[]. production_traffic and customer_onboarding_allowed remain controlled_cli_limited; restart_autostart_proof and Full CLI Production Operations remain missing_or_partial/unaccepted; Phase 12, worker enforcement, UI, Telegram, timers, daemons, Docker/systemd/conntrack mutation, customer/policy/abuse mutation, and unrestricted production remain blocked.

## 0.1.263 current step: fix_execute_time_canonical_backend_binding_drift_contract

Farm5 0.1.262 reached READY live-ready package and READY execute-preflight, then guarded controlled artifact reapply execute failed pre-apply before restore-test/apply because execute-time backend binding drift detection used raw fingerprint/source shape too coarsely. Version 0.1.263 must fix that canonical binding/drift contract, keep real drift/public exposure/unhealthy backend fail-closed, and make the next_required_step: offline sync 0.1.263 to farm5, regenerate/review the live-ready package if needed, run fresh execute-preflight, then run guarded execute only if blockers=[]. Restart/autostart proof remains `missing_or_partial`; Full CLI Production Operations, Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

## 0.1.248 current step: implement_controlled_artifact_reapply_execute_package

Farm5 0.1.247 post-sync evidence showed healthy runtime containers/listeners and no Docker runtime repair requirement. Known controlled customer firewall artifacts are absent after reboot, so the active implementation step is the controlled artifact reapply execute package. Do not run Docker Compose, do not mutate firewall/DB/conntrack/systemd, and keep restart/autostart proof and Full CLI Production Operations unaccepted.

# AI Task — Phase 11 operational completion — Full CLI Production Operations


Phase 11 operational completion 0.1.246 note: farm5 0.1.245 post-reboot evidence discovered that runtime containers partially returned, `mpf-v2raya-socks-bridge` was missing from the expected runtime container set, and controlled Phase 11 firewall artifacts were absent after reboot. Restart/autostart proof remains blocked as `missing_or_partial` until the persistence gap is fixed; `next_required_step` remains `fix_restart_autostart_persistence_gap`.

Phase 11 operational completion 0.1.245 note: restart/autostart proof now has a real read-only service/CLI/helper surface, but remains missing_or_partial until farm5 source-backed restart/autostart evidence is collected; all other Full CLI Production Operations items remain missing_or_partial and Phase 12 remains blocked.

## 0.1.248 current step: implement_controlled_artifact_reapply_execute_package

This operational-completion step adds the controlled restart/autostart persistence fix plan/package, guarded plan-default helper, read-only controlled firewall artifact persistence plan, and post-fix evidence collector. It does not fake READY: restart/autostart proof remains `missing_or_partial` until source-backed farm5 post-fix evidence proves all expected containers, known controlled artifacts, empty `unknown_mpf_artifacts`, false public backend exposure, local-only listeners, and closed Phase 12/worker/UI/Telegram gates. Previous farm5 blockers were `unhealthy_container:mpf-v2raya-socks-bridge` and `post_reboot_known_controlled_phase11_artifacts_absent`. Full CLI Production Operations remains not accepted.

## Purpose

`Phase 11 operational completion — Full CLI Production Operations` is the active post-acceptance completion gate. This is not a new phase. Phase 11 remains accepted on farm5 for the controlled CLI-limited BTC production/customer boundary, and the current working phase remains under Phase 11 operational completion.

Phase 12 Worker Policy Enforcement is blocked until this gate is finally accepted. The purpose of this gate is to complete and prove CLI/service-layer production operations before worker enforcement work starts.

## Required Full CLI Production Operations Scope

The implementation sequence must complete and prove these controlled production CLI surfaces:

1. restart/autostart proof;
2. production customer lifecycle CLI execution;
3. production firewall plan/apply/verify/rollback for real customer ports;
4. production onboarding flow through CLI;
5. production usage/report/check evidence;
6. production abuse runner for all active customers in all enabled lanes;
7. pause/block/expire-run operational controls;
8. backup/restore drill;
9. final acceptance that sets `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`.

Each implementation PR must preserve service-layer architecture, conservative defaults, explicit operator gating, auditability, restore/lock/verify requirements where applicable, and fail-closed behavior.

## Explicitly Closed Boundaries

This completion gate does not authorize:

```text
worker enforcement
UI
Telegram
buyer panel
public API
public backend exposure
direct/ad-hoc DB or firewall mutation
firewall changes outside service-layer planner/apply/verify
abuse hard outside the official restore/backup/firewall/conntrack/audit path
unrestricted production/miner expansion
timers or daemon starts without a later explicit accepted gate
```

The current required implementation step after the 0.1.262 farm5 FAILED_PRE_APPLY evidence is `fix_execute_time_canonical_backend_binding_drift_contract`.

## Progress Update (0.1.239)

`implement_controlled_abuse_operational_core` is implemented as an operator-invoked service/repository/domain boundary with thin `mpf abuse` CLI commands. Hard/unhard remain controlled-package gated; firewall verification failure cannot set `hard_applied_at`. No timer, daemon, worker enforcement, UI, Telegram, or Phase 12 implementation is enabled.

## Progress Update (0.1.240)

The controlled PostgreSQL-backed abuse repository now connects `mpf abuse status`, `mpf abuse events`, and `mpf abuse run --dry-run` to real DB reads. Explicit operator-gated controlled execute may write only `abuse_states`, `abuse_events`, and `job_runs`; missing or stale evidence fails closed. Firewall hard/unhard execution remains blocked and `hard_applied_at` remains unset. No timer, daemon, worker enforcement, UI, Telegram, or Phase 12 implementation is enabled.

## Progress Update (0.1.241)

- Abuse DB-backed surface remains operational and now has regression coverage for local-peer psql row normalization.
- Controlled customer lifecycle CLI surface is now checked/proven as a Phase 11 operational completion surface.
- Restart/autostart proof now has an operator-runnable evidence surface but remains missing_or_partial until farm5 evidence is collected; usage/report/check and controlled firewall apply/rollback surfaces are present but not accepted as final operational completion.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## Progress Update (0.1.242)

- Controlled usage/report/check operational surface is now checked/proven as a Phase 11 operational completion surface.
- Abuse DB-backed surface remains ready.
- Customer lifecycle CLI surface remains ready.
- Restart/autostart proof now has an operator-runnable evidence surface but remains missing_or_partial until farm5 evidence is collected; controlled firewall apply/rollback remains outside final operational completion acceptance.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## Progress Update (0.1.243)

- Controlled firewall apply/rollback operational workflow surface is now checked/proven as a Phase 11 operational completion surface.
- Abuse DB-backed surface remains ready.
- Customer lifecycle CLI surface remains ready.
- Usage/report/check surface remains ready.
- Restart/autostart proof remains pending.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## Progress Update (0.1.244)

- The active Phase 11 operational completion scope is expanded to Full CLI Production Operations without creating a new phase.
- The remaining gap matrix now includes restart/autostart proof, production customer lifecycle execution, production firewall apply/verify/rollback, production onboarding, production usage/report/check evidence, production abuse runner, pause/block/expire-run controls, backup/restore drill, and final CLI production acceptance.
- Final acceptance must set `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`.
- Phase 12, worker enforcement, UI, Telegram, buyer panel, public API, public backend exposure, direct/ad-hoc mutation, and out-of-path abuse hard remain blocked.

## Progress Update (0.1.245)

- Restart/autostart proof now has a service-layer report, thin production CLI command, and read-only farm5 helper script.
- The proof remains fail-closed as `missing_or_partial` until source-backed farm5 evidence is collected after the operator workflow.
- All mutation flags remain false; no reboot, Docker/systemd restart, DB/firewall mutation, iptables-restore, conntrack flush, Phase 12, worker enforcement, UI, Telegram, public API, or unrestricted production is enabled.

## Progress Update (0.1.246)

- farm5 0.1.245 post-reboot evidence showed only partial runtime container return after reboot.
- `mpf-v2raya-socks-bridge` was missing from the expected runtime container set.
- Controlled Phase 11 firewall customer artifacts were absent after reboot while unknown MPF artifacts remained empty.
- Keep `restart_autostart_proof: missing_or_partial` and `next_required_step: sync_and_collect_controlled_filter_packet_path_evidence_on_farm5` until desired artifact semantics, production adapters, and source-backed evidence prove readiness.


0.1.251 controlled runtime-forward note: the source-backed controlled artifact renderer, schema-faithful metadata wiring, and production adapters are implemented, but the filter packet path remains fail-closed until source-backed farm5 evidence proves the correct hook for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`. No farm5 mutation was performed, no live `iptables-restore` was executed during PR development or CI, and no READY farm5 package has been collected. Progression is now `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`. The exact next step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; server sync is allowed only for read-only package/evidence collection first, and controlled execution requires separate package review. `restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

0.1.251 controlled filter packet-path evidence note: static packet-path collection and offline verification capability is implemented for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`; no farm5 packet-path evidence was collected by this PR, no runtime packet was observed, no hook was proven on farm5 during PR development, and no firewall, Docker, systemd, conntrack, PostgreSQL, customer, policy, block, pause, or abuse mutation occurred. Controlled artifact package generation remains blocked by `controlled_filter_packet_path_unresolved`; artifact graph binding and production execution remain unavailable; post-DNAT hook and match semantics require a future reviewed binding PR after a source-backed farm5 bundle. Current progression flags are `read_only_reapply_foundation_implemented=true`, `controlled_filter_packet_path_evidence_capability_implemented=true`, `controlled_filter_packet_path_evidence_ready=false`, `controlled_filter_packet_path_verified=false`, `artifact_graph_binding_ready=false`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`; `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`. The next required step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; a future READY bundle recommends `review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph`, not execution. `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.


## 0.1.253 verified binding/package evidence update

A source-backed 0.1.252 farm5 packet-path READY bundle may now be consumed by `mpf production verified-filter-hook-binding-plan` to bind the verified `DOCKER-USER` / `FORWARD` / `post_dnat_forward_filter` hook to explicit Phase 11 controlled artifact graph semantics. `mpf production controlled-artifact-reapply-package-plan` and `mpf production controlled-artifact-reapply-package-verify` generate and verify package evidence only. Execution remains blocked: `production_execution_available=false`, `iptables_restore_invocation_allowed=false`, `runtime_packet_observed=false`, `post_apply_runtime_verified=false`, `restart_autostart_proof=missing_or_partial`, `full_cli_production_operations=missing_or_partial`, and Phase 12/worker/UI/Telegram remain blocked.


## 0.1.266 Phase 11 controlled reapply audit dependency hardening

Farm5 0.1.265 moved past the prior structure-stable raw snapshot drift blockers: fresh packet-path evidence, live-ready package, and execute-preflight were READY. Guarded execute then failed safely before any `iptables-restore --test` or apply because operational audit metadata used direct local-peer PostgreSQL as root (`postgresql:///mpf`) and hit `role "root" does not exist`. A retry backup directory was already created with `iptables-save.txt`, `ip6tables-save.txt`, `package.json`, `payload.restore`, `rollback-plan.json`, and `manifest.sha256.json`, while `firewall_applies` remained unchanged. No restore test, apply, partial apply, rollback, or public exposure occurred; production gates stayed closed.

Next required step: harden audit metadata local-peer root writes, make backup attempts retry-safe, and expose stage-specific pre-apply dependency evidence before re-running farm5 controlled execute.
