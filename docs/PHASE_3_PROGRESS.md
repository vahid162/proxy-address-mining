# Phase 3 Progress

Status: in progress

Phase 3 is `CLI + Internal API Foundation`.

This file records repository progress only. It does not mark Phase 3 accepted until server validation passes and the Phase 3 acceptance gate is reviewed.

## Implemented So Far

```text
- read-only CLI commands for config, DB status, lanes, customers, jobs, and doctor
- service-layer skeletons for config, DB, lanes, customer read, jobs, and doctor
- read-only repositories for lanes, customers, and jobs
- function-level internal API foundation with no network binding
- stable read-only response DTO shape
- taxonomy foundation in mpf/domain/taxonomy.py
- request context / correlation_id foundation
- tests for CLI/service boundaries
- tests for internal API/service boundaries
- tests for forbidden Phase 3 commands
```

## Still Forbidden

Phase 3 still must not implement or activate:

```text
- customer create/edit/delete/renew
- live customer onboarding
- customer firewall rules
- firewall apply
- NAT redirects
- proxy data-plane containers
- usage timers
- abuse runner automation
- block or pause automation
- UI service
- buyer UI service
- Telegram bot
- production import
- worker enforcement
```

## Server Validation Required

After each Phase 3 repository patch, align `/opt/mpf-py-src` from GitHub `main` or the equivalent uploaded source archive and run:

```bash
cd /opt/mpf-py-src
/opt/mpf-py-src/.venv/bin/python -m pytest -q
/opt/mpf-py-src/.venv/bin/mpf phase-status
/opt/mpf-py-src/.venv/bin/mpf db status
/opt/mpf-py-src/.venv/bin/mpf lanes list
/opt/mpf-py-src/.venv/bin/mpf customer list
/opt/mpf-py-src/.venv/bin/mpf jobs status
```

Safety checks must continue to show:

```text
firewall.apply_mode = plan_only
no Docker proxy data-plane containers
no MPF firewall or NAT rules
no systemd/cron MPF automation
no production customer mutation
```

## Known Non-Blocking Warning

`farm5` still has unconfirmed clock synchronization. This does not block Phase 3 read-only work, but it must be fixed before production traffic, usage accounting, or abuse automation.
