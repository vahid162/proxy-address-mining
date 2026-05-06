# AI Agent Instructions

This repository is a Python-first, API-first greenfield rewrite of a mining proxy customer gateway control plane.

The project replaces an older shell-script-based operational setup, but it must not copy, patch, or extend the old scripts directly.
The goal is to preserve operational capabilities while implementing a clean, testable, PostgreSQL-backed Python architecture.

This file is mandatory reading for every human contributor and AI coding agent before making changes.

## 1. Mandatory Reading Order

Before changing documentation, code, tests, scripts, config, or deployment artifacts, read these files in order:

1. `README.md`
2. `docs/INDEX.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SAFETY.md`
5. `docs/ROADMAP.md`
6. `docs/PHASE_0.md`
7. `docs/PHASE_1.md`
8. `docs/DATA_MODEL.md`
9. `docs/FIREWALL.md`
10. `docs/ABUSE.md`
11. the relevant phase document for the task
12. the relevant domain document for the task

If these documents conflict, follow the stricter safety rule and update the documentation before implementing code.

## 2. Project Identity

This project is:

```text
Python-first
API-first
PostgreSQL-backed
service-layer based
lane-based
firewall-plan based
safety-gated
```

This project is not:

```text
a direct shell-script migration
a CLI-first tool
a random iptables command generator
a SQLite/TSV production state system
a public web panel in early phases
a Telegram-first automation system
```

## 3. Fixed Architecture Decisions

These decisions are frozen for the initial implementation:

```text
server role: forward-only customer gateway
source of truth: local PostgreSQL
code path: /opt/mpf-py
config path: /etc/mpf/mpf.yaml
data path: /var/lib/mpf
logs path: /var/log/mpf
backup path: /var/backups/mpf
CLI name: mpf
first lane: BTC
BTC backend port: 60010
firewall backend: iptables first
firewall apply mechanism: iptables-save / iptables-restore
scheduler: systemd timers
initial firewall mode: plan_only
local API/UI binding: 127.0.0.1 or Unix socket only
```

## 4. API-First Rule

Business logic must live in domain/service modules, not in interfaces.

Required pattern:

```text
CLI / API / UI / Telegram / jobs
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Forbidden patterns:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly updates tables
Telegram directly runs shell commands
job writes state without service validation
adapter owns business decisions
```

Interfaces must be thin.
Services own validation, business transitions, audit, and side-effect ordering.
Repositories own persistence.
Adapters own external system interaction.

## 5. Source of Truth Rule

PostgreSQL is the production source of truth.

Allowed uses of flat files or SQLite:

- import from old scripts
- export/debug artifacts
- temporary migration tooling
- generated restore artifacts
- backup files

Forbidden uses:

- production customer database
- production abuse state
- production usage state
- production firewall desired state
- multiple scattered SQLite databases as active runtime state
- TSV as the main customer source of truth

## 6. Lane Rule

Multi-lane support is required from day one.

BTC is the first lane and uses backend port `60010`.
Future coins such as ZEC/LTC must be implemented through lanes.

Forbidden:

```text
copy scripts per coin
copy command trees per coin
hardcode BTC-only assumptions into service logic
```

Allowed:

```text
lane config
lane database records
lane-aware services
lane-specific adapters only where unavoidable
```

## 7. Firewall Safety Rules

All production firewall changes must go through the firewall service and firewall adapter.

Required lifecycle:

```text
read DB/config
  -> build desired model
  -> compare desired with live firewall
  -> generate plan
  -> show human diff
  -> show JSON diff
  -> create restore point
  -> backup live firewall
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event/audit
  -> rollback or rollback-plan on failure
```

Forbidden production mutations:

```text
iptables -A ...
iptables -D ...
iptables -I ...
iptables -F ...
one-off NAT redirect commands
ad-hoc DOCKER-USER edits
interface-triggered firewall shell commands
```

Allowed apply mechanism:

```text
iptables-save
iptables-restore
```

Direct firewall commands may appear only in diagnostics, tests, or generated emergency restore artifacts, not as normal production state mutation.

## 8. Phase Gates

Follow phase order from `docs/ROADMAP.md`.

### Phase 0

Documentation-only.

Forbidden:

- package installation
- server mutation
- service activation
- firewall mutation
- NAT redirects
- customer onboarding
- automation activation

### Phase 1

Preflight and bootstrap without traffic changes.

Forbidden:

- customer firewall rules
- NAT redirects
- backend exposure
- abuse automation
- block automation
- pause automation
- UI actions
- Telegram actions
- switching away from `firewall.apply_mode=plan_only`

