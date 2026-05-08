# AI Phase 4 Task — Compose Forward-only + Proxy Doctor Planning

Status: active task for Phase 4 planning

This document defines repository-side Phase 4 planning work for AI coding agents.
It does not authorize server runtime activation.

## Required Reading

Read these before changing Phase 4 documentation, code, tests, scripts, config, deployment artifacts, or interfaces:

1. `AGENTS.md`
2. `README.md`
3. `docs/INDEX.md`
4. `docs/PHASE_STATUS.md`
5. `docs/AI_CODING_RULES.md`
6. `docs/ROADMAP.md`
7. `docs/SAFETY.md`
8. `docs/FIREWALL.md`
9. `docs/BACKEND_PORT_POLICY.md`
10. `docs/PHASE_4_SERVER_RUNBOOK.md`

If documents conflict, follow the stricter safety rule and update the documentation before implementing code.

## Current Boundary

Accepted phase:

```text
Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
```

Working phase:

```text
Phase 4 — Compose Forward-only + Proxy Doctor Planning
```

Phase 4 is planning-only until a dedicated server runbook is accepted.

## Roadmap Goal

Phase 4 goal:

```text
prepare the proxy data-plane without customer firewall redirects
```

Required roadmap work:

- v2rayA service design
- v2rayA bridge design when needed
- BTC forwarder/gost design on backend `60010`
- healthcheck design
- Docker Compose doctor design
- proxy reachability probe design
- backend exposure detection

Acceptance target:

- forwarder can listen on the BTC backend when runtime activation is explicitly approved
- v2rayA UI is local-only
- backend direct public exposure is blocked or detected as critical
- proxy doctor passes
- no customer NAT redirect exists yet

## Allowed Planning Work

AI agents may implement repository-side planning and read-only foundations:

- Compose file template, not auto-started
- compose configuration validation helper
- read-only Docker inspection adapter
- proxy doctor service skeleton
- proxy doctor response DTOs
- read-only proxy CLI commands
- backend internal reachability check design
- backend external exposure check design
- v2rayA UI local-only binding contract
- forwarder/gost binding contract
- stop and rollback documentation
- server validation script
- unit tests for doctor classifications

## Forbidden Work

Do not introduce runtime activation or traffic-changing behavior:

- customer NAT redirects
- customer firewall rules
- live firewall apply
- firewall apply mode changes away from `plan_only`
- production customer creation
- production customer mutation
- usage timers
- hash-rate/share collectors
- abuse automation
- block or pause automation
- UI service
- Telegram bot
- public backend publish
- public v2rayA UI publish
- worker enforcement

## Required Design Invariant

Backend ports are internal service ports.

Required future doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by breaking loopback, local server paths, Docker/internal paths, or the future MPF-owned NAT path.

## Required Proxy Doctor Checks

The Phase 4 doctor should report these fields:

- `compose_file_exists`
- `compose_config_valid`
- `v2raya_ui_local_only`
- `backend_listener_state`
- `backend_internal_reachability`
- `backend_external_exposure`
- `backend_docker_publish_mode`
- `proxy_container_state`
- `healthcheck_state`
- `no_customer_nat_redirects`
- `firewall_apply_mode_plan_only`

The doctor must produce a final verdict:

```text
OK
WARN
CRITICAL
```

## Allowed Read-only CLI Shape

Allowed read-only command names:

```text
mpf proxy doctor
mpf proxy status
mpf proxy config-check
```

These commands must not change Docker, firewall, database customer state, NAT, usage jobs, or abuse state.

## Required Tests

Minimum tests:

- missing compose file is not reported as OK
- public UI bind is CRITICAL
- public backend publish is CRITICAL
- localhost-only UI bind is OK
- internal backend unreachable is CRITICAL after runtime activation
- external backend exposure is CRITICAL
- no customer NAT redirects are expected in Phase 4
- `firewall.apply_mode` remains `plan_only`
- proxy CLI commands are read-only

## Phase 4 Planning Acceptance

Planning is accepted only when:

- `docs/AI_PHASE_4_TASK.md` exists
- `docs/PHASE_4_SERVER_RUNBOOK.md` exists
- Compose design is documented
- proxy doctor checks are specified
- server validation script exists
- read-only proxy doctor foundations are tested
- no runtime proxy containers are started during planning
- no firewall/NAT/customer/usage/abuse changes are introduced

## Stop Conditions

Stop and revise if a patch introduces:

- traffic-changing behavior
- firewall apply
- NAT redirects
- customer rules
- customer CRUD
- public backend exposure
- public v2rayA UI exposure
- usage timers
- hash-rate collectors
- abuse automation
- Telegram or UI runtime
