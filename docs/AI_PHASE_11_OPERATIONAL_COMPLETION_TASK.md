## 0.1.249 current step: sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5

Version 0.1.249 implements the controlled artifact reapply capability but does not restore farm5 artifacts. A live source-backed READY package must now be collected and reviewed on farm5 before execution. Restart/autostart proof remains `missing_or_partial`; Full CLI Production Operations, Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.

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

The current required implementation step after farm5 0.1.247 post-sync evidence is `implement_controlled_artifact_reapply_execute_package`.

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
- Keep `restart_autostart_proof: missing_or_partial` and `next_required_step: implement_controlled_artifact_reapply_execute_package` until controlled artifact persistence is implemented and source-backed evidence proves readiness.
