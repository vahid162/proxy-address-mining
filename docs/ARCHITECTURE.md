# ARCHITECTURE

Status: Draft v1

This document defines the target architecture for `proxy-address-mining`.
It is written as an implementation contract for humans and AI coding agents.

## Goal

Build a Python-first, API-first, database-backed mining customer gateway control plane.

The server role is:

```text
forward-only customer gateway
```

The data plane is:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

The first production lane is BTC:

```text
BTC customer ports -> backend 60010 -> forwarder -> v2rayA -> pool
```

Future coins such as ZEC and LTC must be added as lanes, not as copied scripts.

## Non-goals

The following are out of scope for the first stable control-plane version:

- fee-aware Stratum routing
- public web panel
- multi-server central dashboard
- billing / financial accounting
- Telegram write actions
- direct nftables migration
- real-time packet streaming in UI
- auto-tuning firewall policy

## Architecture Rule: API First

API-first means the system is designed around explicit service contracts before CLI or UI behavior.

Business logic must live in domain/service modules.

Interfaces must call the same service layer:

```text
CLI
Local Web UI
Telegram bot
Future internal REST API
```

No interface may own business logic.

Forbidden patterns:

```text
CLI parses command -> directly edits DB
CLI parses command -> directly runs iptables
UI form -> directly writes DB
Telegram command -> directly runs shell command
Job runner -> bypasses service validation
```

Required pattern:

```text
interface
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit record
  -> response DTO
```

The CLI is a thin operator client, not the core application.

## Target Repository Layout

```text
/opt/mpf-py/
  mpf/
    domain/
      abuse.py
      blocks.py
      customers.py
      events.py
      firewall_model.py
      lanes.py
      policies.py
      usage.py
      workers.py

    services/
      abuse_service.py
      block_service.py
      customer_service.py
      firewall_service.py
      job_service.py
      report_service.py
      usage_service.py

    repositories/
      abuse_repo.py
      customer_repo.py
      event_repo.py
      firewall_repo.py
      job_repo.py
      usage_repo.py

    adapters/
      db.py
      conntrack.py
      docker_compose.py
      firewall_iptables.py
      firewall_nft.py
      tcpdump.py
      notifier_telegram.py

    interfaces/
      cli.py
      api.py
      ui.py
      telegram_bot.py

    jobs/
      abuse_runner.py
      backup_runner.py
      block_expiry.py
      session_reconcile.py
      usage_snapshot.py

    migrations/
    tests/

  configs/
    mpf.yaml

  systemd/
```

## Module Responsibilities

### Domain

Domain modules contain pure business rules and state machines.
They should not call subprocesses, Docker, iptables, conntrack, or the network.

Examples:

- customer validity
- policy transitions
- abuse state transition
- lane collision rules
- firewall desired model objects

### Services

Services orchestrate domain logic, repositories, adapters, events, and transactions.

Examples:

- add customer
- renew customer
- build firewall plan
- apply firewall plan
- run abuse scan
- create restore point

### Repositories

Repositories read and write PostgreSQL state.
They must not contain business decisions.

### Adapters

Adapters are the only modules allowed to talk to external systems:

- iptables / iptables-save / iptables-restore
- nftables, later
- Docker Compose
- conntrack
- tcpdump
- systemd, if needed
- Telegram, later

### Interfaces

Interfaces expose commands or UI/API endpoints.
They must be thin wrappers around service calls.

## Configuration

The canonical config path is:

```text
/etc/mpf/mpf.yaml
```

Initial required fields:

```yaml
server:
  name: farm-new-1
  timezone: Europe/Berlin

paths:
  app: /opt/mpf-py
  data: /var/lib/mpf
  logs: /var/log/mpf
  backups: /var/backups/mpf

database:
  url: postgresql:///mpf

firewall:
  backend: iptables
  apply_mode: plan_only
  lock_path: /run/mpf-firewall.lock

lanes:
  btc:
    enabled: true
    backend_port: 60010
    chain_prefix: MPFBTC
    upstreams:
      - host: bitcoin.viabtc.io
        port: 3333

abuse:
  enabled: true
  threshold_sec: 3600
  grace_sec: 900
```

During Phase 0 and Phase 1, `firewall.apply_mode` must remain `plan_only`.

## Lane Model

Lane is a first-class model from day one.

A lane owns:

- coin / protocol name
- backend port
- firewall chain prefix
- upstream pool endpoints
- forwarder configuration
- enabled / disabled status

BTC uses backend `60010`.

Additional coins must be created by adding lanes, not by copying scripts or duplicating command trees.

## Source of Truth

PostgreSQL is the source of truth.

Allowed uses of flat files or SQLite:

- import from old scripts
- export for debugging
- temporary compatibility tooling
- backup artifacts

Forbidden uses:

- primary customer database
- primary abuse state database
- primary usage state database
- split production state across multiple SQLite files

## Firewall Lifecycle

Every firewall operation must follow this lifecycle:

```text
read DB/config
  -> build desired model
  -> generate plan
  -> show human diff + JSON diff
  -> create restore point
  -> backup live firewall snapshot
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event
  -> rollback plan if verify fails
```

No code path may apply a single ad-hoc iptables command for production state.

## Jobs and Scheduling

Use systemd timers, not mixed cron/systemd automation.

Every recurring job must record `job_runs`.
Every job that can overlap must use `scheduler_locks`.

Required early jobs:

- usage snapshot
- abuse runner
- block expiry
- backup runner
- session reconcile, later

## Events and Audit

Every meaningful action must create an event.

Required event categories:

- customer changed
- firewall planned
- firewall applied
- firewall rollback planned
- abuse entered
- abuse hard applied
- abuse unhard applied
- block added / expired
- pause added / removed
- backup created / failed
- restore point created
- job succeeded / failed

Events must be structured enough for CLI, UI, reports, and Telegram notifications.

## Local UI and Telegram

UI and Telegram are future interfaces only.

Rules:

- local UI must bind only to `127.0.0.1` or Unix socket
- first UI version is read-only
- no UI direct DB writes
- no UI direct firewall writes
- Telegram starts as notifications only
- Telegram actions require allowlist and confirmation, later

## Implementation Order

Do not start production data-plane behavior until the earlier phase gates pass.

Recommended order:

```text
0. architecture freeze
1. preflight + bootstrap
2. PostgreSQL + config + domain model
3. CLI / internal API
4. compose forward-only + proxy doctor
5. customer CRUD in DB only
6. firewall planner
7. usage accounting
8. abuse 1h core
9. check / report / diagnostics
10. session / worker / policy timeline
11. local UI read-only
12. UI actions with confirmation
13. Telegram notifications / commands
```

## AI Coding Rules

AI coding agents must preserve these invariants:

- no business logic in CLI handlers
- no direct firewall mutation outside firewall service/adapters
- no direct DB mutation outside repositories/services
- no production firewall apply while `apply_mode=plan_only`
- no customer can be excluded from abuse scanning unless explicit exemption with reason and expiry exists
- no lane-specific copied command tree
- no secrets in repository
- no destructive action without event and restore point
