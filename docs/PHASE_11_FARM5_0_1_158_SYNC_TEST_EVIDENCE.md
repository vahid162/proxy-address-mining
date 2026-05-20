# Phase 11 farm5 sync/test evidence (0.1.158)

- sync command: `sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip`
- backup path: `/var/backups/mpf/source-before-zip-sync-20260520T121743Z`
- version: `0.1.158`
- pytest: `848 passed`
- mpf doctor: `OK`
- mpf db status: `OK`
- mpf proxy doctor: `OK`
- current phase gate during sync: `OK`
- plan mode result: `PLAN_READY_FOR_FARM5_SYNC_EVIDENCE` (non-mutating, all safety flags false)
- execute-control result: `BLOCKED`, `blocker=real_restore_backup_adapter_missing` (all mutation flags false, all safety flags false)
- production traffic: none
- customer NAT redirects: none
- MPF/customer firewall references: none
- local-only listeners: `127.0.0.1:2015`, `127.0.0.1:60010`
- note: later manual `bash scripts/verify_current_phase_gate.sh` failed only because it was run from `/opt/mpf-py` instead of `/opt/mpf-py-src`; sync script gate check itself succeeded.
