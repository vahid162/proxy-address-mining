# Phase 11D Farm5 Manual Canary Execution Runbook

## Prerequisites
- Sync latest `main` on farm5.
- Confirm version is `0.1.166`.
- Do **not** onboard real customers.

## Preflight
- `python -m pytest -q`
- `bash scripts/verify_current_phase_gate.sh`
- `mpf phase-status`
- `mpf doctor`
- `mpf db status`
- `mpf proxy doctor`

## Plan mode (default)
- `mpf production manual-canary-execute --output json > canary-plan.json`

## Execute mode (single explicit canary only)
```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow \
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.166 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11D single canary execution on farm5" \
  --output json > canary-execute.json
```

## Evidence to collect
- `canary-plan.json`
- `canary-execute.json`
- `mpf doctor`, `mpf phase-status`, `mpf db status`, `mpf proxy doctor`
- listener/NAT/firewall status outputs required by reviewer.

## Failure / rollback
- Stop immediately on `BLOCKED` or `EXECUTION_FAILED`.
- Use restore/backup references in JSON output.
- Send failure evidence for review before any new attempt.

## Safety reminders
- Phase 11 remains unaccepted until evidence is reviewed and accepted.
- Limited real customer onboarding remains forbidden until canary evidence is accepted.

> Note: This command is a readiness contract and is expected to return BLOCKED when real production execution adapters are not wired yet.

## Phase 11E adapter wiring note
- Execute mode is now wired to production service-layer adapters.
- Actual host apply remains BLOCKED in this PR; no real host apply executor is wired in production.
- Do **not** run real customer onboarding.

## Restore/backup context guard

- execute-control now requires `MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow` in addition to exact scope, expected version, approvals, and phase safety checks.
- plan command:
  - `mpf production manual-canary-execute --output json`
- execute-control command:
  - `MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow mpf production manual-canary-execute --requested-action execute --customer-key canary-btc-001 --lane btc --port 20001 --miners 1 --farms 1 --maxconn 1 --expected-version 0.1.166 --operator-confirmed --i-understand-this-can-create-a-canary-customer --i-understand-this-can-apply-firewall --i-have-reviewed-rollback --i-have-fresh-farm5-sync --operator "<operator-name>" --reason "Phase 11H restore backup boundary check" --output json`
- exact payload renderer behavior: execute path now renders deterministic exact payload for canary-btc-001/btc/20001->60010 after restore+backup+diff checks.
- expected blocker without host-apply context guard: `single_canary_host_apply_context_not_confirmed`.
- expected blocker with both restore-backup and host-apply context guards enabled: `accepted_single_canary_host_apply_execution_missing`.
- warning: no production traffic, no real customer onboarding, no abuse automation, no UI/Telegram, and no host apply in this PR.

## Two execute-control checks (required)

1) Renderer-only execute-control (host apply context NOT enabled)

```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow \
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.166 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11I renderer-only execute-control check" \
  --output json
```

Expected: `restore_payload_renderer.status=ok`, `firewall_plan.restore_payload` present, `final_decision=BLOCKED`, blocker `single_canary_host_apply_context_not_confirmed`, all mutation flags false, all safety flags false.

2) Pre-host-apply missing-executor execute-control (both guards enabled)

```bash
MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow \
MPF_PHASE11_SINGLE_CANARY_HOST_APPLY=allow \
mpf production manual-canary-execute \
  --requested-action execute \
  --customer-key canary-btc-001 \
  --lane btc \
  --port 20001 \
  --miners 1 \
  --farms 1 \
  --maxconn 1 \
  --expected-version 0.1.166 \
  --operator-confirmed \
  --i-understand-this-can-create-a-canary-customer \
  --i-understand-this-can-apply-firewall \
  --i-have-reviewed-rollback \
  --i-have-fresh-farm5-sync \
  --operator "<operator-name>" \
  --reason "Phase 11I pre-host-apply missing-executor check" \
  --output json
```

Expected: `restore_payload_renderer.status=ok`, `firewall_plan.restore_payload` present, `final_decision=BLOCKED`, blocker `accepted_single_canary_host_apply_execution_missing`, `missing_primitive=accepted_single_canary_host_apply_execution`, all mutation flags false, all safety flags false.

No real host apply executor is wired in production in this PR.

Warnings remain: no production traffic, no real customer onboarding, no abuse automation, no UI, no Telegram, and no host apply implementation in this PR.

## Route-safe successful evidence (farm5, 0.1.164)

- Recorded in `docs/PHASE_11_ROUTE_SAFE_CANARY_NAT_SUCCESS_EVIDENCE.md`.
- External TCP test succeeded to `85.198.11.110:20001` and conntrack showed `ASSURED` flow to `172.18.0.3:60010`.
- NAT evidence confirms exact single-canary DNAT rule and no loopback canary target.

### Important boundary clarification

- TCP/NAT success is **not** full Phase 11 acceptance.
- Current State in `docs/PHASE_STATUS.md` remains authoritative and unchanged (`production_traffic: none`, `customer_onboarding_allowed: db_only`, `abuse_automation_allowed: no`, `ui_allowed: no`, `telegram_allowed: no`).
- Limited real customer onboarding remains forbidden until canary evidence is formally accepted.

### Next required validation before onboarding review

- miner/Stratum canary validation on the same controlled single-canary scope
- usage visibility evidence
- reject visibility evidence
- session visibility evidence
- reviewer sign-off that Phase 11 remains unaccepted until all required evidence is accepted


### v2rayA SOCKS reachability check

```bash
docker exec mpf-forwarder-btc sh -c 'nc -zv mpf-v2raya 20170; echo rc=$?'
```

Expected: `rc=0` before synthetic Stratum validation.
