# AI Task — Phase 11 operational completion — Full CLI Production Operations

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

The first implementation step after this scope expansion remains `implement_restart_autostart_proof`.

## Progress Update (0.1.239)

`implement_controlled_abuse_operational_core` is implemented as an operator-invoked service/repository/domain boundary with thin `mpf abuse` CLI commands. Hard/unhard remain controlled-package gated; firewall verification failure cannot set `hard_applied_at`. No timer, daemon, worker enforcement, UI, Telegram, or Phase 12 implementation is enabled.

## Progress Update (0.1.240)

The controlled PostgreSQL-backed abuse repository now connects `mpf abuse status`, `mpf abuse events`, and `mpf abuse run --dry-run` to real DB reads. Explicit operator-gated controlled execute may write only `abuse_states`, `abuse_events`, and `job_runs`; missing or stale evidence fails closed. Firewall hard/unhard execution remains blocked and `hard_applied_at` remains unset. No timer, daemon, worker enforcement, UI, Telegram, or Phase 12 implementation is enabled.

## Progress Update (0.1.241)

- Abuse DB-backed surface remains operational and now has regression coverage for local-peer psql row normalization.
- Controlled customer lifecycle CLI surface is now checked/proven as a Phase 11 operational completion surface.
- Usage/report/check, controlled firewall apply/rollback, and restart/autostart proof remain pending.
- Phase 12, worker enforcement, UI, Telegram, timer, daemon, and unrestricted production remain blocked.

## Progress Update (0.1.242)

- Controlled usage/report/check operational surface is now checked/proven as a Phase 11 operational completion surface.
- Abuse DB-backed surface remains ready.
- Customer lifecycle CLI surface remains ready.
- Controlled firewall apply/rollback and restart/autostart proof remain pending.
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
