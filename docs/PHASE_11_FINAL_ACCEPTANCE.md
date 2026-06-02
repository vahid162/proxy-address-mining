# Phase 11 Final Acceptance

## Decision

Phase 11 is accepted on farm5 for the controlled CLI-limited production/customer activation boundary only. The accepted operating mode is `controlled_cli_limited`.

## Accepted Scope

- Canary customer: `canary-btc-001`, public port `20001`.
- Limited customer: `limited-btc-001`, public port `20101`.
- Lane: `btc`.
- Evidence backend target: `172.18.0.3:60010` from accepted farm5 artifacts only.
- Stable runtime contract: `127.0.0.1:60010 -> forwarder -> v2rayA -> pool`. Runtime correctness must not depend on a Docker container IP.

## Allowed Controlled Boundaries

- Controlled CLI/service-layer customer onboarding.
- Controlled firewall apply path with planning, restore, lock, verification, and evidence requirements.
- Controlled abuse automation path. This is not unrestricted background automation and this PR starts no timer or daemon.
- Limited BTC production/customer boundary.

## Still Forbidden

- Unrestricted production expansion or unrestricted miner expansion.
- UI, Telegram, or worker enforcement.
- Direct DB/firewall edits outside the service layer.
- Copying legacy scripts as the runtime backend.

## Abuse Safety Invariant

The required one-hour flow remains `normal -> over_tracking -> over_grace -> hard`. All active customers in all enabled lanes must be covered. Farms-over alone and worker-over alone must not harden. Missing or stale evidence must fail closed and must not harden. Before adding customers, post-merge operator checks must include abuse status, doctor, and readiness checks.

## Operator Behavior

Use only `mpf` CLI/service-layer workflows, retain JSON/hash evidence for each controlled operation, and run post-acceptance verification after sync. Default config remains conservative: this acceptance does not automatically switch `firewall.apply_mode` away from `plan_only` or enable proxy runtime activation.

## Next Phase

Phase 12 — Worker Policy Enforcement. Worker enforcement remains disabled until Phase 12 acceptance. UI and Telegram remain later phases.
