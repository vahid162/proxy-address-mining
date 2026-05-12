# Phase 6-F Acceptance Evidence (farm5)

Status: accepted on farm5
Version accepted: 0.1.73
Date: 2026-05-12
Scope: manual canary gate definition only, documentation/test-only, non-authorizing

## Non-Authorization Statement

This Phase 6-F acceptance is documentation/test-only and non-authorizing. It does **not** authorize:

- live firewall read
- live firewall write
- live firewall apply
- live rollback
- live verify
- iptables-save
- iptables-restore
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
- version after sync: `0.1.73`
- source synced to `/opt/mpf-py-src`
- existing venv preserved
- `/usr/local/bin/mpf` updated
- pytest with venv during sync: `426 passed in 8.05s`
- manual pytest with venv: `426 passed in 7.08s`

## Checklist Evidence Summary

- `mpf config validate`: OK
- `mpf doctor`: OK
- `mpf db status`: OK
- `verify_current_phase_gate.sh`: passed
- `docs/PHASE_STATUS.md` confirms Phase 6-F was planned and non-authorizing before this acceptance
- `docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md` is referenced and accepted for documentation/test-only scope

## DB Evidence Summary

- `alembic_version`: `0002_phase5_customer_lifecycle`
- `public_table_count`: `64`
- `lanes`: `3`
- `customers`: `1`
- `job_runs`: `0`
- `firewall_applies`: `0`
- `abuse_states`: `0`

## Proxy/Runtime Safety Summary

- `mpf proxy doctor`: OK
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

## Manual Canary Definition Summary

Phase 6-F acceptance closes manual canary gate definition documentation/test evidence only. It confirms gate-language, checklist consistency, and non-authorizing safety boundaries without opening any live apply behavior.

## Time Synchronization Warning

farm5 time synchronization has previously been reported as not confirmed.
This is not a Phase 6-F acceptance blocker, but it must be resolved before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Test Environment Note

Acceptance evidence was captured on farm5 after sync to version `0.1.73`, using the preserved project virtual environment and local-only runtime safety boundaries.

## Abuse Invariant Preservation

- normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Next Safe Step

The next planned step is Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review, documentation/test-only and non-authorizing until a separate apply gate is explicitly accepted.
