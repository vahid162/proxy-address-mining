Phase 11 operational completion implementation note (0.1.240): added the controlled PostgreSQL-backed abuse repository for DB-backed status/events/dry-run and explicit operator-gated DB-only transition/event/job-run writes. Firewall hard/unhard execution remains blocked and `hard_applied_at` remains unset.
Phase 11 operational completion implementation note (0.1.239): added the first controlled abuse operational core and thin `mpf abuse` CLI surface. Hard/unhard remain controlled-package gated, no timer or daemon is enabled, and Phase 12 remains blocked.
Phase 11 planning/readiness note (0.1.233): records farm5 0.1.232 controlled boundary acceptance package READY evidence and adds read-only controlled boundary acceptance decision plus final Phase 11 acceptance PR readiness gates. Current State is unchanged; this does not mark Phase 11 accepted or authorize production/miner expansion, DB/firewall/runtime mutation, abuse automation, UI, or Telegram.

Phase 11 planning/readiness note (0.1.232): records farm5 0.1.231 limited acceptance decision READY evidence and adds a read-only controlled boundary acceptance package with source-backed runtime, abuse 1h, restart/container-order, artifact, exact-scope, and closed Current State preflight validation. Current State is unchanged; this does not authorize Phase 11 final acceptance, production/miner expansion, DB/firewall/runtime mutation, abuse automation, UI, or Telegram.

Phase 11 planning/readiness note (0.1.230): records farm5 0.1.229 limited activation observation/review READY evidence and adds a read-only limited customer observation window plus a read-only Phase 11 final-acceptance readiness planning report. Current State is unchanged; this does not authorize production/miner expansion, DB/firewall/runtime mutation, abuse automation, UI, Telegram, or Phase 11 final acceptance.

Phase 11 planning/readiness note (0.1.229): adds a read-only limited activation observation collector and a read-only limited activation acceptance review gate after the reported farm5 0.1.228 source-backed post-evidence READY context. Farm5 claims must be validated from supplied JSON artifacts and SHA-256 hashes. This PR does not execute activation, mutate DB/firewall/runtime, perform rollback, mark Phase 11 accepted, or open production/miner/abuse/UI/Telegram gates.

Phase 11 planning/readiness note (0.1.228): accepted nested source-backed DB/proxy health evidence and forwarded optional source evidence into post-evidence recollection without changing Current State or opening runtime gates.

Phase 11 planning/readiness note (0.1.227): fixes Phase11E limited activation execute preflight rollback-package scope validation after farm5 0.1.226 failed closed before mutation with rollback package scope mismatch; no activation is executed by this PR and all public/miner/abuse/UI/Telegram gates remain closed.

# PHASE STATUS

