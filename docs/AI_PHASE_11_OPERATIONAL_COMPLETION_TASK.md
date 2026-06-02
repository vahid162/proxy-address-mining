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
