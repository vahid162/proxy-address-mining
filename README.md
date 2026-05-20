# Proxy Address Mining

`proxy-address-mining` is a Python-first, API-first, PostgreSQL-backed greenfield rewrite of a mining customer gateway control plane.

It preserves the required operational capabilities of the old shell-script setup, but it must not become a direct migration, patch series, or extension of those old scripts.

## Current Status

Source of truth for the current phase:

```text
docs/PHASE_STATUS.md
```

Current repository/server gate:

```text
accepted_phase: Phase 10 — Session / Worker / Policy / Share Timeline accepted on farm5
working_phase: Phase 11 — Production / Customer Activation Gate planning/readiness
server_state: farm5 limited Phase 4 proxy runtime is running and accepted; no production customer traffic is active
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

The accepted Phase 4 runtime remains intentionally limited and local-only:

```text
v2rayA UI: 127.0.0.1:2015 -> container 2017
BTC backend: 127.0.0.1:60010 -> forwarder -> v2rayA -> pool
```

Do not use this repository for production customer traffic yet.
Latest recorded farm5 sync evidence is 0.1.151. The latest recorded farm5 evidence remains 0.1.151 until a newer farm5 sync/test evidence document is recorded. Phase 11D manual canary acceptance package farm5 evidence is recorded. Phase 11D manual canary execution gate package is implemented on GitHub as non-authorizing and has farm5 sync/test evidence recorded. Phase 11D operator-reviewed manual canary execution run preparation package farm5 evidence is recorded. Phase 11D actual operator-approved manual canary execution run package is implemented on GitHub by this PR, but actual farm5 canary execution evidence is still pending and this PR does not run canary traffic. Phase 11D actual execution remains not authorized as accepted farm5 evidence. Phase 10 Session / Worker / Policy / Share Timeline is accepted on farm5. Current target is Phase 11 Production / Customer Activation Gate planning/readiness. Production traffic, controlled CLI canary outside the future explicit single-canary operator run, limited real customer onboarding, firewall apply, iptables-restore, abuse automation runner, customer NAT/customer firewall rules, unrestricted production DB execution, hard/soft block automation, pause automation, UI, and Telegram remain disabled.

Historical compatibility anchors are kept in docs/HISTORICAL_COMPATIBILITY_ANCHORS.md.


## Current Accepted/Working Boundary (Phase 10 accepted / Phase 11 planning)

`docs/PHASE_STATUS.md` is authoritative. Current state is accepted Phase 10 / working Phase 11 planning-readiness. `docs/AI_SAFE_RUNTIME_FIRST.md` is part of the current Phase 11 contract reading path and does not open gates by itself.

Current gate values remain:

```text
production_traffic=none
firewall_apply_allowed=no
abuse_automation_allowed=no
customer_onboarding_allowed=db_only
proxy_data_plane_allowed=limited_runtime_local_only
ui_allowed=no
telegram_allowed=no
live_snapshot_read_allowed=iptables_save_read_only
restore_lock_record_execution_allowed=controlled_boundary_only
```

Current advancement target is Phase 11 Production / Customer Activation Gate planning/readiness. Historical anchors only: Phase 8 Abuse 1h Core, Phase 9 Check / Report / Diagnostics, and Phase 10 Session / Worker / Policy / Share Timeline are completed accepted context and are not active implementation targets unless `docs/PHASE_STATUS.md` explicitly reopens them.

Phase 6 apply-gate materials (D1/E0/E1/E2/E3/F/G/H and apply slices) are historical/reference-only context and remain non-authorizing for current active work. Phase 6 Dedicated Apply Gate Proposal/Review is historical/completed context. Apply Slice 3 and Apply Slice 4 are server-synced and accepted only as documentation/test-only boundaries. Historical compatibility anchor: Future Dedicated Phase 6 Apply Gate Proposal/Review.

No production traffic, controlled CLI canary, limited real customer onboarding, firewall apply, iptables-restore, customer NAT/customer firewall rules, usage automation, abuse automation, worker automation, UI, or Telegram is authorized.

Historical/reference-only notes from accepted Phase 6 boundaries:

```text
repository/documentation cleanup that preserves phase gates
firewall desired-state model refinement
firewall planner/diff contracts
human-readable firewall plan/report output
machine-readable JSON firewall plan/report output
offline snapshot parser and file-backed offline diff fixtures
offline restore payload artifacts
offline apply-readiness contracts
offline apply package reports
```
