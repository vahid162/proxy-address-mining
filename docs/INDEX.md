# Documentation Index

This directory contains the canonical project specification for the Python-first mining proxy customer gateway.

## Mandatory reading order for AI agents

1. `README.md`
2. `AGENTS.md`
3. `docs/INDEX.md`
4. `docs/ARCHITECTURE.md`
5. `docs/ROADMAP.md`
6. `docs/SAFETY.md`
7. `docs/ABUSE.md`
8. `docs/FIREWALL.md`
9. `docs/DATA_MODEL.md`
10. the relevant phase document

## Canonical documents

- `ARCHITECTURE.md` — final target architecture
- `ROADMAP.md` — implementation phases
- `SAFETY.md` — security and operational guardrails
- `ABUSE.md` — miner-abuse state machine and requirements
- `FIREWALL.md` — firewall planner and rollback model
- `DATA_MODEL.md` — PostgreSQL schema direction
- `PHASE_0.md` — architecture freeze tasks
- `PHASE_1.md` — bootstrap/preflight tasks

## Source summaries

The original planning files are represented as sanitized summaries in `docs/source/`.

Raw server dumps and archives must not be committed to this public repository because they may contain sensitive operational data.

## Current execution rule

Start only with Phase 0 and Phase 1.

Do not start implementation phases that touch the data-plane, firewall rules, NAT redirects, abuse automation, UI actions, Telegram actions, or production traffic until previous phase acceptance checks pass.
