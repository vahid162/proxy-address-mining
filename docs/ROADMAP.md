# Roadmap

## Phase 0 — Architecture Freeze

Goal: freeze decisions before installation or data-plane work.

Outputs:

- architecture document
- project scope document
- guardrails
- Phase 1 preflight checklist

Forbidden:

- package installation
- service activation
- firewall changes
- NAT redirects
- customer creation
- automation

## Phase 1 — Preflight + Bootstrap

Goal: prepare the server without touching traffic.

Tasks:

- inspect OS, kernel, timezone
- inspect network interfaces, routes, DNS
- inspect iptables backend and nft/legacy status
- install base tools
- prepare PostgreSQL
- prepare Python virtual environment
- create standard directories
- create initial config with `apply_mode: plan_only`
- create Python skeleton

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

No customer rules, NAT redirects, backend public exposure, abuse automation, or block automation should exist.

## Phase 2 — PostgreSQL + Config + Domain Model

Goal: implement the database and domain model.

Required:

- SQLAlchemy
- Alembic
- config loader
- validation
- lane model
- customer model
- policy model
- abuse model
- event/audit model
- jobs/locks
- restore points
- firewall snapshots

## Phase 3 — CLI / Internal API

Goal: implement `mpf` as the operator entrypoint.

Initial commands:

```bash
mpf config show
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
mpf doctor
```

CLI must call the service layer.

## Phase 4 — Compose Forward-only + Proxy Doctor

Goal: start proxy data-plane without customer firewall rules.

Tasks:

- v2rayA
- v2raya bridge if required
- simple-forwarder/gost for BTC backend `60010`
- healthchecks
- backend exposure detection
- proxy doctor

## Phase 5 — Customer CRUD in DB Only

Goal: manage customers in DB without applying live firewall rules.

Features:

- add/edit/delete/renew/list
- days/expiry
- miners/farms/maxconn/rate/burst
- optional IP whitelist
- status model
- event logging
- port/lane collision detection

## Phase 6 — Firewall Planner

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
- live drift
- missing accounting rules

## Phase 7 — Usage + Policy / Reject Accounting

Goal: collect reliable traffic and reject data before abuse automation.

Features:

- usage snapshots
- 1h / 1d / 30d reports
- connlimit reject events
- hashlimit reject events
- pause/block reject events
- usage doctor

## Phase 8 — Abuse 1h Core

Goal: enforce miner-abuse handling for all active customers.

State machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Hard action:

- backup / restore point
- set maxconn to miners
- firewall apply
- conntrack flush for affected customer/port
- event record
- report output

## Phase 9 — Check / Report / Diagnostics

Goal: provide clear operator verdicts.

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

## Phase 10 — Session / Worker / Policy Timeline

Goal: provide forensic history.

Features:

- flow sessions
- worker events
- worker timeline
- policy/reject timeline
- session reconcile
- worker binding from Stratum authorize/submit
- evidence pack

## Phase 11 — Local Web UI Read-only

Goal: local-only web panel.

Rules:

- bind only to localhost or Unix socket
- read-only first
- no direct DB writes
- no direct firewall writes

## Phase 12 — UI Actions With Confirmation

Goal: controlled UI actions.

Actions:

- add/edit/renew/delete customer
- set IPs
- firewall plan/apply
- block/unblock
- note add
- pause/unpause
- manual unhard

## Phase 13 — Telegram

Goal: notification first, commands later.

Stages:

1. notifications only
2. read-only commands
3. restricted actions with allowlist and confirmation