### Later Phases

Do not implement a later phase until the current phase acceptance gate passes.
A phase is complete only when its tests and acceptance checks pass.

## 9. Abuse Requirement

The one-hour miner-abuse state machine is mandatory.

Required state flow:

```text
normal -> over_tracking -> over_grace -> hard
```

Required rules:

- all active customers in all enabled lanes must be scanned
- no silent skip is allowed
- exemption requires reason and expiry
- farms-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- hard creates restore point
- hard creates policy backup
- hard uses firewall plan/apply/verify path
- hard flushes affected conntrack scope
- manual unhard is audited

A patch that weakens this requirement must be rejected.

## 10. Events, Audit, and Restore Points

Every meaningful mutation must record an event.

Every dangerous or destructive action must create a restore point.

Required before these actions:

- firewall apply
- firewall rollback
- abuse hard
- manual unhard
- bulk customer policy change
- block sync
- pause sync
- risky schema migration

Audit is required for:

- customer create/edit/delete/renew
- policy changes
- firewall apply/rollback
- abuse hard/unhard
- block/pause changes
- backup/restore operations
- UI actions, later
- Telegram actions, later

## 11. Jobs and Scheduling

Use systemd timers, not mixed cron and systemd.

Every recurring job must write `job_runs`.
Every job that can overlap must use `scheduler_locks`.

Required job safety:

- idempotent where possible
- no silent partial state
- clear failed/degraded status
- event references for meaningful actions
- no bypass of service validation

## 12. Secrets

Never commit secrets.

Forbidden in repository:

- Telegram bot tokens
- database passwords
- pool credentials
- private proxy subscription URLs
- production customer private secrets

Secrets belong outside Git, for example:

```text
/etc/mpf/secrets.env
/etc/mpf/secrets.d/
```

Recommended permissions:

```text
0600 for secret files
0750 for secret directories
```

## 13. UI, API, and Telegram

Early API/UI must bind only locally:

```text
127.0.0.1
Unix socket
```

Forbidden in early phases:

```text
0.0.0.0 binding
public IP binding
public Docker port for UI/API
UI direct DB writes
UI direct firewall commands
Telegram direct DB writes
Telegram direct shell commands
```

UI is read-only first.
Telegram is notification-only first.
Actions come later with allowlist, confirmation, event/audit, and restore points when needed.

## 14. Test Expectations

Safety-critical code must include tests.

Minimum risk areas:

### Firewall

- planner generation
- port collision
- lane collision
- backend exposure detection
- orphan chain detection
- desired/live drift
- rollback from snapshot
- failed verify behavior

### Abuse

- state machine transitions
- all active customers scanned
- farms-over alone does not harden
- exemption expiry
- hard creates restore point and policy backup
- manual unhard audit

### Data Model

- migrations
- constraints
- policy versioning
- restore point relationships
- job_runs and scheduler_locks

### Interfaces

- CLI uses services
- API uses services
- no direct DB/firewall mutation from interface layer

## 15. Stop Conditions

Stop and revise before continuing if a change introduces any of these:

1. firewall apply before Phase 6
2. abuse automation before Phase 8
3. customer rule creation during Phase 1
4. NAT redirect during Phase 1
5. backend public exposure
6. UI direct DB write
7. Telegram shell command execution
8. bypassing `apply_mode=plan_only`
9. production TSV/SQLite source of truth
10. customer excluded from abuse without valid exemption
11. business logic inside CLI handler
12. ad-hoc production iptables mutation
13. missing restore point for dangerous action
14. missing event/audit for mutation

## 16. Before Submitting a Patch

Check:

```text
[ ] Required docs were read.
[ ] Change matches the current phase.
[ ] No forbidden phase action was introduced.
[ ] API-first boundary is preserved.
[ ] PostgreSQL remains source of truth.
[ ] Firewall changes go through planner/service.
[ ] Abuse 1h rule is preserved.
[ ] Events/audit are added for mutations.
[ ] Restore points are added for dangerous actions.
[ ] Tests cover safety-critical behavior.
[ ] Secrets are not committed.
[ ] UI/API/Telegram exposure remains local/safe.
```

## 17. Review Standard

A change is not acceptable just because it works locally.

It must also:

- respect phase gates
- preserve safety invariants
- be testable
- be auditable
- avoid hidden side effects
- avoid direct production firewall mutation
- avoid direct interface-to-database writes

When in doubt, choose the safer implementation and document the tradeoff.
