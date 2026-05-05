# Proxy Address Mining

`proxy-address-mining` is a Python-first rewrite and modernization plan for a mining customer gateway.

The goal is to build a clean, maintainable, and extensible control plane for mining proxy customer ports, firewall policy, usage accounting, abuse handling, reporting, and future local UI / Telegram integration.

> This project is planned as a **greenfield implementation**, not a direct migration of old shell scripts.

---


## Current Status

This repository is currently in **Phase 0 / Phase 1** (planning and bootstrap) for a Python-first rewrite.

Implemented so far:

- architecture direction
- project roadmap
- safety and operational guardrails
- initial documentation

Not implemented yet:

- production Python package
- PostgreSQL schema and migrations
- firewall planner
- customer CRUD
- proxy stack management
- abuse runner
- local UI / Telegram integration

---

## Repository Scope

This repository is the implementation home for the new control-plane architecture.

- It defines target design, safety rules, and phased rollout expectations.
- It must stay aligned with the forward-only gateway model.
- It must remain lane-based (BTC, then ZEC/LTC and others through the same model).

---

## Phase 0/1 Execution Rule

Start only with:

1. Phase 0 — Architecture Freeze
2. Phase 1 — Preflight + Bootstrap

Do not start Phase 2+ until Phase 1 acceptance checks pass.

---

## Do Not Use In Production Yet

This project must **not** be used for production traffic yet.

During Phase 0/1, the project must not:

- create customer firewall rules
- create NAT redirects
- expose backend ports
- enable abuse automation
- enable block automation
- expose UI components
- onboard production customers
- apply firewall changes without plan/verify/rollback

---

## Next Implementation Outputs

The next concrete outputs should be:

1. `docs/ARCHITECTURE.md`
2. `docs/SAFETY.md`
3. initial `/etc/mpf/mpf.yaml` draft
4. PostgreSQL schema v1
5. Python package skeleton
6. config/db smoke tests

---

## Acceptance Checklist (Near-term)

- Phase 0 documents are frozen and reviewed.
- Phase 1 preflight checklist is complete.
- `firewall.apply_mode` remains `plan_only`.
- No live customer/NAT/firewall production changes exist.
- Initial config and DB planning artifacts are versioned in repository docs.

---

## Project Goal

This server is designed to act as a **forward-only customer gateway**:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

The first stable lane is expected to be BTC:

```text
BTC customer ports -> backend 60010 -> forwarder -> v2rayA -> pool
```

Future lanes such as ZEC and LTC must be implemented through the same lane model, not by cloning scripts per coin.

---

## Core Principles

### 1. Python-first

The new implementation must be written as a clean Python project with:

- typed domain/service layer
- CLI interface
- database-backed state
- clear adapters for firewall, Docker/Compose, conntrack, tcpdump, and future integrations
- testable modules

### 2. PostgreSQL as Source of Truth

The system should use local PostgreSQL as the primary source of truth.

Flat files and SQLite can be used only for temporary debug, import/export, or compatibility tooling.

### 3. API / Service Layer First

Business logic must not be locked inside the CLI.

The same core service layer should be usable by:

- CLI
- local Web UI
- Telegram bot
- future internal API

### 4. Safe Firewall Model

Firewall changes must never be applied as random one-off commands.

Every firewall operation must follow:

```text
read DB/config
  -> build desired model
  -> generate plan
  -> show diff
  -> backup live firewall
  -> apply atomically
  -> verify
  -> record event
  -> rollback if needed
```

### 5. Abuse Handling From Day One

Miner-abuse handling is a core requirement, not a later patch.

Required abuse state machine:

```text
normal
  -> over_tracking
  -> over_grace
  -> hard
```

Rules:

- all active customers in all enabled lanes must be covered
- no customer is excluded unless `abuse_exempt=true` with reason and expiry
- hardening must happen only after sustained miner-abuse for about 1 hour
- farms-over alone must not trigger hardening
- every hard/unhard action must be auditable
- every hard action must have a backup / restore point

Abuse tests must verify:

- active customers in all enabled lanes are scanned
- farms-over alone does not harden
- miner-over enters `over_tracking`
- temporary recovery enters `over_grace`
- sustained miner-over for about 3600s triggers `hard`
- hard action creates restore point
- manual unhard is audited

---

## What This Project Replaces

The older operational setup included many independent shell tools for:

- customer management
- audit
- usage
- abuse
- monitoring
- port diagnostics
- worker detection
- session/history logging
- policy/reject logging
- block/pause/note/event handling
- backup

