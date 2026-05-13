# PHASE STATUS

Status: Active project control file

This file is the authoritative phase gate for humans and AI coding agents. It must be checked before changing code, scripts, deployment files, services, jobs, tests, migrations, or documentation.

## Current State

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
```

The `Current State` block above is the current gate. Historical compatibility notes and accepted evidence are informational only.

Apply Slice 1 and Slice 2 are server-synced and accepted only as documentation/test-only readiness boundaries. Apply Slice 3 and Slice 4 are server-synced and accepted only as documentation/test-only boundaries. Current planning target: Future Dedicated Phase 6 Apply Gate Proposal/Review. Historical proposal reference: `docs/PHASE_6_DEDICATED_APPLY_GATE_PROPOSAL_REVIEW.md`. The explicitly gated read-only `iptables-save` live snapshot path is authorized (`live_snapshot_read_allowed: iptables_save_read_only`). No apply, restore, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.

## Accepted Server Results

### Phase 1 — Bootstrap Without Traffic Changes

```text
PostgreSQL active
Docker active
containerd active
mpf config validate OK
mpf doctor OK
mpf db ping OK
pytest passed
Docker had no containers
No MPF firewall rules existed
firewall.apply_mode remained plan_only
```

### Phase 2 — PostgreSQL + Config + Domain Model

```text
backup/snapshot created before migration
pytest passed from /opt/mpf-py-src/.venv
alembic current/head = 0001_phase2_initial_schema
public schema table count = 64
runtime tables remained empty
Docker had no containers
No MPF firewall rules existed
firewall.apply_mode remained plan_only
no proxy data-plane was started
no production traffic was changed
```

### Phase 3 — CLI + Internal API Foundation

```text
Phase 3 read-only CLI/API foundation accepted on farm5
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
pytest passed: 48 passed
runtime tables remained empty
Docker had no containers
No MPF firewall or NAT rules existed
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 3.1 — Official Runtime Alignment

```text
official /usr/local/bin/mpf runtime exposed accepted read-only commands
mpf --version reported 0.1.0 during acceptance
mpf phase-status was aligned during verification
pytest passed: 48 passed
runtime-facing tables remained empty
Docker had no containers
No MPF firewall/NAT rules existed
No MPF systemd/cron automation existed
No risky backend/UI ports were listening
firewall.apply_mode remained plan_only
no production traffic was changed
```

### Phase 4 Runtime — Limited Proxy Runtime Startup

See:

```text
docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
```

Accepted evidence summary:

```text
server source aligned with GitHub ZIP
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf proxy config-check final_verdict: OK
mpf-v2raya container started and healthy
mpf-forwarder-btc container started and healthy
v2rayA UI host/operator listener: 127.0.0.1:2015
v2rayA UI container target port: 2017
BTC backend listener: 127.0.0.1:60010
BTC backend internal reachability: OK
no public v2rayA UI exposure detected
no public BTC backend exposure detected
no MPF/customer firewall references detected
no customer NAT redirects detected
customers: 0
job_runs: 0
firewall_applies: 0
abuse_states: 0
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
```

Docker-managed local publish rules for `127.0.0.1:2015` and `127.0.0.1:60010` are accepted only as local Docker publish rules. They are not MPF customer NAT redirects.

### Phase 5 — Customer CRUD in DB Only

See:

```text
docs/PHASE_5_FINAL_ACCEPTANCE.md
```

Accepted evidence summary:

```text
Phase 5 accepted as DB-only customer CRUD + future-readiness contracts
version accepted on server: 0.1.21
final synced repository/server gate: 0.1.26
pytest passed: 182 passed during final clean sync evidence
alembic_version: 0002_phase5_customer_lifecycle
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
ui_allowed: no
telegram_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
no production customer traffic
no live firewall apply
runtime remained limited local-only
```

### Phase 6-C — Offline Apply Gate Readiness/Review

```text
version accepted on farm5: 0.1.56
pytest passed: 337 passed
mpf firewall gate-review final_decision: BLOCKED
risk_summary.total: 18
checklist_summary.total: 4
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall apply
no iptables-save execution
no iptables-restore execution
```