Phase 11 operational completion 0.1.252 note: 0.1.252 controlled filter packet-path evidence note: static packet-path collection and offline verification capability is implemented for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`; no farm5 packet-path evidence was collected by this PR, no runtime packet was observed, no hook was proven on farm5 during PR development, and no firewall, Docker, systemd, conntrack, PostgreSQL, customer, policy, block, pause, or abuse mutation occurred. Controlled artifact package generation remains blocked by `controlled_filter_packet_path_unresolved`; artifact graph binding and production execution remain unavailable; post-DNAT hook and match semantics require a future reviewed binding PR after a source-backed farm5 bundle. Current progression flags are `read_only_reapply_foundation_implemented=true`, `controlled_filter_packet_path_evidence_capability_implemented=true`, `controlled_filter_packet_path_evidence_ready=false`, `controlled_filter_packet_path_verified=false`, `artifact_graph_binding_ready=false`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`; `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`. The next required step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; a future READY bundle recommends `review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph`, not execution. `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

Phase 11 operational completion 0.1.248 note: farm5 0.1.247 post-sync evidence showed runtime container persistence healthy (`mpf-v2raya`, `mpf-v2raya-socks-bridge`, `mpf-forwarder-btc`) with local-only listeners on `127.0.0.1:2015` and `127.0.0.1:60010`, `unknown_mpf_artifacts=[]`, and no Docker runtime repair required. Known controlled customer firewall artifacts remain absent, restart/autostart proof remains `missing_or_partial`, Full CLI Production Operations is not accepted, and the next implementation step is `implement_controlled_artifact_reapply_execute_package`. Phase 12, worker enforcement, UI, and Telegram remain blocked.

Phase 11 operational completion 0.1.247 note: current step remains `fix_restart_autostart_persistence_gap`. This version adds a controlled restart/autostart repair plan, operator-reviewed Docker Compose recovery package, guarded helper, read-only controlled artifact persistence plan, and post-fix evidence collector. It does not mark restart/autostart proof READY without farm5 post-fix evidence. Previous farm5 blockers remain the source context: `unhealthy_container:mpf-v2raya-socks-bridge` and `post_reboot_known_controlled_phase11_artifacts_absent`; `unknown_mpf_artifacts` remained `[]`, public backend exposure remained false, Phase 12/worker enforcement/UI/Telegram remain blocked, and Full CLI Production Operations remains not accepted.

Phase 11 operational completion 0.1.246 note: farm5 0.1.245 post-reboot evidence discovered that runtime containers partially returned, `mpf-v2raya-socks-bridge` was missing from the expected runtime container set, and controlled Phase 11 firewall artifacts were absent after reboot. Restart/autostart proof remains blocked as `missing_or_partial` until the persistence gap is fixed; `next_required_step` remains `fix_restart_autostart_persistence_gap`.

Phase 11 operational completion 0.1.245 note: restart/autostart proof now has a real read-only service/CLI/helper surface, but remains missing_or_partial until farm5 source-backed restart/autostart evidence is collected; all other Full CLI Production Operations items remain missing_or_partial and Phase 12 remains blocked.


## 0.1.246 Phase 11 restart/autostart persistence blocker

- farm5 0.1.245 post-reboot evidence discovered that runtime containers partially returned after reboot.
- `mpf-v2raya-socks-bridge` was missing from the expected runtime container set.
- Known controlled Phase 11 firewall customer artifacts were absent after reboot, while unknown MPF artifacts remained empty.
- `restart_autostart_proof` remains `missing_or_partial`; `next_required_step` is now `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5` because version 0.1.252 implements the read-only static packet-path evidence capability but intentionally keeps evidence readiness, hook binding, desired artifact semantics, controlled package readiness, and production execution blocked until a source-backed farm5 bundle is collected and reviewed. This does not create a new phase and does not authorize Phase 12, timers/daemons, Docker/systemd restarts, DB/firewall mutation, iptables-restore, conntrack flush, worker enforcement, UI, Telegram, public API/backend exposure, or unrestricted production.

## 0.1.245 Phase 11 operational completion — Full CLI Production Operations Scope Update

- Active Phase 11 operational completion scope now requires Full CLI Production Operations before Phase 12 Worker Policy Enforcement.
- This is not a new phase; current working phase remains under `Phase 11 operational completion — Full CLI Production Operations`.
- Required acceptance matrix now includes restart/autostart proof, production customer lifecycle CLI execution, production firewall plan/apply/verify/rollback for real customer ports, production onboarding through CLI, production usage/report/check evidence, production abuse runner for all active customers in all enabled lanes, pause/block/expire-run controls, backup/restore drill, and final CLI production acceptance.
- Final acceptance must set `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`.
- Phase 12, worker enforcement, UI, Telegram, buyer panel, public API, public backend exposure, direct/ad-hoc mutation, firewall changes outside service-layer planner/apply/verify, and abuse hard outside the official restore/backup/firewall/conntrack/audit path remain blocked.

## 0.1.243 Phase 11 operational completion Progress Update

- Controlled firewall apply/rollback operational workflow surface is now checked/proven as a Phase 11 operational completion surface.
- Abuse DB-backed surface remains ready.
- Customer lifecycle CLI surface remains ready.
- Usage/report/check surface remains ready.
- Restart/autostart proof remains pending.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## 0.1.242 Phase 11 operational completion Progress Update

- Controlled usage/report/check operational surface is now checked/proven as a Phase 11 operational completion surface.
- Abuse DB-backed surface remains ready.
- Customer lifecycle CLI surface remains ready.
- Restart/autostart proof now has an operator-runnable evidence surface but remains missing_or_partial until farm5 evidence is collected; controlled firewall apply/rollback remains outside final operational completion acceptance.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## 0.1.241 Phase 11 operational completion Progress Update

- Abuse DB-backed surface remains operational and now has regression coverage for local-peer psql row normalization.
- Controlled customer lifecycle CLI surface is now checked/proven as a Phase 11 operational completion surface.
- Restart/autostart proof now has an operator-runnable evidence surface but remains missing_or_partial until farm5 evidence is collected; usage/report/check and controlled firewall apply/rollback surfaces are present but not accepted as final operational completion.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## 0.1.237 Phase 11 operational completion Entry Gate

Phase 11 remains accepted on farm5 for the controlled CLI-limited BTC production/customer boundary. The current working phase is now `Phase 11 operational completion`, a post-acceptance completion gate required before Phase 12 implementation. This does not roll back Phase 11 acceptance, claim full backend completion, or authorize worker enforcement, UI, Telegram, unrestricted expansion, direct DB/firewall/runtime mutation, timers, or daemon automation.

## 0.1.235 Phase 11 Controlled-Boundary Documentation Clarification

Clarifies current documentation after Phase 11 acceptance: controlled CLI/service-layer onboarding, controlled planner-driven firewall handling, and controlled abuse paths remain the only authorized Phase 11 boundary. Unrestricted expansion, direct/ad-hoc mutation, UI, Telegram, and worker enforcement remain closed. Runtime behavior and conservative configuration defaults are unchanged.

## 0.1.234 Phase 11 Final Acceptance Note

Phase 11 is accepted on farm5 for the controlled CLI-limited BTC production/customer boundary only. The next working phase is Phase 12 — Worker Policy Enforcement. UI, Telegram, worker enforcement, unrestricted production expansion, and unrestricted miner expansion remain closed. This acceptance changes authorization boundaries only; it does not perform DB, firewall, conntrack, Docker, or systemd mutation.


Phase 11 planning/readiness note (0.1.226): adds a gated limited-btc-001 activation execute path, rollback execute path, and post-activation evidence collector after farm5 0.1.225 generated READY decision/execution/rollback packages; this PR does not execute activation during development and does not open unrestricted production/miner/abuse/UI/Telegram gates.

Status: Active project control file

Phase 11 planning/readiness note (0.1.225): fixed Phase11E limited activation package CLI kwargs handling after farm5 0.1.224 sync/test passed but the package helper failed on duplicate config argument.

Phase 11 planning/readiness note (0.1.224): fixed controlled-order source evidence mapping into restart/container-order readiness and restored helper manifest.json generation after farm5 0.1.222 proved source evidence and abuse readiness READY but restart readiness BLOCKED on post_restart_or_controlled_order_test_performed.

Phase 11 planning/readiness note (0.1.222): fixed Phase11E readiness helper customer source handling and venv Python selection after farm5 0.1.221 helper execution reached real source collection and failed on CustomerList.rows.

Phase 11 planning/readiness note (0.1.221): materialized source-backed evidence bundle + artifact gate + abuse/restart readiness chain without opening activation gates.

Phase 11 planning/readiness note (0.1.220): added read-only abuse/restart evidence builders and helper evidence collection; gates remain closed.


Phase 11 planning/readiness note (0.1.219): added single-customer abuse 1h and restart/container-order readiness gates plus a non-activating limited acceptance precheck while recording 0.1.218 visibility evidence and keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.218): stabilized remaining Phase 6/8 expected-version assertions after visibility bundle version alignment while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.217): stabilized Phase 11 canary expected-version tests after visibility bundle version alignment while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.216): aligned single-customer visibility bundle expected-version handling and recorded 0.1.215 reclassified runtime/Stratum visibility evidence while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.215): fixed line-based conntrack ASSURED detection for real NAT tuple order in single-customer runtime evidence while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.214): aligned single-customer runtime-path evidence classifier with captured forwarder/bridge artifacts and added optional repeated conntrack capture while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.213): fixed Phase 11E runtime/Stratum evidence helper log capture and single-customer Stratum transcript expected-version drift while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.212): hardened external Stratum probe timeout handling to produce valid fail-closed transcript output instead of traceback while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.211): fixed current phase safety gate expected-version drift by deriving the artifact gate expected version from VERSION while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.210): added a stdlib-only external Stratum probe and timing-safe Phase 11E runtime/Stratum evidence helper workflow for limited-btc-001/20101 while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.209): added controlled artifact-aware current phase gate and fail-closed runtime/stratum evidence helper while keeping all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.208): added a fail-closed Phase 11E runbook for single-customer runtime + external Stratum evidence collection for limited-btc-001/20101 and kept all production/miner/activation gates closed.
Phase 11 planning/readiness note (0.1.207): recorded farm5 0.1.206 runtime-path BLOCKED evidence and added non-mutating runtime probe diagnostics for limited-btc-001 / 20101 while keeping production/miner/acceptance gates closed.
Phase 11 planning/readiness note (0.1.206): records farm5 0.1.205 post-apply evidence READY and adds read-only single-customer runtime path + Stratum transcript + visibility bundle evidence classifiers for limited-btc-001/20101 while all activation gates remain closed.
Phase 11 planning/readiness note (0.1.205): recorded farm5 0.1.204 controlled single-customer firewall/NAT apply execution evidence for limited-btc-001/20101 and added non-mutating post-apply evidence classifier while keeping global gates closed.
Phase 11 planning/readiness note (0.1.204): added controlled single-customer firewall apply execution package/execute path and recorded 0.1.203 apply-gate evidence while keeping global gates closed.
Phase 11 planning/readiness note (0.1.203): recorded farm5 0.1.202 sync/test and single-customer firewall/NAT plan gate evidence and added non-mutating single-customer firewall apply gate package while preserving closed apply/traffic gates.
Phase 11 planning/readiness note (0.1.202): isolated the Phase 11E single-customer staging create-failure test from real farm5 DB state after DB-only staging while preserving closed apply/traffic gates.

Phase 11 planning/readiness note (0.1.201): recorded farm5 0.1.200 single-customer DB-only staging evidence and added non-mutating single-customer firewall/NAT plan gate while preserving closed apply/traffic gates.

Phase 11 planning/readiness note (0.1.200): recorded farm5 0.1.199 limited-onboarding-execution-gate evidence and added controlled single-customer DB-only staging package while preserving closed firewall/NAT/production gates.

Phase 11 planning/readiness note (0.1.199): recorded farm5 0.1.198 limited-onboarding-gate readiness evidence and added non-mutating Phase 11E limited onboarding execution gate package.

Phase 11 planning/readiness note (0.1.198): recorded farm5 0.1.197 controlled canary acceptance decision evidence and added non-mutating Phase 11E limited onboarding gate/readiness command.

Phase 11 planning/readiness note (0.1.197): added non-mutating Phase 11D controlled canary acceptance decision gate (`mpf production canary-acceptance-decision`) for exact farm5 0.1.195 evidence-pack + archive sha/operator-confirmation validation; this does not change Current State gates and does not record farm5 execution evidence yet.

Phase 11 planning/readiness note (0.1.196): recorded farm5 0.1.195 live canary evidence-pack readiness (`docs/PHASE_11_FARM5_0_1_195_LIVE_CANARY_EVIDENCE_PACK.md`) confirming runtime-path/visibility/acceptance-review READY for exact controlled canary scope while preserving closed production/onboarding/apply gates and non-mutating flags.

Phase 11 planning/readiness note (0.1.195): canary runtime-path evidence now supports NAT-aware conntrack proof and multiline forwarder local ephemeral port correlation for source-backed canary runtime classification; this does not change Current State gates or authorize production/onboarding/apply.

This file is the authoritative phase gate for humans and AI coding agents. It must be checked before changing code, scripts, deployment files, services, jobs, tests, migrations, or documentation.

0.1.254 verifier compatibility note: source-backed 0.1.252 packet-path bundles may now be verified by the 0.1.254 runtime without requiring bundle repository_version fields to equal the runtime version. File/hash/schema/topology/scenario/command/secret/mutation checks remain strict; tampered bundles fail closed and legacy 0.1.251 bundles still require recollection. Execution remains blocked: production_execution_available=false, iptables_restore_invocation_allowed=false, controlled_artifact_execute_available=false, live_ready_package_available=false, phase12_start_allowed=no, worker_enforcement_allowed=no, ui_allowed=no, telegram_allowed=no, full_cli_production_operations=missing_or_partial, and restart_autostart_proof=missing_or_partial.


0.1.259 live-ready reapply preflight integrity note: live-ready controlled artifact reapply packages now use the same stable canonical package SHA contract in generation and executor preflight. The canonical package SHA excludes `package_sha256`, `__package_file_sha256`, and executor-injected transient runtime fields while retaining payload/content tamper detection and keeping file SHA validation separate. This aligns executor preflight only; it does not execute controlled artifact reapply, authorize `iptables-restore`, firewall mutation, DB mutation, runtime mutation, Phase 12, worker enforcement, UI, Telegram, timers, daemons, unrestricted production, or unrestricted miner expansion. Current gates remain `production_traffic=controlled_cli_limited`, `customer_onboarding_allowed=controlled_cli_limited`, `controlled_artifact_execute_available=false`, `iptables_restore_invocation_allowed=false`, and all mutation flags false.

## Current State

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



0.1.253 verified artifact graph binding note: controlled_filter_packet_path_evidence_ready=true and controlled_filter_packet_path_verified=true for the sanitized farm5 0.1.252 source-backed READY packet-path proof. The repository now has an explicit `verified_docker_user_forward_post_dnat` binding path with artifact_graph_binding_ready=true and desired_artifact_semantics_complete=true in tests, plus non-executing controlled_artifact_reapply_package_evidence_ready=true (template/evidence-only, not live-ready) only for generated-and-verified package evidence. Execution remains blocked: production_execution_available=false, live_ready_package_available=false/package-template/evidence-only, runtime_packet_observed=false, post_apply_runtime_verified=false, restart_autostart_proof=missing_or_partial, full_cli_production_operations=missing_or_partial, phase12_start_allowed=no, worker_enforcement_allowed=no, ui_allowed=no, and telegram_allowed=no. This does not accept Full CLI Production Operations, does not change production_traffic or customer_onboarding_allowed, and does not execute iptables-restore or any live package. See docs/PHASE_11_FARM5_0_1_252_FILTER_PACKET_PATH_READY_EVIDENCE.md.

0.1.252 packet-path topology proof note: source-backed bridge derivation, exact backend membership correlation, scenario-level NEW/ESTABLISHED traversal, source-aware policy routing, backend provenance, and schema-versioned verifier compatibility are implemented as read-only evidence semantics only. Legacy 0.1.251 bundles require recollection and must not be marked READY. controlled_filter_packet_path_evidence_ready=false, controlled_filter_packet_path_verified=false, artifact_graph_binding_ready=false, current_renderer_binding_compatible=false, desired_artifact_semantics_complete=false, production_execution_available=false, live_ready_package_available=false, runtime_packet_observed=false, and post_apply_runtime_verified=false remain unchanged. The next required operator step is a new 0.1.252 sync and read-only recollection on farm5.



Phase 9 is accepted only as Check / Report / Diagnostics evidence/readiness on farm5. This acceptance does not authorize production traffic, firewall apply, customer NAT/customer firewall rules, abuse automation runner, scheduler/timer, production DB execution, hard/soft block automation, pause automation, UI, Telegram, or production customer onboarding.

The `Current State` block above is the current gate. Historical compatibility notes and accepted evidence are informational only.

### Phase 10 final acceptance evidence summary

- farm5 0.1.136 sync/test evidence recorded (`docs/PHASE_10_FARM5_0_1_136_SYNC_TEST_EVIDENCE.md`)
- final-acceptance-readiness: ACCEPTED
- final-acceptance: ACCEPTED
- production activation remains disabled
- Phase 11 is planning/readiness only


Apply Slice 1 and Slice 2 are server-synced and accepted only as documentation/test-only readiness boundaries. Apply Slice 3 and Slice 4 are server-synced and accepted only as documentation/test-only boundaries. No-customer runtime execution approval readiness is done. Controlled no-customer runtime execution evidence package is done and farm5 synced at 0.1.95. Manual canary customer proposal + acceptance readiness is done and farm5 synced at 0.1.96. Phase 6 operator acceptance decision is completed and accepted after farm5 0.1.100 sync evidence. Phase 7 is now accepted only as report-only/service-contract/readiness after farm5 0.1.108 evidence and later farm5 0.1.110 sync evidence. Historical note: at that time, current working phase was Phase 8 Abuse 1h Core planning/readiness only; runtime gates remain closed and non-authorizing. Current farm5 has no non-deleted customers. Historical proposal reference: `docs/PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md`. The explicitly gated read-only `iptables-save` live snapshot path remains authorized (`live_snapshot_read_allowed: iptables_save_read_only`). No apply, restore, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, Phase 8 abuse runner, hard/soft blocks, pause automation, UI, or Telegram is authorized.

## Accepted Server Results

- Phase 11 farm5 0.1.190 planning/readiness note: preserved partial source-backed canary runtime path evidence booleans (conntrack/forwarder/bridge) per independent classifier results while keeping final decision fail-closed BLOCKED until all required runtime evidence is present; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.190 planning/readiness note: added source-backed read-only runtime path evidence classifiers for conntrack_assured/forwarder_pool_seen/bridge_loopback_seen with allowlist hardening; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.187 planning/readiness note: added read-only source-backed canary abuse coverage visibility evidence and hardened external transcript import collect-live canary DB validation to use exact-scope customer_read_service checks; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.186 planning/readiness note: added source-backed external Stratum transcript import for canary worker visibility evidence (to handle farm5 self/public-IP hairpin limitation) and integrated it into visibility bundle/acceptance review without opening any runtime gate; Current State remains unchanged and Phase 11 remains not accepted.
### Phase 11 farm5 0.1.147 Sync/Test Evidence

- Phase 11D manual canary customer acceptance package evidence recorded (`docs/PHASE_11_FARM5_0_1_147_SYNC_TEST_EVIDENCE.md`).
- Phase 11 farm5 0.1.149 Sync/Test Evidence recorded (`docs/PHASE_11_FARM5_0_1_149_SYNC_TEST_EVIDENCE.md`): Phase 11D execution gate farm5 evidence recorded; Phase 11D actual execution not authorized; production traffic none; firewall apply no; customer onboarding db_only; abuse automation no; UI no; Telegram no.
- Phase 11 farm5 0.1.151 Sync/Test Evidence recorded (`docs/PHASE_11_FARM5_0_1_151_SYNC_TEST_EVIDENCE.md`): Phase 11D operator-reviewed execution run preparation farm5 evidence recorded; Phase 11D actual execution not authorized; production traffic none; firewall apply no; customer onboarding db_only; abuse automation no; UI no; Telegram no.
- Phase 11 farm5 0.1.153 Sync/Test Evidence recorded (`docs/PHASE_11_FARM5_0_1_153_SYNC_TEST_EVIDENCE.md`): actual operator-approved manual canary execution run package farm5 sync/test evidence recorded; actual canary execution not performed; actual canary execution not accepted; production traffic none; firewall apply no except future explicit single-canary operator-approved run path; customer onboarding db_only except future explicit canary run path; abuse automation no; UI no; Telegram no.
- Phase 11 farm5 0.1.159 Sync/Test Evidence recorded (`docs/PHASE_11_FARM5_0_1_159_SYNC_TEST_EVIDENCE.md`): sync/test evidence accepted; restore/backup boundary exercised successfully; execution remained blocked on `accepted_exact_canary_restore_payload_renderer` before this PR; no actual canary execution; production traffic none; firewall apply no; customer onboarding db_only; abuse automation no; UI no; Telegram no.
- Phase 11 farm5 0.1.161 Sync/Test/Execute-control Evidence recorded (`docs/PHASE_11_FARM5_0_1_161_SYNC_TEST_EVIDENCE.md`): sync/test OK on 2026-05-21, execute-control checks stayed blocked/non-mutating, actual canary execution not performed, Phase 11 remains not accepted, production traffic none, firewall apply no, onboarding db_only, abuse automation no, UI no, Telegram no.
- Phase 11 farm5 0.1.162 Sync/Test Evidence recorded (`docs/PHASE_11_FARM5_0_1_162_SYNC_TEST_EVIDENCE.md`): synced/tested safely; blocker remained `single_canary_restore_payload_not_apply_safe`; no actual canary execution; current state unchanged.
- Route-safe canary target evidence recorded (`docs/PHASE_11_ROUTE_SAFE_CANARY_TARGET_EVIDENCE.md`): 0.1.163 loopback DNAT target (`127.0.0.1:60010`) was structurally applied but external canary timed out; MPF_NAT_PRE counters increased; diagnosis confirms loopback target is not route-safe for external PREROUTING DNAT while route_localnet=0; Phase 11 remains not accepted.
- Route-safe single-canary NAT success evidence recorded (`docs/PHASE_11_ROUTE_SAFE_CANARY_NAT_SUCCESS_EVIDENCE.md`): farm5 0.1.164 execution reached `EXECUTION_COMPLETED_PENDING_REVIEW` with external TCP success and ASSURED conntrack; evidence is controlled and pending review; Current State remains unchanged (production_traffic none, Phase 11 not accepted, onboarding db_only, abuse automation no, UI no, Telegram no).
- v2rayA SOCKS reachability blocker evidence recorded (`docs/PHASE_11_V2RAYA_SOCKS_REACHABILITY_BLOCKER.md`): route-safe NAT path reached forwarder but forwarder->v2rayA upstream `mpf-v2raya:22070` was refused; readiness fix standardizes Docker-reachable SOCKS upstream; Current State remains unchanged and Phase 11 remains unaccepted.
- Synthetic Stratum canary success evidence recorded (`docs/PHASE_11_SYNTHETIC_STRATUM_CANARY_SUCCESS_EVIDENCE.md`): farm5 0.1.167 sync baseline confirmed (`pytest: 870 passed`, doctor/db/proxy doctor OK), Windows synthetic Stratum subscribe/authorize succeeded via `85.198.11.110:20001`, notifications (`mining.set_difficulty`, `mining.notify`) were received, NAT counter/conntrack ASSURED/forwarder/pool/bridge evidence captured, and Current State remains unchanged (Phase 11 not accepted, production traffic none, onboarding db_only, abuse automation no, UI no, Telegram no).
- Phase 11D execution not authorized.
- production_traffic: none
- firewall_apply_allowed: no
- customer_onboarding_allowed: db_only
- abuse_automation_allowed: no
- ui_allowed: no
- telegram_allowed: no


- Phase 11 farm5 0.1.169 planning/readiness note: added read-only `mpf production canary-acceptance-review` verifier to classify exact controlled canary NAT artifact (`controlled_canary_artifact_present`) and fail-closed on any additional MPF/customer references or missing visibility primitives; Current State gate values remain unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.170 hotfix note: fixed `mpf production canary-acceptance-review` customer list contract to use `CustomerList.customers` (not `rows`) and added fail-closed blocker `customer_list_read_failed` when customer list read fails; Current State gate values remain unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.171 planning/readiness note: added read-only live canary evidence collector and `--collect-live` acceptance-review path to classify the exact controlled single-canary NAT artifact from live read-only sources; Current State gate values remain unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.172 hotfix note: normalized live canary proxy evidence status mapping to accept canonical uppercase `HealthStatus` values (`OK`/`WARN`/`CRITICAL`) so `--collect-live` proxy evidence fields match proxy doctor verdicts; NAT parsing path remains unchanged and read-only; Current State gate values remain unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.178 planning/readiness note: added read-only `mpf production canary-usage-visibility` source-backed usage classification plus canary visibility/acceptance-review next-required-step priority fix to classify exact-scope canary visibility primitives (customer-db/usage/reject/session/IP/worker/abuse/check/rollback) as PRESENT/MISSING/BLOCKED without opening any runtime gate; Current State gate values remain unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.179 planning/readiness note: added read-only `mpf production canary-reject-session-ip-evidence-capture` exact-scope evidence capture path for reject/session/unique-IP visibility primitives with fail-closed scope checks and no runtime-gate opening; Current State gate values remain unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.180 hotfix planning/readiness note: merged multiple source-backed canary visibility evidence artifacts for `canary-visibility-bundle` / `canary-acceptance-review` so usage/session/IP evidence primitives are preserved across repeated evidence JSON inputs without fake-ready reject visibility; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.181 planning/readiness note: added read-only canary reject counters visibility capture (`mpf production canary-reject-counters-visibility`) with exact canary-scoped source requirement and evidence JSON merge compatibility; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.182 planning/readiness note: extended exact controlled single-canary restore payload scope to include canary-only filter reject counter source (`MPFC_20001` with `mpf:canary-btc-001:customer_connlimit_reject` and `mpf:canary-btc-001:customer_hashlimit_reject`) so reject visibility stays fail-closed and becomes PRESENT only with exact source-backed counters; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.183 hotfix planning/readiness note: populated read-only `live_nat_prerequisites` during controlled single-canary execute path before exact restore payload rendering when NAT hook prerequisites already exist, preserving fail-closed bootstrap-required behavior when hook is missing; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.185 hotfix planning/readiness note: exact single-canary restore payload rendering is idempotent when the controlled canary NAT rule already exists by emitting filter-only source (`MPFC_20001` connlimit/hashlimit reject rules) and avoiding duplicate NAT append; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.185 corrective planning/readiness note: 0.1.185 introduced canary worker/Stratum evidence capture, but farm5 self/public-IP capture can remain blocked by host hairpin/self-connect behavior; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.186 planning/readiness note: added external canary Stratum transcript import to convert proven external transcript evidence into source-backed machine-readable visibility evidence without opening runtime gates; Current State remains unchanged and Phase 11 remains not accepted.

### Phase 10 farm5 0.1.128 Sync/Test Evidence

- command:
  sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
- backup:
  /var/backups/mpf/source-before-zip-sync-20260517T091747Z
- server version after sync:
  0.1.128
- pytest:
  759 passed
- mpf doctor:
  OK
- current phase gate:
  OK
- phase9 final-acceptance:
  ACCEPTED
- current_accepted_phase:
  Phase 9 — Check / Report / Diagnostics accepted on farm5
- current_working_phase:
  Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness
- production_traffic:
  none
- firewall_apply_allowed:
  no
- abuse_automation_allowed:
  no
- customer_onboarding_allowed:
  db_only
- proxy_data_plane_allowed:
  limited_runtime_local_only
- ui_allowed:
  no
- telegram_allowed:
  no
- apply_mode:
  plan_only
- proxy.runtime_activation_allowed:
  false
- local-only listeners:
  127.0.0.1:2015
  127.0.0.1:60010
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- no customer NAT redirects
- Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is informational only
- final sync verdict:
  OK
- all dangerous authorization flags:
  false



### Phase 9 farm5 0.1.127 Sync/Test Evidence

- command:
  sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
- backup:
  /var/backups/mpf/source-before-zip-sync-20260517T080103Z
- server version after sync:
  0.1.127
- pytest:
  754 passed
- mpf doctor:
  OK
- current phase gate:
  OK
- phase8 final-acceptance:
  ACCEPTED
- phase9 readiness:
  ACCEPTED
- phase9 final-verdict:
  ACCEPTED
- phase9 diagnostics:
  ACCEPTED
- phase9 final-acceptance-readiness:
  ACCEPTED
- production_traffic:
  none
- firewall_apply_allowed:
  no
- abuse_automation_allowed:
  no
- customer_onboarding_allowed:
  db_only
- proxy_data_plane_allowed:
  limited_runtime_local_only
- ui_allowed:
  no
- telegram_allowed:
  no
- apply_mode:
  plan_only
- proxy.runtime_activation_allowed:
  false
- local-only listeners:
  127.0.0.1:2015
  127.0.0.1:60010
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- no customer NAT redirects
- Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is informational only
- final sync verdict:
  OK
- all dangerous authorization flags:
  false

### Phase 9 farm5 0.1.126 Sync/Test Evidence

- command:
  sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
- backup:
  /var/backups/mpf/source-before-zip-sync-20260517T072147Z
- server version after sync:
  0.1.126
- pytest:
  750 passed
- mpf doctor:
  OK
- current phase gate:
  OK
- phase8 final-acceptance:
  ACCEPTED
- phase9 readiness:
  ACCEPTED
- phase9 final-verdict:
  ACCEPTED
- phase9 diagnostics:
  ACCEPTED
- production_traffic:
  none
- firewall_apply_allowed:
  no
- abuse_automation_allowed:
  no
- customer_onboarding_allowed:
  db_only
- proxy_data_plane_allowed:
  limited_runtime_local_only
- ui_allowed:
  no
- telegram_allowed:
  no
- apply_mode:
  plan_only
- proxy.runtime_activation_allowed:
  false
- local-only listeners:
  127.0.0.1:2015
  127.0.0.1:60010
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- no customer NAT redirects
- Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is informational only
- final sync verdict:
  OK
- all dangerous authorization flags:
  false

### Phase 9 farm5 0.1.124 Sync/Test Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T183009Z
server version after sync: 0.1.124
synced to 0.1.124
pytest: 743 passed
mpf doctor: OK
phase gate: OK
phase8 final-acceptance: ACCEPTED
phase9 readiness: ACCEPTED / report-only
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
listeners local-only: 127.0.0.1:2015, 127.0.0.1:60010
no customer NAT redirects
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
all dangerous authorization flags remain false
final sync verdict: OK
```

