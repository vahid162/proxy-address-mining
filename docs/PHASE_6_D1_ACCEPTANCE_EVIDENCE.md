# Phase 6-D1 Acceptance Evidence

Status: accepted on farm5

## Acceptance Snapshot

- Version accepted: 0.1.59
- Date: 2026-05-12
- Scope: documentation/test-only live-apply boundary contract

## Non-Authorization Statement

This Phase 6-D1 acceptance does **not** authorize live apply, live read, live write, `iptables-save`, `iptables-restore`, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

## Server Evidence Summary

```text
mpf --version: 0.1.59
pytest with venv: 357 passed
verify_current_phase_gate.sh: passed
mpf doctor: OK
db status: OK
proxy doctor: OK
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no MPF/customer firewall refs
no customer NAT redirects
no customer firewall rules
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no lock acquisition
no restore point write
no DB apply write
local-only v2rayA UI listener 127.0.0.1:2015
local-only BTC backend listener 127.0.0.1:60010
Docker local publish DNAT for 127.0.0.1:2015 and 127.0.0.1:60010 is informational only and is not MPF customer NAT
runtime remains limited local-only
production customer traffic remains disabled
```

## DB Evidence

```text
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 0
abuse_states: 0
```

## Abuse Invariant Preservation

```text
normal -> over_tracking -> over_grace -> hard
sustained miner-abuse hardens after about 3600 seconds
farms-over alone must not harden
worker-over alone must not harden
all active customers in enabled lanes must be covered
no silent skip
Phase 6-D1 did not implement abuse automation
```

## Next Safe Step

Phase 6-E0 — Isolated Apply Harness Planning/Contracts.

This next step must remain isolated/non-production and must not mutate the host production firewall.
