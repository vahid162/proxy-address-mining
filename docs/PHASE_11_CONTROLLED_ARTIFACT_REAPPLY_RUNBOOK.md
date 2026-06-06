# Phase 11 Controlled Artifact Reapply Runbook (0.1.249)

Version `0.1.249` implements the controlled artifact reapply capability for exactly the accepted BTC customers `canary-btc-001:20001` and `limited-btc-001:20101`.

No farm5 mutation was performed by this PR. Package generation is read-only and a live READY package must be collected and reviewed on farm5 before any execution.

## Read-only package collection

```bash
mpf production controlled-backend-target --output json
mpf production controlled-artifact-reapply-plan --output json
mpf production controlled-artifact-reapply-package --output json
mpf production controlled-artifact-reapply-verify --package-json <package.json> --output json
scripts/phase11_controlled_artifact_reapply.sh --package --out-dir <evidence-dir>
```

Local or CI environments without source-backed Docker, PostgreSQL, listener, and firewall evidence must fail closed and must not fabricate a historical backend target or READY execution package.

## Guarded execution boundary

Execution is operator-gated and requires `--execute`, `--yes`, package path, package SHA-256, package ID, expected version, operator, and reason. The executor rechecks package identity, version, hostname/runtime target fingerprint, customer/policy snapshot hash, firewall snapshot preconditions, unknown/stale/duplicate/public-exposure blockers, lock, backup, restore-point metadata, audit intent, `iptables-restore --test --noflush`, apply, and post-apply verification.

The execution path must not restart Docker, call systemd, flush conntrack, mutate customer/policy/abuse/block/pause state, enable timers/daemons, broaden the two-customer scope, or mark restart/autostart proof READY.

## Current progression

The next step before any execution is `sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5`.

`restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, and timer/daemon automation remain blocked.
