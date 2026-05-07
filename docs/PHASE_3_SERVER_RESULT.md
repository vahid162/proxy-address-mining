# Phase 3 Server Result

Status: accepted server result

Server:

```text
farm5
```

Phase:

```text
Phase 3 — CLI + Internal API Foundation
```

## Summary

Phase 3 repository patches were aligned to the server source artifact and verified on `farm5`.

Only read-only CLI/API foundation code, service/repository boundaries, response DTOs, tests, and documentation were changed.

No production traffic, firewall, NAT redirect, Docker data-plane, customer onboarding, usage timer, abuse automation, UI, Telegram, or import behavior was activated.

## Source Alignment

Server source artifact:

```text
/opt/mpf-py-src
```

The source was aligned from the uploaded GitHub `main` archive.

Backup before the final Phase 3 alignment:

```text
/var/backups/mpf/phase3-source-align-20260507T140233Z
```

Current production runtime remained unchanged:

```text
/opt/mpf-py
/usr/local/bin/mpf
```

## Verification Result

Accepted checks:

```text
pytest passed: 48 passed
mpf phase-status reported Phase 2 accepted / Phase 3 working before final acceptance doc patch
mpf config validate OK
mpf config show OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
alembic current = 0001_phase2_initial_schema (head)
alembic heads = 0001_phase2_initial_schema (head)
public schema table count = 64
runtime tables remain empty
Docker has no containers
No MPF firewall or NAT rules exist
No MPF systemd units or timers exist
No MPF cron jobs exist
Old phase guard string search returned empty
firewall.apply_mode remains plan_only
```

Runtime-facing table counts after verification:

```text
lanes = 0
customers = 0
customer_policies = 0
abuse_states = 0
firewall_applies = 0
job_runs = 0
worker_blocks = 0
buyer_accounts = 0
```

## Phase 3 Acceptance Gate

Accepted:

```text
CLI uses services, not direct business logic
internal API foundation uses services
read-only DB-backed commands work
DB status command works
lane list command is read-only
customer list command is read-only
job status command is read-only
interface boundary tests exist
internal API boundary tests exist
forbidden command tests exist
foundation taxonomy module exists
stable read-only response DTO exists
no live firewall apply exists
no customer firewall rule exists
no NAT redirect exists
no proxy data-plane is started
no production customer mutation exists
```

## Still Forbidden After Phase 3

Do not activate yet:

```text
customer CRUD mutation
customer firewall rules
live firewall apply
NAT redirects
Docker proxy data-plane
v2rayA / forwarder
usage timers
abuse runner
block/pause automation
local UI
buyer UI
Telegram
production import
worker enforcement
```

## Known Warning

Time synchronization is still not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This did not block Phase 3 read-only foundation work, but it must be fixed before production traffic, usage accounting, or abuse automation.

## Next Phase

Next working phase:

```text
Phase 4 — Compose Forward-only + Proxy Doctor Planning
```

Phase 4 planning must start with a dedicated phase task/runbook before any Docker data-plane, v2rayA, or forwarder runtime activation.

Firewall apply, NAT redirects, customer CRUD, usage timers, and abuse automation remain forbidden until their later phase gates pass.
