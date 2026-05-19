# Phase 11D — Manual Canary Customer Acceptance Package

## Scope and Boundary

Phase 11D in this PR is **package preparation only**, not manual canary execution.

This adds a manual canary customer acceptance package that is non-mutating and non-authorizing, while still being an actionable operator package surface (not report-only).

This PR does **not**:
- execute canary
- connect a real miner
- apply firewall
- create customer DB rows
- create customer NAT/rules
- authorize production traffic

All dangerous gates remain closed. Phase 11 accepted state is unchanged.

## What this package adds

- `mpf production canary-acceptance --output json`
- deterministic acceptance criteria
- pre-execution evidence requirements
- explicit execution boundary with blocked `accept`/`execute` actions
- backup/restore/rollback requirements
- operator checklist for post-merge farm5 sync/test evidence

## Post-merge farm5 evidence commands

Run these on farm5 after merge and sync:

```bash
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor
mpf production readiness --output json
mpf production canary-plan --output json
mpf production activation-harness --output json
mpf production canary-acceptance --output json
bash scripts/verify_current_phase_gate.sh
python -m pytest -q
```

Do not claim farm5 execution evidence for this version until operator output is collected and recorded.

## Execution authorization status

A later explicit Phase 11D execution gate is required before any real manual canary execution.