This 0.1.124 farm5 sync/test evidence confirms the Phase 9 report-only diagnostics boundary remains non-mutating, non-authorizing, and safety-gated.

### Phase 9 farm5 0.1.123 Sync/Test Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T175047Z
server version after sync: 0.1.123
synced to 0.1.123
pytest: 742 passed
mpf doctor: OK
phase gate: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
listeners local-only: 127.0.0.1:2015, 127.0.0.1:60010
no customer NAT redirects
no MPF/customer firewall references
final sync verdict: OK
```

Final-acceptance-readiness output summary (`mpf phase8 final-acceptance-readiness --output json`):
- final_decision: BLOCKED
- execution_allowed: false
- phase8_acceptance_allowed: false

This sync/test evidence confirms report/docs alignment inputs for Phase 8 final acceptance while keeping all runtime/dangerous authorization flags false.


### Phase 8 farm5 0.1.122 Final Acceptance Readiness Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T165213Z
server version after sync: 0.1.122
synced to 0.1.122
pytest: 745 passed in 91.57s
OK: GitHub main zip synced successfully.
OK: server source is aligned with GitHub zip.
OK: accepted current phase gate is installed and verified.
OK: Runtime remains limited local-only; production customer traffic is still disabled.
current_accepted_phase before this PR: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5
current_working_phase before this PR: Phase 8 — Abuse 1h Core planning/readiness
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
MPF doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
customer list: no non-deleted customers
btc enabled=True backend_port=60010 chain_prefix=MPFBTC protocol=stratum source=db
ltc enabled=False backend_port=60020 chain_prefix=MPFLTC protocol=stratum source=db
zec enabled=False backend_port=60015 chain_prefix=MPFZEC protocol=stratum source=db
proxy_config final_verdict: OK
proxy_status final_verdict: OK
proxy final_verdict: OK
proxy.runtime_activation_allowed remains disabled
v2rayA UI listener is local-only
BTC backend listener is local-only
no_customer_nat_redirects: OK
firewall_apply_mode_plan_only: OK
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational in accepted limited runtime
accepted limited runtime listeners are local-only
current Phase 7 accepted / Phase 8 working safety gate passed before this PR
production customer traffic remains disabled
final sync verdict: OK
```

Final-acceptance-readiness output summary (`mpf phase8 final-acceptance-readiness --output json`):
- component: phase8_final_acceptance_readiness
- phase: Phase 8 — Abuse 1h Core
- gate_type: final_acceptance_readiness_review
- final_decision: BLOCKED
- readiness_status: READY_FOR_OPERATOR_REVIEW_NOT_ACCEPTED
- authorization_status: PHASE8_FINAL_ACCEPTANCE_NOT_AUTHORIZED
- inspection_only: true
- report_only: true
- execution_allowed: false
- phase8_acceptance_allowed: false
- phase8_accepted_by_this_pr: false
- repository_version: 0.1.122
- latest_recorded_farm5_sync_evidence: 0.1.121
- farm5_0_1_121_sync_evidence_present: true
- farm5_controlled_worker_dry_run_evidence_present: true
- blockers: []
- warnings: []
- errors: []

This 0.1.122 farm5 sync evidence is the final pre-acceptance evidence required for Phase 8 Abuse 1h Core acceptance.

This PR accepts Phase 8, but does not authorize production traffic, firewall apply, iptables-restore, customer NAT/customer firewall rules, abuse automation runner, background worker, scheduler/timer, real production customer evaluation, production DB execution, hard/soft block automation, pause automation, UI, Telegram, or production customer onboarding.


### Phase 8 farm5 0.1.121 Dry-Run Evidence Collection Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T155638Z
server version after sync: 0.1.121
synced to 0.1.121
pytest: 743 passed in 84.63s
OK: GitHub main zip synced successfully.
OK: server source is aligned with GitHub zip.
OK: accepted current phase gate is installed and verified.
OK: Runtime remains limited local-only; production customer traffic is still disabled.
current_accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5
current_working_phase: Phase 8 — Abuse 1h Core planning/readiness
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
MPF doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
customer list: no non-deleted customers
btc enabled=True backend_port=60010 chain_prefix=MPFBTC protocol=stratum source=db
ltc enabled=False backend_port=60020 chain_prefix=MPFLTC protocol=stratum source=db
zec enabled=False backend_port=60015 chain_prefix=MPFZEC protocol=stratum source=db
proxy_config final_verdict: OK
proxy_status final_verdict: OK
proxy final_verdict: OK
proxy.runtime_activation_allowed remains disabled
v2rayA UI listener is local-only
BTC backend listener is local-only
no_customer_nat_redirects: OK
firewall_apply_mode_plan_only: OK
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational in accepted limited runtime
accepted limited runtime listeners are local-only
current Phase 7 accepted / Phase 8 working safety gate passed
production customer traffic remains disabled
final sync verdict: OK
```

This 0.1.121 farm5 sync evidence confirms the dry-run evidence collection preparation package is synced and tested on farm5.

This evidence does not accept Phase 8.
It does not authorize background worker start.
It does not authorize scheduler/timer.
It does not authorize abuse runner.
It does not authorize real production customer evaluation.
It does not authorize production DB execution.
It does not authorize DB writes for abuse runtime.
It does not authorize firewall apply.
It does not authorize iptables-restore.
It does not authorize customer NAT/customer firewall rules.
It does not authorize hard/soft blocks.
It does not authorize pause automation.
It does not authorize UI or Telegram.
It does not authorize production traffic.

### Phase 8 farm5 Controlled Worker Dry-Run Evidence

Commands executed:
- mpf phase8 controlled-worker-dry-run --output json
- mpf phase8 controlled-worker-dry-run --operator-confirmed --output json
- mpf phase8 controlled-worker-dry-run-gate --output json
- mpf phase8 controlled-worker-pre-acceptance --output json
- mpf phase-status
- mpf doctor

Default controlled worker dry-run command summary includes: final_decision: BLOCKED, dry_run_status: CONTROLLED_WORKER_DRY_RUN_SYNTHETIC_ONLY, execution_allowed: false, production_side_effects_allowed: false, phase8_acceptance_allowed: false, repository_version: 0.1.121, latest_recorded_farm5_sync_evidence: 0.1.120, farm5_0_1_120_sync_evidence_present: true, farm5_0_1_121_sync_required_before_farm5_dry_run_evidence: true, operator_confirmed: false, synthetic_item_count: 11, synthetic_scenarios_passed: true, all_items_have_no_side_effects: true, blockers: [fresh_farm5_sync_test_required_before_evidence_collection, operator_confirmation_required].

Operator-confirmed controlled worker dry-run command summary includes: final_decision: BLOCKED, dry_run_status: CONTROLLED_WORKER_DRY_RUN_SYNTHETIC_ONLY, execution_allowed: false, production_side_effects_allowed: false, phase8_acceptance_allowed: false, repository_version: 0.1.121, latest_recorded_farm5_sync_evidence: 0.1.120, farm5_0_1_120_sync_evidence_present: true, farm5_0_1_121_sync_required_before_farm5_dry_run_evidence: true, operator_confirmed: true, synthetic_item_count: 11, synthetic_scenarios_passed: true, all_items_have_no_side_effects: true, blockers: [fresh_farm5_sync_test_required_before_evidence_collection].

The fresh_farm5_sync_test_required_before_evidence_collection blocker appears because the report surface still reads latest recorded farm5 sync evidence from docs as 0.1.120 at the time of execution. This PR records the real 0.1.121 sync evidence and must update the report expectation accordingly. This blocker is a documentation/evidence recording blocker, not a runtime side effect.

Synthetic scenarios observed: no_work, lock_contention, normal_stays_normal, over_tracking_observed_but_no_hard, over_grace_observed_but_no_hard, hard_candidate_reported_but_not_applied, stale_evidence_skipped, missing_evidence_skipped, db_failure_reported_no_write, firewall_failure_reported_no_mutation, idempotency_duplicate_skipped.

All synthetic items had would_write_db: false, would_mutate_firewall: false, would_mutate_customer: false, would_touch_production_traffic: false.

Controlled worker dry-run gate output summary includes: component: phase8_controlled_worker_dry_run_gate, final_decision: BLOCKED, execution_allowed: false, phase8_acceptance_allowed: false, runtime_worker_authorized: false, worker_start_authorized: false, scheduler_authorized: false, timer_authorized: false, abuse_runner_authorized: false, real_customer_evaluation_authorized: false, production_db_execution_authorized: false, db_reads_authorized: false, db_writes_authorized: false, firewall_apply_authorized: false, iptables_restore_authorized: false, customer_nat_authorized: false, customer_firewall_rules_authorized: false, hard_block_authorized: false, soft_block_authorized: false, pause_automation_authorized: false, production_traffic_authorized: false, blockers: [].

This controlled worker dry-run evidence does not accept Phase 8.
It does not authorize runtime automation.
It does not authorize production traffic.
It does not authorize DB writes.
It does not authorize firewall apply.
It does not authorize customer mutation.
It does not authorize hard/soft block.
It does not authorize pause automation.
It is synthetic/report-only evidence only.
### Phase 8 farm5 0.1.120 Operator Dry-Run Package Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup_path: /var/backups/mpf/source-before-zip-sync-20260516T134158Z
server version after sync: 0.1.120
synced to 0.1.120
pytest: 741 passed in 85.74s
mpf doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
customer list: no non-deleted customers
phase status: Phase 7 accepted / Phase 8 working
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
runtime remains limited local-only
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is accepted limited-runtime informational only
accepted limited runtime listeners are local-only
current phase safety gate: OK
final sync verdict: OK
```

This 0.1.120 farm5 sync evidence confirms the operator-invoked controlled worker dry-run package is synced and tested on farm5.

This evidence does not accept Phase 8.
It does not claim controlled worker dry-run evidence has been collected.
It does not authorize background worker start.
It does not authorize scheduler/timer.
It does not authorize abuse runner.
It does not authorize real production customer evaluation.
It does not authorize production DB execution.
It does not authorize DB writes for abuse runtime.
It does not authorize firewall apply.
It does not authorize iptables-restore.
It does not authorize customer NAT/customer firewall rules.
It does not authorize hard/soft blocks.
It does not authorize pause automation.
It does not authorize UI or Telegram.
It does not authorize production traffic.


### Phase 8 farm5 0.1.119 Controlled Worker Gate Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T130517Z
server version after sync: 0.1.119
synced to 0.1.119
pytest: 741 passed in 85.21s
mpf doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
customer list: no non-deleted customers
phase status: Phase 7 accepted / Phase 8 working
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
runtime remains limited local-only
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is accepted limited-runtime informational only
accepted limited runtime listeners are local-only
current phase safety gate: OK
final sync verdict: OK
```

This 0.1.119 farm5 sync evidence confirms the controlled worker dry-run gate preparation package is synced and tested on farm5.

This evidence does not accept Phase 8.
It does not authorize background worker start.
It does not authorize scheduler/timer.
It does not authorize abuse runner.
It does not authorize real production customer evaluation.
It does not authorize production DB execution.
It does not authorize DB writes for abuse runtime.
It does not authorize firewall apply.
It does not authorize iptables-restore.
It does not authorize customer NAT/customer firewall rules.
It does not authorize hard/soft blocks.
It does not authorize pause automation.
It does not authorize UI or Telegram.
It does not authorize production traffic.


### Phase 8 farm5 0.1.118 Batched Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T121320Z
server version after sync: 0.1.118
synced to 0.1.118
pytest: 738 passed in 73.43s
mpf doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
customer list: no non-deleted customers
phase status: Phase 7 accepted / Phase 8 working
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
runtime remains limited local-only
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is accepted limited-runtime informational only
accepted limited runtime listeners are local-only
current phase safety gate: OK
final sync verdict: OK
```

This 0.1.118 farm5 batched sync evidence covers the report-only/readiness-only packages introduced in:
- 0.1.116 — Phase 8 runtime/worker integration readiness
- 0.1.117 — Phase 8 runtime worker dry-run harness
- 0.1.118 — Phase 8 controlled worker pre-acceptance

This evidence does not accept Phase 8.
It does not authorize worker start.
It does not authorize scheduler/timer.
It does not authorize abuse runner.
It does not authorize real customer evaluation.
It does not authorize production DB execution.
It does not authorize DB writes for abuse runtime.
It does not authorize firewall apply.
It does not authorize iptables-restore.
It does not authorize customer NAT/customer firewall rules.
It does not authorize hard/soft blocks.
It does not authorize pause automation.
It does not authorize UI or Telegram.
It does not authorize production traffic.



