# SAFETY

Status: Draft v1

This document defines safety guardrails for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

## Safety Goal

The project manages customer-facing mining gateway traffic and firewall policy.
A mistake can disconnect production customers, expose backend ports, or block valid traffic.

The default posture is:

```text
plan first
show diff
backup
apply atomically
verify
record event
rollback if needed
```

No implementation may optimize away safety steps for convenience.

## Phase Gates

### Phase 0: Architecture Freeze

Allowed:

- write and review documentation
- define architecture
- define safety rules
- define data model
- define preflight checklist

Forbidden:

- package installation
- service activation
- firewall changes
- NAT redirects
- customer creation
- abuse automation
- block automation
- UI exposure
- Telegram bot activation

### Phase 1: Preflight + Bootstrap

Allowed:

- inspect server state
- install base packages
- prepare PostgreSQL
- prepare Python virtual environment
- create standard directories
- create initial config
- create skeleton project
- run smoke tests

Forbidden:

- production customer rules
- NAT redirects
- backend public exposure
- live firewall apply for customer state
- abuse automation
- block automation
- pause automation
- local UI actions
- Telegram actions

During Phase 1:

```yaml
firewall:
  apply_mode: plan_only
```

must remain unchanged.

### Phase 2+

Later phases may introduce DB schema, CLI/API, Compose data plane, customer CRUD, firewall planner, usage, abuse, UI, and Telegram only after earlier acceptance checks pass.

## Global Non-Negotiable Rules

- PostgreSQL is the source of truth.
- `/etc/mpf/mpf.yaml` is configuration, not mutable runtime state.
- CLI, UI, Telegram, and future API must use the same service layer.
- Business logic must not live in CLI handlers.
- No interface may directly write DB tables.
- No interface may directly run iptables commands.
- No recurring job may bypass service validation.
- No customer firewall mutation may happen while `firewall.apply_mode=plan_only`.
- No destructive action may run without an event record.
- No dangerous action may run without a restore point.
- Secrets must not be committed to the repository.
- Backend ports must not be publicly exposed.
- v2rayA UI must not be publicly exposed.
- Early Web UI must not be publicly exposed.

## API-First Safety Boundary

Correct pattern:

```text
CLI / API / UI / Telegram
  -> request DTO / command object
  -> service layer
  -> repository / adapter
  -> event + audit
  -> response DTO
```

Forbidden pattern:

```text
CLI -> subprocess("iptables ...")
UI -> direct SQL update
Telegram -> shell command
job -> direct table mutation without service validation
```

The service layer owns validation, state transitions, audit, and side-effect ordering.

## Firewall Safety

All firewall changes must go through `firewall_service` and firewall adapters.

Required lifecycle:

```text
read DB/config
  -> build desired model
  -> generate plan
  -> show human diff
  -> show JSON diff
  -> create restore point
  -> backup live firewall snapshot
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event
  -> rollback plan if verify fails
```

Required detection before apply:

- port collision
- lane backend collision
- customer chain collision
- orphan chain
- backend direct exposure
- drift between DB desired state and live firewall
- missing accounting rules
- missing NAT redirect
- duplicated rule
- unsupported iptables backend

Allowed apply mechanism:

```text
iptables-save
iptables-restore
```

Direct one-off production mutations are forbidden:

```text
iptables -A ...
iptables -D ...
iptables -I ...
iptables -F ...
```

These commands may only be used in isolated tests, diagnostics, or generated restore scripts, never as normal production state mutation.

## Locking

The following operations require locks:

- firewall apply
- firewall rollback
- abuse hard / unhard
- block expiry job
- pause sync job
- backup creation
- restore point creation
- schema migration

Default lock paths:

```text
/run/mpf-firewall.lock
/run/mpf-jobs.lock
/run/mpf-backup.lock
```

Database-backed scheduler locks are required for recurring jobs.

## Restore Points

Restore points are required before:

- firewall apply
- firewall rollback
- abuse hard
- manual unhard
- bulk customer policy change
- block list sync
- pause sync
- schema migration that changes production tables

A restore point should include:

- PostgreSQL state reference or dump marker
- `/etc/mpf` snapshot
- live firewall snapshot
- desired firewall model
- operation metadata
- operator or job identity
- timestamp

A backup strategy is not accepted until restore has been tested.

## Abuse Safety

Miner-abuse handling is mandatory for all active customers in all enabled lanes.

A customer may be excluded only with:

```text
abuse_exempt = true
reason is not empty
expiry is set
operator/event is recorded
```

Hardening must happen only after sustained miner-abuse for about one hour.

Farms-over alone must not harden a customer.

Hard action must create:

- policy backup
- restore point
- firewall plan
- firewall apply record
- conntrack flush event
- abuse event
- operator/job audit record

Manual unhard must also be audited.

## Secrets and Credentials

Forbidden in repository:

- Telegram bot tokens
- database passwords
- pool credentials
- private proxy subscription URLs
- production customer private notes that include secrets

Secrets must live outside Git:

```text
/etc/mpf/secrets.env
/etc/mpf/secrets.d/
```

Recommended permissions:

```text
owner: root or mpf
mode: 0600
```

## UI and API Exposure

Early API and UI must bind only to local interfaces:

```text
127.0.0.1
Unix socket
```

Forbidden early bindings:

```text
0.0.0.0
public IP
Docker published port without localhost bind
```

UI must be read-only first.

Any future UI action must:

- call service layer
- require confirmation for dangerous operations
- show plan before apply
- record event/audit
- create restore point when needed

Telegram starts as notification-only.

## Job Safety

Use systemd timers, not mixed cron and systemd.

Every job run must write `job_runs`.

Every job must have:

- name
- start time
- finish time
- status
- duration
- error message, if failed
- affected customer count, if applicable
- event references, if applicable

Jobs must be idempotent where possible.

A failed job must not leave partial unaudited state.

## Logging and Retention

Required logs:

- application logs
- job logs
- firewall apply logs
- abuse transition logs
- backup logs
- UI/API audit logs, later

Retention must be explicit for:

- application logs
- usage samples
- policy events
- flow/session history
- worker events
- backups
- restore points

No infinite growth by default.

## Canary Policy

First production traffic must use a canary customer.

Canary validation must verify:

- customer can connect
- NAT hits expected backend
- direct backend public access is blocked
- accounting counters move
- rejects are understandable
- `mpf check` returns a clear verdict
- rollback works

## Failure Behavior

When verification fails after apply:

- do not silently continue
- record failed event
- produce rollback plan
- restore if configured for automatic rollback
- report affected customers

When DB is unavailable:

- read-only diagnostics may degrade
- firewall apply is forbidden
- abuse hard/unhard is forbidden
- customer mutation is forbidden

When config is invalid:

- services must fail closed
- no firewall apply may run

## AI Coding Agent Safety Checklist

Before implementing or changing code, an AI agent must verify:

- this file was read
- `docs/ARCHITECTURE.md` was read
- relevant domain docs were read
- change respects API-first boundaries
- dangerous action has event/audit
- dangerous action has restore point
- tests exist for safety-critical behavior
- no direct firewall or DB mutation was added through an interface
- no Phase 0/1 forbidden action was introduced

A patch that weakens these rules must be rejected.
