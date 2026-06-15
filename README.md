# Proxy Address Mining

0.1.268 controlled post-apply verification note: fixes the Phase 11 controlled artifact reapply verification chain by deriving/propagating `expected_backend_target` from the reviewed package backend target, normalizing live `iptables-save` colon chain declarations against restore-payload `-N` declarations, and verifying exact post-apply controlled artifacts without treating expected live MPF artifacts as unknown. Do not rerun the 0.1.267 execute path. After offline sync to farm5, run only read-only/package/preflight first; guarded execute is allowed only after 0.1.268 tests and fresh READY evidence.

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed greenfield rewrite of a mining customer gateway control plane.

It preserves the required operational capabilities of the old shell-script setup, but it must not become a direct migration, patch series, or extension of those old scripts.

## Current Status

0.1.267 controlled execute recovery note: farm5 0.1.266 proved guarded execute reached `iptables-restore --test --noflush` and `iptables-restore --noflush` with `apply_succeeded=true`, but post-apply verification failed closed because the current artifact gate used a narrower allowlist than the official controlled artifact taxonomy and did not carry the resolved backend target consistently. The immediate recovery used a manually reviewed exact-inverse rollback from the package rollback_plan; rollback test passed, rollback apply succeeded, and the post-rollback gate returned `PASS_NO_CUSTOMER_ARTIFACTS` with MPF/proxy doctors OK and production gates still closed. Before any new execute, taxonomy/gate/post-verify alignment and the reviewed exact-inverse rollback executor path are required.

0.1.253 controlled verified filter-hook binding note: farm5 source-backed 0.1.252 packet-path READY evidence is now represented by an explicit read-only binding mode `verified_docker_user_forward_post_dnat`. Progression flags are `controlled_filter_packet_path_evidence_ready=true`, `controlled_filter_packet_path_verified=true`, `artifact_graph_binding_ready=true`, `desired_artifact_semantics_complete=true`, and `controlled_artifact_reapply_package_evidence_ready=true (template/evidence-only, not live-ready)` when generated and verified from the packet-path bundle. This is package-template/evidence-only: `production_execution_available=false`, `live_ready_package_available=false`, `restart_autostart_proof=missing_or_partial`, `full_cli_production_operations=missing_or_partial`, `phase12_start_allowed=no`, `worker_enforcement_allowed=no`, `ui_allowed=no`, and `telegram_allowed=no`; no firewall apply, package execution, or farm5 mutation is claimed.


0.1.254 controlled packet-path compatibility note: integrity-valid source-backed 0.1.252 packet-path bundles are accepted by the 0.1.254 verifier for verified filter-hook binding and template-only package evidence, while tampered bundles fail closed, legacy 0.1.251 bundles still require recollection, and all execution gates remain blocked (`production_execution_available=false`, `iptables_restore_invocation_allowed=false`, `controlled_artifact_execute_available=false`, `live_ready_package_available=false`, `phase12_start_allowed=no`, `worker_enforcement_allowed=no`, `ui_allowed=no`, `telegram_allowed=no`). No farm5 access or mutation is claimed.

`docs/PHASE_STATUS.md` is the authoritative source of truth for the current phase gate.


0.1.252 controlled filter packet-path topology note: packet-path evidence now uses schema-versioned topology proof with independently reported backend container, Docker network identity, bridge resolution, route, bridge-membership, firewall-parse, and scenario packet-path statuses. Docker bridge names may be verified from either the explicit bridge option or the derived `br-<first 12 hex chars of verified NetworkID>` default, never EndpointID; NetworkID and EndpointID remain separate. The legacy 0.1.251 packet-path bundle remains integrity-verifiable but requires 0.1.252 recollection before readiness. Renderer binding, artifact package generation, production execution, runtime packet observation, and Phase 12 remain blocked; no farm5 access or mutation occurred. The next required operator step remains a new 0.1.252 sync and read-only recollection on farm5.

