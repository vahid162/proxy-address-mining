# Phase 11E Limited Activation Observation and Acceptance Review

## Purpose

Version `0.1.229` adds a read-only observation collector and a read-only limited activation acceptance review gate. They classify operator-supplied farm5 JSON artifacts by path and SHA-256 hash. They do not fabricate server evidence and do not execute activation, rollback, DB mutation, firewall apply, runtime changes, or traffic expansion.

## Exact Scope

```text
candidate_customer_key: limited-btc-001
lane: btc
public_port: 20101
backend_target: 172.18.0.3:60010
preserved canary: canary-btc-001
```

## Required Inputs

The helper requires hashed JSON artifacts for activation execution, post-activation evidence, source evidence, the exact-scope rollback package, and the controlled artifact gate. The observation collector also reads customer status through the service layer and requires both `limited-btc-001` and `canary-btc-001` to remain active.

## Helper Usage

```bash
scripts/phase11e_collect_limited_activation_observation_and_review.sh \
  --expected-version 0.1.229 \
  --activation-execution-json /path/limited-activation-execution.json \
  --activation-execution-json-sha256 "$(cat /path/limited-activation-execution.sha256)" \
  --post-activation-evidence-json /path/post-activation-evidence.json \
  --post-activation-evidence-json-sha256 "$(cat /path/post-activation-evidence.sha256)" \
  --source-evidence-json /path/source-evidence.json \
  --source-evidence-json-sha256 "$(sha256sum /path/source-evidence.json | awk '{print $1}')" \
  --rollback-package-json /path/limited-activation-rollback-package.json \
  --rollback-package-json-sha256 "$(cat /path/limited-activation-rollback-package.sha256)" \
  --artifact-gate-json /path/artifact-gate.json \
  --artifact-gate-json-sha256 "$(sha256sum /path/artifact-gate.json | awk '{print $1}')" \
  --out-dir /path/observation-review \
  --operator OPERATOR_NAME \
  --reason 'read-only Phase 11E limited activation observation and review'
```

The helper hashes every input before invoking `mpf`, runs observation before review, and writes observation JSON, review JSON, their SHA-256 files, `manifest.json`, and `sha256-manifest.txt`.

## Decisions

Observation returns `PHASE11E_LIMITED_ACTIVATION_OBSERVATION_READY` or `BLOCKED`. Review returns `PHASE11E_LIMITED_ACTIVATION_ACCEPTANCE_REVIEW_READY` or `BLOCKED`. Any missing confirmation, wrong hash, scope mismatch, unhealthy DB/proxy source evidence, unsafe artifact gate, changed current gate, inactive limited customer, inactive canary, missing exact rollback scope, or expansion signal fails closed.

## Safety Notes and Non-Authorization

Even a READY review is limited activation review evidence only. It does not authorize activation, rollback, DB/firewall/runtime mutation, production traffic, miner traffic expansion, abuse automation, unrestricted onboarding, UI, Telegram, or Phase 11 final acceptance. `docs/PHASE_STATUS.md` Current State remains authoritative and unchanged.

## Next Step After READY

The only next step is `phase11e_limited_customer_observation_window_or_phase11_final_readiness_planning`. Phase 11 final acceptance, production expansion, and abuse automation remain separate later decisions.
