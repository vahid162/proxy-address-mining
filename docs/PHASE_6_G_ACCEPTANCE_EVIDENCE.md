# Phase 6-G Acceptance Evidence (farm5)

Status: accepted on farm5

## Acceptance Metadata

- Version accepted: `0.1.76`
- Date: `2026-05-12`
- Scope: controlled live apply gate planning / pre-apply review only, documentation/test-only, non-authorizing

## Non-Authorization Statement

This Phase 6-G acceptance is documentation/test-only and non-authorizing. It does **not** authorize:

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
- version after sync: `0.1.76`
- source synced to `/opt/mpf-py-src`
- existing venv preserved
- `/usr/local/bin/mpf` updated
- pytest during sync: `442 passed in 8.15s`
- manual pytest with venv: `442 passed in 7.27s`

## Checklist Evidence Summary

- `mpf --version`: `0.1.76`
- `mpf phase-status`: `Phase 5 accepted / Phase 6 working`
- `mpf config validate`: `OK`
- `mpf doctor`: `OK`
- `mpf db status`: `OK`
- `mpf proxy doctor`: `OK`
- `verify_current_phase_gate.sh`: `OK`

## DB Evidence Summary

- `alembic_version`: `0002_phase5_customer_lifecycle`
- `public_table_count`: `64`
- `lanes`: `3`
- `customers`: `1`
- `job_runs`: `0`
- `firewall_applies`: `0`
- `abuse_states`: `0`

## Proxy/Runtime Safety Summary

- accepted limited proxy runtime remains local-only
- v2rayA UI listener remains `127.0.0.1:2015`
- BTC backend listener remains `127.0.0.1:60010`
- backend internal reachability: `OK`
- production customer traffic remains disabled

## Firewall Safety Summary

- no MPF/customer IPv4 firewall references detected
- no MPF/customer IPv6 firewall references detected
- no customer NAT redirects
- no customer firewall rules
- `firewall.apply_mode` remains `plan_only`
- `proxy.runtime_activation_allowed` remains `false`
- Docker-managed local publish DNAT rules for `127.0.0.1:2015` and `127.0.0.1:60010` are informational only in accepted limited runtime and are not MPF/customer NAT redirects

## Phase 6-G Planning Summary

- Phase 6-G acceptance closes controlled live apply gate planning / pre-apply review documentation/test evidence only.
- Phase 6-G remains non-authorizing.
- Live apply remains forbidden until a dedicated apply gate is explicitly accepted later with separate evidence.

## Time Synchronization Warning

farm5 time synchronization has previously been reported as not confirmed.
This is not a Phase 6-G acceptance blocker, but it must be resolved before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Test Environment Note

Server verification evidence was captured on farm5 against synced source at version `0.1.76` with project venv-based pytest validation (`442 passed`).

## Abuse Invariant Preservation

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Next Safe Step

Do not authorize live apply.
Future dedicated Phase 6 apply gate remains not accepted and not authorized.
Unless `docs/PHASE_STATUS.md` is explicitly updated by a separate accepted gate, planning/review remains documentation/test-only and non-authorizing.
