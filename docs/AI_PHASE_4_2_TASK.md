# AI Phase 4.2 Task — Runtime Activation Runbook Planning

Status: active task for Phase 4.2 planning

This document defines repository-side Phase 4.2 planning work for AI coding agents.
It does not authorize server runtime activation.

## Required Reading

Read these before changing Phase 4.2 documentation, code, tests, scripts, config, deployment artifacts, or interfaces:

1. `AGENTS.md`
2. `README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`
6. `docs/ROADMAP.md`
7. `docs/SAFETY.md`
8. `docs/FIREWALL.md`
9. `docs/BACKEND_PORT_POLICY.md`
10. `docs/AI_PHASE_4_TASK.md`
11. `docs/PHASE_4_SERVER_RUNBOOK.md`
12. `docs/PHASE_4_1_SERVER_RESULT.md`
13. `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`

If documents conflict, follow the stricter safety rule and update the documentation before implementing code.

## Current Boundary

Accepted phase:

```text
Phase 4.1 — Compose Template + Server Config Planning
```

Working phase:

```text
Phase 4.2 — Runtime Activation Runbook Planning
```

Phase 4.2 is planning-only. It prepares the future runtime activation procedure, but it must not start containers or change production traffic.

## Goal

Produce a complete, reviewable, operator-safe runbook for a later explicit proxy runtime activation step.

The future runtime activation step will be allowed to start the proxy data-plane only after this planning work is reviewed and accepted.

## Allowed Work

AI agents may implement repository-side planning only:

- runtime activation runbook documentation
- exact future `docker compose config` validation commands
- exact future startup command with explicit `phase4-runtime` profile, documented only
- backend internal reachability test plan
- backend external exposure test plan
- v2rayA UI local-only test plan
- Docker Compose stop/rollback plan
- post-run evidence checklist
- validation scripts that inspect state but do not start runtime
- tests proving forbidden runtime commands remain unavailable
- documentation updates that preserve phase gates

## Forbidden Work

Do not introduce runtime activation or traffic-changing behavior:

- `docker compose up`
- `docker run`
- starting v2rayA runtime
- starting forwarder/gost runtime
- customer NAT redirects
- customer firewall rules
- live firewall apply
- firewall apply mode changes away from `plan_only`
- `proxy.runtime_activation_allowed=true`
- production customer creation or mutation
- usage timers
- hash-rate/share collectors
- abuse automation
- block or pause automation
- UI service
- Telegram bot
- public backend publish
- public v2rayA UI publish
- worker enforcement

## Required Invariants

These values must remain true during Phase 4.2 planning:

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
proxy_data_plane_allowed = planning_only
production_traffic = none
customer_onboarding_allowed = no
firewall_apply_allowed = no
abuse_automation_allowed = no
```

## Runtime Activation Runbook Requirements

The runbook must include exact future commands for:

1. pre-run safety checks
2. source and config backup
3. Docker Compose config validation
4. startup using an explicit profile
5. container status checks
6. healthcheck inspection
7. v2rayA UI local-only verification
8. BTC backend internal reachability verification
9. BTC backend external exposure verification
10. confirmation that no customer NAT redirects exist
11. confirmation that firewall.apply_mode remains plan_only
12. stop/rollback commands
13. post-run evidence collection

## Backend Port Requirement

The future runtime activation must preserve this split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by breaking loopback, local server paths, Docker/internal paths, or future MPF-owned NAT paths.

## Required Tests

Minimum repository tests for Phase 4.2 planning:

- phase-status reports Phase 4.1 accepted and Phase 4.2 working
- runtime activation commands are not exposed by the CLI
- proxy CLI commands remain read-only
- compose template remains profile-guarded
- backend and v2rayA UI publish are not public
- runbook contains explicit stop/rollback commands
- runbook states no customer NAT redirect will be created
- runbook preserves `firewall.apply_mode=plan_only`
- runbook preserves `proxy.runtime_activation_allowed=false` until runtime approval

## Acceptance Gate

Phase 4.2 planning is accepted only when:

- `docs/AI_PHASE_4_2_TASK.md` exists
- `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md` exists
- phase status and README point to Phase 4.1 accepted / Phase 4.2 planning
- server sync script can handle the Phase 4.1 to Phase 4.2 gate safely
- validation script checks the Phase 4.2 planning gate without starting runtime
- tests pass
- no Docker/proxy runtime is started by planning work
- no firewall/NAT/customer/usage/abuse changes are introduced

## Stop Conditions

Stop and revise if a patch introduces:

- traffic-changing behavior
- Docker proxy runtime startup
- firewall apply
- NAT redirects
- customer rules
- customer CRUD mutation
- public backend exposure
- public v2rayA UI exposure
- usage timers
- hash-rate collectors
- abuse automation
- Telegram or UI runtime
- a script that starts containers as part of sync or validation
