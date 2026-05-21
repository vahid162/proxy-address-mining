# Phase 11 farm5 0.1.159 Sync/Test/Execute-Control Evidence

- sync command: `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- source backup: `/var/backups/mpf/source-before-zip-sync-20260520T125502Z`
- version: `0.1.159`
- pytest: `853 passed in 154.77s`
- mpf doctor: `OK`
- mpf db status: `OK`
- mpf proxy doctor: `OK`
- current phase safety gate: `OK`

## Plan mode

- command: `mpf production manual-canary-execute --output json`
- final_decision: `PLAN_READY_FOR_FARM5_SYNC_EVIDENCE`
- non-mutating: true
- all safety flags: false

## Execute-control (restore backup boundary)

- blocker result: `BLOCKED`
- blocker: `single_canary_restore_payload_renderer_missing`
- missing_primitive: `accepted_exact_canary_restore_payload_renderer`
- restore point created: true
- iptables-save backup created: true
- backup path: `/var/backups/mpf/phase11-single-canary/iptables-save-farm5-20260520T125854Z.txt`
- backup sha256: `bb957ed1987d0a4929f09dcb66d26a261b20acff64aef24668cd5e64bba676d4`
- all mutation flags: false
- all safety flags: false

## Runtime/traffic safety

- production_traffic: `none`
- firewall_apply_allowed: `no`
- abuse_automation_allowed: `no`
- customer_onboarding_allowed: `db_only`
- proxy_data_plane_allowed: `limited_runtime_local_only`
- ui_allowed: `no`
- telegram_allowed: `no`
- no customer NAT redirects
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- local-only listeners:
  - `127.0.0.1:2015`
  - `127.0.0.1:60010`
- Docker-managed local publish DNAT rules for `127.0.0.1:2015` and `127.0.0.1:60010` are informational only.

## Phase guard

- Phase 11 accepted: no
- actual canary execution performed: no
