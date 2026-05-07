# AI Coding Rules

Status: active implementation contract

This file defines rules for AI coding agents working on `proxy-address-mining`.
It complements `AGENTS.md`, `docs/PHASE_STATUS.md`, `docs/SAFETY.md`, and the domain contracts.

## Mandatory Reading

Before changing code, scripts, migrations, config, services, jobs, UI, or documentation, read:

```text
AGENTS.md
README.md
docs/INDEX.md
docs/PHASE_STATUS.md
docs/SAFETY.md
docs/ROADMAP.md
docs/DATA_MODEL.md
docs/FIREWALL.md
docs/ABUSE.md
docs/AI_CODING_RULES.md
```

For hash-rate, share, worker, or observability work, also read:

```text
docs/OBSERVABILITY_HASHRATE.md
```

For proxy, Docker, backend ports, firewall guard, or Phase 4 work, also read:

```text
docs/BACKEND_PORT_POLICY.md
docs/PHASE_3_1_PRE_PHASE4_ALIGNMENT.md
```

## Phase Gate Rule

The current phase in `docs/PHASE_STATUS.md` is authoritative.

If a requested change belongs to a later phase, do not implement runtime behavior. Instead, refine the contract, add safe tests, and keep production behavior disabled.

Phase 4 must not begin until Phase 3.1 passes.

## Phase 3.1 Rule

Phase 3.1 exists because the server check showed that `/opt/mpf-py-src` contains Phase 3 code, while the official `mpf` runtime still executes the older Phase 1 smoke CLI.

Allowed in Phase 3.1:

```text
runtime alignment wrapper for the official mpf command
read-only verification scripts
documentation and contract improvements
hash-rate/share data-model planning
backend internal/external reachability rules
no traffic-changing behavior
```

Forbidden in Phase 3.1:

```text
Docker proxy container startup
v2rayA startup
forwarder/gost startup
customer CRUD mutation
customer firewall rules
NAT redirects
firewall apply
usage timers
abuse automation
block/pause automation
UI service
Telegram bot
production import
worker enforcement
```

## Service Boundary Rule

Business logic belongs in services and domain modules.

Required pattern:

```text
interface or job
  -> request DTO or command object
  -> service
  -> repository or adapter
  -> event and audit
  -> response DTO
```

Interfaces must stay thin. Repositories own persistence. Adapters own external-system interaction. Services own validation, transitions, audit, and side-effect ordering.

## Migration Rule

Schema changes require:

```text
SQLAlchemy model update
Alembic migration
migration test or documented restore strategy
phase approval before server migration
acceptance output recorded after server migration
```

Future production migrations should use explicit Alembic operations instead of relying on bootstrap-style `create_all/drop_all` patterns.

## Runtime Alignment Rule

The official server command must match the accepted repository phase.

For farm5, these commands must run through the accepted Phase 3 CLI before Phase 4 planning can be considered server-aligned:

```bash
mpf phase-status
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
```

If `/usr/local/bin/mpf` reports Phase 1 while `/opt/mpf-py-src` has Phase 3 tests passing, the server is not runtime-aligned.

## Backend Port Rule

Backend ports are internal service ports. They must be closed to direct external/public access while remaining reachable from valid internal server and Docker paths.

Required invariant:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not make internal health checks fail in order to hide backend ports from the outside.

## Hash-rate and Share Observability Rule

Accepted/rejected hash-rate per device is a first-class future capability.

Do not implement it as a UI-only calculation or a loose log parser.

Required future layers:

```text
Stratum/share evidence collection
share_events evidence table
device_hashrate_samples aggregated time-series
customer_hashrate_samples aggregated time-series
report service/API response DTOs
UI charts from aggregated samples
retention policy before high-volume collection
```

The term device must be modeled carefully. In early phases, device identity may be derived from:

```text
customer + lane + normalized_worker_name + src_ip + session evidence
```

Worker name alone must not be treated as a guaranteed physical device.

## Stop Conditions

Stop and revise if a change introduces:

```text
traffic-changing behavior before the matching phase
firewall apply before Phase 6
abuse automation before Phase 8
backend public exposure
backend internal reachability failure
NAT redirect before its phase
customer mutation before Phase 5
runtime CLI older than accepted phase
high-volume share collection without retention policy
UI charts reading raw high-volume events directly
worker blocking modeled as firewall-only
business logic inside interface handlers
secrets committed to the repository
```

When documents conflict, follow the stricter safety rule and update the docs before implementing code.
