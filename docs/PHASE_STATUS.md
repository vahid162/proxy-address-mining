# PHASE STATUS

Status: Active project control file

This file tells humans and AI coding agents what phase is currently allowed.
It must be checked before writing code, scripts, deployment files, services, jobs, or tests.

## Current State

```text
current_accepted_phase: Phase 3 — CLI + Internal API Foundation
current_working_phase: Phase 3.1 — Pre-Phase4 Runtime Alignment + Future Observability Contracts
server_state: farm5 Phase 3 source artifact verified, but official mpf runtime still needs Phase 3 alignment
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: no
proxy_data_plane_allowed: no
ui_allowed: no
telegram_allowed: no
```

Phase 4 planning and runtime activation must not continue until Phase 3.1 is completed and recorded.

## Why Phase 3.1 Exists

The farm5 verification showed:

```text
/opt/mpf-py-src contains Phase 3 source and pytest passes
/usr/local/bin/mpf still points to the older Phase 1 smoke CLI
```

This is safe because no traffic-changing behavior is active, but it is not acceptable to start Phase 4 while the official operator command is older than the accepted repository phase.

## Phase 1 Server Result

Phase 1 bootstrap was completed and verified on `farm5`.

Accepted Phase 1 checks:

```text
PostgreSQL active
Docker active
containerd active
mpf config validate OK
mpf doctor OK
mpf db ping OK
pytest passed
Docker has no containers
No MPF firewall rules exist
firewall.apply_mode remains plan_only
```

Current warning:

```text
system clock synchronization is not confirmed
systemd-timesyncd is active, but public NTP replies timed out
```

This warning is not a Phase 1, Phase 2, Phase 3, or Phase 3.1 blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, or abuse automation.

## Phase 2 Server Result

Phase 2 schema migration was completed and verified on `farm5`.

Accepted Phase 2 checks:

```text
backup/snapshot created before migration
pytest passed from /opt/mpf-py-src/.venv
alembic heads/history passed
alembic current worked as system user mpf
alembic upgrade head completed
alembic_version = 0001_phase2_initial_schema
public schema table count = 64
required table check passed
missing required table count = 0
runtime tables remain empty
Docker has no containers
No MPF firewall rules exist
firewall.apply_mode remains plan_only
no proxy data-plane was started
no production traffic was changed
```

Backup artifact recorded on server:

```text
/var/backups/mpf/phase2-align-20260507T085831Z
```

## Phase 3 Server Result

Phase 3 read-only CLI/API foundation source was completed and verified on `farm5` under:

```text
/opt/mpf-py-src
```

Accepted Phase 3 source checks:

```text
source aligned from uploaded GitHub main archive
backup created before source alignment
pytest passed: 48 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK from Phase 3 source path
mpf lanes list OK and read-only from Phase 3 source path
mpf customer list OK and read-only from Phase 3 source path
mpf jobs status OK and read-only from Phase 3 source path
alembic current/head = 0001_phase2_initial_schema
public schema table count = 64
runtime tables remain empty
Docker has no containers
No MPF firewall or NAT rules exist
No MPF systemd units/timers exist
No MPF cron jobs exist
firewall.apply_mode remains plan_only
no production traffic was changed
```

Backup artifact recorded on server:

```text
/var/backups/mpf/phase3-source-align-20260507T140233Z
```

See also:

```text
docs/PHASE_3_SERVER_RESULT.md
```

## Phase 3.1 Required Work

Allowed work is limited to safe alignment and contracts:

```text
- promote official /usr/local/bin/mpf runtime to the accepted Phase 3 CLI wrapper
- run scripts/verify_phase3_1_alignment.sh
- preserve firewall.apply_mode=plan_only
- preserve empty runtime tables
- preserve no Docker proxy containers
- preserve no MPF firewall/NAT rules
- preserve no MPF systemd/cron automation
- document backend internal/external reachability policy
- document hash-rate/share observability contracts
- update AI coding rules and documentation map
```

Relevant files:

```text
docs/PHASE_3_1_PRE_PHASE4_ALIGNMENT.md
docs/AI_CODING_RULES.md
docs/BACKEND_PORT_POLICY.md
docs/OBSERVABILITY_HASHRATE.md
scripts/promote_phase3_runtime.sh
scripts/verify_phase3_1_alignment.sh
```

## What Is Forbidden Now

Do not implement or activate:

```text
- live customer onboarding
- customer CRUD mutation
- customer firewall rules
- live firewall apply
- NAT redirects
- usage timers
- hash-rate/share collectors
- abuse runner automation
- block or pause automation
- Docker proxy data-plane containers
- v2rayA runtime
- forwarder/gost runtime
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
- public API binding
```

Customer schema/model work is already represented, but live customer operations must wait for the proper later phase.

## Current Safety Invariant

The accepted server and repository must preserve:

```text
firewall.apply_mode = plan_only
```

Any patch that bypasses `plan_only` or introduces traffic-changing behavior before the correct phase must be rejected.

## Backend Port Invariant

Backend ports must be blocked from direct external/public access only. They must remain reachable from valid internal server and Docker paths.

Required future proxy/firewall doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by blocking loopback, local server paths, required Docker/internal paths, or the future MPF-owned NAT redirect path.

## Hash-rate and Share Observability Invariant

Accepted/rejected hash-rate per device is a future first-class capability.

It must be planned through:

```text
share evidence
share_events
device_hashrate_samples
customer_hashrate_samples
report services
UI charts from aggregate samples
retention before high-volume collection
```

Do not implement it later as UI-only calculations or unstructured log parsing.

## Phase 3.1 Acceptance Gate

Before Phase 4 planning resumes, this must pass on farm5:

```bash
sudo bash /opt/mpf-py-src/scripts/promote_phase3_runtime.sh
sudo bash /opt/mpf-py-src/scripts/verify_phase3_1_alignment.sh
```

Acceptance criteria:

```text
official mpf runtime exposes Phase 3 read-only commands
Phase 3 tests pass
Alembic current/head remain 0001_phase2_initial_schema
runtime-facing tables remain empty
Docker still has no proxy containers
No MPF firewall/NAT rules exist
No MPF systemd/cron automation exists
firewall.apply_mode remains plan_only
no production traffic changed
```

## Next Planned Step

Complete Phase 3.1 first.

After Phase 3.1 is recorded, Phase 4 may return to repository-only planning for:

```text
Compose Forward-only + Proxy Doctor
```

Do not move to customer CRUD, firewall apply, customer NAT redirects, usage timers, hash-rate collectors, or abuse automation until the relevant later phase gates pass.
