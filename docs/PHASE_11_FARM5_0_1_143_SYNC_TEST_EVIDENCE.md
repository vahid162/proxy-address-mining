# Phase 11 farm5 0.1.143 sync/test evidence

Status: recorded evidence (report-only, non-authorizing)

## Scope

This document records farm5 sync/test evidence for GitHub version `0.1.143` and accepts only report-only Phase 11A/11B surfaces on farm5.

It does **not** authorize Phase 11C execution, controlled CLI canary execution, production traffic, firewall apply, iptables-restore, customer NAT/customer firewall rules, abuse automation, UI, or Telegram.

## Verified farm5 evidence

- sync command: `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- server version after sync: `0.1.143`
- source aligned with GitHub zip: `OK`
- pytest: `798 passed in 151.30s`
- mpf doctor: `OK`

## Database status summary

- config: `OK`
- database: `OK`
- db status: `OK`
- alembic_version: `0002_phase5_customer_lifecycle`
- public_table_count: `64`
- lanes: `3`
- customers: `1`
- job_runs: `0`
- firewall_applies: `1`
- abuse_states: `0`

## Proxy summary

- proxy config: `OK`
- proxy status: `OK`
- proxy doctor: `OK`
- runtime remains limited local-only.

## Phase and safety gate summary

- phase safety gate: `OK`
- current accepted phase: `Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5`
- current working phase: `Phase 11 — Production / Customer Activation Gate planning/readiness`
- apply_mode: `plan_only`
- traffic_changes: `none`
- firewall_mutation: `disabled`
- abuse_automation: `disabled`

### Safety flags (must remain closed)

- production_traffic: `none`
- firewall_apply_allowed: `no`
- abuse_automation_allowed: `no`
- customer_onboarding_allowed: `db_only`
- proxy_data_plane_allowed: `limited_runtime_local_only`
- ui_allowed: `no`
- telegram_allowed: `no`
- live_snapshot_read_allowed: `iptables_save_read_only`
- restore_lock_record_execution_allowed: `controlled_boundary_only`

## Local-only listener summary

Accepted limited runtime listeners remain local-only:

- `127.0.0.1:2015`
- `127.0.0.1:60010`

Docker local publish DNAT references are informational only for accepted limited runtime.

## Explicit non-authorization statements

- Production customer traffic remains disabled.
- No MPF/customer NAT redirects are active.
- No MPF/customer IPv4 firewall references are active.
- No MPF/customer IPv6 firewall references are active.
- No MPF/customer firewall rules are active.
- This evidence accepts only Phase 11A/11B report-only surfaces on farm5 and does not authorize Phase 11C execution.
