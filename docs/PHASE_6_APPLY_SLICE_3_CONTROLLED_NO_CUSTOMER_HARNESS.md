# Phase 6 Apply Slice 3 — Controlled No-Customer Apply Harness

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define the future controlled no-customer harness contract without authorizing any real no-customer apply, live firewall read/write, DB write, lock, restore point, or runtime mutation.

## Scope

This step is documentation/test-only and test-contract only. It introduces no runtime behavior.

## Non-Authorization Statement

This document does not authorize:

- no-customer apply
- live firewall read
- live firewall write
- live firewall apply
- live rollback
- live verify
- iptables-save
- iptables-restore
- real iptables adapter
- subprocess firewall calls
- restore point writes
- lock acquisition
- DB apply writes
- DB apply records
- migrations/schema changes
- customer NAT redirects
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram

## Current Gate Snapshot

Authoritative source: `docs/PHASE_STATUS.md`.

Current accepted/working gate remains unchanged and non-authorizing.

## Controlled No-Customer Harness Contract

- The future harness may only be proposed later after a separate accepted gate.
- The future harness must be isolated from customer traffic.
- The future harness must not create customer NAT redirects.
- The future harness must not create customer firewall rules.
- The future harness must not touch production traffic.
- The future harness must have deterministic plan -> payload -> simulated apply -> simulated verify ordering.
- The future harness must have explicit failure classification.
- The future harness must remain fake/no-op until a separate real adapter gate is accepted.
- The future harness must not transition from fake/no-op to real adapter in this slice.

## Required Safety Preconditions For Any Future Harness

Any future harness proposal must be tied to a separate accepted gate, explicit operator approval scope, and passing documentation/test safety checks before any runtime behavior is even proposed.

## Failure Behavior

- simulated apply failure must not change runtime state
- simulated verify failure must not trigger real rollback
- no destructive cleanup may run
- failed harness result must be operator-visible in future reports
- no success may be reported if simulated verify fails
- no fallback to real adapter is allowed

## Abuse Invariant Preservation

- normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed
- abuse automation remains forbidden until Phase 8

## Boundary With Apply Slice 4

- Apply Slice 4 may later define Manual Canary Apply Gate Proposal.
- Slice 3 does not authorize manual canary apply.
- Slice 3 does not authorize no-customer apply.
- Slice 3 does not authorize real runtime apply.
- Slice 3 does not authorize customer NAT/customer firewall rules.
- Slice 3 does not authorize production traffic.

## Acceptance Criteria For This Documentation/Test Step

- document exists and is indexed
- status remains planned, documentation/test-only, non-authorizing
- Current State in `docs/PHASE_STATUS.md` remains unchanged
- Slice 3 is documented only and not marked accepted
- next planned sub-step is Apply Slice 4 — Manual Canary Apply Gate Proposal
- no runtime/firewall/DB behavior is introduced