### Phase 8 farm5 0.1.115 DB-Only Execution Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T093152Z
server version after sync: 0.1.115
synced to 0.1.115
pytest during sync: 725 passed in 69.14s
mpf doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
customer list: no non-deleted customers
proxy config/status/doctor: OK
proxy.runtime_activation_allowed: disabled for general app/API mutation
v2rayA UI listener: 127.0.0.1:2015 local-only
BTC backend listener: 127.0.0.1:60010 local-only
no_customer_nat_redirects: OK
firewall_apply_mode_plan_only: OK
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
accepted limited runtime listeners are local-only
current phase safety gate: OK
final sync verdict: OK
```

Phase 8 db-transition-execution report summary after 0.1.115 sync:
- `mpf phase8 db-transition-execution --output json` => component=phase8_db_transition_execution, final_decision=BLOCKED, execution_allowed=false, phase8_acceptance_allowed=false, farm5_0_1_114_sync_evidence_present=true, farm5_0_1_114_phase8_reports_evidence_present=true, no_farm5_0_1_115_sync_evidence_claimed=true, synthetic_execution_scenarios_passed=true, blockers=[], errors=[].

0.1.115 sync is accepted as DB-only execution package evidence.
It does not accept Phase 8, does not authorize runtime worker, scheduler, abuse runner, real customer evaluation, production DB execution, firewall apply, production customer traffic, hard/soft blocks, or pause automation.
It confirms DB-only execution report remains fail-closed on farm5.

### Phase 8 Runtime/Worker Integration Readiness Boundary

- This PR defines runtime/worker integration readiness only.
- This PR does not start an abuse worker.
- This PR does not enable scheduler jobs.
- This PR does not enable timers.
- This PR does not enable abuse runner.
- This PR does not evaluate real customers.
- This PR does not execute DB transitions on real customers.
- This PR does not connect to production DB for worker execution.
- This PR does not mutate firewall rules.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- It defines future worker loop, scheduler, lock, kill-switch, failure-mode, and observability contracts.
- Missing/stale evidence must not harden.
- DB failure must not harden.
- Firewall failure must not harden.
- Lock contention must report explicit skip; no silent skip is allowed.
- Runtime worker execution remains future-gated and requires fresh farm5 evidence.


### Phase 8 farm5 0.1.114 Batched Readiness Sync Evidence

```text
command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260516T081446Z
server version after sync: 0.1.114
synced to 0.1.114
pytest on farm5: 720 passed in 67.58s
mpf doctor: OK
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
db status: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
lane status: btc enabled=True backend_port=60010 chain_prefix=MPFBTC protocol=stratum source=db
lane status: ltc enabled=False backend_port=60020 chain_prefix=MPFLTC protocol=stratum source=db
lane status: zec enabled=False backend_port=60015 chain_prefix=MPFZEC protocol=stratum source=db
customer list: no non-deleted customers
proxy config/status/doctor: OK
proxy.runtime_activation_allowed: disabled for general app/API mutation
v2rayA UI: 127.0.0.1:2015 local-only
BTC backend: 127.0.0.1:60010 local-only
no_customer_nat_redirects: OK
firewall_apply_mode_plan_only: OK
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
final sync verdict: OK
```

Phase 8 report commands executed on farm5 after 0.1.114 sync:
- `mpf phase8 abuse-state-machine-contract --output json` => BLOCKED, execution_allowed=false, phase8_acceptance_allowed=false, blockers=[], errors=[]
- `mpf phase8 abuse-evidence-reporting-contract --output json` => BLOCKED, execution_allowed=false, phase8_acceptance_allowed=false, blockers=[], errors=[]
- `mpf phase8 abuse-dry-run-evaluator --output json` => BLOCKED, execution_allowed=false, phase8_acceptance_allowed=false, blockers=[], errors=[], synthetic_scenarios_passed=true
- `mpf phase8 db-transition-readiness --output json` => BLOCKED, readiness_status=DB_ONLY_CONTROLLED_TRANSITION_READINESS_DEFINED_NOT_ACCEPTED, execution_allowed=false, phase8_acceptance_allowed=false, blockers=[], errors=[]

0.1.114 sync is accepted as readiness/report-only baseline evidence.
It does not accept Phase 8, does not authorize abuse runner, does not authorize DB execution on real customers, does not authorize firewall apply, does not authorize production customer traffic, does not authorize hard/soft blocks, and does not authorize pause automation.
It confirms all previous Phase 8 reports remain fail-closed on farm5.

### Phase 8 DB-Only Controlled Transition Execution Boundary

- This PR defines controlled DB-only transition execution code.
- This PR does not enable runtime automation.
- This PR does not enable abuse runner.
- This PR does not enable firewall apply.
- This PR does not enable production traffic.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable hard/soft firewall blocks.
- This PR does not enable pause automation.
- CLI defaults to dry-run.
- Production DB execution is not run by this PR.
- Any real DB execution must be manual, explicit, idempotent, and operator-confirmed.
- Hard transitions require operator approval fields.
- Missing/stale evidence blocks execution.
- Manual unhard remains future-gated.
- Any acceptance of DB execution on farm5 requires a future sync/test result for 0.1.115 or later.

### Phase 7 farm5 0.1.108 Final Acceptance Evidence

```text
Evidence-only update: farm5 synced to 0.1.108 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T181252Z
mpf --version: 0.1.108
pytest during sync: 694 passed
manual pytest after sync: 694 passed in 64.23s
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 6 accepted / Phase 7 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```

### Phase 7 Acceptance Scope

- Phase 7 is accepted only as report-only/service-contract/readiness.
- Phase 7 acceptance does not authorize production traffic.
- Phase 7 acceptance does not authorize firewall apply.
- Phase 7 acceptance does not authorize iptables-restore.
- Phase 7 acceptance does not authorize customer NAT/customer firewall rules.
- Phase 7 acceptance does not authorize usage collectors.
- Phase 7 acceptance does not authorize policy/reject collectors.
- Phase 7 acceptance does not authorize usage_samples writes.
- Phase 7 acceptance does not authorize policy_events writes.
- Phase 7 acceptance does not authorize abuse automation.
- Phase 7 acceptance does not start Phase 8 runtime automation.
- Phase 8 starts only as planning/readiness.
- Phase 8 Abuse 1h Core remains mandatory before production completeness.

### Phase 8 Planning/Readiness Boundary

- Phase 8 is now the current working phase.
- Phase 8 starts as planning/readiness only.
- Phase 8 must implement the abuse 1h invariant before production completeness.
- This PR does not implement the abuse runner.
- This PR does not write abuse_states.
- This PR does not write abuse_events.
- This PR does not enable hard/soft blocks.
- This PR does not enable pause automation.
- This PR does not enable firewall apply.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- The abuse invariant remains mandatory:
  normal -> over_tracking -> over_grace -> hard
  farms-over alone must not harden
  worker-over alone must not harden
  sustained miner-abuse hardens after about 3600 seconds
  all active customers in enabled lanes must be covered
  no silent skip


### Phase 7 farm5 0.1.107 Batched Sync + Reports/Doctor Evidence

```text
Evidence-only update: farm5 synced to 0.1.107 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T171232Z
mpf --version: 0.1.107
pytest during sync: 690 passed
manual pytest after sync: 690 passed in 64.72s
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 6 accepted / Phase 7 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
mpf phase7 usage-policy-readiness --output json final_decision: BLOCKED
mpf phase7 usage-policy-readiness --output json execution_allowed: false
mpf phase7 usage-policy-readiness --output json phase8_start_allowed: false
mpf phase7 usage-accounting-contract --output json final_decision: BLOCKED
mpf phase7 usage-accounting-contract --output json firewall_counter_live_read_authorized: false
mpf phase7 policy-reject-accounting-contract --output json final_decision: BLOCKED
mpf phase7 summary --output json final_decision: BLOCKED
mpf phase7 doctor --output json final_verdict: OK
all child reports blockers: []
```

### Phase 7 Final Acceptance Readiness Boundary

- Phase 7 has the following report-only components present: usage-policy readiness, usage accounting contract, policy/reject accounting contract, read-only summary, and read-only doctor.
- farm5 0.1.107 batched sync is evidenced.
- phase7 doctor final_verdict is OK while final_decision remains BLOCKED.
- blockers are empty across Phase 7 child reports.
- Phase 7 can now be reviewed for acceptance as a report-only/service-contract/readiness phase.
- This PR does not enable production traffic, firewall apply, iptables-restore, customer NAT/customer firewall rules, usage collectors, policy/reject collectors, usage_samples writes, policy_events writes, abuse automation, or Phase 8 start.
- Phase 8 Abuse 1h Core remains future-only until explicitly accepted in a later PR.
- Abuse invariant remains mandatory: normal -> over_tracking -> over_grace -> hard; farms-over alone must not harden; worker-over alone must not harden; sustained miner-abuse hardens after about 3600 seconds; all active customers in enabled lanes must be covered; no silent skip.



### Phase 7 farm5 0.1.104 Sync + Readiness Detector Fix Evidence

```text
Evidence-only update: farm5 synced to 0.1.104 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T155057Z
mpf --version: 0.1.104
pytest during sync: 673 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 6 accepted / Phase 7 working safety gate passed
ai_phase7_task_present: true
blockers: []
no runtime gate opened
runtime restrictions remain unchanged
mpf phase7 usage-policy-readiness --output json final_decision: BLOCKED
mpf phase7 usage-policy-readiness --output json execution_allowed: false
mpf phase7 usage-policy-readiness --output json usage_automation_authorized: false
mpf phase7 usage-policy-readiness --output json usage_collectors_authorized: false
mpf phase7 usage-policy-readiness --output json policy_reject_collectors_authorized: false
mpf phase7 usage-policy-readiness --output json abuse_automation_authorized: false
mpf phase7 usage-policy-readiness --output json customer_nat_authorized: false
mpf phase7 usage-policy-readiness --output json production_traffic_authorized: false
```

### Phase 7 farm5 0.1.102 Sync + Planning Readiness Evidence

```text
Evidence-only update: farm5 synced to 0.1.102 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T112408Z
mpf --version: 0.1.102
pytest during sync: 665 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 6 accepted / Phase 7 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```

### Phase 7 Usage + Policy/Reject Accounting — Planning/Readiness Boundary

- Phase 7 is the current working phase.
- Phase 7 starts as read-only/reporting/service-contract only.
- This PR does not enable usage automation, usage collectors, or policy/reject collectors.
- This PR does not enable production traffic, firewall apply, customer NAT/customer firewall rules, iptables-restore, abuse automation, or block/pause automation.
- Phase 8 remains the future Abuse 1h Core phase.
- Abuse invariant remains mandatory: `normal -> over_tracking -> over_grace -> hard`; farms-over alone must not harden; worker-over alone must not harden; sustained miner-abuse hardens after about 3600 seconds; all active customers in enabled lanes must be covered; no silent skip.


### Phase 6 farm5 0.1.100 Sync + Operator Acceptance Evidence

```text
Evidence-only update: farm5 synced to 0.1.100 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T103836Z
mpf --version: 0.1.100
pytest during sync: 661 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 5 accepted / Phase 6 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```

### Phase 6 Operator Acceptance Decision — Accepted Planner/Reporting Boundary

- Phase 6 Firewall Planner is accepted on farm5.
- Acceptance is planner/reporting/gate-readiness only.
- Acceptance does not authorize runtime firewall mutation.
- Acceptance does not authorize customer NAT.
- Acceptance does not authorize customer firewall rules.
- Acceptance does not authorize production traffic.
- Acceptance does not authorize iptables-restore.
- Acceptance does not authorize live apply.
- Acceptance does not authorize live verify.
- Acceptance does not authorize live rollback.
- Acceptance does not authorize usage automation.
- Acceptance does not authorize abuse automation.
- Acceptance does not authorize UI.
- Acceptance does not authorize Telegram.
- Phase 7 may start next only under its own planning/readiness gate.
- Phase 8 abuse automation remains future-only and must preserve the 1h abuse invariant.


### Phase 6 farm5 0.1.99 Sync + Final Acceptance Review Evidence

```text
Evidence-only update: farm5 synced to 0.1.99 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T092830Z
mpf --version: 0.1.99
pytest during sync: 657 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 5 accepted / Phase 6 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```


### Phase 6 farm5 0.1.98 Sync + Final Review Readiness Evidence

```text
Evidence-only update: farm5 synced to 0.1.98 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T090826Z
mpf --version: 0.1.98
pytest during sync: 652 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 5 accepted / Phase 6 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```

### Phase 6 Final Acceptance Review Package — Report-only

Report-only, non-executing, non-authorizing, BLOCKED. This package does not accept Phase 6 by itself, does not change Current State, does not permit customer NAT/customer firewall rules/production traffic/iptables-restore/live apply/live verify/live rollback, and does not permit usage automation or abuse automation. Phase 7 and Phase 8 remain future-only. Phase 6 final acceptance still requires operator review after this PR and fresh farm5 0.1.99 sync evidence.


### Phase 6 farm5 0.1.96 Sync + Manual Canary Proposal Readiness Evidence

```text
Evidence-only update: farm5 synced to 0.1.96 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T083309Z
mpf --version: 0.1.96
pytest during sync: 647 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
current customer list: no non-deleted customers
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 5 accepted / Phase 6 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```

### Manual Canary Customer Server Evidence / Final Gate Review (Report-only)

Non-authorizing, non-executing, BLOCKED. Does not permit customer NAT/customer firewall rules/production traffic.

### Phase 6 Final Acceptance Readiness (Report-only)

Non-authorizing, non-executing, BLOCKED. phase6_acceptance_allowed=false, customer_nat_authorized=false, customer_firewall_rules_authorized=false.


### Phase 6 farm5 0.1.95 Sync + Controlled Runtime Evidence Package Evidence

```text
Evidence-only update: farm5 synced to 0.1.95 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T073503Z
mpf --version: 0.1.95
pytest during sync: 636 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 5 accepted / Phase 6 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```

### Phase 6 farm5 0.1.94 Sync + Runtime Approval Readiness Evidence

```text
Evidence-only update: farm5 synced to 0.1.94 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup path: /var/backups/mpf/source-before-zip-sync-20260515T070627Z
mpf --version: 0.1.94
pytest during sync: 631 passed
mpf config validate: OK
mpf doctor: OK
db status: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
proxy doctor/status: OK
proxy runtime remains limited local-only
v2rayA UI listener local-only: 127.0.0.1:2015
BTC backend listener local-only: 127.0.0.1:60010
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
current Phase 5 accepted / Phase 6 working safety gate passed
no runtime gate opened
runtime restrictions remain unchanged
```


### Phase 6 farm5 0.1.93 Sync + Gate-Review JSON Evidence

```text
Evidence-only update: farm5 synced to 0.1.93 via sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
Backup path: /var/backups/mpf/source-before-zip-sync-20260514T192415Z
mpf --version: 0.1.93
pytest during sync: 625 passed in 16.69s
mpf config validate / doctor / db status / proxy doctor / current phase safety gate: OK
source aligned with GitHub zip: OK
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no MPF/customer IPv4 firewall references detected
no MPF/customer IPv6 firewall references detected
no customer NAT redirects
accepted runtime listeners are local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational in accepted limited runtime only and do not authorize MPF/customer NAT redirects
PR #100 gate-review JSON serialization fix validated on farm5
mpf firewall gate-review --source config-only --output json completed without traceback
JSON output validated with python3 -m json.tool
final_decision: BLOCKED
applyable: false
live_apply_allowed: false
errors: []
warnings serialized as dictionaries with code/message/severity
safety_flags.database_write: false
safety_flags.filesystem_write: false
safety_flags.iptables_restore_executed: false
safety_flags.iptables_save_executed: false
safety_flags.live_firewall_read: false
safety_flags.live_firewall_write: false
safety_flags.lock_acquired: false
safety_flags.restore_point_written: false
safety_flags.rollback_written: false
safety_flags.runtime_change: no
abuse_requirement_summary.preserved: true
abuse state flow remains normal -> over_tracking -> over_grace -> hard
sustained_hardening_seconds: 3600
No runtime gate opened; this evidence is non-authorizing and runtime restrictions remain unchanged
```

### Phase 1 — Bootstrap Without Traffic Changes

```text
PostgreSQL active
Docker active
containerd active
mpf config validate OK
mpf doctor OK
mpf db ping OK
pytest passed
Docker had no containers
No MPF firewall rules existed
firewall.apply_mode remained plan_only
```

### Phase 2 — PostgreSQL + Config + Domain Model

```text
backup/snapshot created before migration
pytest passed from /opt/mpf-py-src/.venv
alembic current/head = 0001_phase2_initial_schema
public schema table count = 64
runtime tables remained empty
Docker had no containers
No MPF firewall rules existed
firewall.apply_mode remained plan_only
no proxy data-plane was started
no production traffic was changed
```

### Phase 3 — CLI + Internal API Foundation

```text
Phase 3 read-only CLI/API foundation accepted on farm5
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
pytest passed: 48 passed
runtime tables remained empty
Docker had no containers
No MPF firewall or NAT rules existed
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 3.1 — Official Runtime Alignment

