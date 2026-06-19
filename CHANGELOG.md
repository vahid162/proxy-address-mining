# Changelog

## 0.1.299

- docs: establish canonical AI entrypoints by separating project orientation, dynamic phase state, task routing, and release history; no runtime gate, firewall, database, or service behavior changes.

## 0.1.298
- fix(phase11): recognize official 60046 generic activation artifacts in the current controlled artifact gate while keeping unknown artifacts and backend public exposure fail-closed.

## 0.1.297

- fix(phase11): classify Docker bridge-internal backend ACCEPT rules as non-public for generic real-customer activation verify while keeping real backend 60010 exposure fail-closed; enables item-9 readiness to proceed after verify plus first-connect DB evidence without accepting Full CLI Production Operations.

## 0.1.296

- feat(phase11): add official CLI path for generic real-customer activation package/preflight/apply/verify/transcript/first-connect/readiness; PR/CI does not execute runtime apply, Full CLI Production Operations remains unaccepted, `production_traffic` and `customer_onboarding_allowed` remain controlled_cli_limited, and Phase 12/worker/UI/Telegram remain closed. Next farm5 step is CLI regeneration/review followed by controlled apply only with all confirmations and `MPF_PHASE11_GENERIC_ACTIVATION_APPLY=1`.

## 0.1.295
- fix(phase11): fix generic real-customer activation package/preflight false blockers by normalizing empty/null deleted_at values and aligning accepted controlled MPF artifact taxonomy. Reinforce the 10-item Phase 11 matrix while keeping Full CLI Production Operations unaccepted, production_traffic/customer_onboarding_allowed controlled_cli_limited, no DB/firewall/NAT/runtime mutation, no iptables-restore, no Docker/systemd/conntrack changes, and no Phase 12/worker/UI/Telegram.

## 0.1.294
- feat(phase11): add generic activation execution runner, iptables-save verification conversion, transcript import, and first-connect DB evidence guards.

## 0.1.293

- feat(phase11): add generic real-customer activation as official item 9 before final acceptance, with fail-closed package/preflight/apply/verify/runtime/rollback readiness service contracts and gap inventory integration.

## 0.1.292

- fix(phase11): close pre-final CLI usability and readiness evidence inconsistencies without runtime mutation or final acceptance.

## 0.1.291

- feat(phase11): add non-destructive backup/restore drill readiness service, CLI, collector output, and gap inventory evidence consumption while keeping final acceptance and Phase 12 closed.

## 0.1.290

- fix(phase11): keep controls gap inventory evidence-driven so no-evidence server pytest remains fail-closed while explicit collector controls evidence can advance to backup_restore_drill.

## 0.1.289

- feat(phase11): define read-only customer block control-intent preflight so production controls pause/block/expire readiness can advance without DB, firewall, or runtime mutation.

## 0.1.288

- Stabilize Phase 11 post-sync validation by isolating farm5-sensitive gap inventory tests and resolving firewall completion wrapper/nested evidence handoff without runtime mutation or final acceptance.

## 0.1.287

- fix(phase11): align operational completion evidence progression after lifecycle execution by resolving nested restart proof evidence, validating firewall completion readiness JSON, correcting lifecycle readiness final decisions, and propagating onboarding context without runtime mutation or opening Phase 12/worker/UI/Telegram gates.

## 0.1.286

- fix(phase11): wires terminal no-reapply controlled-artifact readiness into Phase 11 gap inventory so gap inventory no longer reports a stale reapply package next step, while preserving no execution, no firewall apply, no DB mutation, no Phase 12, and no worker/UI/Telegram enablement.

## 0.1.285

- fix(phase11): treat exact-present controlled artifacts/no-reapply readiness as a terminal Phase 11 reapply state, fix stale `next_required_step` and no-reapply package blocker reporting, and preserve no execution, no firewall apply, no DB mutation, no Phase 12, and no worker/UI/Telegram enablement.

## 0.1.284

- fix(phase11): make customer update/disable dry-run peer-safe with read-only resolution so root-run controls readiness/gap inventory no longer false-report pause/expire dry-run failures. Real --yes writes remain guarded; no DB/firewall/runtime mutation; Phase 12/worker/UI/Telegram remain closed.

## 0.1.283
- feat(phase11): add read-only production controls pause/block/expire preflight readiness; pause/expire dry-runs are surfaced, block remains `block_capability_not_defined`, root non-`--yes` dry-runs can reach the service layer, nullable customer show mapping and blocked-status CLI validation are controlled.
## 0.1.282