### Phase 6-D1 — Live-Apply Boundary Contract

```text
version accepted on farm5: 0.1.59
pytest passed: 357 passed
docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md accepted
docs/PHASE_6_D1_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-E0 — Isolated Apply Harness Contracts

```text
version accepted on farm5: 0.1.61
pytest passed: 376 passed
docs/PHASE_6_E0_ISOLATED_APPLY_HARNESS.md accepted
docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
fake/no-op harness only
report-only harness service
deterministic plan -> apply -> verify ordering tested
verify-failure rollback-guidance ordering tested
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```


### Phase 6-E1 — Isolated Harness Contract Hardening

```text
version accepted on farm5: 0.1.63
pytest with venv: 392 passed
docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md accepted
docs/PHASE_6_E1_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-E2 — Isolated Harness Evidence Package / Boundary Planning

```text
version accepted on farm5: 0.1.66
pytest with venv: 403 passed
docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md accepted
docs/PHASE_6_E2_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```


### Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist

```text
version accepted on farm5: 0.1.70
pytest with venv: 413 passed
docs/PHASE_6_E3_NON_AUTHORIZING_GATE_CHECKLIST.md accepted
docs/PHASE_6_E3_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```



### Phase 6-F — Manual Canary Gate Definition

```text
version accepted on farm5: 0.1.73
pytest with venv: 426 passed
docs/PHASE_6_F_MANUAL_CANARY_GATE_DEFINITION.md accepted
docs/PHASE_6_F_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-G — Controlled Live Apply Gate Planning / Pre-Apply Review

```text
version accepted on farm5: 0.1.76
pytest with venv: 442 passed
docs/PHASE_6_G_CONTROLLED_LIVE_APPLY_GATE_PLANNING.md accepted
docs/PHASE_6_G_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no live rollback
no live verify
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary

```text
version accepted on farm5: 0.1.79
pytest with venv: 457 passed
docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md accepted
docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md added
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no customer NAT redirects
no customer firewall rules
no MPF/customer firewall refs
accepted runtime remained limited local-only
no live firewall read
no live firewall write
no live firewall apply
no live rollback
no live verify
no iptables-save execution
no iptables-restore execution
no subprocess firewall calls
no real iptables adapter
no lock acquisition
no restore point write
no DB apply write
```

### Phase 6 Apply Slice 1-2 — Documentation/Readiness Boundary Sync

```text
version accepted on farm5: 0.1.83
pytest with venv: 486 passed
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T055542Z
current phase safety gate: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
Slice 1 and Slice 2 are accepted only as documentation/test-only readiness boundaries
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Apply Slice 3-4 — Documentation Boundary Sync

```text
version accepted on farm5: 0.1.86
pytest during sync: 499 passed
manual pytest after sync: 499 passed
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T071337Z
current phase safety gate: OK
source aligned with GitHub zip: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
Slice 3 and Slice 4 are accepted only as documentation/test-only boundaries
no manual canary apply
no no-customer apply
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Apply Gate Proposal Review — Documentation Sync

