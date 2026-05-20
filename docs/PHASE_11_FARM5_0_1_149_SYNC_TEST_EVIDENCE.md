# Phase 11 farm5 0.1.149 Sync/Test Evidence

Status: accepted farm5 sync/test evidence record for Phase 11D manual canary execution gate package (non-authorizing).

## Sync command

```text
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
```

## Backup created

```text
/var/backups/mpf/source-before-zip-sync-20260519T132315Z
```

## Server version after sync

```text
0.1.149
```

## Pytest result from sync wrapper

```text
819 passed in 139.70s
```

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

## Safe smoke checks / doctor summary

```text
mpf doctor: OK
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

There is one customer row in the database, but no non-deleted/active customer is currently onboarded.

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

## Proxy config/status/doctor summary

```text
proxy config: OK
proxy status: OK
proxy doctor: OK
```

## Current phase safety gate result from sync wrapper

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

- 127.0.0.1:2015
- 127.0.0.1:60010

This is accepted limited local-only runtime behavior and is **not** MPF/customer NAT.
MPF/customer NAT redirect paths remain forbidden and absent.

## Listening port safety

```text
127.0.0.1:2015 local-only
127.0.0.1:60010 local-only
```

## Direct canary-execution-gate command evidence

Command:

```text
mpf production canary-execution-gate --output json
```

Important output summary:

```text
component: phase11_manual_canary_execution_gate
phase: Phase 11D — Manual canary execution gate package
final_decision: READY_FOR_FARM5_SYNC_EVIDENCE
authorization_status: MANUAL_CANARY_EXECUTION_GATE_NON_AUTHORIZING
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

All dangerous safety flags remain false, including production/customer/firewall/NAT/abuse/worker/scheduler/collector/UI/Telegram authorization flags.

## Direct phase-status and doctor evidence

```text
mpf phase-status
current_accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
current_working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
ui_allowed: no
telegram_allowed: no

mpf doctor
config: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
```

## Absolute-path safety-script caveat (post-sync operator note)

After sync, the operator ran:

```text
bash /opt/mpf-py-src/scripts/verify_current_phase_gate.sh
```

from `/root`, and it failed with:

```text
CRITICAL: docs/PHASE_STATUS.md is missing
```

This was **not** a phase failure and **not** a sync failure; the sync wrapper had already passed the current phase safety gate. The failure was due to CWD-dependent relative-path assumptions in `scripts/verify_current_phase_gate.sh` before this PR hardening.

## Final verdict

- OK: GitHub main zip synced successfully.
- OK: server source is aligned with GitHub zip.
- OK: accepted current phase gate is installed and verified.
- OK: runtime remains limited local-only.
- OK: production customer traffic is still disabled.

Phase 11D manual canary execution gate package evidence is recorded in this document.

This evidence package does **not** authorize Phase 11D actual execution.
Production traffic, firewall apply, customer NAT/customer firewall rules, customer DB mutation, abuse automation, UI, and Telegram remain closed/disabled.
