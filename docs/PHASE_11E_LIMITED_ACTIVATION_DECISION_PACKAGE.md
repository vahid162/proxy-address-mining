# Phase 11E Limited Activation Decision Package (0.1.225)

Purpose: prepare explicit, non-mutating decision/execution/rollback package for `limited-btc-001` only.

Scope: `limited-btc-001` / `btc` / `20101` / `172.18.0.3:60010`.

Non-goals: no activation in this PR, no Phase 11 acceptance, no production/miner traffic open, no abuse automation enablement.

Operator helper (post-merge):
`scripts/phase11e_prepare_limited_activation_decision_package.sh --expected-version 0.1.225 ...`

READY means: operator can review and then run later controlled activation manually.

READY does not mean: Phase 11 accepted, production open, abuse automation enabled.
