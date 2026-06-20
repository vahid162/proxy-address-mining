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
