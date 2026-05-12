# Phase 6-E2 Acceptance Evidence

Status: accepted on farm5

## Acceptance Metadata

- Version accepted: `0.1.66`
- Date: `2026-05-12`
- Scope: isolated harness evidence package / boundary planning only

## Non-Authorization Statement

This acceptance is documentation/evidence-only and does **not** authorize:

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
- version after sync: `0.1.66`
- source synced to `/opt/mpf-py-src`
- existing venv preserved
- `/usr/local/bin/mpf` updated
- pytest with venv during sync: `403 passed in 7.80s`
- manual pytest with venv: `403 passed in 7.23s`
- `mpf config validate`: `OK`
- `mpf doctor`: `OK`
- `mpf db status`: `OK`
- `verify_current_phase_gate.sh`: passed

## Evidence Package Summary

- `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md` accepted on farm5 as isolated/non-production evidence package and boundary planning only
- no live apply gate opened
- no runtime mutation scope expanded

## DB Evidence Summary

- `alembic_version`: `0002_phase5_customer_lifecycle`
- `public_table_count`: `64`
- `lanes`: `3`
- `customers`: `1`
- `job_runs`: `0`
- `firewall_applies`: `0`
- `abuse_states`: `0`

## Proxy/Runtime Safety Summary

- `mpf proxy doctor`: `OK`
- proxy runtime remains limited local-only
- v2rayA UI listener remains `127.0.0.1:2015`
- BTC backend listener remains `127.0.0.1:60010`
- backend internal reachability: `OK`
- production customer traffic remains disabled

## Firewall Safety Summary

- no customer NAT redirects
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- `firewall.apply_mode` remains `plan_only`
- `proxy.runtime_activation_allowed` remains `false`

## Test Environment Note

All acceptance checks were run with the project virtual environment and farm5 sync workflow; this acceptance records isolated/non-production evidence only.

## Abuse Invariant Preservation

The mandatory abuse invariant remains unchanged and preserved:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Next Safe Step

Phase 6-E2 is accepted as isolated/non-production evidence package / boundary planning only.

The next planned step is **Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist**, isolated/non-production only, and it remains non-authorizing for live firewall or runtime mutation.
