# AI-safe Runtime-first Boundary

Status: active Phase 11 implementation principle, non-authorizing by itself

This document defines the Phase 11 runtime-first rule for humans and AI coding agents.

`docs/PHASE_STATUS.md` remains authoritative. This document does not open production traffic, controlled CLI canary execution, firewall apply, customer NAT/customer firewall rules, abuse automation, worker enforcement, UI, or Telegram by itself.

## Definition

AI-safe Runtime-first means the project should now prefer the shortest safe path to a real controlled runtime gate while preserving:

```text
fail-closed behavior
explicit phase authorization
operator approval for dangerous actions
Python/service-layer business logic
PostgreSQL as source of truth
firewall planner boundaries
restore point / backup / lock / verify / rollback evidence
audit/events for mutations
server evidence, not fabricated evidence
canary-first production activation
```

Runtime-first does not mean bypassing safety. It means avoiding long chains of report-only PRs that do not move the server closer to controlled production operation.

## Phase 11 Intent

Phase 11 should make the server operational enough for real sales after final Phase 11 acceptance.

By the end of Phase 11, the project should have evidence for:

```text
fresh farm5 sync/test evidence
server time/NTP readiness
restart and container-order safety
controlled firewall apply/verify/rollback path
customer NAT/customer firewall rules through planner only
controlled CLI canary customer
limited real customer onboarding after successful canary evidence
usage/reject/session/worker visibility for real customers
abuse 1h runtime coverage for all active customers in enabled lanes
backup/restore-plan evidence
operator runbook and final activation report
```

## What Phase 11 May Open After Evidence

Only after explicit sub-gate acceptance, Phase 11 may move these states from closed/planning to controlled operational modes:

```text
production_traffic: controlled_cli_canary or controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled
customer_onboarding_allowed: controlled_cli_canary or controlled_cli_limited
```

These gates must not jump directly to unrestricted production.

## What Phase 11 Must Keep Closed

Phase 11 must keep these later-phase gates closed:

```text
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
public API binding: no
public v2rayA UI exposure: no
unrestricted production onboarding: no
```

Worker Policy Enforcement remains Phase 12. Local UI remains Phase 13. Operator UI Actions remain Phase 14. Telegram remains Phase 15 unless a future explicit roadmap gate changes this order.

## Required PR Direction From Phase 11 Onward

From Phase 11 onward, PRs should be evaluated by whether they advance a real controlled runtime gate or remove a blocker for such a gate.

Preferred PR types:

```text
server/runtime readiness inventory
restart/container-order verification
controlled apply harness contracts and implementation
operator confirmation and kill-switch enforcement
canary customer plan and acceptance evidence
limited real customer onboarding gate
abuse runtime coverage gate
backup/restore and rollback evidence
final Phase 11 acceptance evidence
```

Avoid repeated PRs that only add report-only surfaces without a clear path to controlled runtime evidence.

## Hard Stop Conditions

Stop and revise if a change introduces:

```text
ad-hoc iptables mutation
customer NAT outside the firewall desired model/planner
firewall apply without backup/lock/verify/rollback path
production traffic without canary evidence
unrestricted customer onboarding
abuse hardening without all-active-customer coverage
hardening on missing/stale evidence
DB failure or firewall failure that causes unsafe hardening
UI or Telegram mutation path in Phase 11
direct DB/firewall mutation from CLI handlers
legacy shell scripts as runtime backend
```

## Acceptance Language

A Phase 11 PR is not accepted merely because it adds a report.

A Phase 11 PR is accepted when it either:

```text
moves a controlled runtime gate forward safely
adds a required runtime safety mechanism
records real server evidence
or removes a concrete blocker to controlled production activation
```

When in doubt, choose the safer runtime path and document the tradeoff.
