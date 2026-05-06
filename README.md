# Proxy Address Mining

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed rewrite of a mining customer gateway control plane.

The goal is to build a clean, maintainable, safe, and extensible system for:

- customer ports
- firewall policy
- NAT redirects
- usage accounting
- abuse handling
- reporting and diagnostics
- future local Web UI
- future Telegram integration

This is a **greenfield implementation**, not a direct migration or patching of old shell scripts.

---

## Current Status

This repository is currently in:

```text
Phase 0 — Architecture Freeze
Phase 1 — Preflight + Bootstrap Without Traffic Changes
```

Current focus:

- architecture standard
- safety rules
- API-first boundaries
- data model contract
- firewall planner contract
- mandatory abuse state machine
- roadmap and phase gates
- Phase 1 preflight/bootstrap contract

Not implemented yet:

- production Python package
- PostgreSQL migrations
- customer CRUD
- live firewall planner/apply
- proxy stack management
- usage accounting
- abuse runner
- local UI
- Telegram integration

Do not use this repository for production traffic yet.

---

## Project Objective

Build a new MPF control plane that preserves the operational capabilities of the old shell-based setup while replacing the implementation with a testable Python architecture.

The target system is:

```text
Python-first
API-first
PostgreSQL-backed
service-layer based
lane-based
firewall-plan based
safety-gated
```

The system must support future UI and Telegram integrations without rewriting business logic.

---

## Target Data Plane

The server is a **forward-only customer gateway**:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

The first stable lane is BTC:

```text
BTC customer ports -> backend 60010 -> forwarder -> v2rayA -> pool
```

Future coins such as ZEC and LTC must be implemented through the lane model.
Do not clone scripts per coin.

---

## Fixed Architecture Decisions

Initial implementation decisions:

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

---

## API-First Rule

Business logic must live in domain/service modules.

Required flow:

```text
CLI / API / UI / Telegram / jobs
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Forbidden:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly writes DB
Telegram directly runs shell commands
job bypasses service validation
```

---

## Source of Truth

PostgreSQL is the production source of truth.

Flat files and SQLite may be used only for:

- import from old scripts
- export/debug artifacts
- temporary migration tooling
- generated restore artifacts
- backups

They must not become production customer, firewall, usage, or abuse state.

---

## Mandatory Abuse Requirement

Miner-abuse handling is a core feature from day one.

Required state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Rules:

- all active customers in all enabled lanes must be scanned
- no silent skip is allowed
- exemption requires reason and expiry
- farms-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- hard creates restore point and policy backup
- hard uses firewall plan/apply/verify path
- hard flushes affected conntrack scope
- manual unhard is audited

A patch that weakens this requirement must be rejected.

---

## Firewall Safety Model

Firewall changes must be model-driven.

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

Forbidden production pattern:

```text
ad-hoc iptables commands
one-off NAT redirects
interface-triggered firewall shell commands
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

## Documentation Map

Start here:

```text
AGENTS.md
README.md
docs/INDEX.md
```

Core contracts:

```text
docs/ARCHITECTURE.md
docs/SAFETY.md
docs/ROADMAP.md
docs/DATA_MODEL.md
docs/FIREWALL.md
docs/ABUSE.md
```

Current phase contracts:

```text
docs/PHASE_0.md
docs/PHASE_1.md
```

---

## Roadmap Summary

```text
Phase 0  — Architecture Freeze
Phase 1  — Preflight + Bootstrap Without Traffic Changes
Phase 2  — PostgreSQL + Config + Domain Model
Phase 3  — CLI + Internal API Foundation
Phase 4  — Compose Forward-only + Proxy Doctor
Phase 5  — Customer CRUD in DB Only
Phase 6  — Firewall Planner + Apply/Verify/Rollback
Phase 7  — Usage + Policy/Reject Accounting
Phase 8  — Abuse 1h Core
Phase 9  — Check / Report / Diagnostics
Phase 10 — Session / Worker / Policy Timeline
Phase 11 — Local Web UI Read-only
Phase 12 — UI Actions With Confirmation
Phase 13 — Telegram Notifications, Read-only Commands, Restricted Actions
```

Do not start a later phase until the current phase acceptance gate passes.

---

## Phase 0/1 Execution Rule

Start only with:

1. Phase 0 — Architecture Freeze
2. Phase 1 — Preflight + Bootstrap Without Traffic Changes

During Phase 0/1, the project must not:

- create customer firewall rules
- create NAT redirects
- expose backend ports
- enable abuse automation
- enable block automation
- expose UI components
- activate Telegram
- onboard production customers
- switch away from `firewall.apply_mode=plan_only`

---

## Phase 1 Acceptance Snapshot

Phase 1 is accepted only when these pass:

```bash
mpf --help
mpf doctor
mpf config validate
mpf config show
mpf db ping
python -m pytest
systemctl status postgresql
docker version
docker compose version
conntrack -V
iptables --version
```

And these remain true:

```text
no customer firewall rule exists
no NAT redirect exists
no backend public exposure exists
no abuse automation is active
no block automation is active
firewall.apply_mode is still plan_only
```

---

## Testing Strategy

Minimum risk areas:

```text
config validation
database migrations
policy versioning
lane collision
port collision
firewall planner
firewall drift detection
backend exposure detection
firewall rollback
abuse state machine
all-active-customer abuse coverage
usage counter delta
job locking
backup/restore
interface boundary tests
```

---

## Security Guardrails

- never expose backend ports publicly
- never expose v2rayA UI publicly
- never expose early Web UI/API publicly
- never hardcode Telegram tokens
- secrets must live outside the repository
- firewall changes must be auditable
- dangerous actions need restore points
- direct DB edits are not normal operation
- direct iptables edits are not normal operation

---

## License

License is not defined yet.

Choose and add a license before public or multi-person use.
