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
