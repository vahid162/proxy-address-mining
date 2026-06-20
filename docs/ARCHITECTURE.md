# ARCHITECTURE

Status: Canonical architecture contract

This document defines static architecture authority for `proxy-address-mining`. Current runtime state, current phase, gates, and permissions come only from [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).

## Goal

Build a Python-first, API-first, PostgreSQL-backed mining customer gateway control plane for a forward-only customer gateway.

## Data plane

```text
customer_port -> firewall policy -> NAT redirect -> lane backend -> forwarder -> v2rayA -> pool
```

Lanes model coin/backend routing. New coins are added as lanes, not copied scripts.

## Product and expansion boundaries

UI, Telegram, worker enforcement, buyer-facing features, public exposure, public API, and broad production expansion are future or out-of-scope unless a current explicit gate in `docs/PHASE_STATUS.md` opens them. They must never become implementation backends.

## API-first service model

Business logic lives in domain and service modules. Interfaces call the same service layer:

```text
CLI / Local UI / Future API / Future Buyer UI / Future Telegram
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit record
  -> response DTO
```

Forbidden patterns:

```text
CLI parses command -> directly edits DB
CLI parses command -> directly runs iptables
UI form -> directly writes DB
Buyer UI -> directly mutates customer policy/firewall/abuse state
Telegram command -> directly runs shell command
Job runner -> bypasses service validation
```

## Module responsibilities

### Domain

Domain modules contain pure business rules and state machines. They do not call subprocesses, Docker, iptables, conntrack, systemd, the database, or the network.

### Services

Services orchestrate domain logic, repositories, adapters, transactions, locks, events, audit, restore points, and evidence.

### Repositories

Repositories own PostgreSQL persistence and queries. PostgreSQL is the source of truth for control-plane state.

### Adapters

Adapters own external I/O: firewall backends, Docker, conntrack, tcpdump, systemd integration, notifications, and future worker-enforcement integrations.

### Interfaces

Interfaces expose commands or endpoints and remain thin wrappers around service calls.

### Jobs

Jobs are scheduled entrypoints that call services, use locks, emit evidence, and record events/audit. They must not bypass service validation.

## Configuration

Local configuration is file-based and should remain separate from mutable runtime state. Configuration supplies local paths, database connection details, firewall backend, lane definitions, and safe defaults.


## Canonical paths

The canonical local operating paths are:

```text
/opt/mpf-py        application checkout/runtime package path
/etc/mpf/mpf.yaml local configuration file
/var/lib/mpf      durable application data
/var/log/mpf      logs and diagnostics
/var/backups/mpf  backups and restore-point artifacts
```

These paths describe the static operating model. They do not authorize live server mutation, installation, migration, or production execution.

## Lane model

A lane owns the protocol or coin, backend port, firewall chain prefix, upstreams, forwarder configuration, and enabled state. Customer-facing ports attach to lanes through policy and firewall planning. New coins or protocols must be modeled as lanes rather than copied scripts or one-off per-coin command paths.

## Source-of-truth boundary

PostgreSQL is authoritative for production control-plane state. Flat files, JSON artifacts, CSV exports, and SQLite may be used only for import, export, debug, test, evidence, or compatibility artifacts. They must not become split production state or an alternate source of truth for customers, policy, firewall, usage, abuse, events, or audit.

## Customer, buyer, and operator identity boundary

Customers are service and port allocation records. Buyer and operator identities are separate access, ownership, or review concepts and must not be conflated with customer service records. Future buyer-facing interfaces are read-only first and may not directly mutate customer policy, firewall, abuse, block, pause, or database state.

## Worker-enforcement boundary

Worker identity is Stratum-layer evidence. Worker enforcement cannot be implemented as firewall-only enforcement because firewall rules do not prove worker identity. Future worker enforcement requires session/worker evidence, approved adapters, service-layer decisions, audit records, and rollback/disable paths.

## Sequencing and authorization links

Implementation sequencing and long-term product ordering live in [`docs/ROADMAP.md`](ROADMAP.md). Current runtime authorization, phase state, gates, and next required work remain only in [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).

## Firewall lifecycle

Firewall changes use the service and adapter boundary:

```text
read DB/config -> build desired model -> generate plan -> show diff -> create restore point -> acquire lock -> apply atomically -> verify -> event/audit -> rollback path
```

The preferred apply family is snapshot/restore based, not direct one-off command mutation from interfaces.

## Scheduling direction

Recurring automation should use systemd timers/services through service-layer jobs, with locks, evidence, and audit records. Mixing hidden cron behavior with systemd direction is not part of the canonical design.

## Event and audit requirements

Dangerous decisions, state transitions, side effects, verification results, restore points, and rollback outcomes must produce event/audit records. Audit records must be sufficient for operator review without exposing secrets.

## Future interface boundaries

Future UI and Telegram work may call only service contracts and must preserve validation, authorization, restore, evidence, event, and audit boundaries. Future worker enforcement requires explicit gated support and cannot be implemented as a firewall-only shortcut.