```text
official /usr/local/bin/mpf runtime exposed accepted read-only commands
mpf --version reported 0.1.0 during acceptance
mpf phase-status was aligned during verification
pytest passed: 48 passed
runtime-facing tables remained empty
Docker had no containers
No MPF firewall/NAT rules existed
No MPF systemd/cron automation existed
No risky backend/UI ports were listening
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 4 Runtime — Limited Proxy Runtime Startup

See:

```text
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
```

Accepted evidence summary:

```text
server source aligned with GitHub ZIP
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf proxy config-check final_verdict: OK
mpf-v2raya container started and healthy
mpf-forwarder-btc container started and healthy
v2rayA UI host/operator listener: 127.0.0.1:2015
v2rayA UI container target port: 2017
BTC backend listener: 127.0.0.1:60010
BTC backend internal reachability: OK
no public v2rayA UI exposure detected
no public BTC backend exposure detected
no MPF/customer firewall references detected
no customer NAT redirects detected
customers: 0
job_runs: 0
firewall_applies: 0
abuse_states: 0
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
```

Docker-managed local publish rules for `127.0.0.1:2015` and `127.0.0.1:60010` are accepted only as local Docker publish rules. They are not MPF customer NAT redirects.

### Phase 5 — Customer CRUD in DB Only

See:

```text
docs/PHASE_5_FINAL_ACCEPTANCE.md
```

Accepted evidence summary:

```text
Phase 5 accepted as DB-only customer CRUD + future-readiness contracts
version accepted on server: 0.1.21
final synced repository/server gate: 0.1.26
pytest passed: 182 passed during final clean sync evidence
alembic_version: 0002_phase5_customer_lifecycle
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
ui_allowed: no
telegram_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
no production customer traffic
no live firewall apply
runtime remained limited local-only
```

### Phase 6-C — Offline Apply Gate Readiness/Review

```text
version accepted on farm5: 0.1.56
pytest passed: 337 passed
mpf firewall gate-review final_decision: BLOCKED
risk_summary.total: 18
checklist_summary.total: 4
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall apply
no iptables-save execution
no iptables-restore execution
```

### Phase 6-D1 — Live-Apply Boundary Contract

```text
version accepted on farm5: 0.1.59
pytest passed: 357 passed
docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md accepted
docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-E0 — Isolated Apply Harness Contracts

```text
version accepted on farm5: 0.1.61
pytest passed: 376 passed
docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md accepted
docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
fake/no-op harness only
report-only harness service
deterministic plan -> apply -> verify ordering tested
verify-failure rollback-guidance ordering tested
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```


### Phase 6-E1 — Isolated Harness Contract Hardening

```text
version accepted on farm5: 0.1.63
pytest with venv: 392 passed
docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md accepted
docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning

```text
version accepted on farm5: 0.1.66
pytest with venv: 403 passed
docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md accepted
docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```


### Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist

```text
version accepted on farm5: 0.1.70
pytest with venv: 413 passed
docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md accepted
docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```



### Phase 6-F — Manual Canary Gate Definition

```text
version accepted on farm5: 0.1.73
pytest with venv: 426 passed
docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md accepted
docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review

```text
version accepted on farm5: 0.1.76
pytest with venv: 442 passed
docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md accepted
docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no live rollback
no live verify
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary

```text
version accepted on farm5: 0.1.79
pytest with venv: 457 passed
docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md accepted
docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no live rollback
no live verify
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6 Apply Slice 1-2 — Documentation/Readiness Boundary Sync

```text
version accepted on farm5: 0.1.83
pytest with venv: 486 passed
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T055542Z
current phase safety gate: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
Slice 1 and Slice 2 are accepted only as documentation/test-only readiness boundaries
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Apply Slice 3-4 — Documentation Boundary Sync

```text
version accepted on farm5: 0.1.86
pytest during sync: 499 passed
manual pytest after sync: 499 passed
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T071337Z
current phase safety gate: OK
source aligned with GitHub zip: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
Slice 3 and Slice 4 are accepted only as documentation/test-only boundaries
no manual canary apply
no no-customer apply
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Apply Gate Proposal Review — Documentation Sync

```text
version accepted on farm5: 0.1.88
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T084028Z
pytest during sync: 504 passed
manual pytest with project venv: 504 passed
current phase safety gate: OK
source aligned with GitHub zip: OK
mpf --version: 0.1.88
/opt/mpf-py-src/VERSION: 0.1.88
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
Future Dedicated Phase 6 Apply Gate Proposal/Review remains documentation/test-only and non-authorizing
no dedicated apply gate
no manual canary apply
no no-customer apply
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Apply Gate Readiness Integration — Server Sync

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T095401Z
pytest with venv during sync: 511 passed
current phase safety gate: OK
source aligned with GitHub zip: OK
mpf --version: 0.1.90
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
mpf firewall apply-gate-readiness remains read-only/report-only and BLOCKED
mpf firewall gate-review includes apply_gate_readiness_summary and remains BLOCKED
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Live Snapshot Readiness Report-Only Server Sync

```text
version accepted on farm5: 0.1.90
sync: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip (backup: /var/backups/mpf/source-before-zip-sync-20260513T124116Z)
pytest: 532 passed in 11.70s (venv), 532 passed in 10.00s (/opt/mpf-py-src)
source aligned with GitHub zip: OK; phase safety gate: OK; mpf --version: 0.1.90
mpf checks: config validate OK, doctor OK, db status OK, proxy doctor final_verdict OK
database: alembic_version=0002_phase5_customer_lifecycle, public_table_count=64, lanes=3, customers=1, job_runs=0, firewall_applies=0, abuse_states=0
runtime/gates: firewall.apply_mode=plan_only, proxy.runtime_activation_allowed=false, production_traffic=none, firewall_apply_allowed=no, abuse_automation_allowed=no, customer_onboarding_allowed=db_only, proxy_data_plane_allowed=limited_runtime_local_only, ui_allowed=no, telegram_allowed=no
safety: no MPF/customer IPv4/IPv6 firewall refs, no customer NAT redirects, listeners local-only (v2rayA 127.0.0.1:2015, BTC backend 127.0.0.1:60010), Docker local publish DNAT informational only
live-snapshot-scaffold: BLOCKED, NOT_AUTHORIZED, no live read, no iptables-save, no subprocess, no firewall/db mutation, no restore/lock, current_state_preserved=true
live-snapshot-readiness: BLOCKED, NOT_AUTHORIZED, live read allowed/executed=false, iptables-save allowed/executed=false, subprocess/filesystem allowed/executed=false, no mutation, snapshot counts=0/0/0, current_state_preserved=true, next_required_gate=explicit docs/PHASE_STATUS.md acceptance plus farm5 evidence
apply-gate-readiness: BLOCKED, plan_only preserved, live firewall read/write not allowed, iptables-save/restore not allowed, real adapter/subprocess calls not allowed, customer NAT/firewall rules not allowed, live snapshot scaffold/read summaries present and BLOCKED
firewall gate-review: BLOCKED, applyable=false, inspection_only=true, artifact_only=true, live_apply_allowed=false, abuse requirement preserved (normal -> over_tracking -> over_grace -> hard, sustained_hardening_seconds=3600), safety flags confirm no live read/write/save/restore/database/filesystem mutations
```

This server result is report-only for the earlier readiness boundary and remains non-authorizing for apply/write paths.
The explicitly gated read-only `iptables-save` snapshot path is now authorized with successful farm5 evidence (see section below).
No firewall write/apply/rollback/verify, `iptables-restore`, restore point write, lock acquisition, DB apply write/record, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is restore point + lock + DB apply record readiness, still without customer NAT/customer firewall rules.


### Phase 6 Read-Only iptables-save Snapshot — Server Evidence

```text
version accepted on farm5: 0.1.90
sync: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip (backup: /var/backups/mpf/source-before-zip-sync-20260513T134528Z)
pytest (venv during sync): 536 passed in 11.57s
source aligned with GitHub zip: OK; phase safety gate: OK
current state preserved: production_traffic=none, firewall_apply_allowed=no, abuse_automation_allowed=no, customer_onboarding_allowed=db_only, proxy_data_plane_allowed=limited_runtime_local_only, ui_allowed=no, telegram_allowed=no, live_snapshot_read_allowed=iptables_save_read_only
mpf checks: config validate OK; doctor OK; db status OK; proxy doctor final_verdict OK
runtime safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; no MPF/customer IPv4/IPv6 refs; no customer NAT redirects; listeners local-only (v2rayA 127.0.0.1:2015, BTC backend 127.0.0.1:60010)
live-snapshot-readiness: READY_FOR_READ_ONLY_SNAPSHOT; AUTHORIZED_READ_ONLY; live_firewall_read_allowed=true; iptables_save_allowed=true; apply_decision=BLOCKED; blockers=none; errors=none
live-snapshot-read (dry, no execute): READY_FOR_READ_ONLY_SNAPSHOT; AUTHORIZED_READ_ONLY; subprocess_executed=false; iptables_save_executed=false; apply_decision=BLOCKED
live-snapshot-read (--execute, json output): READ_ONLY_SNAPSHOT_COLLECTED; AUTHORIZED_READ_ONLY; live_firewall_read_executed=true; iptables_save_executed=true; subprocess_args=["iptables-save"]; subprocess_returncode=0; parser_input_source=iptables-save stdout; stdout_line_count=60; source_snapshot_sha256=4f506c5871a4fa518b874e6a635eac56cb61351f49901a1ff6fc9aeb4fb94019; snapshot_rule_count=0; snapshot_chain_count=0; snapshot_table_count=0; filesystem_write_executed=false; firewall_mutation=false; db_mutation=false; restore_point_written=false; lock_acquired=false; customer_nat_changed=false; customer_firewall_rules_changed=false; production_traffic_changed=false; apply_decision=BLOCKED; errors=none
parser scope note: snapshot counters track MPF-owned chains/rules only; with no MPF/customer firewall refs, counts 0/0/0 are expected while stdout_line_count=60 confirms iptables-save returned content
```

This server result proves only the explicitly gated read-only `iptables-save` snapshot path.
No `iptables-restore` is authorized.
No firewall write, apply, rollback, restore point write, lock acquisition, DB apply write, DB apply record, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is separate explicit restore point + lock + DB apply record gate proposal/acceptance boundary, still without customer NAT/customer firewall rules.

### Phase 6 Restore/Lock/DB Apply Record Readiness — Server Sync

```text
version accepted on farm5: 0.1.90
sync: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip (backup: /var/backups/mpf/source-before-zip-sync-20260513T182123Z)
pytest (venv during sync): 544 passed in 12.13s
source aligned with GitHub zip: OK; current phase safety gate: OK; mpf --version: 0.1.90
mpf checks: config validate OK; doctor OK; db status OK; proxy doctor final_verdict OK
runtime/gates: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no
runtime safety: no MPF/customer IPv4/IPv6 firewall refs; no customer NAT redirects; listeners local-only (v2rayA 127.0.0.1:2015, BTC backend 127.0.0.1:60010)
restore-lock-record-readiness: final_decision=BLOCKED; authorization_status=NOT_AUTHORIZED_FOR_WRITES; inspection_only=true; report_only=true
actions executed: restore_point_write=false; lock_acquired=false; db_apply_record_write=false; iptables_restore_executed=false; customer_nat_changed=false; customer_firewall_rules_changed=false
apply-gate-readiness: final_decision=BLOCKED
gate-review: final_decision=BLOCKED
time_sync_required_before_future_write/production/usage/abuse_gate=true
```

This server result proves only the report-only restore point + lock + DB apply record readiness surface.
No restore point write is authorized.
No lock acquisition is authorized.
No DB apply write or DB apply record is authorized.
No firewall write/apply/rollback/verify, iptables-restore, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is a separate explicit restore point + lock + DB apply record gate proposal/acceptance boundary, still without customer NAT/customer firewall rules.


### Phase 6 Restore/Lock/DB Apply Record Gate — Proposal Boundary

Compatibility note: `restore-lock-record-readiness` remains report-only readiness (`NOT_AUTHORIZED_FOR_WRITES` / `BLOCKED`), while `restore-lock-record-gate` is the proposal-boundary/preflight surface (`NOT_ACCEPTED` / `BLOCKED`). Both are inspection/report-only and do not permit restore point writes, lock acquisition, DB apply writes/records, firewall write/apply/rollback/verify, `iptables-restore`, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram. `apply-gate-readiness` and `gate-review` remain `BLOCKED`.

Status:
- proposal/boundary only
- non-authorizing
- no runtime behavior enabled by this PR

Purpose:
- define the future explicit gate boundary for restore point write, lock acquisition, and DB apply record write
- prepare the next controlled Phase 6 step before any no-customer apply/verify/rollback work

This PR does not authorize the gate yet.
It only defines what a later explicit acceptance must require.

Future gate may be considered only after all of these are true:

- separate explicit acceptance in docs/PHASE_STATUS.md
- operator approval
- farm5 evidence included
- python -m pytest -q passes
- current phase safety gate passes
- mpf config validate OK
- mpf doctor OK
- mpf db status OK
- mpf proxy doctor final_verdict OK
- mpf firewall restore-lock-record-readiness final_decision remains BLOCKED and NOT_AUTHORIZED_FOR_WRITES before the gate is accepted
- mpf firewall apply-gate-readiness remains BLOCKED
- mpf firewall gate-review remains BLOCKED
- firewall.apply_mode remains plan_only
- proxy.runtime_activation_allowed remains false
- production_traffic remains none
- firewall_apply_allowed remains no
- abuse_automation_allowed remains no
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- no customer NAT redirects
- no customer firewall rules
- backend external exposure remains NO
- backend internal reachability remains OK
- accepted limited runtime listeners remain local-only
- time synchronization is fixed and evidenced, or explicitly remains a blocker for any write/production/usage/abuse gate

Future allowed operation if accepted later:

Only after a later explicit acceptance in docs/PHASE_STATUS.md, the future gate may allow:

- create one restore point record/artifact for inspection-controlled apply preparation
- acquire one scoped firewall/apply lock
- create one DB apply record in a pre-apply or prepared/blocked state
- correlate restore point, lock, DB apply record, source snapshot hash, payload hash, operator identity, and correlation_id
- keep final apply decision BLOCKED unless a later apply gate is separately accepted

Even if the future gate is later accepted, it must still NOT allow:

- live firewall write
- live firewall apply
- live rollback
- live verify
- iptables-restore
- customer NAT
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram
- public API binding
- public v2rayA UI exposure
- public backend exposure

Stop conditions:

The future gate must be blocked if any of these are true:

- Current State changes unexpectedly
- firewall_apply_allowed becomes yes
- production_traffic is enabled
- abuse_automation_allowed becomes yes before Phase 8
- firewall.apply_mode is not plan_only before explicit gate acceptance
- proxy.runtime_activation_allowed becomes true
- backend external exposure appears
- backend internal reachability breaks
- MPF/customer firewall references appear unexpectedly
- customer NAT redirects appear
- customer firewall rules appear
- time synchronization is still unverified for write-dependent work
- tests fail
- operator evidence is missing
- restore point/lock/DB apply record behavior is implemented without separate explicit acceptance

This boundary does not authorize restore point writes, lock acquisition, DB apply writes, DB apply records, firewall write/apply/rollback/verify, iptables-restore, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is an operator-approved controlled restore point + lock + DB apply record execution gate with fresh farm5 evidence, still without customer NAT/customer firewall rules and still without firewall apply.

### Phase 6 Restore/Lock/DB Apply Record Gate Report — Server Sync

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T190936Z
pytest with venv during sync: 552 passed in 14.05s
source aligned with GitHub zip: OK
current phase safety gate: OK
mpf --version: 0.1.90
core smoke checks: mpf config validate=OK; mpf doctor=OK; mpf db status=OK; mpf proxy doctor final_verdict=OK
database status: alembic_version=0002_phase5_customer_lifecycle; public_table_count=64; lanes=3; customers=1; job_runs=0; firewall_applies=0; abuse_states=0
runtime/safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no; no MPF/customer IPv4/IPv6 firewall refs; no customer NAT redirects; listeners local-only (v2rayA UI 127.0.0.1:2015, BTC backend 127.0.0.1:60010); Docker-managed local publish DNAT informational only
restore-lock-record-readiness: final_decision=BLOCKED; authorization_status=NOT_AUTHORIZED_FOR_WRITES; inspection_only=true; report_only=true; read_only_snapshot_gate_authorized=true; read_only_snapshot_evidence_present=true; restore_point_write_allowed=false; lock_acquisition_allowed=false; db_apply_record_write_allowed=false; iptables_restore_allowed=false; customer_nat_allowed=false; customer_firewall_rules_allowed=false; blockers=none; errors=none
restore-lock-record-gate: final_decision=BLOCKED; authorization_status=NOT_ACCEPTED; gate_status=PROPOSAL_BOUNDARY_DEFINED; inspection_only=true; report_only=true; preflight_only=true; proposal_boundary_present=true; read_only_snapshot_evidence_present=true; restore_lock_record_readiness_evidence_present=true; restore_point_write_allowed=false; lock_acquisition_allowed=false; db_apply_record_write_allowed=false; iptables_restore_allowed=false; customer_nat_allowed=false; customer_firewall_rules_allowed=false; blockers=none; errors=none
apply-gate-readiness: final_decision=BLOCKED; restore_lock_record_readiness_present=true; restore_lock_record_readiness_authorization_status=NOT_AUTHORIZED_FOR_WRITES; restore_lock_record_readiness_final_decision=BLOCKED; restore_lock_record_gate_present=true; restore_lock_record_gate_authorization_status=NOT_ACCEPTED; restore_lock_record_gate_final_decision=BLOCKED; missing_requirements=none; blockers=none
gate-review: final_decision=BLOCKED; applyable=false; live_apply_allowed=false; restore_lock_record_gate summary present; restore_lock_record_gate authorization_status=NOT_ACCEPTED; restore_lock_record_readiness summary present; restore_lock_record_readiness authorization_status=NOT_AUTHORIZED_FOR_WRITES; abuse requirement preserved normal->over_tracking->over_grace->hard; sustained_hardening_seconds=3600
```

