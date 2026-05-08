# Phase 3.1 Server Result

Status: accepted server result

Server:

```text
farm5
```

Phase:

```text
Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
```

## Summary

Phase 3.1 runtime alignment was completed and verified on `farm5`.

The official `mpf` command now runs through the Phase 3 read-only CLI source under `/opt/mpf-py-src` instead of the older Phase 1 smoke CLI.

No production traffic, firewall, NAT redirect, Docker proxy data-plane, customer onboarding, usage timer, hash-rate/share collector, abuse automation, UI, Telegram, import, or worker enforcement behavior was activated.

## Source Alignment

Source artifact was refreshed from the GitHub `main` archive.

Source backup before the final Phase 3.1 verification:

```text
/var/backups/mpf/source-before-phase3-1-20260508T133637Z
```

Runtime backup before final promotion:

```text
/var/backups/mpf/phase3-runtime-promote-20260508T133650Z
```

Official runtime command:

```text
/usr/local/bin/mpf
```

Final runtime command state:

```text
-rwxr-xr-x 1 root root 194 May  8 17:06 /usr/local/bin/mpf
```

## Verification Commands

Executed on `farm5`:

```bash
sudo bash /opt/mpf-py-src/scripts/promote_phase3_runtime.sh
sudo bash /opt/mpf-py-src/scripts/verify_phase3_1_alignment.sh
```

## Accepted Checks

```text
mpf --version reported 0.1.0
mpf phase-status reported Phase 3 accepted / Phase 3.1 working
mpf config validate OK
mpf config show OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
pytest passed: 48 passed
alembic current = 0001_phase2_initial_schema (head)
alembic heads = 0001_phase2_initial_schema (head)
firewall.apply_mode remains plan_only
runtime-facing tables remain empty
Docker has no containers
No MPF firewall/NAT rules exist
No MPF systemd/cron automation exists
No risky backend/UI ports are listening
no production traffic changed
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

## Official CLI Output Confirmed

Read-only commands worked through `/usr/local/bin/mpf`:

```text
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
```

BTC lane remains represented from config when DB lanes are empty:

```text
btc enabled=True backend_port=60010 chain_prefix=MPFBTC protocol=stratum source=config
```

## Known Warning

Time synchronization is still not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This does not block Phase 3.1 acceptance, but it blocks later production-sensitive features:

```text
production traffic
usage accounting
expiry/renew automation
hash-rate time-series collection
abuse automation
job automation that depends on reliable time
```

Do not activate the abuse runner or time-series collection while system time is unsynchronized.

## Acceptance Decision

```text
accepted: yes
```

## Still Forbidden After Phase 3.1

Do not activate yet:

```text
customer CRUD mutation
customer firewall rules
live firewall apply
NAT redirects
Docker proxy data-plane runtime
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

## Next Phase

Next working phase:

```text
Phase 4 — Compose Forward-only + Proxy Doctor Planning
```

Phase 4 must start with repository planning and a dedicated runbook. Runtime activation of Docker proxy components still requires an accepted Phase 4 execution plan and server validation.