0.1.251 controlled filter packet-path evidence note: static packet-path collection and offline verification capability is implemented for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`; no farm5 packet-path evidence was collected by this PR, no runtime packet was observed, no hook was proven on farm5 during PR development, and no firewall, Docker, systemd, conntrack, PostgreSQL, customer, policy, block, pause, or abuse mutation occurred. Controlled artifact package generation remains blocked by `controlled_filter_packet_path_unresolved`; artifact graph binding and production execution remain unavailable; post-DNAT hook and match semantics require a future reviewed binding PR after a source-backed farm5 bundle. Current progression flags are `read_only_reapply_foundation_implemented=true`, `controlled_filter_packet_path_evidence_capability_implemented=true`, `controlled_filter_packet_path_evidence_ready=false`, `controlled_filter_packet_path_verified=false`, `artifact_graph_binding_ready=false`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`; `restart_autostart_proof` and `full_cli_production_operations` remain `missing_or_partial`. The next required step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; a future READY bundle recommends `review_and_bind_verified_filter_hook_and_match_semantics_to_controlled_artifact_graph`, not execution. `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

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

Phase 11 is accepted: controlled CLI-limited production/customer activation is ready on farm5 for the limited BTC boundary only. The stable runtime contract remains local-only: `127.0.0.1:60010 -> forwarder -> v2rayA -> pool`. The accepted artifact evidence recorded `172.18.0.3:60010`, but future runtime correctness must not depend on that Docker container IP.

The accepted boundary remains Phase 11 controlled_cli_limited BTC operation. The current working gate is Phase 11 operational completion — Full CLI Production Operations. Phase 12 — Worker Policy Enforcement is blocked until operational completion acceptance. UI and Telegram remain later phases. Unrestricted production expansion and unrestricted miner expansion remain closed. Version 0.1.252 implements a source-backed controlled two-customer artifact renderer and production adapter vertical slice: `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, and `live_ready_package_available=false`. Public production execute remains unavailable until the filter packet path is proven; package generation blocks on `controlled_filter_packet_path_unresolved` plus any snapshot/schema/target/phase/drift/backup/audit/rollback/verification issue. The current next implementation step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; restart/autostart proof remains `missing_or_partial`, Full CLI Production Operations remains unaccepted, and Phase 12/worker enforcement/UI/Telegram/timer-daemon automation remain blocked.

Full CLI Production Operations acceptance must prove restart/autostart, production customer lifecycle execution, production firewall plan/apply/verify/rollback for real customer ports, CLI onboarding, usage/report/check evidence, abuse runner coverage for all active customers in all enabled lanes, pause/block/expire-run controls, backup/restore drill, and final acceptance that advances `production_traffic` and `customer_onboarding_allowed` to `cli_production`. Until that final acceptance PR lands, the current gate remains `controlled_cli_limited` and Phase 12 remains blocked.

