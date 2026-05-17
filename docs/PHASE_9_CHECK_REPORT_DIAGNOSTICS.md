# Phase 9 Check / Report / Final-Verdict Diagnostics

Status: report-only/read-only planning-readiness contract.

## Purpose

This document defines the next Phase 9 diagnostics surface after the initial Phase 9 readiness package.

It is intended to give the operator one compact, structured report for:
- current phase gate status
- Phase 8 final-acceptance status
- Phase 9 readiness status
- doctor/config/database expectations
- proxy/runtime diagnostic expectations
- customer diagnostics readiness
- abuse status visibility readiness
- usage/accounting visibility readiness
- policy/reject visibility readiness
- evidence-pack readiness
- troubleshooting/final-verdict readiness

## Scope

The diagnostic report is read-only and report-only.

It may inspect repository documentation and compose existing report-only contract signals.
It must not execute production workflows or mutate server state.

## Stop Conditions

This diagnostics contract must not:
- enable production traffic
- enable firewall apply
- run iptables-restore
- create customer NAT/customer firewall rules
- enable or start abuse automation runner
- start workers, schedulers, or timers
- evaluate real production customers
- execute production DB transitions
- write production abuse state
- write customer policy state
- apply hard/soft blocks
- apply pause automation
- enable UI
- enable Telegram

## Required Safety Flags

The report must expose all dangerous authorization flags and keep them false:
- execution_allowed
- production_activation_allowed
- production_traffic_authorized
- firewall_apply_authorized
- iptables_restore_authorized
- customer_nat_authorized
- customer_firewall_rules_authorized
- abuse_runner_authorized
- runtime_worker_authorized
- worker_start_authorized
- scheduler_authorized
- timer_authorized
- production_db_execution_authorized
- db_writes_authorized
- customer_policy_mutation_authorized
- hard_block_authorized
- soft_block_authorized
- pause_automation_authorized
- ui_authorized
- telegram_authorized

## Acceptance Boundary

Acceptance of this contract means only that a report-only diagnostic summary exists.

It does not authorize production activation, live firewall changes, runtime automation, customer mutation, hard/soft blocks, pause automation, UI, or Telegram.

## Next Work After This Contract

After this report-only diagnostics contract is synced and tested on farm5, future Phase 9 work may add richer diagnostic details in separate gated PRs, such as customer-specific read-only diagnostics, evidence-pack export readiness, and troubleshooting summaries.