- Added read-only Phase 11 firewall completion evidence bundle/preflight builder and verifier; no firewall apply, iptables-restore, rollback apply, DB mutation, Docker/systemd restart, conntrack flush, abuse execute, Phase 12 opening, or cli_production gate change.

## 0.1.281

- Align Phase 11 source evidence mutation classification so copied historical lifecycle evidence is reported separately from current collector-run mutation flags.
- Add target-aware read-only controlled artifact reapply diagnostics and a fail-closed production firewall apply/verify/rollback completion evidence contract.
- Keep Phase 11 operational completion blocked on `production_firewall_apply_verify_rollback`; no firewall apply, DB mutation, abuse execute, or Phase 12 opening is performed.

## 0.1.280

- Fix Phase 11 lifecycle evidence readiness/gap false-negative under root peer-auth DB read context by using the project read-only DB helper path for correlation checks.
- Fix operational surfaces collector lifecycle evidence pass-through and manifest/checksum recording.
- Fix `mpf abuse status --output json` compatibility while preserving read-only status semantics.
- No runtime mutation, firewall apply, abuse execute, final Phase 11 operational completion acceptance, or Phase 12 opening.
- Next runtime step after farm5 sync/test remains `production_firewall_apply_verify_rollback` if fresh evidence confirms the expected state.

## 0.1.279

- Harden Phase 11 controlled production customer lifecycle execution package/preflight/execute/verify around the farm5-proven `mpf` execution user.
- Add operator context, backup-root writability preflight checks, execute-time preflight rerun, controlled JSON error responses, orphan backup artifact reporting, and stricter verify correlation across backups, restore points, events, and audit rows.
- Keep lifecycle execute unrun in this PR; backup_restore_drill, Full CLI Production Operations, cli_production gates, Phase 12, worker enforcement, UI, and Telegram remain closed.

## 0.1.278

- Adds controlled exact-scope DB-only Phase 11 production customer lifecycle execution evidence for limited-btc-001 / btc / 20101.
- The path creates a reversible backup artifact, backups row, restore point, event, and audit row before updating safe lifecycle metadata only.
- Full CLI Production Operations, backup_restore_drill, unrestricted production, Phase 12, worker enforcement, UI, and Telegram remain closed.

## 0.1.277 - 2026-06-16

- Phase 11 runtime-first consolidation: resolved and propagated controlled backend targets into the current phase gate and firewall apply/rollback operational surface to avoid false unknown DNAT artifact blockers for known controlled artifacts.
- Upgraded production customer lifecycle execution readiness to aggregate read-only customer lifecycle, firewall, usage/report/check, restart/autostart, and abuse visibility surfaces while keeping Full CLI Production Operations unaccepted.
- Added `scripts/phase11_collect_operational_surfaces_evidence.sh` as the official read-only operational surfaces evidence collector.
- Clarified `mpf db status` `abuse_states` as persisted table rows, distinct from `mpf abuse status` active customer visibility rows.

## 0.1.276

- Fix Phase 11 restart/autostart proof collection so official JSON evidence remains strict machine-readable JSON, pass evidence directories into post-cleanup and gap inventory summaries, and add a safe production customer lifecycle execution readiness gate package.

## 0.1.275

- Add read-only Phase 11 post-cleanup restart/autostart and controlled artifact persistence evidence bundle tooling with expected backend target propagation.

## 0.1.274
- controlled duplicate NAT cleanup note: adds the official operator-facing controlled duplicate NAT cleanup plan/package/execute-preflight/execute/verify/rollback-contract path and post-cleanup readiness summary for the exact Phase 11 canary-btc-001:20001 and limited-btc-001:20101 duplicate NAT redirects. The path resolves and passes expected_backend_target into the current controlled artifact gate, remains operator-gated, writes backups/evidence/manifests during execute, and does not restart Docker/systemd, flush conntrack, mutate DB/customer/policy/abuse state, enable Phase 12, worker enforcement, UI, Telegram, unrestricted production, or accept Phase 11 operational completion. production_traffic and customer_onboarding_allowed remain controlled_cli_limited.

## 0.1.273 - AI runtime-first PR preflight hardening

