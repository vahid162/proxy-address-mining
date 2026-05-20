# Phase 11 farm5 0.1.153 Sync/Test Evidence

Status: recorded evidence (non-authorizing)

## Scope

This document records farm5 0.1.153 sync/test evidence for the **Phase 11D actual operator-approved manual canary execution run package**.

This evidence is documentation-only and non-authorizing:
- actual canary execution is **not performed**
- actual canary execution is **not accepted**
- Phase 11 remains **not accepted**

## Sync command and backup

- sync command:
  - `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- backup created:
  - `/var/backups/mpf/source-before-zip-sync-20260520T065905Z`

## Server version after sync

- `0.1.153`

## Pytest during sync wrapper

- `835 passed in 155.97s`

## Phase status summary after sync

```text
current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

## mpf doctor summary

```text
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
```

## DB status summary

```text
database: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 1
abuse_states: 0
```

Customer interpretation:
- one customer row exists in DB
- no non-deleted/active customer is currently onboarded

## Lane status summary

```text
btc enabled=True backend_port=60010 chain_prefix=MPFBTC protocol=stratum source=db
ltc enabled=False backend_port=60020 chain_prefix=MPFLTC protocol=stratum source=db
zec enabled=False backend_port=60015 chain_prefix=MPFZEC protocol=stratum source=db
```

## Customer status summary

```text
no non-deleted customers
firewall_change: no
nat_change: no
runtime_change: no
```

## Proxy checks summary

```text
proxy config: OK
proxy status: OK
proxy doctor: OK
```

## Proxy safety summary

```text
proxy.runtime_activation_allowed: OK — proxy runtime activation remains disabled for general app/API mutation
v2raya_ui_local_only: OK
lane.btc.forwarder_bind: OK — lane forwarder bind is not public
compose_runtime_profile_guard: OK
backend_docker_publish_mode.v2raya_ui: OK
backend_docker_publish_mode.btc: OK
healthcheck_state: OK
firewall_apply_mode_plan_only: OK
no_customer_nat_redirects: OK
```

## Current phase safety gate result

```text
OK: current Phase 10 accepted / Phase 11 planning safety gate passed.
Production customer traffic remains disabled.
```

## Firewall safety result

```text
OK: no MPF/customer IPv4 firewall references detected
OK: no MPF/customer IPv6 firewall references detected
```

## Docker local publish NAT explanation (informational only)

Docker-managed local publish DNAT references exist only for:
- `127.0.0.1:2015`
- `127.0.0.1:60010`

This is informational only for accepted limited local-only runtime.
Do **not** treat this as MPF/customer NAT.
MPF/customer NAT redirect paths remain forbidden and absent.

## Listening port safety result

- `127.0.0.1:2015` local-only
- `127.0.0.1:60010` local-only

## Direct command evidence after sync

### `mpf --version`

- output: `0.1.153`

### `mpf production manual-canary-execute --output json`

Important output summary:

```text
component: phase11_manual_canary_execution_run
phase: Phase 11D — Actual operator-approved manual canary execution run
mode: plan
final_decision: PLAN_READY_FOR_FARM5_SYNC_EVIDENCE
authorization_status: MANUAL_CANARY_EXECUTION_PACKAGE_NON_AUTHORIZING
execution_allowed: false
actual_canary_execution_performed: false
mutation_performed: false
customer_db_mutation_performed: false
firewall_mutation_performed: false
nat_mutation_performed: false
conntrack_mutation_performed: false
production_traffic_enabled: false
validation_errors: []
warnings:
- plan mode is non-mutating and non-authorizing
```

Request defaults:

```text
customer_key: canary-btc-001
lane: btc
port: 20001
miners: 1
farms: 1
maxconn: 1
requested_action: plan
expected_version: null
operator_confirmed: false
understand_canary_customer: false
understand_firewall_apply: false
reviewed_rollback: false
fresh_farm5_sync_confirmed: false
```

Prerequisite evidence and preflight summary:

```text
farm5_0_1_151_sync_evidence_recorded: true
run_preparation_evidence_recorded: true
farm5_execution_evidence_pending: true
phase_gate: OK
mpf_doctor: OK
db_status: OK
proxy_doctor: OK
no_customer_nat_baseline: OK
no_customer_firewall_baseline: OK
local_only_runtime_baseline: OK
```

All dangerous safety flags are false:

```text
production_traffic_authorized: false
controlled_cli_canary_execution_authorized: false
limited_customer_onboarding_authorized: false
customer_db_mutation_authorized: false
firewall_apply_authorized: false
iptables_restore_authorized: false
customer_nat_apply_authorized: false
customer_firewall_rules_apply_authorized: false
abuse_automation_authorized: false
conntrack_flush_authorized: false
worker_enforcement_authorized: false
scheduler_authorized: false
collector_authorized: false
ui_authorized: false
telegram_authorized: false
```

### `mpf production canary-execution-run-prep --output json`

Important output summary:

```text
component: phase11_manual_canary_execution_run_preparation
phase: Phase 11D — Operator-reviewed manual canary execution run preparation
final_decision: READY_FOR_FARM5_SYNC_EVIDENCE
authorization_status: MANUAL_CANARY_EXECUTION_RUN_PREPARATION_NON_AUTHORIZING
execution_allowed: false
actual_canary_execution_performed: false
mutation_performed: false
customer_db_mutation_performed: false
firewall_mutation_performed: false
nat_mutation_performed: false
conntrack_mutation_performed: false
production_traffic_enabled: false
validation_errors: []
```

### `mpf phase-status`

```text
current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
ui_allowed: no
telegram_allowed: no
```

### `mpf doctor`

```text
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
```

### `bash /opt/mpf-py-src/scripts/verify_current_phase_gate.sh`

Output summary:

```text
OK: current Phase 10 accepted / Phase 11 planning safety gate passed.
Production customer traffic remains disabled.
No MPF/customer IPv4 firewall references detected.
No MPF/customer IPv6 firewall references detected.
Accepted limited runtime listeners are local-only.
```

## Final sync verdict

```text
OK: GitHub main zip synced successfully.
OK: server source is aligned with GitHub zip.
OK: accepted current phase gate is installed and verified.
OK: Runtime remains limited local-only.
OK: production customer traffic is still disabled.
```

## Evidence boundary statements

- Actual operator-approved manual canary execution run package farm5 sync/test evidence is recorded.
- This document does **not** execute canary traffic and does **not** accept canary execution.
- Production traffic, firewall apply, customer NAT/customer firewall rules, customer DB mutation, abuse automation, UI, and Telegram remain closed.
- Limited real customer onboarding remains forbidden until canary execution evidence is accepted.