The new project should preserve those operational capabilities, but implement them in a cleaner, testable, database-backed Python architecture.

---

## Target Architecture

```text
/opt/mpf-py/
  mpf/
    domain/
      customers.py
      policies.py
      abuse.py
      firewall_model.py
      events.py
      usage.py
      workers.py
      lanes.py

    adapters/
      db.py
      firewall_iptables.py
      firewall_nft.py
      docker_compose.py
      conntrack.py
      tcpdump.py
      notifier_telegram.py

    interfaces/
      cli.py
      api.py
      ui.py
      telegram_bot.py

    jobs/
      abuse_runner.py
      usage_snapshot.py
      block_expiry.py
      session_reconcile.py
      backup_runner.py

    migrations/
    tests/

  configs/
    mpf.yaml

  systemd/
```

---

## Standard Paths

Recommended production paths:

```text
Code:    /opt/mpf-py
Config:  /etc/mpf/mpf.yaml
Data:    /var/lib/mpf
Logs:    /var/log/mpf
Backups: /var/backups/mpf
CLI:     mpf
```

---

## Initial Configuration Model

Example `/etc/mpf/mpf.yaml`:

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

  zec:
    enabled: false
    backend_port: 60015
    chain_prefix: MPFZEC
    upstreams: []

  ltc:
    enabled: false
    backend_port: 60020
    chain_prefix: MPFLTC
    upstreams: []

abuse:
  enabled: true
  threshold_sec: 3600
  grace_sec: 900
