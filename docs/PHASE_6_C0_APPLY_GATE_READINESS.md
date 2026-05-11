# Phase 6-C0 — Live Apply Gate Readiness Contract + Manual Canary Runbook

Status: contract-only documentation for future apply gate readiness

## Purpose

Phase 6-C0 defines the **readiness contract** and **manual canary runbook** that must be satisfied before any future dedicated live-apply gate can be accepted.

This step is documentation/contract/test only. It prepares review criteria and operator evidence expectations.

## Explicit Non-Authorization

This document **does not authorize live apply**.

Current safety gate remains unchanged:

```text
current_accepted_phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
current_working_phase: Phase 6 — Firewall Planner
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
```

## Current Forbidden Behavior

The following remain forbidden in current phase and this document does not change that:

- mpf firewall apply remains forbidden
- mpf firewall rollback remains forbidden
- mpf firewall verify remains forbidden
- iptables-save execution remains forbidden
- iptables-restore execution remains forbidden
- live firewall read/write remains forbidden
- lock acquisition remains forbidden
- restore point write remains forbidden
- rollback artifact filesystem write remains forbidden
- database write for apply/rollback/preflight/evidence remains forbidden
- customer NAT redirect creation remains forbidden
- customer firewall rule creation remains forbidden

## Required Prerequisites Before Any Future Live Apply

All prerequisites below must be reviewed and accepted before a future apply gate can be proposed:

- Phase 6-B evidence bundle accepted
- server time synchronization fixed before production-dependent jobs
- firewall.apply_mode remains plan_only until explicit gate change
- backend direct external exposure remains NO
- internal backend reachability remains OK
- no public v2rayA UI exposure
- no public backend exposure
- no customer NAT redirect until reviewed apply gate
- no customer firewall rules until reviewed apply gate
- restore point contract accepted
- lock contract accepted
- verify contract accepted
- rollback contract accepted
- evidence bundle accepted
- operator has reviewed generated restore payload
- rollback artifact strategy is defined and testable
- canary target is non-production or explicit reviewed test customer only
- production traffic remains none until explicitly accepted

## Required Manual Canary Flow (Future Gate Only)

Manual canary phases for a future dedicated apply gate:

1. pre-canary review
2. offline evidence capture
3. explicit live snapshot capture only after future gate allows it
4. restore point creation only after future gate allows it
5. lock acquisition only after future gate allows it
6. atomic apply only after future gate allows it
7. verify
8. rollback readiness check
9. post-canary evidence
10. acceptance or rollback decision

In Phase 6-C0, this runbook is contract-only and non-executable.

## Required Evidence Before Canary

Operator review set must include:

- accepted offline plan/diff/doctor/preflight/evidence outputs
- backend exposure classification report proving external non-exposure
- backend reachability evidence proving internal path health
- explicit apply-readiness contract showing blocked_for_live_apply prior to gate acceptance
- restore payload review acknowledgment
- rollback artifact strategy document and test evidence
- current gate evidence showing `firewall_apply_allowed: no` and `production_traffic: none`

## Required Evidence During Canary (Future Gate Only)

When and only when a future gate allows live steps, operator evidence must capture:

- exact command history with UTC timestamps
- snapshot hash and restore payload hash
- lock lifecycle evidence
- verify results against expected desired state
- backend reachability/exposure status throughout canary
- explicit anomaly log and operator decisions

## Required Evidence After Canary

Post-canary evidence package must include:

- final acceptance or rollback decision with rationale
- before/after diff summary
- verify summary and unresolved warnings/errors
- safety flag summary for all canary steps
- signed operator checklist

## Required Rollback Readiness

Before any future live apply:

- rollback readiness must be proven by artifact availability and restore procedure review
- rollback trigger conditions must be explicit and operator-known
- rollback command path must be testable in approved non-production conditions
- rollback decision authority and escalation path must be documented

## Required Stop Conditions

Stop immediately and rollback/revise if any occurs:

- backend direct external exposure detected
- internal backend reachability failure
- verify mismatch with desired state
- unexpected traffic impact
- missing restore payload/snapshot/hash evidence
- lock contract inconsistency
- any step bypasses approved service-layer contract

## Required Server Commands for Operator Review

For current Phase 6-C0 (inspection-only), minimum operator review commands include:

```bash
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor
mpf firewall plan --json
mpf firewall diff --json
mpf firewall doctor --json
mpf firewall apply-contract --json
mpf firewall package --json
mpf firewall preflight --json
mpf firewall evidence --json
python -m pytest -q
```

These commands are review-only in current phase and do not authorize apply/rollback/verify execution.

## Required Failure Handling

For any failed prerequisite/check:

- mark canary status as blocked
- record failure reason and remediation owner
- preserve gathered evidence without mutation retries
- require explicit re-review after remediation
- do not continue to any live step without approved gate acceptance

## Future Audit / Restore / Snapshot Expectations

For a future dedicated apply gate (not this phase):

- every dangerous action must be audited
- restore point creation must be mandatory before live apply
- live snapshot capture must be explicit and attributable
- rollback artifacts and verification results must be auditable
- apply/rollback lifecycle must be event-linked end-to-end

## Abuse Future Requirement (Unchanged)

This Phase 6-C0 contract does not weaken abuse requirements.

Mandatory future state machine remains:

```text
normal -> over_tracking -> over_grace -> hard
```

Rules that must remain true:

- all active customers in all enabled lanes must eventually be scanned
- no silent skip is allowed
- exemption requires reason and expiry
- farms-over alone must not harden
- sustained miner-abuse hardens after about 3600 seconds
- hard creates restore point and policy backup
- hard uses firewall plan/apply/verify path after the relevant apply gate
- hard flushes affected conntrack scope after the relevant runtime gate
- manual unhard is audited
