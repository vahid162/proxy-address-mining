# Phase 11C — Controlled Activation Harness

Status: implemented in GitHub as controlled, non-mutating, non-authorizing harness.

This is **Phase 11C**.

It adds a controlled activation harness surface and is **not simple report-only**, but it remains **non-mutating** and **non-authorizing** in this PR.

## Command

```bash
mpf production activation-harness --output json
```

## What this adds

- deterministic activation package modeling
- preflight gate checks
- explicit execution boundary with apply/no-dry-run blocked
- preview requirements for backup/restore/lock/verify/rollback
- operator checklist for post-merge farm5 evidence

## Explicit non-authorization boundary

This PR does **not**:

- execute canary
- apply firewall
- create customer DB rows
- create customer NAT/customer firewall rules
- authorize production traffic

Phase 11C remains non-authorizing until farm5 sync/test evidence is collected after merge.
Phase 11D or later is required before any manual canary execution.

## Post-merge farm5 evidence commands

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
bash scripts/verify_current_phase_gate.sh
python -m pytest -q
```

Do not claim these commands were run on farm5 unless real operator output is recorded.
