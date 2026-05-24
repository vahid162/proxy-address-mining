# Phase 11D Canary Acceptance Decision Gate

## Purpose
Define a non-mutating, operator-controlled decision gate that validates the exact farm5 `0.1.195` canary evidence-pack and decides whether it is accepted as **Phase 11D controlled canary acceptance evidence**.

## Exact Scope
- customer_key: `canary-btc-001`
- lane: `btc`
- port: `20001`
- backend_target: `172.18.0.3:60010`
- expected_version: current `__version__` (`0.1.197`)
- farm5_baseline_version: `0.1.168`

## Inputs
CLI command: `mpf production canary-acceptance-decision` with explicit scope, evidence paths, archive hash, and operator confirmation flags.

## Evidence-pack Validation Rules
Required files:
- `manifest.json`
- `runtime-path-evidence.json`
- `visibility-bundle.json`
- `acceptance-review.json`

The gate fail-closes unless all required manifest/runtime/visibility/acceptance-review fields match the recorded farm5 `0.1.195` evidence expectations and all mutation/authorization flags remain closed (`false` / `no_onboarding_authorized=true`).

## Archive Hash Validation
If archive path and expected hash are provided, gate computes SHA256 and requires exact match.
- Missing archive with provided hash => `evidence_archive_missing`
- Hash mismatch => `evidence_archive_sha256_mismatch`

## Operator Approval Flags
Gate blocks unless all are explicitly set:
- `--operator` and `--reason`
- `--operator-confirmed`
- `--i-have-reviewed-evidence-pack`
- `--i-confirm-no-real-customer-onboarding`
- `--i-confirm-no-production-traffic-authorized`
- `--i-confirm-phase11-not-final-accepted`

## Positive Decision Semantics
- `final_decision: CANARY_ACCEPTANCE_DECISION_ACCEPTED`
- `phase11d_canary_accepted: true`
- `phase11_accepted: false`
- `limited_onboarding_allowed: false`
- `production_traffic_enabled: false`
- `no_onboarding_authorized: true`
- `mutation_performed: false`
- `next_required_step: phase11e_limited_onboarding_gate_design`

## Blocked Decision Semantics
- `final_decision: BLOCKED`
- `phase11d_canary_accepted: false`
- closed authorization flags stay closed
- `blockers` includes explicit reasons

## Safety Boundary
`CANARY_ACCEPTANCE_DECISION_ACCEPTED` is **Phase 11D controlled canary acceptance only**.
It is **not** Phase 11 final acceptance.
It does **not** authorize real customer onboarding.
It does **not** authorize production traffic.
It does **not** authorize abuse automation.
It does **not** authorize UI/Telegram/scheduler/worker enforcement.

## Farm5 Command Example
```bash
mpf production canary-acceptance-decision \
  --expected-version 0.1.197 \
  --farm5-baseline-version 0.1.168 \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --backend-target 172.18.0.3:60010 \
  --evidence-pack-dir /tmp/phase11-canary-evidence-pack-0.1.195-live \
  --evidence-archive-path /tmp/phase11-canary-evidence-pack-0.1.195-live.tar.gz \
  --expected-archive-sha256 ebd1832d374dcf907aa54b0628d6ab022f9e8b988779ab1953f5e072e254fc51 \
  --operator "<operator-name>" \
  --reason "Accept Phase 11D controlled canary evidence-pack after farm5 0.1.195 live evidence review" \
  --operator-confirmed \
  --i-have-reviewed-evidence-pack \
  --i-confirm-no-real-customer-onboarding \
  --i-confirm-no-production-traffic-authorized \
  --i-confirm-phase11-not-final-accepted \
  --output json
```
