# Phase 8 Controlled Worker Dry-Run Gate

Status: Draft / Gate Preparation Only

## Purpose
Define the minimum requirements before a future operator-invoked controlled worker dry-run on farm5.

## Non-Authorization
This document does not:
- start worker
- enable scheduler
- enable timers
- enable abuse runner
- evaluate real customers
- execute production DB transitions
- write abuse_states
- write abuse_events
- mutate firewall
- change customer policy
- apply hard/soft blocks
- apply pause automation
- enable production traffic

## Required Before Controlled Worker Dry-Run
- PR #126 merged
- farm5 0.1.118 batch sync evidence recorded
- this 0.1.119 PR merged
- farm5 0.1.119 sync/test evidence collected
- operator explicitly approves controlled dry-run
- dry-run mode must be explicit
- batch limit must be explicit and small
- kill-switch must be documented
- lock behavior must be documented
- idempotency behavior must be documented
- skip/no-work/failure behavior must be documented
- no silent skip
- output must be saved for review

## Allowed Future Dry-Run Scope
- synthetic/in-memory worker cycle
- report-only CLI output
- no real customer mutation
- no DB writes
- no firewall mutation
- no production traffic

## Forbidden Future Dry-Run Scope
- background worker
- daemon
- scheduler
- timers
- cron
- systemd activation
- docker runtime changes
- customer policy mutation
- firewall apply
- conntrack flush
- hard/soft blocks
- pause automation
- production traffic

## Future Acceptance Criteria
Future controlled worker dry-run evidence must show:
- command used
- version
- config path
- final_decision remains BLOCKED or DRY_RUN_ONLY
- execution_allowed=false
- scheduler_authorized=false
- abuse_runner_authorized=false
- production_db_execution_authorized=false
- firewall_apply_authorized=false
- customer mutation false
- production traffic false
- explicit no-work/skip/lock/failure/idempotency reporting
- no silent skip
- no runtime side effects

## Operator-Invoked Synthetic Dry-Run Package

- This PR adds an operator-invoked synthetic dry-run package.
- It does not run background workers.
- It does not schedule anything.
- It does not evaluate real production customers.
- It does not read or write production DB data.
- It does not mutate firewall/customer state.
- It does not accept Phase 8.
- It prepares the command surface and report contract for future farm5 evidence collection.
- A future 0.1.120 farm5 sync/test is required before collecting farm5 controlled dry-run evidence.
