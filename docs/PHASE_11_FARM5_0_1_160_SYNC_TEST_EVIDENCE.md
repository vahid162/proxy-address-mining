# Phase 11 farm5 0.1.160 Sync/Test/Execute-Control Evidence

- sync command: `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- backup: `/var/backups/mpf/source-before-zip-sync-20260521T073055Z`
- version: `0.1.160`
- pytest: `857 passed in 147.28s`
- mpf doctor: `OK`
- db status: `OK`
- proxy doctor: `OK`
- current phase gate: `OK`
- production_traffic: `none`
- firewall_apply_allowed: `no`
- abuse_automation_allowed: `no`
- customer_onboarding_allowed: `db_only`
- proxy_data_plane_allowed: `limited_runtime_local_only`
- ui_allowed: `no`
- telegram_allowed: `no`
- no MPF/customer IPv4 firewall references detected
- no MPF/customer IPv6 firewall references detected
- no customer NAT redirects
- accepted listeners local-only: `127.0.0.1:2015`, `127.0.0.1:60010`

## Execute-control evidence

- plan mode command: `mpf production manual-canary-execute --output json`
  - final_decision: `PLAN_READY_FOR_FARM5_SYNC_EVIDENCE`
  - mutation_performed: `false`
  - all safety_flags: `false`

- renderer-only command used `MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow`
  - final_decision: `BLOCKED`
  - blocker: `single_canary_host_apply_context_not_confirmed`
  - restore payload sha256: `797cba5393b2b7e736bd3511fb92c8e89a1885be60cc89c3b5240fee3580ffcc`
  - restore point: `phase11-single-canary-farm5`
  - iptables-save backup: `/var/backups/mpf/phase11-single-canary/iptables-save-farm5-20260521T074426Z.txt`
  - backup sha256: `acc5878031bf51ebff943db1a5767abb1b1f670cd4322784b50456662efa8b21`
  - all mutation and safety flags: `false`

- both-guards command used `MPF_PHASE11_SINGLE_CANARY_RESTORE_BACKUP=allow` and `MPF_PHASE11_SINGLE_CANARY_HOST_APPLY=allow`
  - final_decision: `BLOCKED`
  - blocker: `accepted_single_canary_host_apply_execution_missing`
  - missing_primitive: `accepted_single_canary_host_apply_execution`
  - restore payload sha256: `797cba5393b2b7e736bd3511fb92c8e89a1885be60cc89c3b5240fee3580ffcc`
  - restore point: `phase11-single-canary-farm5`
  - iptables-save backup: `/var/backups/mpf/phase11-single-canary/iptables-save-farm5-20260521T074432Z.txt`
  - backup sha256: `13bd1a427f154f8932103142081a14ff7300efc65c2b04544724d462284a427a`
  - all mutation and safety flags: `false`

Phase 11 remains unaccepted. No actual farm5 canary execution was performed in this evidence package.
