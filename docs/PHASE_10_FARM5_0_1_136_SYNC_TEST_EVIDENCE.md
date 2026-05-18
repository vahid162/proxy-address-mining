# Phase 10 farm5 0.1.136 Sync/Test Evidence

command:
  sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip

backup:
  /var/backups/mpf/source-before-zip-sync-20260518T085532Z

server version after sync:
  0.1.136

pytest:
  782 passed in 146.83s (0:02:26)

doctor/config/db/proxy:
  OK

phase gate:
  OK

current state before this acceptance PR:
  current_accepted_phase: Phase 9 — Check / Report / Diagnostics accepted on farm5
  current_working_phase: Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness
  production_traffic: none
  firewall_apply_allowed: no
  abuse_automation_allowed: no
  customer_onboarding_allowed: db_only
  proxy_data_plane_allowed: limited_runtime_local_only
  ui_allowed: no
  telegram_allowed: no
  live_snapshot_read_allowed: iptables_save_read_only
  restore_lock_record_execution_allowed: controlled_boundary_only

Phase 10 readiness evidence:
  final-acceptance-readiness: ACCEPTED
  implementation-readiness: ACCEPTED
  session_model_readiness: ACCEPTED
  worker_identity_readiness: ACCEPTED
  worker_policy_contract_readiness: ACCEPTED
  share_timeline_model_readiness: ACCEPTED
  collector_dry_run_gate_readiness: ACCEPTED
  collector_dry_run_plan: ACCEPTED
  runtime_worker_dry_run_readiness: ACCEPTED
  scheduler_dry_run_readiness: ACCEPTED
  worker_cycle_dry_run_plan: ACCEPTED
  downstream_dangerous_authorization_flags: []
  blockers: []
  warnings: []
  errors: []

Safety observations:
  apply_mode: plan_only
  traffic_changes: none
  firewall_mutation: disabled
  abuse_automation: disabled
  no MPF/customer IPv4 firewall references detected
  no MPF/customer IPv6 firewall references detected
  no customer NAT redirects
  accepted limited runtime listeners are local-only:
    127.0.0.1:2015
    127.0.0.1:60010

Final verdict:
  GitHub main zip synced successfully.
  server source is aligned with GitHub zip.
  accepted current phase gate is installed and verified.
  runtime remains limited local-only.
  production customer traffic is still disabled.

Non-authorization statement:
  This evidence does not authorize:
    Phase 11 production activation
    controlled CLI canary
    production traffic
    firewall apply
    iptables-restore
    customer NAT/customer firewall rules
    abuse automation runner
    real worker runtime
    scheduler/timer
    collector daemon
    live share ingestion
    production DB execution
    hard/soft block automation
    pause automation
    UI
    Telegram
    production customer onboarding
