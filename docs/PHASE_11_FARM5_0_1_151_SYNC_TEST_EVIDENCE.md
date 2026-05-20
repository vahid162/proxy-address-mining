# Phase 11 farm5 0.1.151 Sync/Test Evidence

Status: recorded (non-authorizing evidence)

This document records farm5 sync/test evidence for the **Phase 11D operator-reviewed manual canary execution run preparation package**.

## Sync Command

```bash
sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
```

## Backup Created

```text
/var/backups/mpf/source-before-zip-sync-20260520T052448Z
```

## Server Version After Sync

```text
0.1.151
```

## Pytest During Sync Wrapper

```text
825 passed in 153.23s
```

## Phase Status After Sync

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

## Safe Smoke Checks

- mpf doctor: OK
- config: OK
- database: OK
- apply_mode: plan_only
- traffic_changes: none
- firewall_mutation: disabled
- abuse_automation: disabled

## DB Status Summary

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

Customer interpretation: one customer row exists in DB, but no non-deleted/active customer is currently onboarded.

## Lane Status Summary

```text
btc enabled=True backend_port=60010 chain_prefix=MPFBTC protocol=stratum source=db
ltc enabled=False backend_port=60020 chain_prefix=MPFLTC protocol=stratum source=db
zec enabled=False backend_port=60015 chain_prefix=MPFZEC protocol=stratum source=db
```

## Customer Status Summary

```text
no non-deleted customers
firewall_change: no
nat_change: no
runtime_change: no
```

## Proxy Config/Status/Doctor Summary

- proxy config: OK
- proxy status: OK
- proxy doctor: OK

## Current Phase Safety Gate

- OK: current Phase 10 accepted / Phase 11 planning safety gate passed.
- Production customer traffic remains disabled.

`bash scripts/verify_current_phase_gate.sh` now passes after absolute-path hardening (previous CWD-dependent invocation issue is fixed).

## Firewall Safety

- OK: no MPF/customer IPv4 firewall references detected
- OK: no MPF/customer IPv6 firewall references detected

## Docker Local Publish NAT (Informational)

Docker-managed local publish DNAT references exist only for:

- 127.0.0.1:2015
- 127.0.0.1:60010

This is informational-only for accepted limited local-only runtime. It is **not** MPF/customer NAT. MPF/customer NAT redirect paths remain forbidden and absent.

## Listening Port Safety

- 127.0.0.1:2015 local-only
- 127.0.0.1:60010 local-only

## Final Sync Verdict

- OK: GitHub main zip synced successfully.
- OK: server source is aligned with GitHub zip.
- OK: accepted current phase gate is installed and verified.
- OK: runtime remains limited local-only.
- OK: production customer traffic is still disabled.

## Authorization Boundary Statement

- Phase 11D operator-reviewed manual canary execution run preparation package evidence is recorded.
- This evidence package does **not** authorize Phase 11D actual execution.
- Production traffic, firewall apply, customer NAT/rules, customer DB mutation, abuse automation, UI, and Telegram remain closed.
