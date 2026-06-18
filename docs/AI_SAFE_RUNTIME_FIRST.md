## Current Gate Update (0.1.234)

Phase 11 is accepted only for the farm5 `controlled_cli_limited` BTC boundary. Phase 12 — Worker Policy Enforcement is next. UI, Telegram, worker enforcement, and unrestricted expansion remain closed. Controlled firewall/apply and abuse authorization are operator-gated boundaries, not permission for unrestricted background automation or direct mutation.

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

## Phase 11 target vocabulary and acceptance guard

- Phase 11 controlled boundary target: `controlled_cli_limited`. This boundary is accepted for controlled BTC operation on farm5 only.
- Phase 11 operational completion final target: `cli_production`. Only final acceptance may set `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`.
- AI-safe Runtime-first is a discipline for moving through evidence-backed runtime gates; it is not a shortcut around the Phase 11 completion matrix.
- Final acceptance is forbidden based only on report-only/readiness surfaces. `final_acceptance_ready` requires `generic_customer_ready` plus all other 10 matrix items.
- Readiness vocabulary: `surface_ready` means a command/report surface exists; `evidence_ready` means supplied artifacts validate; `controlled_execution_ready` means operator-gated execution prerequisites are met; `runtime_verified_ready` means post-execution runtime proof exists; `generic_customer_ready` means package, preflight, controlled apply, verify, external traffic, transcript/first-connect DB, abuse, and rollback evidence are complete for a real DB-backed customer; `final_acceptance_ready` means generic customer readiness plus the full 10-item matrix.
- Phase 12, worker enforcement, UI, and Telegram remain closed before later accepted phases.
