# Phase 6 Dedicated Apply Gate Proposal/Review

Status: proposal/review contract only; documentation/test-only; non-authorizing

## A. Purpose

Define the review contract for a future dedicated Phase 6 apply gate before any live firewall interaction can be considered.

## B. Non-authorization statement

This document does not authorize dedicated apply gate acceptance, manual canary apply, no-customer apply, live firewall read/write/apply/rollback/verify, iptables-save, iptables-restore, real adapters, subprocess firewall calls, restore point writes, lock acquisition, DB writes, migrations, customer NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram.

## C. Required evidence before a future gate can be accepted

- farm5 source aligned with GitHub main
- VERSION consistency verified
- python -m pytest -q passed
- mpf phase-status or current phase safety gate OK
- firewall.apply_mode remains plan_only before authorization
- proxy.runtime_activation_allowed remains false before authorization
- production_traffic remains none before authorization
- firewall_apply_allowed remains no before authorization
- abuse_automation_allowed remains no before authorization
- no MPF/customer IPv4 firewall references
- no MPF/customer IPv6 firewall references
- no customer NAT redirects
- accepted limited runtime listeners remain local-only
- backend internal reachability preserved
- backend external exposure absent
- server time synchronization problem is either fixed and evidenced, or explicitly marked as a blocking condition for production-dependent phases
- operator has reviewed rollback/restore/lock/verify ordering
- operator has reviewed exact stop conditions
- operator has reviewed emergency rollback guidance
- operator has explicitly approved a future gate in docs/PHASE_STATUS.md in a separate PR

## D. Required design decisions before a future gate

- whether first future gate is live snapshot read only, no-customer apply, or canary apply
- exact boundary between read, write, apply, rollback, verify
- whether iptables-save is allowed before iptables-restore
- how restore points are created and where stored
- how firewall lock is acquired and released
- how failed verify results in rollback-plan or rollback
- how backend internal reachability and external non-exposure are verified
- how DB apply records are written only after successful future gate authorization
- how customer NAT/customer firewall rules remain blocked until explicitly authorized
- why abuse automation remains blocked until Phase 8

## E. Stop conditions

- Current State changed unexpectedly
- firewall_apply_allowed is yes before accepted gate
- production_traffic is enabled
- abuse_automation_allowed is yes before Phase 8
- live firewall read/write appears outside approved boundary
- iptables-save or iptables-restore appears outside approved boundary
- backend external exposure detected
- backend internal reachability broken
- customer NAT/customer firewall rules detected before authorization
- server time synchronization remains unfixed for production-dependent automation
- tests fail
- operator evidence is missing

## F. Future PR boundary

The actual gate-opening PR must be separate and must explicitly update docs/PHASE_STATUS.md with server evidence. This proposal/review PR must not change any current gate.