```text
version accepted on farm5: 0.1.88
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T084028Z
pytest during sync: 504 passed
manual pytest with project venv: 504 passed
current phase safety gate: OK
source aligned with GitHub zip: OK
mpf --version: 0.1.88
/opt/mpf-py-src/VERSION: 0.1.88
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
Future Dedicated Phase 6 Apply Gate Proposal/Review remains documentation/test-only and non-authorizing
no dedicated apply gate
no manual canary apply
no no-customer apply
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Apply Gate Readiness Integration — Server Sync

```text
version accepted on farm5: 0.1.90
sync command: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip
backup: /var/backups/mpf/source-before-zip-sync-20260513T095401Z
pytest with venv during sync: 511 passed
current phase safety gate: OK
source aligned with GitHub zip: OK
mpf --version: 0.1.90
mpf config validate: OK
mpf doctor: OK
mpf db status: OK
mpf proxy doctor final_verdict: OK
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
no MPF/customer IPv4 firewall references
no MPF/customer IPv6 firewall references
no customer NAT redirects
accepted limited runtime listeners remain local-only
v2rayA UI listener: 127.0.0.1:2015
BTC backend listener: 127.0.0.1:60010
mpf firewall apply-gate-readiness remains read-only/report-only and BLOCKED
mpf firewall gate-review includes apply_gate_readiness_summary and remains BLOCKED
no live firewall read/write/apply/rollback/verify
no iptables-save or iptables-restore
no real adapters or subprocess firewall calls
no restore point writes, lock acquisition, DB apply writes, DB apply records, or migrations
no customer NAT/customer firewall rules
no production traffic
no usage automation
no abuse automation
no UI
no Telegram
```

### Phase 6 Live Snapshot Readiness Report-Only Server Sync

```text
version accepted on farm5: 0.1.90
sync: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip (backup: /var/backups/mpf/source-before-zip-sync-20260513T124116Z)
pytest: 532 passed in 11.70s (venv), 532 passed in 10.00s (/opt/mpf-py-src)
source aligned with GitHub zip: OK; phase safety gate: OK; mpf --version: 0.1.90
mpf checks: config validate OK, doctor OK, db status OK, proxy doctor final_verdict OK
database: alembic_version=0002_phase5_customer_lifecycle, public_table_count=64, lanes=3, customers=1, job_runs=0, firewall_applies=0, abuse_states=0
runtime/gates: firewall.apply_mode=plan_only, proxy.runtime_activation_allowed=false, production_traffic=none, firewall_apply_allowed=no, abuse_automation_allowed=no, customer_onboarding_allowed=db_only, proxy_data_plane_allowed=limited_runtime_local_only, ui_allowed=no, telegram_allowed=no
safety: no MPF/customer IPv4/IPv6 firewall refs, no customer NAT redirects, listeners local-only (v2rayA 127.0.0.1:2015, BTC backend 127.0.0.1:60010), Docker local publish DNAT informational only
live-snapshot-scaffold: BLOCKED, NOT_AUTHORIZED, no live read, no iptables-save, no subprocess, no firewall/db mutation, no restore/lock, current_state_preserved=true
live-snapshot-readiness: BLOCKED, NOT_AUTHORIZED, live read allowed/executed=false, iptables-save allowed/executed=false, subprocess/filesystem allowed/executed=false, no mutation, snapshot counts=0/0/0, current_state_preserved=true, next_required_gate=explicit docs/PHASE_STATUS.md acceptance plus farm5 evidence
apply-gate-readiness: BLOCKED, plan_only preserved, live firewall read/write not allowed, iptables-save/restore not allowed, real adapter/subprocess calls not allowed, customer NAT/firewall rules not allowed, live snapshot scaffold/read summaries present and BLOCKED
firewall gate-review: BLOCKED, applyable=false, inspection_only=true, artifact_only=true, live_apply_allowed=false, abuse requirement preserved (normal -> over_tracking -> over_grace -> hard, sustained_hardening_seconds=3600), safety flags confirm no live read/write/save/restore/database/filesystem mutations
```

This server result is report-only for the earlier readiness boundary and remains non-authorizing for apply/write paths.
The explicitly gated read-only `iptables-save` snapshot path is now authorized with successful farm5 evidence (see section below).
No firewall write/apply/rollback/verify, `iptables-restore`, restore point write, lock acquisition, DB apply write/record, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is restore point + lock + DB apply record readiness, still without customer NAT/customer firewall rules.


### Phase 6 Read-Only iptables-save Snapshot — Server Evidence

```text
version accepted on farm5: 0.1.90
sync: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip (backup: /var/backups/mpf/source-before-zip-sync-20260513T134528Z)
pytest (venv during sync): 536 passed in 11.57s
source aligned with GitHub zip: OK; phase safety gate: OK
current state preserved: production_traffic=none, firewall_apply_allowed=no, abuse_automation_allowed=no, customer_onboarding_allowed=db_only, proxy_data_plane_allowed=limited_runtime_local_only, ui_allowed=no, telegram_allowed=no, live_snapshot_read_allowed=iptables_save_read_only
mpf checks: config validate OK; doctor OK; db status OK; proxy doctor final_verdict OK
runtime safety: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; no MPF/customer IPv4/IPv6 refs; no customer NAT redirects; listeners local-only (v2rayA 127.0.0.1:2015, BTC backend 127.0.0.1:60010)
live-snapshot-readiness: READY_FOR_READ_ONLY_SNAPSHOT; AUTHORIZED_READ_ONLY; live_firewall_read_allowed=true; iptables_save_allowed=true; apply_decision=BLOCKED; blockers=none; errors=none
live-snapshot-read (dry, no execute): READY_FOR_READ_ONLY_SNAPSHOT; AUTHORIZED_READ_ONLY; subprocess_executed=false; iptables_save_executed=false; apply_decision=BLOCKED
live-snapshot-read (--execute, json output): READ_ONLY_SNAPSHOT_COLLECTED; AUTHORIZED_READ_ONLY; live_firewall_read_executed=true; iptables_save_executed=true; subprocess_args=["iptables-save"]; subprocess_returncode=0; parser_input_source=iptables-save stdout; stdout_line_count=60; source_snapshot_sha256=4f506c5871a4fa518b874e6a635eac56cb61351f49901a1ff6fc9aeb4fb94019; snapshot_rule_count=0; snapshot_chain_count=0; snapshot_table_count=0; filesystem_write_executed=false; firewall_mutation=false; db_mutation=false; restore_point_written=false; lock_acquired=false; customer_nat_changed=false; customer_firewall_rules_changed=false; production_traffic_changed=false; apply_decision=BLOCKED; errors=none
parser scope note: snapshot counters track MPF-owned chains/rules only; with no MPF/customer firewall refs, counts 0/0/0 are expected while stdout_line_count=60 confirms iptables-save returned content
```

This server result proves only the explicitly gated read-only `iptables-save` snapshot path.
No `iptables-restore` is authorized.
No firewall write, apply, rollback, restore point write, lock acquisition, DB apply write, DB apply record, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is separate explicit restore point + lock + DB apply record gate proposal/acceptance boundary, still without customer NAT/customer firewall rules.

### Phase 6 Restore/Lock/DB Apply Record Readiness — Server Sync

```text
version accepted on farm5: 0.1.90
sync: sudo mpf-sync-main-zip /tmp/proxy-address-mining-main.zip (backup: /var/backups/mpf/source-before-zip-sync-20260513T182123Z)
pytest (venv during sync): 544 passed in 12.13s
source aligned with GitHub zip: OK; current phase safety gate: OK; mpf --version: 0.1.90
mpf checks: config validate OK; doctor OK; db status OK; proxy doctor final_verdict OK
runtime/gates: firewall.apply_mode=plan_only; proxy.runtime_activation_allowed=false; production_traffic=none; firewall_apply_allowed=no; abuse_automation_allowed=no
runtime safety: no MPF/customer IPv4/IPv6 firewall refs; no customer NAT redirects; listeners local-only (v2rayA 127.0.0.1:2015, BTC backend 127.0.0.1:60010)
restore-lock-record-readiness: final_decision=BLOCKED; authorization_status=NOT_AUTHORIZED_FOR_WRITES; inspection_only=true; report_only=true
actions executed: restore_point_write=false; lock_acquired=false; db_apply_record_write=false; iptables_restore_executed=false; customer_nat_changed=false; customer_firewall_rules_changed=false
apply-gate-readiness: final_decision=BLOCKED
gate-review: final_decision=BLOCKED
time_sync_required_before_future_write/production/usage/abuse_gate=true
```

This server result proves only the report-only restore point + lock + DB apply record readiness surface.
No restore point write is authorized.
No lock acquisition is authorized.
No DB apply write or DB apply record is authorized.
No firewall write/apply/rollback/verify, iptables-restore, customer NAT, customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
Apply and gate-review final decisions remain BLOCKED.
The next implementation target is a separate explicit restore point + lock + DB apply record gate proposal/acceptance boundary, still without customer NAT/customer firewall rules.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This is not a Phase 6 planning blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## What Is Allowed Now

Allowed work is limited to **Phase 6 — Firewall Planner** preparation and planning-only implementation:

```text
- repository/documentation cleanup that preserves the current gate
- firewall desired-model design and implementation
- firewall planner/diff design and implementation
- human-readable and JSON plan output
- dry-run evidence generation
- planner tests and safety regression tests
- proxy/backend safety checks that preserve internal reachability + external non-exposure contracts
```

## What Is Forbidden Now

Do not implement, run, or activate:

```text
- production traffic
- customer NAT redirects
- customer firewall rules
- live firewall apply
- iptables-restore
- usage timers
- hash-rate/share collectors
- abuse runner automation
- block or pause automation
- local UI service
- buyer UI service
- Telegram bot
- production customer import
- worker enforcement
- public API binding
- public v2rayA UI exposure
- public backend exposure
```

Live firewall apply remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.

## Next Planned Step

Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing.
Phase 6-H is accepted as dedicated apply gate entry criteria / authorization boundary only, documentation/test-only and non-authorizing.

Phase 6-G does not authorize host production firewall mutation, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, restore point writes, lock acquisition, DB writes, migrations, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

- Phase 6-G and Phase 6-H remain accepted historical safety sub-steps only.
- Apply Slice 1 has been server-synced and accepted only as a documentation/test-only readiness boundary.
- Apply Slice 2 has been server-synced and accepted only as a documentation/test-only readiness boundary.
- Apply Slice 1 and Slice 2 are server-synced and accepted only as documentation/test-only readiness boundaries.
- Apply Slice 3 and Slice 4 are server-synced and accepted only as documentation/test-only boundaries.
- The explicitly gated read-only `iptables-save` snapshot path is authorized and has successful farm5 evidence.
- No firewall write/apply/rollback/verify, `iptables-restore`, restore point write, lock acquisition, DB apply write/record, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
- Apply and gate-review final decisions remain BLOCKED.
- Next implementation target: separate explicit restore point + lock + DB apply record gate proposal/acceptance boundary, still without customer NAT/customer firewall rules.
- Historical/reference context only: Next planning target is Future Dedicated Phase 6 Apply Gate Proposal/Review.
- Future Dedicated Phase 6 Apply Gate Proposal/Review remains historical/reference context only.
- Future dedicated Phase 6 apply gate remains not accepted and not authorized.
- No dedicated apply gate, manual canary apply, no-customer apply, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, restore point writes, lock acquisition, DB writes, migrations, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram is authorized.
- Live apply remains forbidden until a dedicated apply gate is explicitly accepted.

## Current Safety Invariants

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = limited_runtime_local_only
customer_onboarding_allowed = db_only
```