0.1.247 farm5 post-sync evidence showed all three expected runtime containers healthy and both required listeners local-only, while known controlled Phase 11 firewall artifacts were absent after reboot and `unknown_mpf_artifacts` remained `[]`. Version 0.1.248 kept `restart_autostart_proof=missing_or_partial` and pointed the operator next step to `implement_controlled_artifact_reapply_execute_package`; version 0.1.252 supersedes that with `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; it does not start a new phase, open Phase 12, run Docker repair, or accept Full CLI Production Operations.

Historical compatibility anchors are kept in docs/HISTORICAL_COMPATIBILITY_ANCHORS.md.


## Current Accepted/Working Boundary (Phase 11 accepted / Phase 11 operational completion working)

`docs/PHASE_STATUS.md` is authoritative. Current state is accepted Phase 11 controlled_cli_limited BTC operation / working Phase 11 operational completion — Full CLI Production Operations. Phase 12 Worker Policy Enforcement is blocked until operational completion acceptance. `docs/AI_SAFE_RUNTIME_FIRST.md` remains a safety contract and does not open unrestricted gates by itself.

Current gate values remain:

```text
production_traffic=controlled_cli_limited
firewall_apply_allowed=controlled
abuse_automation_allowed=controlled_operator_gated
customer_onboarding_allowed=controlled_cli_limited
proxy_data_plane_allowed=limited_runtime_local_only
worker_enforcement_allowed=no
ui_allowed=no
telegram_allowed=no
phase12_start_allowed=no
live_snapshot_read_allowed=iptables_save_read_only
restore_lock_record_execution_allowed=controlled_boundary_only
```

Current advancement target is Phase 11 operational completion — Full CLI Production Operations. Phase 12 — Worker Policy Enforcement is blocked until operational completion acceptance. Phase 11 is accepted only for controlled CLI-limited production/customer activation. Historical anchors only: Phase 8 Abuse 1h Core, Phase 9 Check / Report / Diagnostics, and Phase 10 Session / Worker / Policy / Share Timeline are completed accepted context and are not active implementation targets unless `docs/PHASE_STATUS.md` explicitly reopens them.

Phase 6 apply-gate materials (D1/E0/E1/E2/E3/F/G/H and apply slices) are historical/reference-only context and remain non-authorizing for current active work. Phase 6 Dedicated Apply Gate Proposal/Review is historical/completed context. Apply Slice 3 and Apply Slice 4 are server-synced and accepted only as documentation/test-only boundaries. Historical compatibility anchor: Future Dedicated Phase 6 Apply Gate Proposal/Review.

Only the controlled CLI-limited Phase 11 boundary is authorized. Unrestricted production/miner expansion, direct DB/firewall edits, worker enforcement, UI, and Telegram remain unauthorized.

Historical/reference-only notes from accepted Phase 6 boundaries:

```text
repository/documentation cleanup that preserves phase gates
firewall desired-state model refinement
firewall planner/diff contracts
human-readable firewall plan/report output
machine-readable JSON firewall plan/report output
offline snapshot parser and file-backed offline diff fixtures
offline restore payload artifacts
offline apply-readiness contracts
offline apply package reports
offline rollback artifacts from explicit snapshot files
offline preflight inspection/failure matrix
planner/contract/preflight safety tests
proxy/backend safety checks that preserve internal reachability and external non-exposure
```

Forbidden now:

```text
unrestricted production traffic expansion
unrestricted miner traffic expansion
customer onboarding outside the controlled CLI/service-layer path
direct or ad-hoc customer NAT redirects outside the accepted planner/service-layer path
direct or ad-hoc customer firewall rules outside the accepted planner/service-layer path
firewall apply, rollback, or verify outside the controlled operator-gated path
unauthorized iptables-save execution
iptables-restore execution outside the accepted controlled path
conntrack flush outside the relevant runtime gate
usage timers or daemon starts outside an explicit accepted gate
high-volume hash-rate/share collectors without retention and partition review
unrestricted abuse runner or background automation outside the controlled boundary
worker automation
block or pause automation outside an explicit accepted gate
local UI service
buyer UI service
Telegram bot
production customer import outside the controlled CLI-limited path
worker enforcement before Phase 11 operational completion acceptance
public API binding
public v2rayA UI exposure
public backend exposure
```

Required invariants remain:

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = controlled_cli_limited
firewall_apply_allowed = controlled
abuse_automation_allowed = controlled_operator_gated
customer_onboarding_allowed = controlled_cli_limited
proxy_data_plane_allowed = limited_runtime_local_only
worker_enforcement_allowed = no
ui_allowed = no
telegram_allowed = no
live_snapshot_read_allowed = iptables_save_read_only
restore_lock_record_execution_allowed = controlled_boundary_only
```

## Implemented So Far

```text
Phase 0 architecture and safety contracts
Phase 1 preflight/bootstrap runbook and Ubuntu 24.04 bootstrap script
safe CLI smoke skeleton
config validator
PostgreSQL DB ping helper
SQLAlchemy model skeletons
Alembic bootstrap
Phase 2 schema representation and migration accepted on farm5
Phase 3 read-only CLI/API foundation accepted on farm5
Phase 3.1 official runtime alignment accepted on farm5
read-only DB status, lane list, customer list, and job status commands
service/repository boundaries for CLI/API commands
internal API foundation with stable read-only response DTOs
foundation taxonomy and request context/correlation_id contracts
future-ready buyer/account and worker-policy boundaries
extension-ready control-plane schema contracts
pytest CI on GitHub Actions
backend internal/external reachability policy contract
accepted/rejected hash-rate and share observability contract
Phase 4 limited local-only proxy runtime accepted on farm5
Phase 5 DB-only customer CRUD accepted on farm5
Phase 6 firewall planner accepted on farm5 as planner/reporting/gate-readiness
Phase 7 usage + policy/reject accounting accepted on farm5 as report-only/service-contract/readiness
Phase 8 Abuse 1h Core accepted on farm5 as evidence/readiness only
Phase 9 Check / Report / Diagnostics accepted on farm5 as report-only/final diagnostics
Phase 10 Session / Worker / Policy / Share Timeline accepted on farm5
Phase 11 Production / Customer Activation Gate accepted on farm5 for controlled CLI-limited BTC operation
```

## Not Open or Not Implemented Yet

The accepted Phase 11 boundary is intentionally limited. The following unrestricted or later-phase capabilities remain closed:

```text
unrestricted production customer traffic expansion
unrestricted miner traffic expansion
firewall apply or rollback outside the controlled operator-gated path
customer NAT redirects or customer firewall rules outside the accepted planner/service-layer path
usage timers or daemon starts outside an explicit accepted gate
high-volume hash-rate/share collectors without retention and partition review
unrestricted abuse runner or background automation
block/pause automation outside an explicit accepted gate
local UI
buyer UI
Telegram bot
authentication/billing
worker enforcement before Phase 11 operational completion acceptance
unrestricted production import
```

## Project Objective

Build a new MPF control plane that preserves the operational capabilities of the old shell-based setup while replacing it with a testable Python architecture.

The target system is:

```text
Python-first
API-first
PostgreSQL-backed
service-layer based
lane-based
firewall-plan based
safety-gated
AI-safe Runtime-first
future-ready for local UI, buyer UI, Telegram, worker intelligence, and hash-rate/share observability
```

## Target Data Plane

The server is a forward-only customer gateway:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

The first stable lane is BTC:

```text
BTC customer ports -> backend 60010 -> forwarder -> v2rayA -> pool
```

Future coins such as ZEC and LTC must be implemented through the lane model. Do not clone scripts per coin.

## Fixed Architecture Decisions

```text
server role: forward-only customer gateway
source of truth: local PostgreSQL
code path: /opt/mpf-py
config path: /etc/mpf/mpf.yaml
data path: /var/lib/mpf
logs path: /var/log/mpf
backup path: /var/backups/mpf
CLI name: mpf
first lane: BTC
BTC backend port: 60010
firewall backend: iptables first
future firewall apply mechanism: iptables-save / iptables-restore after explicit apply gate
scheduler: systemd timers
initial/current firewall mode: plan_only
local API/UI binding: 127.0.0.1 or Unix socket only
```

## API-First Rule

Business logic must live in domain/service modules.

Required flow:

```text
CLI / API / UI / Telegram / jobs
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Forbidden:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly writes DB
buyer UI directly mutates production state
Telegram directly runs shell commands
job bypasses service validation
```

## Source of Truth

PostgreSQL is the production source of truth.

Flat files and SQLite may be used only for:

```text
import from old scripts
export/debug artifacts
temporary migration tooling
generated restore artifacts
backups
```

They must not become production customer, firewall, usage, abuse, hash-rate, or share state.

## Mandatory Abuse Requirement

Miner-abuse handling is a core feature from day one.

Required state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Rules:

```text
all active customers in all enabled lanes must be scanned
no silent skip is allowed
exemption requires reason and expiry
farms-over alone must not harden
sustained miner-abuse hardens after about 3600 seconds
hard creates restore point and policy backup
hard uses firewall plan/apply/verify path after the relevant apply gate
hard flushes affected conntrack scope after the relevant runtime gate
manual unhard is audited
```

A patch that weakens this requirement must be rejected.

## Firewall Safety Model

Firewall changes must be model-driven.

Required future lifecycle:

```text
read DB/config
  -> build desired model
  -> compare desired with live firewall
  -> generate plan
  -> show human diff
  -> show JSON diff
  -> create restore point
  -> backup live firewall
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event/audit
  -> rollback or rollback-plan on failure
```

Forbidden production pattern:

```text
ad-hoc iptables commands
one-off NAT redirects
interface-triggered firewall shell commands
```

Phase 6-H is accepted as historical documentation/test-only context. Apply Slice 3 and Apply Slice 4 are server-synced documentation/test-only boundaries. Historical compatibility anchor: Future Dedicated Phase 6 Apply Gate Proposal/Review. Live apply remains disabled until the Phase 11 Production / Customer Activation Gate explicitly accepts a controlled apply path.

## Backend Port Policy

Backend ports are internal service ports. They must be blocked from direct external/public access only while remaining reachable from valid internal server and Docker paths.

Required future doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not block loopback, required Docker/internal paths, or the future MPF-owned NAT redirect path just to hide backend ports externally.

## Hash-rate and Share Observability

Accepted/rejected hash-rate per device is a future first-class capability.

It must be planned through structured data and services:

```text
share evidence
share_events
device_hashrate_samples
customer_hashrate_samples
report services
UI charts from aggregate samples
retention before high-volume collection
```

Do not add this later as UI-only calculations, unstructured logs, or raw chart queries over high-volume events.

## Documentation Map

Start here:

