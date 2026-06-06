# Phase 11 Controlled Artifact Reapply Runbook (0.1.249)

Version `0.1.249` implements controlled artifact reapply read-only package evidence surfaces for exactly the accepted BTC customers `canary-btc-001:20001` and `limited-btc-001:20101`.

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

## Execution boundary

Public production execution intentionally fails closed before any `iptables-restore` invocation until real live preflight, OS lock, non-empty firewall backup, PostgreSQL operational metadata, exact rollback-plan, and post-apply verification adapters are implemented and tested. The command still validates package file hash, canonical content hash, scope, version, hostname, phase gates, payload safety, and rollback metadata before reporting blockers.

The execution path must not restart Docker, call systemd, flush conntrack, mutate customer/policy/abuse/block/pause state, enable timers/daemons, broaden the two-customer scope, or mark restart/autostart proof READY.

## Current progression

The next step before any execution is `sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5`.

`restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, and timer/daemon automation remain blocked.
