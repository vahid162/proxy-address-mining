# Phase 11 farm5 0.1.147 Sync/Test Evidence

Status: accepted farm5 sync/test evidence record for Phase 11D manual canary customer acceptance package (non-authorizing).

## Sync command

```text
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
```

## Backup created

```text
/var/backups/mpf/source-before-zip-sync-20260519T113949Z
```

## Server version after sync

```text
0.1.147
```

## Pytest result from sync wrapper

```text
813 passed in 139.03s
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

## Safe smoke checks

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

## Proxy checks

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

## Current phase safety gate

```text
OK: current Phase 10 accepted / Phase 11 planning safety gate passed.
Production customer traffic remains disabled.
```

## Firewall safety

```text
OK: no MPF/customer IPv4 firewall references detected
OK: no MPF/customer IPv6 firewall references detected
```

## Docker local publish NAT (informational only)

Docker-managed local publish DNAT references exist only for:

```text
127.0.0.1:2015
127.0.0.1:60010
```

These are informational for accepted limited local-only runtime and are not MPF/customer NAT. MPF/customer NAT redirect paths remain forbidden and absent.

## Listening port safety

```text
127.0.0.1:2015 local-only
127.0.0.1:60010 local-only
```

Accepted listeners are local-only and no customer NAT redirects are active.

## Phase 11A command evidence summary

```text
command: mpf production readiness --output json
component: phase11_production_readiness
final_decision: READY_FOR_SERVER_SYNC_EVIDENCE
authorization_status: REPORT_ONLY_NON_AUTHORIZING
execution_allowed: false
all dangerous safety flags: false
```

## Phase 11B command evidence summary

```text
command: mpf production canary-plan --output json
component: phase11_canary_plan
final_decision: PLAN_READY_REPORT_ONLY
authorization_status: REPORT_ONLY_NON_AUTHORIZING
execution_allowed: false
mutation_performed: false
all dangerous safety flags: false
```

## Phase 11C command evidence summary

```text
command: mpf production activation-harness --output json
component: phase11_controlled_activation_harness
final_decision: HARNESS_READY_FOR_FARM5_SYNC_EVIDENCE
authorization_status: CONTROLLED_HARNESS_NON_AUTHORIZING
execution_allowed: false
mutation_performed: false
live_apply_performed: false
customer_db_mutation_performed: false
firewall_mutation_performed: false
nat_mutation_performed: false
conntrack_mutation_performed: false
all dangerous safety flags: false
```

## Phase 11D canary-acceptance command evidence summary

```text
command: mpf production canary-acceptance --output json
component: phase11_manual_canary_acceptance
final_decision: MANUAL_CANARY_PACKAGE_READY_FOR_FARM5_SYNC_EVIDENCE
authorization_status: MANUAL_CANARY_PACKAGE_NON_AUTHORIZING
execution_allowed: false
mutation_performed: false
live_canary_performed: false
customer_db_mutation_performed: false
firewall_mutation_performed: false
nat_mutation_performed: false
conntrack_mutation_performed: false
production_traffic_enabled: false
all dangerous safety flags: false
```

## Manual-tail CWD caveat

After the sync wrapper completed successfully, a manual chained command block was run from `/root`.
In that manual tail:
- `bash scripts/verify_current_phase_gate.sh` failed with `No such file or directory`.
- `python -m pytest -q` returned `no tests ran in 0.01s`.

This is not a sync failure. Those manual tail commands were not run from the repository source directory, so they are not valid repository-local evidence. The sync wrapper's pytest and safety-gate results are the accepted evidence.

## Final sync verdict

```text
OK: GitHub main zip synced successfully.
OK: server source is aligned with GitHub zip.
OK: accepted current phase gate is installed and verified.
OK: Runtime remains limited local-only.
OK: production customer traffic is still disabled.
```

## Phase 11D evidence and gate statements

- Phase 11D manual canary customer acceptance package evidence is recorded on farm5 at sync/test version 0.1.147.
- This evidence does **not** authorize Phase 11D execution.
- Phase 11 remains non-accepted in this PR.
- Production traffic, firewall apply, customer NAT/customer rules, customer DB mutation, abuse automation, UI, and Telegram remain closed.
