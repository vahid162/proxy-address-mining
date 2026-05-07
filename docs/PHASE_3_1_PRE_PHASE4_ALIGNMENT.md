# Phase 3.1 — Pre-Phase4 Alignment Gate

Status: active gate before Phase 4

Phase 3.1 is a safety and alignment gate between accepted Phase 3 and Phase 4 planning.

It exists because the server verification showed two different states on `farm5`:

```text
/opt/mpf-py-src      contains Phase 3 source and tests pass
/usr/local/bin/mpf   still points to the older Phase 1 smoke CLI
```

The server is safe because no production traffic, firewall, NAT, Docker data-plane, usage timer, abuse automation, UI, Telegram, or import behavior is active. However, the official operator command must be aligned before Phase 4 work continues.

## Goal

Align the official runtime command with the accepted Phase 3 read-only CLI/API foundation without changing traffic.

## Allowed Work

```text
backup current runtime path
install a safe runtime wrapper for `mpf`
point official `mpf` command to the accepted Phase 3 source artifact
run read-only verification
record the result
update docs and tests
```

## Forbidden Work

```text
start Docker proxy containers
start v2rayA
start forwarder/gost
create or mutate customers
create customer firewall rules
create NAT redirects
run firewall apply
run usage timers
run abuse automation
run block/pause automation
start UI service
start Telegram bot
run production import
activate worker enforcement
change firewall.apply_mode away from plan_only
```

## Required Runtime Invariant

After alignment, these commands must run through the accepted Phase 3 CLI and must not show the old Phase 1 smoke help:

```bash
mpf --version
mpf phase-status
mpf config validate
mpf config show
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
```

Expected Phase 3 behavior:

```text
mpf phase-status reports Phase 3 accepted and Phase 4 planning
mpf db status reports database status
mpf lanes list reports DB/config lanes read-only
mpf customer list reports no customers or read-only rows
mpf jobs status reports no job runs or read-only rows
```

## Required Safety Invariants

These must remain true after alignment:

```text
firewall.apply_mode = plan_only
Docker has no proxy containers
No MPF firewall rules exist
No MPF NAT rules exist
No MPF systemd units/timers exist
No MPF cron jobs exist
runtime tables remain empty
no production traffic changed
```

## Time Sync Gate

Time synchronization is not required for Phase 3.1 runtime alignment, but it is a hard blocker before:

```text
production traffic
usage accounting
abuse automation
expiry/renew timing
job automation
hash-rate time-series collection
```

A later phase must not activate those features while `timedatectl` reports:

```text
System clock synchronized: no
```

## Backend Port Policy Gate

Phase 4 proxy doctor must distinguish these two checks:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

It is not acceptable to make backend ports unreachable from inside the server just to hide them from outside access.

## Acceptance Script

Run this after runtime alignment:

```bash
set -euo pipefail

mpf --version
mpf phase-status
mpf config validate
mpf config show
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status

cd /opt/mpf-py-src
.venv/bin/python -m pytest -q
sudo -u mpf .venv/bin/alembic current
sudo -u mpf .venv/bin/alembic heads

docker ps -a
iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
systemctl list-unit-files --no-pager | grep -Ei 'mpf|v2raya|gost|forwarder' || true
grep -RInE 'mpf|v2raya|gost|forwarder' /etc/cron* /var/spool/cron/crontabs 2>/dev/null || true
timedatectl
```

## Acceptance Criteria

Phase 3.1 is accepted only when:

```text
official `mpf` runtime exposes Phase 3 read-only commands
Phase 3 tests pass
Alembic current/head remain 0001_phase2_initial_schema
public schema still has expected tables
runtime-facing tables remain empty
Docker still has no proxy containers
No MPF firewall/NAT rules exist
No MPF systemd/cron automation exists
firewall.apply_mode remains plan_only
Phase 4 activation runbook remains not executed
```

## Result Recording

After the server passes, record the result in:

```text
docs/PHASE_STATUS.md
docs/PHASE_3_1_SERVER_RESULT.md
```

Do not advance to Phase 4 runtime activation until Phase 3.1 is recorded.
