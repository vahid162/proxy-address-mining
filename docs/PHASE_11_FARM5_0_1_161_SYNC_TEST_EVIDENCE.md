# Phase 11 farm5 sync/test evidence — 0.1.161

- sync command: `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- backup: `/var/backups/mpf/source-before-zip-sync-20260521T083622Z`
- version: `0.1.161`
- pytest: `857 passed in 150.92s`
- mpf doctor/db/proxy/phase gate: `OK`
- production_traffic=`none`, firewall_apply_allowed=`no`, abuse_automation_allowed=`no`, customer_onboarding_allowed=`db_only`, proxy_data_plane_allowed=`limited_runtime_local_only`, ui_allowed=`no`, telegram_allowed=`no`
- no MPF/customer IPv4 or IPv6 references; no customer NAT redirects
- accepted local-only listeners: `127.0.0.1:2015`, `127.0.0.1:60010`
- docker local publish DNAT refs informational only: `127.0.0.1:2015`, `127.0.0.1:60010`

## Execute-control evidence
- plan mode: `PLAN_READY_FOR_FARM5_SYNC_EVIDENCE`, all mutation/safety flags false.
- restore-backup only env: blocked by `single_canary_host_apply_context_not_confirmed`; renderer status ok, payload sha256 `797cba...ffcc`, backup sha256 `60a5...7eb4`; mutation false.
- host context env: blocked by `single_canary_host_apply_execution_not_confirmed`; renderer status ok, payload sha256 `797cba...ffcc`, backup sha256 `c99e...f024`; mutation false.
