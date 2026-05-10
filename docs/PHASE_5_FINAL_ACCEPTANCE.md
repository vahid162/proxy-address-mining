# Phase 5 Final Acceptance — Customer CRUD in DB Only

Status: accepted on farm5

Date: 2026-05-10

Version accepted: 0.1.21

Final acceptance patch version: 0.1.22

## Summary

Phase 5 is complete as a DB-only implementation phase.
It delivered customer CRUD and future-readiness contracts without introducing production traffic, customer firewall/NAT behavior, or live runtime mutation.

Accepted Phase 5 components:

- customer lifecycle contract
- customer schema/lifecycle migration 0002 (`0002_phase5_customer_lifecycle`)
- domain/DTO validation
- DB-only repository/service mutation path
- DB-only CLI customer commands
- DB-only read/list/show/report/history commands
- event/audit preservation
- policy versioning
- dry-run safety
- first-connect intent is DB-only
- soft-delete
- troubleshooting evidence contract F1
- product roles and UX journey contract F2

## Final Server Evidence (farm5)

```text
version: 0.1.21
pytest: 174 passed in 3.69s
current_accepted_phase: Phase 4 Runtime Activation — Limited Proxy Runtime Startup accepted on farm5
current_working_phase: Phase 5 — Customer CRUD in DB Only
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
ui_allowed: no
telegram_allowed: no
customer_onboarding_allowed: db_only_after_phase5_gate
proxy_data_plane_allowed: limited_runtime_local_only
config validate: OK
doctor: OK
database: OK
apply_mode: plan_only
traffic_changes: none
firewall_mutation: disabled
abuse_automation: disabled
db status: OK
alembic_version: 0002_phase5_customer_lifecycle
public_table_count: 64
lanes: 3
customers: 1
job_runs: 0
firewall_applies: 0
abuse_states: 0
proxy config-check: OK
proxy status: OK
proxy doctor: OK
v2raya UI listener: local-only
btc backend listener: local-only
backend internal reachability: OK
no customer NAT redirects
no MPF/customer firewall refs
runtime remains limited local-only
production customer traffic remains disabled
```

## Safety Assertions

- No production customer traffic was enabled.
- No customer firewall rules were added.
- No customer NAT redirects were added.
- No live firewall apply was introduced.
- No usage timer, hashrate collector, abuse runner, UI, Telegram, or public API was activated.
- Limited Phase 4 proxy runtime remains local-only and accepted.
- Backend internal reachability is allowed, while public backend exposure remains forbidden.
- Active customers remain future abuse-evaluable, and the mandatory one-hour abuse requirement remains preserved for Phase 8.

## Next Phase

Phase 6 is next: **Firewall Planner**.

Phase 6 must start with planner/model/diff work only and must not use ad-hoc firewall mutation.
