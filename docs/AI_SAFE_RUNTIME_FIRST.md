# AI-safe Runtime-first

Status: Phase 11 operating principle

This document defines the `AI-safe Runtime-first` principle for `proxy-address-mining`.

`docs/PHASE_STATUS.md` remains authoritative. This document does not open any production, firewall, customer, abuse, worker, UI, or Telegram gate by itself.

## Definition

`AI-safe Runtime-first` means: prefer the shortest safe path from planning/readiness to a real controlled runtime gate, while preserving fail-closed behavior, explicit operator approval, service-layer boundaries, planner-driven firewall changes, rollback evidence, and current phase authorization.

It is a Phase 11 execution discipline, not a shortcut around safety gates.

## What It Allows

During Phase 11, implementation should move toward real runtime evidence in small accepted steps:

```text
server/runtime readiness
restart and container-order verification
controlled firewall/customer activation harness
manual canary customer
canary evidence collection
limited real customer onboarding after canary acceptance
final Phase 11 activation report
```

Every step must be backed by services, tests, and farm5 evidence before it is treated as accepted.

## What It Forbids

`AI-safe Runtime-first` does not authorize:

```text
production traffic before explicit Phase 11 authorization
controlled CLI canary before explicit Phase 11 authorization
limited real customer onboarding before canary evidence
firewall apply before accepted controlled apply gate
iptables-restore before accepted controlled apply gate
customer NAT/customer firewall rules outside planner/service layer
ad-hoc iptables commands
abuse automation before explicit runtime gate
worker enforcement before Phase 12
UI or Telegram before their later phases
unrestricted customer onboarding
legacy shell scripts as the runtime backend
```

## Required Runtime Safety Properties

Any Phase 11 runtime step must be:

```text
canary-first
operator-approved
service-layer backed
PostgreSQL-backed
planner-driven for firewall/NAT
fail-closed by default
idempotent where practical
rollback-aware
restart-safe
container-order-safe
audited through events
covered by tests
backed by farm5 evidence before acceptance
```

## Phase 11 Final Target

By the end of Phase 11, the server should be operational for controlled real customer sales through CLI/service-layer workflows:

```text
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled
customer_onboarding_allowed: controlled_cli_limited
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
```

Later phases should then improve the scenario and operator surfaces:

```text
Phase 12 — Worker Policy Enforcement
Phase 13 — Local UI
Phase 14 — Operator UI Actions
Phase 15 — Telegram
```

These later phases must remain service-layer interfaces over the accepted runtime path, not new implementation backends.
