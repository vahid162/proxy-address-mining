# Phase 11A — Production Readiness Inventory

Status: implemented as report-only, non-authorizing, fail-closed.

This is the first implementation step of Phase 11.

## Scope

This step adds a deterministic readiness inventory report:

```text
mpf production readiness --output json
```

The report is read-only and non-mutating. It does not authorize runtime actions.

## Explicit Non-Authorization

This step does **not** open:

- production traffic
- controlled CLI canary
- limited real customer onboarding
- firewall apply
- iptables-restore
- customer NAT/customer firewall rules
- abuse automation
- worker runtime
- scheduler/timer
- collector daemon
- UI
- Telegram

## Why this is AI-safe Runtime-first

This step moves toward real runtime evidence in small, safe increments without bypassing phase gates.
It creates clear blockers and post-merge farm5 evidence requirements before any future runtime gate decision.

## Required farm5 post-merge evidence commands

Run these commands **after merge and sync** on farm5:

```bash
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor
mpf production readiness --output json
bash scripts/verify_current_phase_gate.sh
python -m pytest -q
```

Do not claim farm5 execution evidence in this PR unless an operator provides real outputs.

## Next required step

Merge PR, sync main to farm5, run Phase 11A evidence commands, then record farm5 evidence in the next PR.
