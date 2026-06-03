# AI Task — Phase 11 operational completion

## Purpose

`Phase 11 operational completion` is a post-acceptance completion gate. Phase 11 remains accepted on farm5 for the controlled CLI-limited BTC production/customer boundary. This gate does not roll back that acceptance and does not claim full backend completion.

Phase 12 Worker Policy Enforcement is blocked until this gate is finally accepted. The purpose of this gate is to complete controlled CLI/service-layer operational surfaces before worker enforcement work starts.

## Required Operational Completion Scope

The implementation sequence must complete and prove these controlled surfaces:

1. abuse operational runner and CLI;
2. customer lifecycle CLI;
3. usage/report/check CLI;
4. controlled firewall apply/rollback workflow;
5. restart/autostart proof.

Each implementation PR must preserve service-layer architecture, conservative defaults, explicit operator gating, auditability, restore/lock/verify requirements where applicable, and fail-closed behavior.

## Explicitly Closed Boundaries

This completion gate does not authorize:

```text
worker enforcement
UI
Telegram
unrestricted production/miner expansion
direct DB/firewall/runtime mutation
unrestricted background automation
timers or daemon starts without a later explicit accepted gate
```

The first implementation step after this entry gate is `implement_controlled_abuse_operational_core`.

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
