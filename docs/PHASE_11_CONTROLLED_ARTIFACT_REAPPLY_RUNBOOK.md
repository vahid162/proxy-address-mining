# Phase 11 Controlled Artifact Reapply Runbook (0.1.250)

Version `0.1.250` implements controlled artifact reapply source-backed renderer and production adapter surfaces for exactly the accepted BTC customers `canary-btc-001:20001` and `limited-btc-001:20101`.

No farm5 mutation was performed by this PR. Package generation is read-only, but this version cannot produce a READY package because desired firewall artifact semantics remain unresolved. Server sync for READY package collection must wait for the next runtime-forward PR that implements the source-backed renderer and production adapters.

## Read-only shape and evidence collection

```bash
mpf production controlled-backend-target --output json
mpf production controlled-artifact-reapply-plan --output json
mpf production controlled-artifact-reapply-package --output json
mpf production controlled-artifact-reapply-verify --package-json <package.json> --output json
scripts/phase11_controlled_artifact_reapply.sh --package --out-dir <evidence-dir>
```

The verify command builds a fresh read-only live plan and compares it with the supplied package; while `controlled_policy_artifact_semantics_unresolved` remains present, verification must return a blocked decision. Local or CI environments without source-backed Docker, PostgreSQL, listener, and firewall evidence must fail closed and must not fabricate a historical backend target or READY execution package.

## Execution boundary

Public production execution intentionally fails closed before any `iptables-restore` invocation until real live preflight, OS lock, non-empty firewall backup, PostgreSQL operational metadata, exact rollback-plan, and post-apply verification adapters are implemented and tested. The command still validates package file hash, canonical content hash, scope, version, hostname, phase gates, payload safety, and rollback metadata before reporting blockers.

The execution path must not restart Docker, call systemd, flush conntrack, mutate customer/policy/abuse/block/pause state, enable timers/daemons, broaden the two-customer scope, or mark restart/autostart proof READY.

## Current progression

The next step before execution is `sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5`. Current flags are `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=true`, `production_execution_available=true`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`.

`restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, and timer/daemon automation remain blocked.


0.1.250 controlled runtime-forward note: the source-backed controlled artifact renderer and production adapters are implemented for exactly `canary-btc-001/btc/20001` and `limited-btc-001/btc/20101`. No farm5 mutation was performed, no live `iptables-restore` was executed during PR development or CI, and no READY farm5 package has been collected. Progression is now `read_only_reapply_foundation_implemented=true`, `desired_artifact_semantics_complete=true`, `production_execution_available=true`, `live_ready_package_available=false`, and `controlled_artifact_reapply_package_evidence_ready=false`. The exact next step is `sync_and_collect_controlled_artifact_reapply_package_evidence_on_farm5`; server sync is allowed only for read-only package/evidence collection first, and controlled execution requires separate package review. `restart_autostart_proof` remains `missing_or_partial`; Full CLI Production Operations remains unaccepted; `production_traffic` and `customer_onboarding_allowed` remain `controlled_cli_limited`; Phase 12, worker enforcement, UI, Telegram, timers, and daemons remain blocked.
