# Phase 11E Limited Activation Execution Runbook (0.1.227)

## Farm5 baseline

The reviewed baseline is farm5 `0.1.225`: sync succeeded, `python -m pytest` reported `1437 passed`, and the current phase gate was OK. The decision, execution, and rollback packages are READY. `limited-btc-001` is still paused before execution. `canary-btc-001` is active and must be preserved. Production and miner traffic remain closed.

## Exact scope

Only `limited-btc-001` / `btc` / `20101` / `172.18.0.3:60010` is in scope.

## What 0.1.227 fixes

- the rollback package now records its exact reviewed rollback scope explicitly;
- limited activation execute preflight accepts only that strict rollback package schema and still fails closed on missing or mismatched scope.

This PR does **not** execute activation. All public, miner, abuse, UI, and Telegram gates remain closed.

## What 0.1.226 adds

- a hash-backed gated execute command;
- an exact-scope rollback execute command;
- a read-only post-activation evidence collector;
- `scripts/phase11e_run_limited_activation_execute_package.sh` for an operator-reviewed run folder.

This PR does **not** activate the customer during development, open unrestricted production, expand miner traffic, enable abuse automation, accept Phase 11, or enable UI/Telegram.

## Operator flow after merge and sync

1. Run `scripts/verify_current_phase_gate.sh` and stop on any failure.
2. Regenerate or validate the artifact gate when needed.
3. Review all package paths and SHA-256 values, then run the helper with all required inputs, `--execute`, and every explicit execute confirmation flag.
4. Include `--collect-post-evidence` and every explicit post-evidence confirmation flag for immediate read-only post-activation evidence collection.
5. Send `manifest.json`, `sha256-manifest.txt`, execution JSON, and evidence JSON for review.

## Stop conditions

Stop on any blocker, version mismatch, hash mismatch, unknown artifact, public exposure, canary preservation failure, scope mismatch, a non-paused limited customer before execute, an opened safety gate, or any unexpected changed customer.

## Rollback flow

Use `mpf production phase11e-limited-activation-rollback-execute` with the reviewed activation execution JSON, rollback package, artifact gate, hashes, operator identity, reason, and all confirmations. Then collect post-rollback evidence for review. Rollback is exact-scope DB state rollback only: no firewall mutation, conntrack flush, or service restart.
