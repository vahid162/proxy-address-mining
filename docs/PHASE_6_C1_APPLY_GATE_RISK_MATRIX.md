# Phase 6-C1 — Apply Gate Risk Matrix + Operator Approval Checklist

Status: documentation/contract/test-only (non-executable)

## Purpose

Phase 6-C1 defines a structured risk matrix and operator approval checklist for a **future** dedicated live apply gate review.

This document exists to reduce operator ambiguity, force explicit evidence review, and prevent accidental gate drift.

## Explicit Non-Authorization

This document does not authorize live apply.

The current gate remains unchanged:

```text
firewall_apply_allowed: no
production_traffic: none
abuse_automation_allowed: no
```

The following remain forbidden in current state:

- mpf firewall apply remains forbidden
- mpf firewall rollback remains forbidden
- mpf firewall verify remains forbidden
- iptables-save execution remains forbidden
- iptables-restore execution remains forbidden
- live firewall read/write remains forbidden
- lock acquisition remains forbidden
- restore point write remains forbidden
- customer NAT redirects remain forbidden
- customer firewall rules remain forbidden

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
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
```

## Risk Matrix

Each row includes: risk_id, severity (CRITICAL|HIGH|MEDIUM|LOW), detection evidence, blocker status, required mitigation, acceptance owner.

| risk_id | risk | severity | detection evidence | blocker status | required mitigation | acceptance owner |
|---|---|---|---|---|---|---|
| R001 | backend direct external exposure | CRITICAL | backend exposure report shows public inbound path | BLOCKER | prove external_backend_exposed = NO with reviewed evidence bundle | Security reviewer + operator |
| R002 | internal backend reachability failure | CRITICAL | backend reachability report shows failed internal path | BLOCKER | prove internal_backend_reachable = OK and required local/internal paths are healthy | Runtime/network reviewer |
| R003 | stale or missing restore artifact | HIGH | artifact hash/timestamp missing or stale | BLOCKER | refresh and re-review restore artifact provenance and hashes | Operator + change manager |
| R004 | rollback strategy not reviewed | HIGH | no signed rollback strategy review evidence | BLOCKER | complete rollback strategy review and sign-off | Operator lead |
| R005 | apply-readiness contract not reviewed | HIGH | missing apply-contract/preflight review markers | BLOCKER | review Phase 6-B apply-readiness artifacts and record sign-off | Gate reviewers |
| R006 | evidence bundle missing or stale | HIGH | evidence package incomplete/outdated | BLOCKER | regenerate/re-collect evidence and verify timestamps | Operator |
| R007 | version/changelog/docs mismatch | MEDIUM | version values differ across version sources/changelog/docs | BLOCKER | synchronize version and documentation references | Maintainer |
| R008 | server time synchronization not fixed before production-dependent jobs | MEDIUM | time sync report unresolved | SOFT WARNING | resolve synchronization before production-dependent automation | Ops owner |
| R009 | unreviewed customer NAT redirect | CRITICAL | any unreviewed customer NAT redirect intent | BLOCKER | reject until formally reviewed in future accepted gate | Security reviewer |
| R010 | unreviewed customer firewall rule | CRITICAL | any unreviewed customer firewall rule intent | BLOCKER | reject until formally reviewed in future accepted gate | Security reviewer |
| R011 | hidden fallback from DB-backed input to config-only | HIGH | planner/evidence source ambiguity | BLOCKER | make data source explicit and reviewed | Service owner |
| R012 | final_verdict accidentally OK while apply is forbidden | CRITICAL | report shows final_verdict=OK for live apply path | BLOCKER | enforce BLOCKED outcome while apply gate is forbidden | Gate reviewers |
| R013 | applyable accidentally true while apply is forbidden | CRITICAL | readiness output indicates applyable=true | BLOCKER | force applyable=false until dedicated gate accepted | Service owner |
| R014 | abuse coverage weakened | CRITICAL | abuse contract no longer enforces required state machine/rules | BLOCKER | restore full abuse requirement contract and tests | Safety reviewer |
| R015 | customer silently excluded from future abuse scan | HIGH | evidence shows active customer scan gaps without approved exemption | BLOCKER | require full coverage or explicit exemption reason + expiry | Abuse reviewer |
| R016 | public v2rayA UI exposure | CRITICAL | listener/exposure report shows public v2rayA path | BLOCKER | restrict to local-only binding and verify | Security reviewer |
| R017 | public backend exposure | CRITICAL | listener/exposure report shows public backend path | BLOCKER | close public path and verify non-exposure | Security reviewer |
| R018 | command examples inconsistent with actual CLI syntax | LOW | docs/tests show stale or invalid command examples | SOFT WARNING | align docs/examples with actual CLI (`--output json`) | Documentation owner |

## Operator Approval Checklist

All checklist items must be explicitly reviewed:

- [ ] phase gate reviewed
- [ ] Phase 6-B evidence reviewed
- [ ] Phase 6-C0 runbook reviewed
- [ ] risk matrix reviewed
- [ ] backend exposure NO
- [ ] internal backend reachability OK
- [ ] restore/rollback strategy reviewed
- [ ] canary target reviewed
- [ ] abuse future requirement preserved
- [ ] version sources synchronized
- [ ] changelog updated
- [ ] docs examples match actual CLI
- [ ] tests pass

## Required Evidence Before Approval

Required evidence set:

- phase-status output proving `firewall_apply_allowed: no`, `production_traffic: none`, `abuse_automation_allowed: no`
- Phase 6-B offline planner/diff/doctor/apply-contract/package/preflight/evidence outputs
- Phase 6-C0 apply gate readiness runbook review evidence
- backend exposure classification proving external non-exposure
- internal backend reachability classification proving required internal paths are healthy
- version alignment evidence (VERSION, package version, changelog, docs references)
- test evidence (`python -m pytest -q`)

If firewall JSON examples are used, they must use `--output json`.

## Required Reviewer/Operator Sign-off Categories

- Safety gate reviewer
- Firewall/domain reviewer
- Runtime/network reviewer
- Security reviewer (exposure/reachability)
- Operator/release owner
- Documentation/test reviewer

## Hard Blockers

Immediate BLOCKED state if any occurs:

- backend direct external exposure
- internal backend reachability failure
- missing/stale restore or rollback readiness artifacts
- apply-readiness contract not reviewed
- hidden fallback from DB-backed input to config-only
- final_verdict accidentally OK while apply is forbidden
- applyable accidentally true while apply is forbidden
- any unreviewed customer NAT redirect
- any unreviewed customer firewall rule
- abuse coverage weakened
- customer silently excluded from future abuse scan
- public v2rayA UI exposure
- public backend exposure

## Soft Warnings

Warnings requiring remediation plan before any future gate review:

- time synchronization unresolved for production-dependent jobs
- command examples inconsistent with actual CLI syntax
- minor documentation/version drift without gate mutation

## Rollback Readiness Checks

Before any future live gate review:

- rollback strategy is reviewed and signed
- rollback artifacts/hashes are current and attributable
- rollback trigger conditions are explicit
- rollback ownership/escalation path is documented

## Canary Readiness Checks

Before any future canary approval:

- canary target and blast radius are reviewed
- pre-canary evidence set is complete
- stop conditions are acknowledged by operator/reviewers
- operator checklist is complete and signed

## Backend Exposure/Reachability Checks

Required split must remain:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

## Abuse Requirement Preservation Checks

Mandatory future abuse state machine remains unchanged:

```text
normal -> over_tracking -> over_grace -> hard
```

Required rules remain unchanged:

- all active customers in all enabled lanes must eventually be scanned
- no silent skip is allowed
- exemption requires reason and expiry
- farms-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- hard creates restore point and policy backup
- hard uses firewall plan/apply/verify path after the relevant apply gate
- hard flushes affected conntrack scope after the relevant runtime gate
- manual unhard is audited

## Version/Documentation Alignment Checks

- `VERSION`, `pyproject.toml`, and `mpf/__init__.py` versions are synchronized
- changelog top entry matches current version/date and scope
- Phase status next-step wording matches accepted evidence state
- no stale firewall CLI examples using `--json`

## Stop Conditions

Stop and revise immediately if any of the following appears:

- live firewall apply/rollback/verify behavior
- `iptables-save` or `iptables-restore` execution path
- live firewall read dependency
- lock acquisition
- restore point or rollback artifact write behavior
- database/apply state mutation
- customer NAT or customer firewall live mutation
- traffic-changing behavior
- any weakening of one-hour abuse requirement

## Final Decision States

Allowed decision states for this Phase 6-C1 contract:

- BLOCKED
- READY_FOR_FUTURE_GATE_REVIEW
- REJECTED_NEEDS_REWORK

Current state in Phase 6-C1 is:

```text
BLOCKED
```

Live apply remains forbidden until a dedicated apply gate is explicitly accepted.
