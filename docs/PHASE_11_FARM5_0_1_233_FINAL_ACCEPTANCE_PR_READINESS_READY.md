# Phase 11 Farm5 0.1.233 Final Acceptance PR Readiness READY

Farm5 `0.1.233` sync/test completed successfully with `1551 passed`. The controlled boundary acceptance package, controlled boundary decision, and final acceptance PR readiness reports are READY with `blockers = []` and `warnings = []`.

## Accepted Limited Evidence Scope

- Canary: `canary-btc-001`, public port `20001`.
- Limited customer: `limited-btc-001`, lane `btc`, public port `20101`.
- Evidence backend target: `172.18.0.3:60010`.
- Stable runtime contract: `127.0.0.1:60010 -> forwarder -> v2rayA -> pool`; runtime correctness must not depend on the evidence Docker IP.

## Input Package

- Path: `/tmp/phase11-0.1.232-controlled-boundary-acceptance-package-20260601T181801Z/phase11-controlled-boundary-acceptance-package.json`
- SHA-256: `06f5c33086030d2da5c330c08c47ea36d49cdecd9284b2fcdb6ebe393b7e7271`
- Decision: `PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY`.
- Abuse 1h readiness, restart/container-order readiness, and the artifact gate with known controlled Phase 11 artifacts were included and accepted.

## Final Readiness Helper

Output directory: `/tmp/phase11-0.1.233-controlled-boundary-decision-final-readiness-20260601T190831Z`

| Artifact | SHA-256 |
| --- | --- |
| `phase11-controlled-boundary-acceptance-decision.json` | `fad4cdfcfa874a5712c4b79595e8675405b420dc0adff84356f67ed4901d55bc` |
| `phase11-controlled-boundary-acceptance-decision.sha256` | `6786681ceb90284d74ee66a5f594aee4671bc475ef73dcde2a8b39690ad8415f` |
| `phase11-final-acceptance-pr-readiness.json` | `f7efe4921e8018c88b3670bf4c4be3d4dcb2a5b5285b7fd0102b6aa3b073a717` |
| `phase11-final-acceptance-pr-readiness.sha256` | `a12c359e9dabcfefc7752c8fde144a2d63107d85aa0cbda53f8b7eee563d1d12` |
| `manifest.json` | `3a0a6f4677d233a7d2d4413c9b7d7abf6d32abe2a111d9dbbc23087ac2279a2b` |

The decision JSON is `PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_DECISION_READY`. The readiness JSON is `PHASE11_FINAL_ACCEPTANCE_PR_READINESS_READY`. Before this PR, `phase11_accepted = false` and `current_state_changed = false`; this PR is the explicit final acceptance PR.

After this PR, Phase 11 is accepted only for `controlled_cli_limited` operation. Phase 12 — Worker Policy Enforcement is next. UI and Telegram remain closed, and `worker_enforcement_allowed` remains `no`.
