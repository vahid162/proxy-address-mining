# Phase 4 Runtime Activation Execution Review

Status: active review gate

This document defines the review step after Phase 4.2 server sync was verified.
It does not authorize runtime activation by itself.

## Current Accepted State

```text
accepted_phase: Phase 4.2 — Runtime Activation Runbook Planning, synced and verified on farm5
working_phase: Phase 4 Runtime Activation Execution Review
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: planning_only
ui_allowed: no
telegram_allowed: no
```

## Purpose

The purpose of this review is to decide whether to proceed to a limited Phase 4 runtime activation execution step.

That future execution step may start only the proxy data-plane containers through the documented `phase4-runtime` Docker Compose profile.

It must still not create customer NAT redirects, customer firewall rules, customers, usage timers, abuse automation, local UI service, buyer UI service, Telegram, production import, or worker enforcement.

## Required Inputs Before Approval

Before any runtime execution command is approved, review:

1. `docs/PHASE_STATUS.md`
2. `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`
3. `docs/PHASE_4_2_SERVER_SYNC_RESULT.md`
4. `docs/BACKEND_PORT_POLICY.md`
5. latest server sync output
6. current CI status on `main`

## Required Server Baseline

The server must show:

```text
mpf config validate OK
mpf doctor OK
mpf proxy config-check final_verdict: OK
pytest passed
Docker has no proxy runtime containers
no risky backend/UI ports are listening
no MPF/backend firewall references exist
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
customers = 0
job_runs = 0
```

The expected remaining warning is:

```text
lane.btc.backend_internal_reachability: WARN
```

This warning is acceptable only before runtime activation, because backend internal reachability cannot be checked until the proxy containers are started.

## Review Questions

Runtime execution may be considered only if all answers are yes:

```text
Is the server synced with the latest green GitHub main?
Is the Phase 4.2 runtime activation runbook present on the server?
Is the Compose config validation command documented?
Is the startup command documented with the explicit phase4-runtime profile?
Is stop/rollback documented?
Is v2rayA UI local-only validation documented?
Is BTC backend 60010 internal reachability validation documented?
Is external backend exposure validation documented?
Are customer NAT redirects explicitly forbidden?
Is firewall.apply_mode still plan_only?
Is proxy.runtime_activation_allowed still false until explicit runtime approval?
```

## Forbidden During Review

Do not run during this review step:

```bash
docker compose up
docker run
mpf firewall apply
mpf customer add
mpf customer edit
mpf abuse run
mpf usage snapshot
```

## Future Execution Boundary

If explicitly approved later, the future runtime execution step is limited to:

```text
start proxy containers with the phase4-runtime profile
verify v2rayA UI is local-only
verify BTC backend 60010 is internally reachable
verify BTC backend 60010 is not externally/publicly exposed
verify no customer NAT redirect exists
verify no customer firewall rule exists
verify stop/rollback works
collect post-run evidence
```

Still forbidden after that future runtime execution:

```text
customer CRUD mutation
customer NAT redirects
customer firewall rules
firewall apply
usage timers
hash-rate/share collectors
abuse automation
block/pause automation
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
```

## Acceptance For Review Completion

This review is complete only when an operator explicitly approves or rejects the limited runtime activation execution step.

No implicit approval exists. Documentation, CI, or server sync passing does not start runtime activation automatically.