```text
AGENTS.md
README.md
docs/INDEX.md
docs/PHASE_STATUS.md
docs/AI_CODING_RULES.md
docs/AI_PHASE_11_TASK.md
docs/PRODUCTION_ACTIVATION_GATE.md
docs/AI_SAFE_RUNTIME_FIRST.md
```

Core contracts:

```text
docs/ARCHITECTURE.md
docs/SAFETY.md
docs/ROADMAP.md
docs/DATA_MODEL.md
docs/FIREWALL.md
docs/ABUSE.md
docs/FUTURE_EXTENSIONS.md
docs/TAXONOMY.md
docs/BACKEND_PORT_POLICY.md
docs/OBSERVABILITY_HASHRATE.md
```

Current phase and accepted result contracts:

```text
docs/PHASE_STATUS.md
docs/AI_PHASE_11_TASK.md
docs/PRODUCTION_ACTIVATION_GATE.md
docs/AI_SAFE_RUNTIME_FIRST.md
docs/AI_PHASE_10_TASK.md
docs/PHASE_10_FARM5_0_1_136_SYNC_TEST_EVIDENCE.md
docs/PHASE_8_FINAL_ACCEPTANCE_EVIDENCE.md
docs/PHASE_5_FINAL_ACCEPTANCE.md
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
docs/INTRANET_INSTALL.md
```

## Roadmap Summary

```text
Phase 0   — Architecture Freeze
Phase 1   — Preflight + Bootstrap Without Traffic Changes
Phase 2   — PostgreSQL + Config + Domain Model
Phase 3   — CLI + Internal API Foundation
Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
Phase 4   — Compose Forward-only + Proxy Doctor
Phase 4.1 — Compose Template + Server Config Planning
Phase 4.2 — Runtime Activation Runbook Planning
Phase 4 Review — Runtime Activation Execution Review
Phase 4 Runtime — Limited Proxy Runtime Startup
Phase 5   — Customer CRUD in DB Only
Phase 6   — Firewall Planner + Apply/Verify/Rollback
Phase 7   — Usage + Policy/Reject Accounting
Phase 8   — Abuse 1h Core
Phase 9   — Check / Report / Diagnostics
Phase 10  — Session / Worker / Policy / Share Timeline
Phase 11  — Production / Customer Activation Gate
Phase 12  — Worker Policy Enforcement
Phase 13  — Local UI
Phase 14  — Operator UI Actions
Phase 15  — Telegram
```

Do not start a later phase until the current phase acceptance gate passes.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This warning is not a Phase 11 documentation/planning blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Security Guardrails

```text
never expose backend ports publicly
never block backend ports from valid internal paths
never expose v2rayA UI publicly
never expose early Web UI/API publicly
never hardcode Telegram tokens
secrets must live outside the repository
firewall changes must be auditable
dangerous actions need restore points
direct DB edits are not normal operation
direct iptables edits are not normal operation
buyer UI must not directly mutate production state
worker block must not be modeled as firewall-only
hash-rate/share collectors need retention before activation
```

## License

License is not defined yet.

Choose and add a license before public or multi-person use.

Historical Phase 8 references: the Phase 8 abuse evidence/reporting contract, DB-only controlled transition readiness package, and DB-only controlled transition execution package are completed Phase 8 context only; they are not active targets.

Compatibility anchors for historical Phase 8 report surfaces:

```text
DB-only controlled transition readiness package
report-only/non-mutating/non-authorizing
Current advancement target is the Phase 8 DB-only controlled transition execution package, manual and dry-run-by-default/non-runtime/non-authorizing.
Current advancement target is the Phase 8 runtime/worker integration readiness package, report-only/readiness-only/non-runtime/non-authorizing.
```

Historical gate reference: accepted_phase: Phase 7 — Usage + Policy/Reject Accounting accepted on farm5 / working_phase: Phase 8 — Abuse 1h Core planning/readiness.


0.1.251 controlled runtime-forward note: the source-backed controlled artifact renderer, schema-faithful metadata wiring, and production adapters are implemented, but the filter packet path remains fail-closed until source-backed farm5 evidence proves the correct hook for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`. No farm5 mutation was performed, no live `iptables-restore` was executed during PR development or CI, and no READY farm5 package has been collected. Progression is now `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`. The exact next step is `sync_and_collect_controlled_filter_packet_path_evidence_on_farm5`; server sync is allowed only for read-only package/evidence collection first, and controlled execution requires separate package review. `restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.