This server result proves only the report-only/preflight restore-lock-record gate surface and the compatibility-preserved readiness surface.
No restore point write is authorized.
No lock acquisition is authorized.
No DB apply write or DB apply record is authorized.
No firewall write/apply/rollback/verify, iptables-restore, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.

### Phase 6 Restore/Lock/DB Apply Record Acceptance Gate — Server Sync

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260514T075352Z
pytest with venv during sync: 559 passed in 12.64s
source aligned with GitHub zip: OK
current phase safety gate: OK
mpf --version: 0.1.90
core smoke checks: mpf config validate=OK; mpf doctor=OK; mpf db status=OK; mpf proxy doctor final_verdict=OK
database status: alembic_version=0002_phase5_customer_lifecycle; public_table_count=64; lanes=3; customers=1; job_runs=0; firewall_applies=0; abuse_states=0
runtime/safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no; no MPF/customer IPv4/IPv6 firewall refs; no customer NAT redirects; listeners local-only (v2rayA UI 127.0.0.1:2015, BTC backend 127.0.0.1:60010); Docker-managed local publish DNAT informational only
restore-lock-record-acceptance-gate: final_decision=BLOCKED; gate_status=ACCEPTANCE_PREREQUISITES_READY; authorization_status=NOT_ACCEPTED_FOR_EXECUTION; inspection_only=true; report_only=true; preflight_only=true; execution_allowed=false; farm5_time_sync_evidence_present=true; farm5_time_sync_resolved=true; restore_point_write_allowed=false; lock_acquisition_allowed=false; db_apply_record_write_allowed=false; iptables_restore_allowed=false; customer_nat_allowed=false; customer_firewall_rules_allowed=false; apply_decision=BLOCKED; blockers=none; errors=none
restore-lock-record-acceptance-gate --output json: current_state_preserved=true; read_only_snapshot_evidence_present=true; restore_lock_record_readiness_evidence_present=true; restore_lock_record_gate_proposal_present=true; restore_lock_record_gate_server_sync_evidence_present=true; farm5_time_sync_evidence_present=true; farm5_time_sync_resolved=true; future_restore_point_gate_prereq_ready=true; future_lock_gate_prereq_ready=true; future_db_apply_record_gate_prereq_ready=true; execution_allowed=false; restore_point_written=false; lock_acquired=false; db_apply_record_written=false; iptables_restore_executed=false; customer_nat_changed=false; customer_firewall_rules_changed=false; production_traffic_changed=false
apply-gate-readiness: final_decision=BLOCKED; restore_lock_record_acceptance_gate_present=true; restore_lock_record_acceptance_gate_authorization_status=NOT_ACCEPTED_FOR_EXECUTION; restore_lock_record_acceptance_gate_final_decision=BLOCKED; missing_requirements=none; blockers=none
gate-review: final_decision=BLOCKED; applyable=false; live_apply_allowed=false; restore_lock_record_acceptance_gate summary present; restore_lock_record_acceptance_gate authorization_status=NOT_ACCEPTED_FOR_EXECUTION; restore_lock_record_readiness authorization_status=NOT_AUTHORIZED_FOR_WRITES; restore_lock_record_gate authorization_status=NOT_ACCEPTED; abuse requirement preserved normal->over_tracking->over_grace->hard; sustained_hardening_seconds=3600; command=mpf firewall gate-review --output json
```

This server result proves only the report-only/preflight restore-lock-record acceptance gate surface.
No restore point write is authorized.
No lock acquisition is authorized.
No DB apply write or DB apply record is authorized.
No firewall write/apply/rollback/verify, iptables-restore, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is an operator-approved controlled restore point + lock + DB apply record execution gate with fresh farm5 evidence, still without customer NAT/customer firewall rules and still without firewall apply.

### Phase 6 Restore/Lock/DB Apply Record Execution Gate Scaffold — Server Sync

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260514T095337Z
pytest with venv during sync: 566 passed in 12.51s
source aligned with GitHub zip: OK
current phase safety gate: OK
mpf --version: 0.1.90
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
database status: alembic_version=0002_phase5_customer_lifecycle; public_table_count=64; lanes=3; customers=1; job_runs=0; firewall_applies=0; abuse_states=0
runtime/safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
restore-lock-record-execution-gate: final_decision=BLOCKED; gate_status=EXECUTION_GATE_SCAFFOLD_READY; authorization_status=NOT_AUTHORIZED_FOR_EXECUTION; execution_allowed=false; explicit_execution_authorization_present=false; operator_approval_present=false; fresh_farm5_execution_evidence_present=false; farm5_time_sync_resolved=true
execution-gate safety: restore_point_write_allowed=false; lock_acquisition_allowed=false; db_apply_record_write_allowed=false; iptables_restore_allowed=false; customer_nat_allowed=false; customer_firewall_rules_allowed=false; apply_decision=BLOCKED
execution-gate blocker: explicit controlled restore point + lock + DB apply record execution authorization is not accepted
apply-gate-readiness: final_decision=BLOCKED; restore_lock_record_execution_gate_present=true; restore_lock_record_execution_gate_authorization_status=NOT_AUTHORIZED_FOR_EXECUTION; restore_lock_record_execution_gate_final_decision=BLOCKED; restore_lock_record_execution_gate_execution_allowed=false
gate-review: final_decision=BLOCKED; applyable=false; live_apply_allowed=false
no restore point write
no lock acquisition
no DB apply record write
no firewall write/apply/rollback/verify
no iptables-restore
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

This server result proves only the fail-closed execution-gate scaffold for future controlled restore point + lock + DB apply record work. It does not authorize execution. Actual restore point writes, lock acquisition, DB apply record writes, firewall apply/rollback/verify, iptables-restore, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, and Telegram remain blocked until a later explicit gate acceptance with fresh farm5 evidence.

### Phase 6 Controlled Restore/Lock/DB Apply Record Execution Gate — Proposal Review

Status: proposal/review only (documentation/test-only, non-authorizing).

This PR does not authorize execution. The execution-gate scaffold remains `BLOCKED` / `NOT_AUTHORIZED_FOR_EXECUTION`, and execution_allowed remains false.

The following remain forbidden: restore point writes, lock acquisition, DB apply record writes, firewall apply/rollback/verify, iptables-restore, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, and Telegram.

Purpose: define the exact future acceptance criteria for a separate PR that may request controlled execution of one restore point record/artifact, one scoped lock, and one DB apply record in prepared/blocked state only. Even in that future execution gate, apply_decision must remain BLOCKED and no firewall apply is allowed.

Future acceptance criteria (all required, with fresh farm5 evidence):

- operator approval is explicitly recorded
- fresh farm5 evidence is included
- python -m pytest -q passes from the project venv
- current phase safety gate passes
- mpf --version reports 0.1.90 unless a later version bump is intentionally accepted
- mpf config validate OK
- mpf doctor OK
- mpf db status OK
- mpf proxy doctor final_verdict OK
- mpf firewall restore-lock-record-execution-gate remains BLOCKED / NOT_AUTHORIZED_FOR_EXECUTION before the gate is accepted
- mpf firewall apply-gate-readiness remains BLOCKED
- mpf firewall gate-review remains BLOCKED
- firewall.apply_mode remains plan_only
- proxy.runtime_activation_allowed remains false
- production_traffic remains none
- firewall_apply_allowed remains no
- abuse_automation_allowed remains no
- live_snapshot_read_allowed remains iptables_save_read_only
- farm5 time sync remains resolved: System clock synchronized: yes; NTPSynchronized=yes; NTP source 194.225.150.25
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- no customer NAT redirects
- no customer firewall rules
- accepted limited runtime listeners remain local-only: v2rayA UI 127.0.0.1:2015; BTC backend 127.0.0.1:60010

Future allowed operation only after separate explicit acceptance:

- create one restore point record/artifact for controlled pre-apply preparation
- acquire one scoped firewall/apply lock
- create one DB apply record in prepared/blocked state
- correlate restore point, lock, DB apply record, source snapshot hash, intended payload hash, operator identity, and correlation_id
- preserve apply_decision=BLOCKED
- preserve firewall_apply_allowed=no
- preserve production_traffic=none

Future still forbidden even after that controlled execution gate:

- iptables-restore
- live firewall apply
- live rollback
- live verify
- customer NAT
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram
- public API binding
- public v2rayA UI exposure
- public backend exposure

Stop conditions (gate remains blocked):

- Current State changes unexpectedly
- tests fail
- operator approval is missing
- fresh farm5 evidence is missing
- farm5 time synchronization is unresolved
- firewall.apply_mode is not plan_only
- proxy.runtime_activation_allowed is true
- production_traffic is not none
- firewall_apply_allowed is not no
- abuse_automation_allowed is not no
- backend external exposure appears
- backend internal reachability fails
- MPF/customer firewall references appear unexpectedly
- customer NAT redirects appear
- customer firewall rules appear
- restore point/lock/DB apply record behavior is implemented without separate explicit acceptance
- any code path introduces iptables-restore, firewall apply, rollback, verify, customer NAT, customer firewall rules, usage automation, or abuse automation

The next implementation target after this proposal review is a separate controlled execution-gate PR that may request explicit acceptance for restore point + scoped lock + DB apply record writes only, still without firewall apply and still without customer NAT/customer firewall rules.

### Phase 6 Controlled Restore/Lock/DB Apply Record Execution Boundary — Accepted

Status:

- accepted boundary only
- documentation/test-only
- no execution performed by this PR
- no runtime behavior enabled by this PR

Accepted boundary:

A future implementation PR may add guarded code paths for exactly:

- creating one restore point record/artifact
- acquiring one scoped firewall/apply lock
- creating one DB apply record in prepared/blocked state
- correlating restore point, lock, DB apply record, source snapshot hash, intended payload hash, operator identity, and correlation_id

The future implementation must still keep:

- final_decision=BLOCKED until the guarded execution is explicitly invoked
- apply_decision=BLOCKED always
- firewall_apply_allowed=no
- production_traffic=none
- abuse_automation_allowed=no

The accepted boundary still forbids:

- iptables-restore
- live firewall apply
- live rollback
- live verify
- customer NAT
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram
- public API binding
- public v2rayA UI exposure
- public backend exposure

Required future implementation guardrails:

The next implementation PR must be blocked unless all are true:

- Current State contains restore_lock_record_execution_allowed: controlled_boundary_only
- production_traffic is none
- firewall_apply_allowed is no
- abuse_automation_allowed is no
- live_snapshot_read_allowed is iptables_save_read_only
- firewall.apply_mode is plan_only
- proxy.runtime_activation_allowed is false
- farm5 time sync evidence exists and remains resolved
- read-only iptables-save snapshot evidence exists
- restore-lock-record readiness evidence exists
- restore-lock-record gate report evidence exists
- restore-lock-record acceptance gate evidence exists
- restore-lock-record execution-gate scaffold evidence exists
- controlled execution proposal review exists
- controlled execution boundary acceptance exists
- operator approval is supplied at invocation time
- explicit command flag is supplied at invocation time
- dry-run/default mode does not write anything

The future implementation must default to dry-run/report-only.

The future implementation must require an explicit flag such as:

- --execute-controlled-boundary

The future implementation must refuse execution without operator identity and reason fields.

The future implementation must write only the minimum controlled artifacts/records:

- one restore point record/artifact
- one scoped lock
- one DB apply record in prepared/blocked state

The future implementation must not perform:

- iptables-restore
- firewall apply
- firewall rollback
- firewall verify
- customer NAT
- customer firewall rules
- production traffic changes
- usage automation
- abuse automation

Stop conditions for the future implementation:

- Current State does not contain restore_lock_record_execution_allowed: controlled_boundary_only
- Current State changes unexpectedly
- tests fail
- operator approval is missing
- explicit execution flag is missing
- operator identity is missing
- reason is missing
- farm5 time synchronization is unresolved
- firewall.apply_mode is not plan_only
- proxy.runtime_activation_allowed is true
- production_traffic is not none
- firewall_apply_allowed is not no
- abuse_automation_allowed is not no
- live_snapshot_read_allowed is not iptables_save_read_only
- MPF/customer firewall references appear unexpectedly
- customer NAT redirects appear
- customer firewall rules appear
- backend external exposure appears
- backend internal reachability fails

The next implementation target is a separate guarded code PR for `mpf firewall restore-lock-record-execution-gate` that may add a dry-run default and an explicit `--execute-controlled-boundary` path for the accepted controlled boundary only: one restore point record/artifact, one scoped lock, and one DB apply record in prepared/blocked state, still without firewall apply and still without customer NAT/customer firewall rules.

### Phase 6 Controlled Restore/Lock/DB Apply Record Execution — Server Evidence

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260514T120405Z
pytest with venv during sync: 583 passed in 13.10s
source aligned with GitHub zip: OK
current phase safety gate: OK
mpf --version: 0.1.90
Current State preserved: OK
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
dry-run before execution: authorization_status=CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN; execution_allowed=false; restore_point_written=false; lock_acquired=false; db_apply_record_written=false; db_mutation=false; errors=none
controlled execution: authorization_status=CONTROLLED_BOUNDARY_EXECUTED; execution_allowed=true; restore_point_written=true; restore_point_id=1; lock_acquired=true; lock_name=phase6_restore_lock_record_execution; lock_owner=vahid; db_apply_record_written=true; firewall_apply_id=1; db_mutation=true; errors=none
controlled execution safety: final_decision=BLOCKED; apply_decision=BLOCKED; firewall_apply_allowed=no; production_traffic=none; iptables_save_executed=false; iptables_restore_executed=false; live_firewall_apply_allowed=false; live_firewall_rollback_allowed=false; live_firewall_verify_allowed=false; customer_nat_changed=false; customer_firewall_rules_changed=false; production_traffic_changed=false; usage_automation_allowed=false; abuse_automation_allowed_runtime=false; ui_allowed_runtime=false; telegram_allowed_runtime=false
database status after execution: alembic_version=0002_phase5_customer_lifecycle; public_table_count=64; lanes=3; customers=1; firewall_applies=1; abuse_states=0
apply-gate-readiness: final_decision=BLOCKED; restore_lock_record_execution_gate_present=true; restore_lock_record_execution_gate_execution_allowed=false
gate-review: final_decision=BLOCKED; applyable=false; live_apply_allowed=false
no firewall apply
no firewall rollback
no firewall verify
no iptables-restore
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

This server result proves only the explicitly gated controlled restore point + scoped lock + DB apply record preparation boundary. It does not authorize firewall apply, firewall rollback, firewall verify, iptables-restore, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram. Apply and gate-review final decisions remain BLOCKED.

### Phase 6 Dedicated Apply Gate — Proposal Review

Status:

```text
proposal/review only
documentation/test-only
non-authorizing
no runtime behavior enabled by this PR
firewall_apply_allowed remains no
production_traffic remains none
apply_decision remains BLOCKED
```

Purpose: define the exact future gate for the first no-customer apply/verify/rollback lifecycle inside Phase 6.

This proposal may prepare a future gate for:

- using the already proven read-only iptables-save snapshot evidence
- using the already proven restore point + scoped lock + DB apply record preparation boundary
- preparing a no-customer apply payload
- applying only a no-customer-safe firewall payload
- verifying the result
- rolling back the result
- recording apply/verify/rollback evidence

Important: the future apply gate still must NOT include customer NAT, customer firewall rules, production customer traffic, usage automation, abuse automation, UI, Telegram, public API binding, public v2rayA UI exposure, or public backend exposure.

Future gate may be considered only after all are true and evidenced: operator approval explicitly recorded; fresh farm5 evidence included; `python -m pytest -q` passes from project venv; current phase safety gate passes; `mpf --version` reports `0.1.90` unless a later version bump is explicitly accepted; `mpf config validate OK`; `mpf doctor OK`; `mpf db status OK`; `mpf proxy doctor final_verdict OK`; `mpf firewall restore-lock-record-execution-gate` default dry-run remains `BLOCKED / CONTROLLED_BOUNDARY_ACCEPTED_DRY_RUN`; `mpf firewall apply-gate-readiness` remains BLOCKED; `mpf firewall gate-review` remains BLOCKED; `firewall.apply_mode` remains `plan_only` until explicit future gate acceptance; `proxy.runtime_activation_allowed` remains false; `production_traffic` remains none; `firewall_apply_allowed` remains no until explicit future apply gate acceptance; `abuse_automation_allowed` remains no; `live_snapshot_read_allowed` remains `iptables_save_read_only`; `restore_lock_record_execution_allowed` remains `controlled_boundary_only`; farm5 time sync remains resolved; no MPF/customer IPv4 firewall references appear unexpectedly; no MPF/customer IPv6 firewall references appear unexpectedly; no customer NAT redirects appear; no customer firewall rules appear; accepted limited runtime listeners remain local-only (`v2rayA UI 127.0.0.1:2015`, `BTC backend 127.0.0.1:60010`); backend external exposure remains NO; backend internal reachability remains OK.

Future allowed operation, only after separate explicit acceptance: a later implementation PR may add a guarded no-customer apply/verify/rollback path for a no-customer-safe payload. The future implementation must default to dry-run/report-only, require an explicit execution flag, require operator identity, require reason, require confirmation, acquire a scoped apply lock, create or reference a restore point, create or reference a `firewall_applies` record, use atomic apply mechanics, verify after apply, provide rollback, and keep customer NAT/customer firewall rules forbidden.

Future still forbidden even after this proposal: customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, Telegram.

Stop conditions for any future apply gate: Current State changes unexpectedly; tests fail; operator approval missing; fresh farm5 evidence missing; farm5 time sync unresolved; `firewall.apply_mode` not explicitly accepted for the future gate; `proxy.runtime_activation_allowed` is true; `production_traffic` is not none; `abuse_automation_allowed` is not no; customer NAT redirects appear; customer firewall rules appear; backend external exposure appears; backend internal reachability fails; restore point/lock/DB apply record evidence missing; rollback plan missing; verify plan missing; any customer rule included in the no-customer payload.

Evidence anchor references for this proposal/review context: `CONTROLLED_BOUNDARY_EXECUTED`, `restore_point_id=1`, `firewall_apply_id=1`, `apply_decision=BLOCKED`, `iptables_restore_executed=false`, `customer_nat_changed=false`, `customer_firewall_rules_changed=false`, `production_traffic_changed=false`.

The next implementation target after this proposal review is a separate guarded no-customer apply/verify/rollback scaffold PR that must remain dry-run/report-only by default and must not include customer NAT/customer firewall rules.


### Phase 6 No-Customer Apply/Verify/Rollback Scaffold — Report-Only

```text
scaffold/report-only and non-authorizing surface only
no runtime behavior enabled
no firewall apply
no firewall verify
no firewall rollback
no iptables-restore
no subprocess firewall calls
no real adapter execution
no customer NAT
no customer firewall rules
no production traffic
no DB writes
no restore point writes
no lock acquisition
final_decision remains BLOCKED
apply_decision remains BLOCKED
verify_decision remains BLOCKED
rollback_decision remains BLOCKED
```

Purpose: Prepare an inspectable report-only surface for the future no-customer apply/verify/rollback lifecycle.

Next step after this scaffold: a separate explicit acceptance gate with fresh farm5 evidence before any real no-customer apply execution.


### Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Report-Only

```text
explicit acceptance-gate report only
non-executing
non-authorizing for runtime
no firewall apply
no firewall verify
no firewall rollback
no iptables-restore
no subprocess firewall calls
no real adapter execution
no customer NAT
no customer firewall rules
no production traffic
no DB writes
no restore point writes
no lock acquisition
final_decision remains BLOCKED
apply_decision remains BLOCKED
verify_decision remains BLOCKED
rollback_decision remains BLOCKED
execution_allowed remains false
```

Purpose: Record that the acceptance gate for future no-customer apply/verify/rollback is now modeled and inspectable, but future execution still requires separate server evidence and a separate execution PR/gate.



### Phase 6 No-Customer Apply/Verify/Rollback Acceptance Gate — Server Evidence

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260514T134606Z
pytest with venv during sync: 606 passed in 14.29s
current phase safety gate: OK
source aligned with GitHub zip: OK
mpf --version: 0.1.90
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
database status: alembic_version=0002_phase5_customer_lifecycle; public_table_count=64; lanes=3; customers=1; job_runs=0; firewall_applies=1; abuse_states=0
runtime safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no
runtime listeners: v2rayA UI 127.0.0.1:2015; BTC backend 127.0.0.1:60010
firewall safety: no MPF/customer IPv4 firewall references detected; no MPF/customer IPv6 firewall references detected; no customer NAT redirects detected
Docker-managed local publish DNAT references for 127.0.0.1:2015 and 127.0.0.1:60010 are accepted limited-runtime local publish rules only
accepted limited runtime listeners remain local-only
current Phase 5 accepted / Phase 6 working safety gate passed
production customer traffic remains disabled
```

