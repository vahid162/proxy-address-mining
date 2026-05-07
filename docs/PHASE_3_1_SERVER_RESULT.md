# Phase 3.1 Server Result

Status: pending server verification

Server:

```text
farm5
```

Phase:

```text
Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
```

## Purpose

This document must record the server result after official `mpf` runtime alignment.

Phase 3.1 is not accepted until this document is updated with real server output showing that the official runtime command is aligned with the accepted Phase 3 source and that no traffic-changing behavior was introduced.

## Required Commands

Run on farm5 after pulling/copying the updated repository artifact to `/opt/mpf-py-src`:

```bash
sudo bash /opt/mpf-py-src/scripts/promote_phase3_runtime.sh
sudo bash /opt/mpf-py-src/scripts/verify_phase3_1_alignment.sh
```

## Expected Result

```text
official mpf runtime exposes Phase 3 read-only commands
mpf phase-status reports Phase 3 accepted / Phase 3.1 or Phase 4 planning according to current repo state
mpf db status works
mpf lanes list works
mpf customer list works
mpf jobs status works
pytest passes
alembic current/head remains 0001_phase2_initial_schema
runtime-facing tables remain empty
Docker still has no proxy containers
No MPF firewall/NAT rules exist
No MPF systemd/cron automation exists
firewall.apply_mode remains plan_only
no production traffic changed
```

## Server Output Summary

Pending.

## Backup Artifact

Pending.

Expected format:

```text
/var/backups/mpf/phase3-runtime-promote-YYYYMMDDTHHMMSSZ
```

## Known Warnings

Time synchronization may remain unsynchronized after Phase 3.1.

If so, record:

```text
System clock synchronized: no
```

This blocks production traffic, usage accounting, expiry automation, abuse automation, and hash-rate time-series collection, but does not block Phase 3.1 runtime alignment.

## Acceptance Decision

Pending.

Use one of:

```text
accepted: yes
accepted: no
```

## Still Forbidden After Phase 3.1

Unless a later phase explicitly accepts them, do not activate:

```text
customer CRUD mutation
customer firewall rules
live firewall apply
NAT redirects
Docker proxy data-plane
v2rayA / forwarder runtime
usage timers
hash-rate/share collectors
abuse runner
block/pause automation
local UI
buyer UI
Telegram
production import
worker enforcement
```
