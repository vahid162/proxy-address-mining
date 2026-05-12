# Phase 6-E3 Acceptance Evidence (farm5)

Status: accepted on farm5

## Acceptance Metadata

- Version accepted: `0.1.70`
- Date accepted: `2026-05-12`
- Scope: isolated harness evidence review / non-authorizing gate checklist only

## Non-Authorization Statement

This Phase 6-E3 acceptance is documentation/evidence acceptance only and does **not** authorize any runtime or production mutation.

It does **not** authorize:

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
- version after sync: `0.1.70`
- source synced to `/opt/mpf-py-src`
- existing venv preserved
- `/usr/local/bin/mpf` updated
- pytest with venv during sync: `413 passed in 8.52s`
- manual pytest with venv: `413 passed in 7.43s`

## Checklist Evidence Summary

- `docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md` reviewed and accepted for isolated/non-production scope
- `verify_current_phase_gate.sh`: passed
- production customer traffic remains disabled

## DB Evidence Summary

- `mpf db status`: OK
- `alembic_version`: `0002_phase5_customer_lifecycle`
- `public_table_count`: `64`
- lanes: `3`
- customers: `1`
- job_runs: `0`
- firewall_applies: `0`
- abuse_states: `0`

## Proxy/Runtime Safety Summary

- `mpf proxy doctor`: OK
- proxy runtime remains limited local-only
- v2rayA UI listener remains `127.0.0.1:2015`
- BTC backend listener remains `127.0.0.1:60010`
- backend internal reachability: OK

## Firewall Safety Summary

- no customer NAT redirects
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- `firewall.apply_mode` remains `plan_only`
- `proxy.runtime_activation_allowed` remains `false`

## Time Synchronization Warning

farm5 time synchronization has previously been reported as not confirmed.
This is not a Phase 6-E3 acceptance blocker, but it must be resolved before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Test Environment Note

All acceptance tests were executed with the project virtual environment on farm5.
System Python is not an acceptance environment for this phase evidence.

## Abuse Invariant Preservation

The abuse 1h invariant remains explicit and unchanged:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Next Safe Step

Phase 6-E3 is accepted as isolated/non-production evidence review and non-authorizing checklist closure only.
The next planned implementation step is **Phase 6-F — Manual Canary Gate Definition**, documentation/test-only and non-authorizing.
Live apply remains forbidden until a dedicated apply gate is explicitly accepted.
