# Phase 11D Actual Manual Canary Execution Run Package

Status: implementation package only for a later operator-approved farm5 run.

Command:
- `mpf production manual-canary-execute --output json`

Plan mode (`--requested-action plan`, default): non-mutating, no DB/firewall/NAT writes, returns checklist, blockers, rollback plan, and evidence requirements.

Execute mode (`--requested-action execute`) requires all explicit approvals:
- `--operator-confirmed`
- `--i-understand-this-can-create-a-canary-customer`
- `--i-understand-this-can-apply-firewall`
- `--i-have-reviewed-rollback`
- `--i-have-fresh-farm5-sync`
- `--expected-version 0.1.153`
- `--customer-key canary-btc-001`
- `--lane btc`
- `--port 20001`

Required preflight commands include: `mpf phase-status`, `mpf doctor`, `mpf db status`, `mpf proxy doctor`, `bash scripts/verify_current_phase_gate.sh`.

This PR does **not** run canary execution. Farm5 execution evidence is still required after merge/sync/explicit approval. Limited real customer onboarding remains forbidden until accepted canary execution evidence.
