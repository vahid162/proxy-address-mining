# Phase 6-E1 Acceptance Evidence (farm5)

Status: accepted on farm5  
Version accepted: 0.1.63  
Date: 2026-05-12  
Scope: isolated/non-production harness contract hardening

## Non-Authorization Statement

This Phase 6-E1 acceptance evidence is **non-authorizing**. It records isolated/non-production hardening evidence only and does **not** authorize any live or production behavior.

This acceptance does **not** authorize:

- live firewall read
- live firewall write
- live firewall apply
- live rollback
- live verify
- `iptables-save`
- `iptables-restore`
- real iptables adapter
- DB apply writes
- lock acquisition
- restore point writes
- customer NAT redirects
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram

## Server Evidence Summary

- sync command: `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- source synced to `/opt/mpf-py-src`
- existing venv preserved
- `/usr/local/bin/mpf` updated
- version after sync: `0.1.63`
- `verify_current_phase_gate.sh`: passed

## Harness Evidence Summary

- `./.venv/bin/python -m pytest -q`: `392 passed in 7.93s`
- isolated/no-op harness contract hardening remained within non-production boundaries
- no subprocess firewall calls
- no real iptables adapter introduced

## DB Evidence Summary

- `mpf db status`: OK
- `alembic_version`: `0002_phase5_customer_lifecycle`
- `public_table_count`: `64`
- `lanes`: `3`
- `customers`: `1`
- `job_runs`: `0`
- `firewall_applies`: `0`
- `abuse_states`: `0`
- no DB apply writes

## Proxy/Runtime Safety Summary

- `mpf doctor`: OK
- proxy doctor: OK
- proxy runtime remains limited local-only
- v2rayA UI listener remains `127.0.0.1:2015`
- BTC backend listener remains `127.0.0.1:60010`
- backend internal reachability: OK
- production customer traffic remains disabled

## Firewall Safety Summary

- no customer NAT redirects
- no customer firewall rules
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- `firewall.apply_mode` remains `plan_only`
- `proxy.runtime_activation_allowed` remains `false`
- no live firewall read/write/apply/rollback/verify
- no `iptables-save` execution
- no `iptables-restore` execution
- no lock acquisition
- no restore point writes

## Test Environment Note

The operator also ran `python -m pytest -q` outside the preserved project venv and saw expected missing dependency errors (`typer`/`pydantic`/`sqlalchemy`) from system Python.

This is **not** a project failure. For server acceptance, run tests with:

- `./.venv/bin/python -m pytest -q`
- or the sync script path that uses the preserved project venv

## Abuse Invariant Preservation

The abuse safety invariant remains unchanged and preserved:

- state flow remains `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about `3600` seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip

## Next Safe Step

Phase 6-E1 is accepted as isolated/non-production harness contract hardening only.

Next planned implementation step: **Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning**, isolated/non-production only.

Phase 6-E2 remains non-authorizing and does not authorize host production firewall mutation, live firewall read/write, `iptables-save`, `iptables-restore`, real iptables adapters, DB apply writes, lock acquisition, restore point writes, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.
