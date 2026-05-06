# PHASE STATUS

Status: Active project control file

This file tells humans and AI coding agents what phase is currently allowed.
It must be checked before writing code, scripts, deployment files, services, jobs, or tests.

## Current State

```text
current_accepted_phase: Phase 0 — Architecture Freeze
current_working_phase: Phase 1 — Repository Bootstrap Skeleton / Preflight Preparation
server_state: raw server, not bootstrapped
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
ui_allowed: no
telegram_allowed: no
```

## What Is Allowed Now

Allowed work is limited to safe repository preparation for Phase 1:

```text
- minimal Python package skeleton
- safe CLI smoke commands
- config loader and validator
- DB ping helper
- read-only preflight script
- example config with firewall.apply_mode=plan_only
- smoke tests
- documentation updates that preserve phase gates
```

## What Is Forbidden Now

Do not implement or activate:

```text
- customer CRUD
- production PostgreSQL migrations
- live firewall planner/apply
- NAT redirects
- Docker proxy data-plane
- v2rayA or forwarder activation
- usage timers
- abuse runner automation
- block or pause automation
- local UI service
- Telegram bot
- production customer import
```

## Current Safety Invariant

During this phase, the repository may contain code, tests, and scripts, but no code path may mutate production traffic state.

Required invariant:

```text
firewall.apply_mode = plan_only
```

Any patch that bypasses `plan_only` or introduces traffic-changing behavior before the correct phase must be rejected.

## Phase 1 Completion Gate

Phase 1 is complete only after the real server preflight is reviewed and these checks pass on the target server:

```bash
mpf --help
mpf doctor
mpf config validate
mpf config show
mpf db ping
python -m pytest
systemctl status postgresql
docker version
docker compose version
conntrack -V
iptables --version
```

And these remain true:

```text
no customer firewall rule exists
no NAT redirect exists
no backend public exposure exists
no abuse automation is active
no block automation is active
firewall.apply_mode is still plan_only
```

## Next Planned Step

Prepare and test the Phase 1 repository skeleton only.
After that, run the read-only preflight on the raw server and review the output before writing any server bootstrap commands.