Any patch that bypasses these invariants or introduces traffic-changing behavior before the correct accepted phase must be rejected.

## Backend Port Invariant

Backend ports are internal service ports. They must be blocked from direct external/public access only while remaining reachable from valid internal server and Docker paths.

Required proxy/firewall doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not hide backend ports by blocking loopback, local server paths, required Docker/internal paths, or the future MPF-owned NAT redirect path.

## Phase 5 Gate Status

Phase 5 is accepted and closed.

Current Phase 5 state is:

```text
customer CRUD works in DB only
policy history is preserved
events/audit are recorded for DB-only customer mutations
port/lane collisions are validated
no iptables rule is created
no NAT redirect is created
no runtime customer traffic is enabled
```

Future customer records remain DB-only until Phase 6 apply and customer NAT/customer firewall gates are accepted.


Phase 6-H reference:

```text
docs/PHASE_6_H_DEDICATED_APPLY_GATE_ENTRY_CRITERIA.md
docs/PHASE_6_H_ACCEPTANCE_EVIDENCE.md
```


### Phase 6 Read-Only Live Snapshot Gate — Limited Authorization

- limited authorization: iptables-save read-only snapshot only
- no iptables-restore
- no firewall write
- no apply
- no rollback
- no restore point write
- no lock acquisition
- no DB apply write
- no DB apply record
- no customer NAT
- no customer firewall rules
- no production traffic
- no usage automation
- no abuse automation
- no UI
- no Telegram
- output is inspection-only
- failure must be fail-closed
- empty snapshot fallback is forbidden
- guessed firewall state is forbidden
- result may feed parser/planner/diff only
- apply/gate-review final decision must remain BLOCKED