```

During early phases, `firewall.apply_mode` must remain `plan_only`.

---

## Roadmap

### Phase 0 — Architecture Freeze

Goal: freeze decisions before any installation or data-plane work.

Outputs:

- architecture document
- project scope document
- guardrails
- Phase 1 preflight checklist

No package installation, service activation, firewall change, NAT redirect, customer creation, or automation must happen in this phase.

---

### Phase 1 — Preflight + Bootstrap

Goal: prepare the server without touching traffic.

Tasks:

- inspect OS, kernel, timezone, interfaces, routes, DNS
- inspect iptables backend and nft/legacy status
- install base tools
- prepare PostgreSQL
- prepare Python virtual environment
- create standard directories
- create initial config with `apply_mode: plan_only`
- create Python project skeleton

Acceptance:

```bash
mpf --help
mpf doctor
mpf config validate
mpf db ping
python -m pytest
systemctl status postgresql
docker version
docker compose version
conntrack -V
iptables --version
```

No customer rules, NAT redirects, backend public exposure, abuse automation, or block automation should exist yet.

---

### Phase 2 — PostgreSQL + Config + Domain Model

Goal: implement the real database and domain model.

Required tables include:

- lanes
- customers
- customer_policies
- customer_ip_pins
- blocks
- pauses
- notes
- events
- usage_samples
- abuse_state
- job_runs
- scheduler_locks
- firewall_snapshots
- firewall_rules_desired
- firewall_rules_live
- restore_points
- schema_migrations

Acceptance:

- migrations up/down pass
- config validation passes
- DB ping passes
- BTC lane seed exists
- no live firewall apply yet

---

### Phase 3 — CLI / Internal API

Goal: implement `mpf` as the main operator entrypoint.

Initial commands:

```bash
mpf config show
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
mpf doctor
```

The CLI should call the service layer, not implement business logic directly.

---

### Phase 4 — Compose Forward-only + Proxy Doctor

Goal: start the proxy data-plane without customer firewall rules.

Tasks:

- v2rayA
- v2raya bridge if needed
- simple-forwarder / gost for BTC backend `60010`
- healthchecks
- backend exposure detection
- proxy doctor

Acceptance:

- forwarder is listening
- v2rayA UI is local only
- backend direct external access is blocked or detected
- proxy doctor passes

---

### Phase 5 — Customer CRUD in DB Only

Goal: manage customers in DB without applying live firewall rules.

Features:

- add/edit/delete/renew/list
- days / expiry
- miners / farms / maxconn / rate / burst
- optional IP whitelist
- status model
- event logging
- port/lane collision detection

Acceptance:

- CRUD works in DB
- events are recorded
- collisions are detected
- no iptables rule is created yet

---

### Phase 6 — Firewall Planner

Goal: implement safe firewall plan/apply/verify/rollback.

Commands:

```bash
mpf firewall doctor
mpf firewall plan
mpf firewall diff
mpf firewall apply --yes
mpf firewall verify
mpf firewall rollback <apply_id> --yes
```

Planner must detect:

- port collision
- lane collision
- backend exposure
- orphan chains
- drift between DB and live firewall
- missing accounting rules

---

### Phase 7 — Usage + Policy / Reject Accounting

Goal: collect reliable traffic and reject data before abuse automation.

Features:

- usage snapshots
- 1h / 1d / 30d reports
- connlimit reject events
- hashlimit reject events
- pause/block reject events
- usage doctor

Acceptance:

- every active customer has accounting rules
- missing rule count is zero
- delta counters are reliable

---

### Phase 8 — Abuse 1h Core

Goal: enforce miner-abuse handling for all active customers.

State machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Hard action:

- backup / restore point
- set maxconn to miners
- firewall apply
- conntrack flush for the affected port/customer
- event record
- report output

Acceptance:

- all active customers in all enabled lanes are covered
- `abuse_exempt` requires reason and expiry
- farms-over alone does not harden
- sustained miner-abuse hardens after about 1 hour
- manual unhard is audited

---

### Phase 9 — Check / Report / Diagnostics

Goal: provide a clear final verdict for operators.

Commands:

```bash
mpf check <name|port>
mpf report <name|port>
mpf monitor summary
mpf monitor port <target>
mpf diag <target>
mpf audit miners-over
mpf audit farms-over
mpf audit suspicious
```

`mpf check` should answer:

- is the customer connected?
- does the customer have live rules?
- does NAT hit?
- are rejects from connlimit or hashlimit?
- is usage normal?
- is there IP/worker mismatch?
- what is the abuse state?

---

### Phase 10 — Session / Worker / Policy Timeline

Goal: provide forensic history.

Features:

- flow sessions
- worker events
- customer worker timeline
- policy/reject timeline
- session reconcile
- worker binding from Stratum authorize/submit
- evidence pack

Acceptance:

- active sessions visible per customer
- recently closed sessions visible
- unique IPs visible
- unique workers visible
- reject timeline visible
- worker timeline visible

---

### Phase 11 — Local Web UI Read-only

Goal: local-only web panel.

Pages:

- Dashboard
- Customers
- Customer detail
- Report
- Abuse status
- Usage
- Blocks
- Runbook

Rules:

- bind only to `127.0.0.1` or Unix socket
- read-only first
- no direct DB writes
- no direct firewall writes
- use service layer / API only

---

### Phase 12 — UI Actions With Confirmation

Goal: controlled UI actions.

Actions:

- add/edit/renew/delete customer
- set IPs
- firewall plan/apply
- block/unblock
- note add
- pause/unpause
- manual unhard

Rules:

- every action requires confirmation
- every action is audited
- dangerous actions create restore points
- plan output must be visible before apply

---

### Phase 13 — Telegram

Goal: notification first, commands later.

Stages:

1. notifications only
2. read-only commands
3. restricted actions with allowlist and confirmation

Notifications:

- abuse entered
- hard applied
- backend exposure detected
- backup failed
- proxy down
- customer due/expired

---

## Security Guardrails

- never expose backend ports publicly
- never expose v2rayA UI publicly
- never expose early Web UI publicly
- never hardcode Telegram tokens in source code
- secrets must live outside the repository
- service users should be least-privilege where possible
- firewall changes must be auditable
- all destructive actions need restore points
- direct DB edits are not normal operation
- direct iptables edits are not normal operation

---

## Operational Guardrails

Early phases must not:

- create production customers
- create NAT redirects
- enable abuse automation
- enable block automation
- expose backend ports
- expose UI
- onboard production traffic
- apply firewall rules without plan/verify/rollback

---

## Testing Strategy

Minimum test groups:

```text
config validation
database migrations
customer CRUD
lane collision
port collision
firewall plan generation
firewall drift detection
backend exposure detection
firewall rollback
abuse state machine
usage counter delta
job locking
backup/restore
```

---

## Backup / Restore

Backups must include:

- PostgreSQL dump
- `/etc/mpf`
- `/var/lib/mpf`
- `/var/log/mpf` if needed
- firewall snapshots
- restore points
- compose/config files

A backup strategy is not accepted until restore has been tested.

---

## Current Status

This repository is intended to become the implementation home for the Python rewrite.

Recommended first implementation steps:

```text
1. write Phase 0 architecture docs
2. run Phase 1 preflight on the new server
3. create Python project skeleton
4. create PostgreSQL schema v1
5. keep firewall.apply_mode = plan_only
```

---

## License

License is not defined yet.

Choose and add a license before public or multi-person use.