This server result proves only repository/server sync and report-only acceptance-gate availability. It does not authorize firewall apply, firewall verify, firewall rollback, iptables-restore, subprocess firewall calls, real adapter execution, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram. Apply, verify, rollback, and execution decisions remain BLOCKED.

### Phase 6 No-Customer Apply/Verify/Rollback Execution Gate — Report-Only

This section defines a controlled execution-gate report only surface for future no-customer apply/verify/rollback and is non-executing and non-authorizing for runtime. It does not authorize firewall apply, firewall verify, firewall rollback, iptables-restore, subprocess firewall calls, real adapter execution, customer NAT, customer firewall rules, production traffic, DB writes, restore point writes, or lock acquisition. final_decision remains BLOCKED; apply_decision remains BLOCKED; verify_decision remains BLOCKED; rollback_decision remains BLOCKED; execution_allowed remains false.


### Phase 6 No-Customer Apply/Verify/Rollback Execution Gate — Server Evidence

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260514T142818Z
pytest with venv during sync: 613 passed in 14.90s
current phase safety gate: OK
source aligned with GitHub zip: OK
mpf --version: 0.1.90
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
database status: alembic_version=0002_phase5_customer_lifecycle; public_table_count=64; lanes=3; customers=1; job_runs=0; firewall_applies=1; abuse_states=0
runtime safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no
runtime listeners: v2rayA UI 127.0.0.1:2015; BTC backend 127.0.0.1:60010
firewall safety: no MPF/customer IPv4 firewall references detected; no MPF/customer IPv6 firewall references detected; no customer NAT redirects detected
Docker-managed local publish DNAT references for 127.0.0.1:2015 and 127.0.0.1:60010 are accepted limited-runtime local publish rules only
accepted limited runtime listeners remain local-only
current Phase 5 accepted / Phase 6 working safety gate passed
production customer traffic remains disabled
```

This server result proves only repository/server sync and report-only execution-gate availability. It does not authorize firewall apply, firewall verify, firewall rollback, iptables-restore, subprocess firewall calls, real adapter execution, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram. Apply, verify, rollback, and execution decisions remain BLOCKED.

### Phase 6 No-Customer Apply/Verify/Rollback Execution Acceptance Package — Report-Only

- execution acceptance package report only
- no-customer package is artifact-only/in-memory
- non-executing
- non-authorizing for runtime
- no firewall apply
- no firewall verify
- no firewall rollback
- no iptables-restore
- no subprocess firewall calls
- no real adapter execution
- no customer NAT
- no customer firewall rules
- no production traffic
- no DB writes
- no restore point writes
- no lock acquisition
- final_decision remains BLOCKED
- apply_decision remains BLOCKED
- verify_decision remains BLOCKED
- rollback_decision remains BLOCKED
- execution_allowed remains false

Purpose: execution acceptance package for future controlled no-customer apply/verify/rollback is now modeled and inspectable, but future runtime execution still requires separate explicit runtime execution approval, operator approval, and fresh farm5 runtime evidence.

### Phase 6 farm5 Time Synchronization — Server Evidence

```text
date -Is: 2026-05-14T10:19:31+03:30
timedatectl: Local time Thu 2026-05-14 10:19:31 +0330; Universal time Thu 2026-05-14 06:49:31 UTC; Time zone Asia/Tehran (+0330); System clock synchronized: yes; NTP service: active; RTC in local TZ: no
timedatectl show: Timezone=Asia/Tehran; NTP=yes; NTPSynchronized=yes; TimeUSec=Thu 2026-05-14 10:19:31 +0330
timesync-status: Server=194.225.150.25; Poll interval=1min 4s; Leap=normal; Version=4; Stratum=2; Root distance=85.822ms; Offset=+44us; Delay=1.862ms; Jitter=16us; Packet count=2
configured NTP source: /etc/systemd/timesyncd.conf.d/10-mpf-intranet-ntp.conf -> [Time] NTP=194.225.150.25 158.252.7.7; FallbackNTP=
journal evidence: systemd-timesyncd contacted 194.225.150.25:123; initial clock synchronization completed
context: farm5 has no public internet access and now uses intranet-accessible NTP; previous ntp.ubuntu.com timeout issue resolved
```

This server result resolves the previous farm5 time synchronization blocker for future write-dependent gate planning. It does not authorize restore point writes, lock acquisition, DB apply writes/records, firewall write/apply/rollback/verify, iptables-restore, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram. Apply and gate-review final decisions remain BLOCKED. Future controlled restore point + lock + DB apply record acceptance still requires a separate explicit gate and farm5 evidence.

## Current Server Warning

Time synchronization warning status on `farm5` is now resolved with accepted server evidence:

```text
historical note: unsynchronized state was observed previously
System clock synchronized: yes
NTPSynchronized: yes
NTP source: 194.225.150.25
NTP service: active
```

Historical context remains important: time synchronization must still be re-checked before any future production/write/usage/abuse gate.

## What Is Allowed Now

Allowed work is limited to **Phase 6 — Firewall Planner** preparation and planning-only implementation:

```text
- repository/documentation cleanup that preserves the current gate
- firewall desired-model design and implementation
- firewall planner/diff design and implementation
- human-readable and JSON plan output
- dry-run evidence generation
- planner tests and safety regression tests
- proxy/backend safety checks that preserve internal reachability + external non-exposure contracts
```

## What Is Forbidden Now

Do not implement, run, or activate:

```text
- production traffic
- customer NAT redirects
- customer firewall rules
- live firewall apply
- iptables-restore
- usage timers
- hash-rate/share collectors
- abuse runner automation
- block or pause automation
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
- public API binding
- public v2rayA UI exposure
- public backend exposure
```

Live firewall apply remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.

## Next Planned Step

Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing.
Phase 6-H is accepted as dedicated apply gate entry criteria / authorization boundary only, documentation/test-only and non-authorizing.

Phase 6-G does not authorize host production firewall mutation, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, restore point writes, lock acquisition, DB writes, migrations, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

- Phase 6-G and Phase 6-H remain accepted historical safety sub-steps only.
- Apply Slice 1 has been server-synced and accepted only as a documentation/test-only readiness boundary.
- Apply Slice 2 has been server-synced and accepted only as a documentation/test-only readiness boundary.
- Apply Slice 1 and Slice 2 are server-synced and accepted only as documentation/test-only readiness boundaries.
- Apply Slice 3 and Slice 4 are server-synced and accepted only as documentation/test-only boundaries.
- The explicitly gated read-only `iptables-save` snapshot path is authorized and has successful farm5 evidence.
- No firewall write/apply/rollback/verify, `iptables-restore`, restore point write, lock acquisition, DB apply write/record, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
- Apply and gate-review final decisions remain BLOCKED.
- Next implementation target: explicit controlled restore point + lock + DB apply record acceptance gate, still without customer NAT/customer firewall rules and still requiring fresh farm5 evidence.
- Historical/reference context only: Next planning target is Future Dedicated Phase 6 Apply Gate Proposal/Review.
- Future Dedicated Phase 6 Apply Gate Proposal/Review remains historical/reference context only.
- Future dedicated Phase 6 apply gate remains not accepted and not authorized.
- No dedicated apply gate, manual canary apply, no-customer apply, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, restore point writes, lock acquisition, DB writes, migrations, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
- Live apply remains forbidden until a dedicated apply gate is explicitly accepted.

## Current Safety Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = limited_runtime_local_only
customer_onboarding_allowed = db_only
```

