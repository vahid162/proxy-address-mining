# Phase 11 farm5 0.1.145 Sync/Test Evidence

Status: recorded evidence for Phase 11C controlled activation harness (non-authorizing)

This document records verified farm5 sync/test evidence after syncing GitHub main zip at version 0.1.145.

It explicitly confirms that this evidence records Phase 11C controlled activation harness status only and does **not** authorize Phase 11D execution or any runtime gate opening.

## Sync command

```bash
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
```

## Backup created

```text
/var/backups/mpf/source-before-zip-sync-20260519T095052Z
```

## Server version after sync

```text
0.1.145
```

## Pytest

```text
806 passed in 135.84s
```

## Phase status summary

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

## Proxy safety summary

```text
proxy.runtime_activation_allowed: OK — proxy runtime activation remains disabled for general app/API mutation
v2raya_ui_local_only: OK
lane.btc.forwarder_bind: OK
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

## Docker local publish NAT

127.0.0.1:2015 and 127.0.0.1:60010 Docker-managed local publish DNAT references are informational only for accepted limited runtime.
MPF/customer NAT redirect paths remain forbidden.

## Listening port safety

```text
127.0.0.1:2015 local-only
127.0.0.1:60010 local-only
```

Accepted listeners are local-only and no customer NAT redirects are active.

## Final verdict

```text
OK: GitHub main zip synced successfully.
OK: server source is aligned with GitHub zip.
OK: accepted current phase gate is installed and verified.
OK: Runtime remains limited local-only.
OK: production customer traffic is still disabled.
```

## Phase 11C evidence and gate statements

- Phase 11C controlled activation harness evidence is recorded on farm5 at sync/test version 0.1.145.
- This evidence does **not** authorize Phase 11D manual canary customer execution.
- Production traffic remains closed (`none`).
- Firewall apply remains closed (`no`) and apply mode remains `plan_only`.
- Customer NAT/customer firewall rules remain closed.
- Customer DB mutation runtime path remains closed.
- Abuse automation remains closed (`no`).
- UI remains closed (`no`).
- Telegram remains closed (`no`).
