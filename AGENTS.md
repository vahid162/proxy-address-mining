# AI Agent Instructions

This repository is a Python-first greenfield rewrite of a mining proxy customer gateway.

The project replaces an older shell-script-based operational setup, but it must not copy or patch the old scripts directly. The goal is to preserve operational capabilities while implementing a clean, testable, database-backed Python architecture.

## Mandatory reading order

Before changing code, AI agents and contributors must read:

1. `README.md`
2. `docs/INDEX.md`
3. `docs/ARCHITECTURE.md`
4. `docs/ROADMAP.md`
5. `docs/SAFETY.md`
6. `docs/ABUSE.md`
7. `docs/FIREWALL.md`
8. `docs/DATA_MODEL.md`
9. the relevant phase document, such as `docs/PHASE_0.md` or `docs/PHASE_1.md`

The historical planning material is summarized under `docs/source/`.

## Non-negotiable architecture rules

- This is a greenfield implementation, not a direct migration of old shell scripts.
- Preserve operational capabilities from the old system, but implement them cleanly in Python.
- PostgreSQL is the source of truth.
- Flat files and SQLite may only be used for debug, import/export, or compatibility tooling.
- Business logic must live in domain/service modules, not in CLI handlers.
- CLI, local UI, Telegram, and future API must use the same service layer.
- Multi-lane support is required from day one.
- Do not clone scripts per coin.
- BTC backend is `60010`.
- Future coins such as ZEC/LTC must be implemented through lanes.
- Configuration must be centralized in `/etc/mpf/mpf.yaml`.
- Early phases must keep `firewall.apply_mode = plan_only`.

## Firewall rules

Firewall changes must use this lifecycle:

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

Never apply random one-off firewall commands as part of normal operation.

## Abuse requirement

Miner-abuse handling is a core requirement from day one.

Required state machine:

```text
normal -> over_tracking -> over_grace -> hard
```

Rules:

- all active customers in all enabled lanes must be scanned
- no customer is exempt unless `abuse_exempt=true` with reason and expiry
- hardening only after sustained miner-abuse for about 1 hour
- farms-over alone must not trigger hardening
- hard/unhard must create events
- hard actions must create backup/restore points

## Phase safety rules

Phase 0 and Phase 1 must not:

- create customer firewall rules
- create NAT redirects
- expose backend ports
- enable abuse automation
- enable block automation
- onboard production customers
- expose UI or Telegram controls

## Required engineering behavior

For every meaningful change:

- update or add tests
- update docs if behavior changes
- keep commands idempotent where possible
- prefer plan/dry-run before apply
- return clear operator-facing errors
- add audit/event records for state-changing actions
- avoid hidden side effects

## Python architecture

Use this structure:

```text
mpf/
  domain/
  services/
  adapters/
  interfaces/
  jobs/
  migrations/
  tests/
```

Do not put business logic directly in CLI, UI, or Telegram handlers.

## Security rules

- never expose backend ports publicly
- never expose v2rayA UI publicly
- never commit secrets, tokens, private keys, production credentials, or customer-private data
- secrets must live outside the repository
- direct DB edits are not normal operation
- direct iptables edits are not normal operation