Any patch that bypasses these invariants or introduces traffic-changing behavior before the correct accepted phase must be rejected.

## Backend Port Invariant

Backend ports are internal service ports. They must be blocked from direct external/public access only while remaining reachable from valid internal server and Docker paths.

Required proxy/firewall doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by blocking loopback, local server paths, required Docker/internal paths, or the future MPF-owned NAT redirect path.

## Phase 5 Gate Status

Phase 5 is accepted and closed.

Current Phase 5 state is:

```text
customer CRUD works in DB only
policy history is preserved
events/audit are recorded for DB-only customer mutations
port/lane collisions are validated
no iptables rule is created
no NAT redirect is created
no runtime customer traffic is enabled
```

Future customer records remain DB-only until Phase 6 apply and customer NAT/customer firewall gates are accepted.


Phase 6-H reference:

```text
docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md
docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md
```


### Phase 6 Read-Only Live Snapshot Gate — Limited Authorization

- limited authorization: iptables-save read-only snapshot only
- no iptables-restore
- no firewall write
- no apply
- no rollback
- no restore point write
- no lock acquisition
- no DB apply write
- no DB apply record
- no customer NAT
- no customer firewall rules
- no production traffic
- no usage automation
- no abuse automation
- no UI
- no Telegram
- output is inspection-only
- failure must be fail-closed
- empty snapshot fallback is forbidden
- guessed firewall state is forbidden
- result may feed parser/planner/diff only
- apply/gate-review final decision must remain BLOCKED


### Phase 6 No-Customer Runtime Execution Approval Readiness — Report-Only

```text
Readiness/approval surface exists as report-only, non-executing, and non-authorizing
final_decision: BLOCKED
execution_allowed: false
operator approval still required
fresh farm5 runtime execution evidence still required
separate runtime execution PR still required
no firewall apply/verify/rollback
no iptables-save execution added by this PR
no iptables-restore
no subprocess firewall calls
no customer NAT
no customer firewall rules
no production traffic
no usage automation
no abuse automation
Current State block unchanged
```


## Accepted Server Sync Result — farm5 synced to 0.1.110

- farm5 synced to 0.1.110 using the fixed bootstrap sync path:
  sudo bash "/tmp/tmp.qmZaC8UsaG/proxy-address-mining-main/scripts/sync_main_zip_on_server.sh" /tmp/proxy-address-mining-main.zip
- backup path: /var/backups/mpf/source-before-zip-sync-20260515T192056Z
- mpf --version: 0.1.110
- pytest during sync: 701 passed in 68.84s
- manual pytest after sync: 701 passed in 65.21s
- mpf config validate: OK
- mpf doctor: OK
- db status: OK
- database: OK
- alembic_version: 0002_phase5_customer_lifecycle
- public_table_count: 64
- lanes: 3
- customers: 1
- job_runs: 0
- firewall_applies: 1
- abuse_states: 0
- current customer list: no non-deleted customers
- proxy doctor/status: OK
- proxy runtime remains limited local-only
- v2rayA UI listener local-only: 127.0.0.1:2015
- BTC backend listener local-only: 127.0.0.1:60010
- no MPF/customer IPv4 firewall references detected
- no MPF/customer IPv6 firewall references detected
- no customer NAT redirects
- Docker-managed local publish DNAT rules for 127.0.0.1:2015 and 127.0.0.1:60010 are informational only in accepted limited runtime
- firewall.apply_mode: plan_only
- proxy.runtime_activation_allowed: false
- production_traffic: none
- firewall_apply_allowed: no
- abuse_automation_allowed: no
- current Phase 7 accepted / Phase 8 working safety gate passed
- no runtime gate opened
- runtime restrictions remain unchanged
- sync script final verdict:
  OK: GitHub main zip synced successfully.
  OK: server source is aligned with GitHub zip.
  OK: accepted current phase gate is installed and verified.
  OK: Runtime remains limited local-only; production customer traffic is still disabled.


### Phase 8 Abuse State-Machine Contract Boundary

- This PR defines the abuse state-machine contract only.
- This PR does not run an abuse runner.
- This PR does not write abuse_states.
- This PR does not write abuse_events.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- This PR does not mutate firewall rules.
- This PR does not enable iptables-restore.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- The mandatory state path is normal -> over_tracking -> over_grace -> hard.
- farms-over alone must not harden.
- worker-over alone must not harden.
- sustained miner-abuse hardens after about 3600 seconds.
- all active customers in enabled lanes must be covered.
- no silent skip is allowed.
- runtime implementation remains future-gated.


### Phase 8 Abuse Evidence/Reporting Contract Boundary

State:
- This PR defines the abuse evidence/reporting contract only.
- This PR does not run an abuse runner.
- This PR does not read DB customers.
- This PR does not read abuse_states.
- This PR does not write abuse_states.
- This PR does not write abuse_events.
- This PR does not read usage_samples.
- This PR does not write usage_samples.
- This PR does not read policy_events.
- This PR does not write policy_events.
- This PR does not read live conntrack.
- This PR does not read live firewall counters.
- This PR does not run iptables-save.
- This PR does not mutate firewall rules.
- This PR does not enable iptables-restore.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- It defines future evidence source, evidence snapshot, customer evaluation report, coverage report, missing evidence report, operator summary, and failure-mode report contracts.
- Missing evidence must be explicit and must not harden.
- Stale evidence must be explicit and must not harden.
- Farms-over alone must remain report-only and must not harden.
- Worker-over alone must remain report-only and must not harden.
- All active customers in enabled lanes must appear in future coverage reports.
- No silent skip is allowed.
- Runtime implementation remains future-gated.


### Phase 8 Abuse Dry-Run Evaluator Boundary

State:
- This PR defines the abuse dry-run evaluator only.
- This PR evaluates synthetic/in-memory examples only.
- This PR does not evaluate real customers.
- This PR does not run an abuse runner.
- This PR does not read DB customers.
- This PR does not read abuse_states.
- This PR does not write abuse_states.
- This PR does not write abuse_events.
- This PR does not read usage_samples.
- This PR does not write usage_samples.
- This PR does not read policy_events.
- This PR does not write policy_events.
- This PR does not read live conntrack.
- This PR does not read live firewall counters.
- This PR does not run iptables-save.
- This PR does not mutate firewall rules.
- This PR does not enable iptables-restore.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- It defines pure dry-run transition proposals for normal, over_tracking, over_grace, and hard.
- It may compute would_transition and would_harden for synthetic input only.
- It must keep transition_allowed=false and hardening_allowed=false.
- Missing evidence must block hardening.
- Stale evidence must block hardening.
- Farms-over alone must remain report-only and must not harden.
- Worker-over alone must remain report-only and must not harden.
- Sustained miner-abuse after about 3600 seconds may produce would_harden=true only in dry-run output.
- All active customers in enabled lanes must remain a future coverage requirement.
- No silent skip is allowed.
- Runtime implementation remains future-gated.


### Phase 8 DB-Only Controlled Transition Readiness Boundary

State:
- This PR defines DB-only controlled transition readiness only.
- This PR does not execute DB transitions.
- This PR does not connect to PostgreSQL.
- This PR does not read DB customers.
- This PR does not read abuse_states.
- This PR does not write abuse_states.
- This PR does not write abuse_events.
- This PR does not read usage_samples.
- This PR does not write usage_samples.
- This PR does not read policy_events.
- This PR does not write policy_events.
- This PR does not create migrations.
- This PR does not create scheduler jobs.
- This PR does not evaluate real customers.
- This PR does not run an abuse runner.
- This PR does not read live conntrack.
- This PR does not read live firewall counters.
- This PR does not run iptables-save.
- This PR does not mutate firewall rules.
- This PR does not enable iptables-restore.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- It defines future transition intent, DB mutation plan, audit payload, restore-reference payload, idempotency, and operator approval contracts.
- It may compute would_write_abuse_state and would_write_abuse_event only as future-intent in report output.
- It must keep writes_allowed=false and execution_allowed=false.
- Missing evidence must block DB transition planning.
- Stale evidence must block DB transition planning.
- Farms-over alone must remain report-only and must not harden.
- Worker-over alone must remain report-only and must not harden.
- Sustained miner-abuse after about 3600 seconds may produce future hard-state DB write intent only in report output.
- Any real DB execution must come in a later explicitly gated PR with fresh farm5 evidence.
- Runtime implementation remains future-gated.


### Phase 8 Runtime Worker Dry-Run Harness Boundary

State:
- This PR defines runtime worker dry-run harness only.
- This PR does not start an abuse worker.
- This PR does not enable scheduler jobs.
- This PR does not enable timers.
- This PR does not enable abuse runner.
- This PR does not evaluate real customers.
- This PR does not execute DB transitions on real customers.
- This PR does not connect to production DB for worker execution.
- This PR does not mutate firewall rules.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- It defines synthetic worker-cycle dry-run harness behavior only.
- It defines explicit skip reporting, no-work reporting, kill-switch behavior, lock-contention behavior, idempotency duplicate behavior, batch-limit behavior, and failure-mode behavior.
- Missing/stale evidence must not harden.
- DB failure must not harden.
- Firewall failure must not harden.
- Lock contention must report explicit skip; no silent skip is allowed.
- Runtime worker execution remains future-gated and requires fresh farm5 evidence.


### Phase 8 Controlled Worker Pre-Acceptance Boundary

- This PR defines controlled worker pre-acceptance only.
- This PR does not start an abuse worker.
- This PR does not enable scheduler jobs.
- This PR does not enable timers.
- This PR does not enable abuse runner.
- This PR does not evaluate real customers.
- This PR does not execute DB transitions on real customers.
- This PR does not connect to production DB for worker execution.
- This PR does not mutate firewall rules.
- This PR does not enable customer NAT/customer firewall rules.
- This PR does not enable production traffic.
- This PR does not apply hard/soft blocks.
- This PR does not apply pause automation.
- It defines the prerequisites required before any future controlled worker dry-run on farm5.
- It requires fresh farm5 sync/test evidence before controlled worker dry-run.
- It recommends batching sync for 0.1.116, 0.1.117, and 0.1.118 if this PR remains report-only.
- It requires operator approval before future controlled worker dry-run.
- It requires kill-switch, lock, explicit skip, no-silent-skip, and fail-closed behavior.
- Runtime worker execution remains future-gated.


## Accepted server result updates

- farm5 0.1.158 sync/test evidence recorded: sync OK, pytest OK, doctor/db/proxy doctor OK, plan mode non-mutating, execute-control blocked on `real_restore_backup_adapter_missing`; Current State remains unchanged and Phase 11 remains not accepted.
- Phase 11 farm5 0.1.178 planning/readiness note: added read-only canary usage evidence capture (`mpf production canary-usage-evidence-capture`) and operator execution context guard (`mpf production operator-context`) to prevent local-peer DB-write execution as root while preserving read-only root status checks; Current State gate values remain unchanged and Phase 11 remains not accepted.


- Phase 11 farm5 0.1.185 planning/readiness note: added source-backed canary worker/Stratum evidence capture for unique worker visibility and Stratum subscribe/authorize/notify evidence; Current State unchanged; Phase 11 not accepted; production traffic none; customer onboarding db_only; abuse automation/UI/Telegram closed.

- 2026-05-23 (farm5, v0.1.188 planning/readiness): added source-backed canary final-check-report visibility and rollback/restore-plan visibility artifacts; acceptance remains BLOCKED pending conntrack_assured/forwarder_pool_seen/bridge_loopback_seen evidence.

- 0.1.191: Added read-only `mpf production canary-evidence-pack` planning/readiness evidence orchestration. Phase 11 remains not accepted and Current State gate values unchanged.
- 0.1.193: Phase 11 planning/readiness canary evidence-pack fix merges exact-scope PRESENT usage visibility evidence into visibility-bundle inputs; Current State unchanged, Phase 11 remains not accepted, production_traffic remains none, customer_onboarding_allowed remains db_only, abuse_automation_allowed remains no, ui/telegram remain no.
- 0.1.192: Phase 11 planning/readiness wiring update for canary evidence-pack visibility artifact integration, UTF-8 BOM tolerant external transcript import, and forwarder diagnostics hardening; Current State unchanged, Phase 11 remains not accepted, production_traffic remains none, customer_onboarding_allowed remains db_only, abuse_automation_allowed remains no, ui/telegram remain no.


0.1.202 planning/readiness: isolated the Phase 11E single-customer staging create-failure test from real farm5 DB state after DB-only staging while preserving closed apply/traffic gates.
0.1.201 planning/readiness: recorded farm5 0.1.200 single-customer DB-only staging evidence and added non-mutating single-customer firewall/NAT plan gate while preserving closed apply/traffic gates.

- farm5 0.1.227 Phase 11E limited activation execution evidence note: `limited-btc-001` transitioned `paused -> active` through the DB-only controlled activation path; `canary-btc-001` remained active; no firewall/NAT/runtime change occurred; production/miner traffic remains closed; abuse automation remains disabled; Phase 11 remains not accepted. Post-evidence classified READY with `blockers=[]` and warning `source_evidence_not_provided_db_proxy_checks_unavailable`; the helper forwarding fix in 0.1.228 allows optional source-backed DB/proxy evidence to be supplied on recollection.

- 0.1.231 planning/readiness note: recorded farm5 0.1.230 observation-window/final-readiness READY evidence and added a read-only explicit limited acceptance decision gate for `limited-btc-001` while preserving `canary-btc-001`. Current State is unchanged; Phase 11 final acceptance, production expansion, miner traffic expansion, abuse automation, UI, and Telegram remain closed. A READY decision gate only prepares `phase11_controlled_boundary_acceptance_package_pr`.

## Historical/reference-only pre-final-acceptance Current State snapshot

The following snapshot is retained only so historical Phase 11 evidence and regression tests can be interpreted. It is non-authorizing and must not be parsed as the authoritative `## Current State` block.

```text
current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```


## 0.1.256 Phase 11 live-ready controlled artifact reapply readiness package

- Adds `mpf production controlled-artifact-reapply-readiness --output json` and `scripts/phase11_controlled_artifact_reapply.sh --readiness` as an operator-reviewable live-ready readiness/package review surface only.
- This does not execute `iptables-restore`, does not apply firewall changes, does not call controlled artifact execute, and does not mutate DB, firewall, Docker, systemd, conntrack, customer, abuse, or policy state.
- `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`; production traffic and onboarding remain `controlled_cli_limited`.
- Phase 12, worker enforcement, UI, Telegram, timers, daemons, public backend/API, and unrestricted production remain closed.
- When readiness is READY, the next required step becomes `sync_and_review_live_ready_controlled_artifact_reapply_package_on_farm5`; otherwise it remains `prepare_live_ready_controlled_artifact_reapply_package`.


## 0.1.257 Phase 11 live-ready verified packet-path reapply package

This update creates a live-ready package/review artifact from the verified packet-path/filter-hook binding. It still does not execute `iptables-restore`, does not apply firewall changes, does not accept restart/autostart proof, and does not accept Full CLI Production Operations. Phase 12, worker enforcement, UI, Telegram, timers, daemons, public backend/API, and unrestricted production remain closed; production traffic and customer onboarding remain `controlled_cli_limited`.
