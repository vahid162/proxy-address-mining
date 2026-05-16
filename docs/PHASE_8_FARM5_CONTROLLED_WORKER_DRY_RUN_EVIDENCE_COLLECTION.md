# Phase 8 farm5 Controlled Worker Dry-Run Evidence Collection

Draft / Evidence Collection Runbook / Not Yet Executed

## Status

- Runbook only.
- Not executed by this PR.
- Does not accept Phase 8.
- Does not authorize background worker, scheduler, abuse runner, DB writes, firewall mutation, customer mutation, hard/soft blocks, pause automation, UI, Telegram, or production traffic.

## Preconditions

- PR #128 merged.
- farm5 synced/tested to 0.1.120.
- This PR merged.
- farm5 synced/tested to 0.1.121.
- Current State remains Phase 7 accepted / Phase 8 working.
- production_traffic: none.
- firewall_apply_allowed: no.
- abuse_automation_allowed: no.
- apply_mode: plan_only.
- proxy.runtime_activation_allowed remains disabled.
- no non-deleted customers.
- operator explicitly invokes dry-run commands.

## Commands To Run After 0.1.121 Sync

The operator should run only these report-only commands:

mpf phase8 controlled-worker-dry-run --output json
mpf phase8 controlled-worker-dry-run --operator-confirmed --output json
mpf phase8 controlled-worker-dry-run-gate --output json
mpf phase8 controlled-worker-pre-acceptance --output json
mpf phase-status
mpf doctor

These commands must not be run as background services.
These commands must not be scheduled.
These commands must not be wrapped in systemd/cron/docker runtime automation.

## Expected Dry-Run Evidence

The controlled worker dry-run output must show:

- component: phase8_controlled_worker_dry_run
- final_decision: BLOCKED or DRY_RUN_ONLY
- dry_run_status: CONTROLLED_WORKER_DRY_RUN_SYNTHETIC_ONLY
- authorization_status: NOT_AUTHORIZED_FOR_RUNTIME_EXECUTION
- inspection_only: true
- report_only: true
- synthetic_only: true
- operator_invoked_only: true
- execution_allowed: false
- production_side_effects_allowed: false
- phase8_acceptance_allowed: false
- repository_version: 0.1.121
- latest_recorded_farm5_sync_evidence: 0.1.120
- farm5_0_1_120_sync_evidence_present: true
- future_phase8_final_acceptance_pr_required: true
- all authorization flags false
- synthetic_item_count >= 10
- synthetic_scenarios_passed: true
- all_items_have_no_side_effects: true
- default command without --operator-confirmed includes operator_confirmation_required blocker
- command with --operator-confirmed does not include operator_confirmation_required, but still has execution_allowed=false and production_side_effects_allowed=false

## Required Safety Evidence

Evidence must prove:

- no DB write
- no abuse_states write
- no abuse_events write
- no job_runs write
- no firewall apply
- no iptables-restore
- no customer NAT/rules
- no customer policy mutation
- no hard/soft block
- no pause automation
- no production traffic
- no background worker
- no scheduler
- no timer
- no abuse runner

## Evidence Capture Format

The operator should paste the full terminal output into the next PR prompt.

The next PR must record exact command output and must not summarize missing fields.
