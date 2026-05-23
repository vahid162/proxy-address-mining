# Phase 11 Farm5 0.1.195 Live Canary Evidence Pack

## Date/Time Context

- Recorded during Phase 11 planning/readiness on **2026-05-23 (UTC)**.
- Farm5 was synced to `main` after PR #209 and running repository version `0.1.195` during evidence collection.

## Version and Baseline

- Repository version under evidence: `0.1.195`
- Farm5 baseline version: `0.1.168`
- Evidence out directory on farm5: `/tmp/phase11-canary-evidence-pack-0.1.195-live`

## Canary Scope

- customer_key: `canary-btc-001`
- lane: `btc`
- public_port: `20001`
- backend_target: `172.18.0.3:60010`

## Evidence Archive

- Archive path (farm5): `/tmp/phase11-canary-evidence-pack-0.1.195-live.tar.gz`
- SHA256: `ebd1832d374dcf907aa54b0628d6ab022f9e8b988779ab1953f5e072e254fc51`
- Archive size: `4.5K`
- Archive listing verification command: `tar -tzf /tmp/phase11-canary-evidence-pack-0.1.195-live.tar.gz`

## Archive Listing Summary

Verified archive contents:

- `manifest.json`
- `runtime-path-evidence.json`
- `visibility-bundle.json`
- `acceptance-review.json`
- `worker-stratum-evidence.json`
- `usage-evidence.json`
- `usage-visibility.json`
- `reject-session-ip-evidence.json`
- `reject-counters-visibility.json`
- `external-stratum-transcript-import.json`
- `abuse-coverage-visibility.json`
- `final-check-report-visibility.json`
- `rollback-restore-visibility.json`
- `live-canary-evidence.json`

## Manifest Summary (`manifest.json`)

- runtime_path_final_decision: `RUNTIME_PATH_EVIDENCE_READY`
- visibility_bundle_final_decision: `VISIBILITY_READY`
- acceptance_review_final_decision: `ACCEPTANCE_REVIEW_READY`
- next_required_step: `none`
- missing_visibility_primitives: `[]`
- missing_evidence_primitives: `[]`
- phase11_accepted: `false`
- limited_onboarding_allowed: `false`
- no_onboarding_authorized: `true`
- mutation_performed: `false`
- production_traffic_enabled: `false`

## Runtime Path Summary (`runtime-path-evidence.json`)

- final_decision: `RUNTIME_PATH_EVIDENCE_READY`
- blockers: `[]`
- conntrack_assured: `true`
- forwarder_pool_seen: `true`
- bridge_loopback_seen: `true`
- phase11_accepted: `false`
- limited_onboarding_allowed: `false`
- no_onboarding_authorized: `true`
- mutation_performed: `false`
- production_traffic_enabled: `false`

## Visibility Bundle Summary (`visibility-bundle.json`)

- final_decision: `VISIBILITY_READY`
- next_required_step: `none`
- missing_visibility_primitives: `[]`
- missing_evidence_primitives: `[]`
- blockers: `[]`
- warnings: `[]`
- phase11_accepted: `false`
- limited_onboarding_allowed: `false`
- no_onboarding_authorized: `true`
- mutation_performed: `false`
- production_traffic_enabled: `false`

## Acceptance Review Summary (`acceptance-review.json`)

- final_decision: `ACCEPTANCE_REVIEW_READY`
- next_required_step: `none`
- missing_visibility_primitives: `[]`
- missing_evidence_primitives: `[]`
- blockers: `[]`
- warnings: `[]`
- phase11_accepted: `false`
- limited_onboarding_allowed: `false`
- no_onboarding_authorized: `true`
- mutation_performed: `false`
- production_traffic_enabled: `false`

## Controlled-Canary Interpretation

This evidence confirms controlled canary runtime evidence-path readiness for the exact canary scope:

- `conntrack_assured=true`
- `forwarder_pool_seen=true`
- `bridge_loopback_seen=true`
- Visibility bundle has no missing primitives
- Acceptance review reached readiness

## Explicit Safety Boundary (Unchanged)

- Phase 11 remains **not accepted**.
- Real customer onboarding remains **forbidden**.
- Production traffic remains **unauthorized**.
- Abuse automation remains **unauthorized**.
- UI remains **unauthorized**.
- Telegram remains **unauthorized**.
- Scheduler/worker enforcement remain **unauthorized**.
- Additional firewall apply remains **unauthorized**.
- All mutation flags remain `false`.

## Phase-Gate Note

The current phase gate may report a canary artifact as an expected controlled-canary condition, not as a general production authorization.
