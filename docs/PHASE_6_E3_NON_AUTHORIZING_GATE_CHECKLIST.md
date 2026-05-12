# Phase 6-E3 — Isolated Harness Evidence Review / Non-Authorizing Gate Checklist

Status: planned, isolated/non-production only, non-authorizing.

## Purpose

Define a deterministic evidence-review and non-authorizing checklist contract after Phase 6-E2 acceptance, before any future manual canary gate definition.

## Current Gate Snapshot

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
customer_onboarding_allowed: db_only
proxy_data_plane_allowed: limited_runtime_local_only
ui_allowed: no
telegram_allowed: no
```

## Non-Authorization Statement

Phase 6-E3 is documentation/test-only and does not authorize:

- live firewall read
- live firewall write
- live firewall apply
- live rollback
- live verify
- iptables-save
- iptables-restore
- real iptables adapter
- DB apply writes
- lock acquisition
- restore point writes
- customer NAT redirects
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram

## E2 Accepted Baseline

Phase 6-E2 is accepted as isolated/non-production evidence package and boundary planning only. E3 starts from that baseline and remains non-authorizing.

## E3 Scope

- evidence review checklist definition only
- non-authorizing gate language alignment
- deterministic checklist sections and review rules
- test guards that prevent accidental gate opening

## Review Checklist Contract

A Phase 6-E3 checklist review must be reproducible from repository artifacts and must yield a clear pass/fail rationale without host firewall mutation.

## Required Checklist Sections

1. phase/gate state verification
2. non-authorization verification
3. evidence completeness verification
4. safety flag verification
5. failure evidence verification
6. negative safety assertions verification
7. manual canary readiness boundary verification

## Evidence Review Rules

- use repository evidence and deterministic test assertions
- treat missing required evidence as checklist failure
- do not replace missing evidence with assumptions
- do not execute live firewall read/write/apply/rollback/verify actions

## Safety Flag Review

Review must confirm safety flags remain unchanged:

- production_traffic: none
- firewall_apply_allowed: no
- abuse_automation_allowed: no
- proxy_data_plane_allowed: limited_runtime_local_only

## Failure Evidence Review

If any checklist section fails, record failure evidence and keep Phase 6-E3 non-authorizing status unchanged. No fallback host interaction is allowed to “fix” evidence during review.

## Negative Safety Assertions

Checklist output must explicitly assert that no live firewall read/write/apply, no iptables-save/iptables-restore execution, no real adapter, no DB apply writes, no locks, no restore point writes, and no customer NAT/firewall rule authorization were introduced.

## Manual Canary Readiness Boundary

Phase 6-E3 may prepare checklist inputs for future manual canary gate definition only. It is not a canary execution phase and does not permit live apply behavior.

## Forbidden Host Interactions

During Phase 6-E3 review/checklist work:

- no live firewall read/write/apply/rollback/verify
- no iptables-save or iptables-restore execution
- no real iptables adapter integration
- no DB apply write, lock acquisition, or restore point write
- no customer NAT redirects or customer firewall rules

## Time Synchronization Warning

farm5 time synchronization has previously been reported as not confirmed.
This is not a Phase 6-E3 documentation/test blocker, but it must be resolved before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Abuse Requirement Preservation

The mandatory abuse requirement remains preserved:

- normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed

## Acceptance Criteria

- document exists and is indexed in required documentation maps
- wording remains planned + isolated/non-production only + non-authorizing
- phase state remains unchanged in `docs/PHASE_STATUS.md` Current State
- regression tests enforce non-authorization language and gate preservation

## Future Phase 6-F Entry Criteria

Phase 6-F may only be manual canary gate definition, not live apply execution, unless a later dedicated accepted gate explicitly says otherwise.