- Enforce strict runtime-first PR body validation, including the required `Version: X.Y.Z -> A.B.C` line, the validator command in `How to test`, exactly one official PR class, and rejection of unofficial `docs/evidence-only`, `test-only`, and `refactor-only` options.
- Add post-create GitHub PR body verification to the runtime-first PR wrapper, add `scripts/codex_pre_pr_check.sh`, and split CI into `validate-pr-body` and `tests` jobs for clearer diagnosis.

## 0.1.272 - Phase 11 post-refresh verification and duplicate NAT cleanup

- Fix post-refresh verification to use the current controlled artifact gate plus strict corrected post-DNAT semantics instead of legacy pre-DNAT exact reapply classification.
- Detect duplicate controlled MPF NAT redirects, add a targeted operator-gated duplicate NAT cleanup package contract, standardize execute evidence files, and return non-zero for BLOCKED/FAILED refresh CLI decisions.
- Keep farm5 controlled_cli_limited; Phase 11 operational completion is not accepted and Phase 12, UI, Telegram, and worker enforcement remain closed.

## 0.1.271 - Phase 11 controlled stale-artifact refresh

- Add an operator-gated controlled refresh/rollback-first package path for exact stale 0.1.269 post-DNAT artifacts while preserving controlled_cli_limited gates.
- Add explicit stale graph classification, execute-preflight, post-apply verification contract, and operator wrapper script guidance.

## 0.1.270 - Phase 11 post-DNAT customer graph original-destination routing

- Fix verified Docker-user post-DNAT controlled artifact semantics to route 20001/20101 customer traffic by conntrack original destination before the direct backend guard.
- Add any-mode MPFC_<port> -> MPFO_<port> policy dispatch and fail-closed diagnostics for the farm5 0.1.269 guard-before-accounting runtime graph blocker.

## 0.1.269 - Phase 11 post-apply semantic classification and AI PR wrapper

- Fix 0.1.268 post-apply semantic classification mismatch: guarded execute applied successfully but failed post-apply verification because exact string comparison did not accept iptables-save canonicalized official rules.
- Record that the official rollback returned farm5 to PASS_NO_CUSTOMER_ARTIFACTS; 0.1.269 must be synced, then read-only/package/preflight must be rerun before any guarded execute.
- Add AI PR wrapper governance hardening so AI agents create PRs only through the validated runtime-first wrapper.

## 0.1.268 - Phase 11 controlled post-apply verification fix

- Fix controlled artifact reapply post-apply verification by deriving and propagating the reviewed backend target, normalizing live iptables-save chain declarations against restore-payload artifacts, and requiring exact controlled artifacts without treating expected live MPF chains as unknown. Do not rerun the 0.1.267 execute path; sync 0.1.268, run read-only/package/preflight first, then execute only after fresh READY evidence.

## 0.1.267

- Align Phase 11 current controlled artifact classification with the official taxonomy, resolved backend target checks, post-apply exact-present verification, and reviewed exact-inverse rollback execution.

## 0.1.266

- fix(phase11): harden controlled reapply audit metadata writes for local-peer root execution, retry-safe backup attempts, dependency-stage evidence, and execute-preflight readiness.

## 0.1.265
- fix(phase11): use structure-stable iptables/ip6tables snapshot hashes for guarded controlled execute drift while keeping raw hashes as diagnostics.

## 0.1.264
- fix(phase11): ignore package placeholder backend metadata during guarded execute identity checks while preserving hard safety drift failures.

## 0.1.263
- fix(phase11): canonicalize guarded controlled artifact reapply execute-time backend binding drift comparison and improve pre-apply diagnostics.

## 0.1.262
- fix(phase11): revalidate live-ready packet-path binding semantics during guarded controlled artifact reapply execute while preserving fail-closed drift and operator gates.

## 0.1.261
- feat(phase11): harden guarded controlled artifact reapply helper with execute-preflight, script-level --yes, evidence capture, manifest writing, and regression tests while keeping execution and later-phase gates closed.

## 0.1.260

- feat(phase11): add read-only controlled artifact reapply execution gate preflight without opening execute, iptables-restore, mutation, Phase 12, worker, UI, Telegram, timer, daemon, or unrestricted production gates.

## 0.1.259

- fix(phase11): align live-ready package canonical SHA validation with executor preflight while preserving file SHA, operator gates, tamper detection, and closed runtime gates.

## 0.1.258

