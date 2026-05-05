# Copilot Instructions

This project is a Python-first greenfield rewrite of a mining proxy customer gateway.

Before suggesting code:

- Read `AGENTS.md`.
- Read `docs/INDEX.md`.
- Respect phase boundaries.
- Keep PostgreSQL as source of truth.
- Keep business logic in domain/service layers.
- Do not place business logic inside CLI/UI/Telegram handlers.
- Use lane-based design for BTC/ZEC/LTC and future coins.
- Do not clone scripts per coin.
- Never suggest direct firewall mutation without plan/diff/backup/apply/verify/rollback.
- Never suggest exposing backend ports or v2rayA UI publicly.
- Abuse 1h state machine is mandatory: `normal -> over_tracking -> over_grace -> hard`.
- Farms-over alone must not trigger hardening.
- Early phases must keep firewall mode as `plan_only`.
- Do not commit secrets or customer-private operational dumps.
