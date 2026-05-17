# Phase 10 farm5 0.1.130 Sync/Test Evidence

Status: evidence record

This document records the operator-provided farm5 sync/test result for repository version 0.1.130.

This evidence does not open production traffic, firewall apply, customer NAT/customer firewall rules, abuse automation, worker runtime, scheduler/timer, collector, UI, or Telegram gates.

## Commands executed on farm5

```bash
mpf --version
mpf phase-status
mpf doctor
mpf config validate
mpf db status
mpf proxy doctor
mpf phase10 readiness --output json
mpf phase10 session-readiness --output json
mpf phase10 worker-policy-readiness --output json
mpf phase10 share-timeline-readiness --output json
mpf phase10 enforcement-boundary --output json
cd /opt/mpf-py-src
/opt/mpf-py-src/.venv/bin/python -m pytest -q
```

## Evidence summary

```text
server version: 0.1.130
pytest: 767 passed in 82.44s (0:01:22)
mpf doctor: OK
config validate: OK
database: OK
proxy doctor: OK
phase10 readiness: ACCEPTED
session-readiness: ACCEPTED
worker-policy-readiness: ACCEPTED
share-timeline-readiness: ACCEPTED
enforcement-boundary: ACCEPTED
```

## Current gate preserved

```text
current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5
current_working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

## Runtime safety observations

```text
firewall.apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
all dangerous authorization flags: false
```

Proxy doctor showed the accepted limited local-only proxy runtime remains healthy:

```text
proxy final_verdict: OK
proxy.runtime_activation_allowed remains disabled for general app/API mutation
v2rayA UI listener is local-only
BTC backend listener is local-only
backend internal reachability is accepted through the local-only runtime listener
no customer NAT redirects exist
firewall apply mode remains plan_only
```

## Python test environment note

The first test invocation used system Python and failed during collection because system Python did not have project dependencies such as `typer`, `pydantic`, and `sqlalchemy` installed.

The correct farm5 test command uses the project virtual environment used by `/usr/local/bin/mpf`:

```bash
/opt/mpf-py-src/.venv/bin/python -m pytest -q
```

That venv-based test run passed with `767 passed in 82.44s`.

## Non-authorization statement

This evidence is report-only and non-mutating. It does not authorize:

```text
production traffic
firewall apply
iptables-restore
customer NAT/customer firewall rules
abuse automation runner
worker runtime
scheduler/timer
collector/live share ingestion
production DB execution
hard/soft block automation
pause automation
UI
Telegram
production customer onboarding
```
