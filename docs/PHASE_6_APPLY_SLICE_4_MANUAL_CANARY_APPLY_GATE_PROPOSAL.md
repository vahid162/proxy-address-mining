# Phase 6 Apply Slice 4 — Manual Canary Apply Gate Proposal

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define the future manual canary apply gate proposal boundary without authorizing manual canary apply, no-customer apply, live firewall reads/writes, DB writes, locks, restore points, or runtime mutation.

## Scope

This step is documentation/test-only and test-contract only. It introduces no runtime behavior.

## Non-Authorization Statement

This document does not authorize:

- manual canary apply
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

## Manual Canary Proposal Contract

- Manual canary may only be proposed later after a separate accepted gate.
- Manual canary must require explicit operator approval.
- Manual canary must require server sync evidence.
- Manual canary must require passing pytest.
- Manual canary must require passing current phase gate script.
- Manual canary must require mpf --version matching repository version.
- Manual canary must require mpf phase-status matching docs/PHASE_STATUS.md Current State.
- Manual canary must require config/doctor/db/proxy checks OK.
- Manual canary must require backend external exposure = NO.
- Manual canary must require backend internal reachability = OK.
- Manual canary must require no MPF/customer firewall refs.
- Manual canary must require no customer NAT redirects.
- Manual canary must require production_traffic = none.
- Manual canary must require time synchronization fixed and evidenced.
- Manual canary must not include customer traffic until a later explicit customer traffic gate.

## Required Preconditions Before Any Future Manual Canary

Any future manual canary proposal must be tied to a separate accepted gate and explicit operator sign-off with complete safety evidence before any runtime behavior is even proposed.

## Stop Conditions

Any future canary must stop immediately if:

- Current State gate does not match docs/PHASE_STATUS.md
- time sync is not fixed
- tests fail
- current phase gate fails
- backend is externally exposed
- customer NAT redirects exist
- customer firewall rules exist
- MPF/customer firewall refs exist unexpectedly
- production traffic is enabled
- firewall.apply_mode is not plan_only before explicit gate
- proxy.runtime_activation_allowed is true before explicit gate

## Abuse Invariant Preservation

- normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed
- abuse automation remains forbidden until Phase 8

## Boundary With Future Dedicated Apply Gate

- Slice 4 does not accept or open the dedicated apply gate.
- Slice 4 only defines proposal requirements.
- A future dedicated apply gate must be separate and explicitly accepted.
- No production/customer traffic is authorized by Slice 4.
- No real firewall mutation is authorized by Slice 4.

## Acceptance Criteria For This Documentation/Test Step

- document exists and is indexed
- status remains planned, documentation/test-only, non-authorizing
- Current State in `docs/PHASE_STATUS.md` remains unchanged
- Slice 4 is documented only and not marked accepted
- next operational step is batch server sync/review for Slice 3 and Slice 4 documentation/test-only boundaries
- no runtime/firewall/DB behavior is introduced