- Enforce AI runtime-first project governance with PR body validation, regression tests, and support for coherent runtime-first bundle PRs.

## 0.1.257

- Bind verified Phase 11 packet-path/filter-hook evidence to a live-ready controlled artifact reapply package-review path while keeping execution and later-phase gates closed.

## 0.1.256

- Add fail-closed live-ready controlled artifact reapply readiness/package review surface for Phase 11 operational completion while keeping live execution and later-phase gates closed.

## 0.1.255

- Align Phase 11 operational completion progression with verified packet-path, filter-hook binding, and controlled artifact package evidence while keeping live execution and Phase 12 gates closed.

## 0.1.254

- Accept integrity-valid source-backed 0.1.252 packet-path bundles under the 0.1.254 verifier while keeping tamper, legacy recollection, and execution gates fail-closed.

## 0.1.253

- Bind the farm5 0.1.252 verified DOCKER-USER/FORWARD post-DNAT packet-path proof to explicit Phase 11 controlled artifact graph semantics and add read-only package evidence generation/verification while execution remains blocked.

## 0.1.252

- fix(phase11): resolve packet-path topology proof blockers with schema-versioned bridge derivation, source-aware backend provenance, exact bridge membership correlation, scenario-level Docker filter traversal, and fail-closed legacy bundle recollection.

## 0.1.251
- Add read-only Phase 11 controlled filter packet-path plan/collect/verify capability, sanitized evidence bundles, packet-path graph decisions, CLI/helper surfaces, and tests while keeping farm5 evidence, artifact graph binding, and production execution blocked.

## 0.1.250
- Implemented source-backed Phase 11 controlled artifact renderer, live classification, production adapters, gated execution wiring, and focused tests without farm5 mutation.

## 0.1.249

- Add controlled Phase 11 two-customer artifact reapply resolver and read-only plan/package/verify/evidence surfaces, while keeping production execute fail-closed until real live preflight, lock, backup, PostgreSQL metadata, rollback, and verification adapters are implemented and tested.
- Record the truthful progression flags: `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=false`, `production_execution_available=false`, and `live_ready_package_available=false`; the next step is `implement_source_backed_controlled_artifact_renderer_and_production_adapters`, not farm5 READY package sync.
- Fix the controlled artifact reapply executor so injected empty environment mappings in CI are honored and drift checks are not masked by ambient CI variables.

## 0.1.248

- Fix Phase 11 restart/autostart persistence planning/package integration so healthy runtime state does not fabricate Docker repair needs, and record farm5 0.1.247 post-sync evidence.

## 0.1.247

- Add controlled Phase 11 restart/autostart persistence fix planning/package/evidence tooling and read-only artifact persistence planning while keeping Phase 12, worker enforcement, UI, Telegram, public backend exposure, and Full CLI Production Operations acceptance blocked.

## 0.1.246

- Add read-only Phase 11 post-reboot restart/autostart persistence diagnosis for missing runtime containers and controlled firewall artifacts.

## 0.1.245

- Add a read-only Phase 11 restart/autostart proof surface and farm5 evidence helper while keeping operational completion fail-closed.
- Fix restart/autostart helper firewall artifact evidence to derive known/unknown MPF artifacts from the official current-controlled-artifact-gate classifier.

## 0.1.244

- Expand active Phase 11 operational completion to the Full CLI Production Operations matrix and update the fail-closed gap inventory.
- Align docs/INDEX.md Current Phase Contracts with the active Full CLI Production Operations scope.

## 0.1.243

- Add controlled Phase 11 firewall apply/rollback operational surface while preserving fail-closed safety boundaries.

## 0.1.242

- Add controlled Phase 11 usage/report/check operational surface while preserving read-only/fail-closed safety boundaries.

## 0.1.241

- Add controlled Phase 11 customer lifecycle operational surface checks and align the operational completion gap inventory after the DB-backed abuse surface.
- Add regression coverage for local-peer PostgreSQL/psql row type normalization in the abuse repository.

## 0.1.240

- Add controlled PostgreSQL-backed abuse repository for status/events/run while keeping firewall hard/unhard execution blocked.

## 0.1.239

- Add the controlled abuse operational core and thin `mpf abuse` CLI surface with fail-closed evidence and controlled-package hard/unhard gates; Phase 12 remains blocked.

## 0.1.238

- Fix farm5 main-zip sync sanity check for Phase 11 operational completion `server_state`.
