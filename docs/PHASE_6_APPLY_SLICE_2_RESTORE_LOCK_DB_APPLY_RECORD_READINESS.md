# Phase 6 Apply Slice 2 — Restore Point + Lock + DB Apply Record Readiness

Status: planned, documentation/test-only, non-authorizing

## Purpose

Define planning-only contracts and future entry criteria for restore point readiness, lock readiness, and DB apply record readiness.

## Scope

This step is documentation/test-only. It defines boundaries and ordering contracts for future gates, without implementing runtime behavior.

## Non-Authorization Statement

This document does not authorize:

- live firewall read
- iptables-save
- live firewall write
- live firewall apply
- live rollback
- live verify
- iptables-restore
- real iptables adapter
- subprocess firewall calls
- restore point writes
- lock acquisition
- DB apply writes
- DB apply records
- migration/schema changes
- customer NAT redirects
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram

## Current Gate Snapshot

Authoritative source is `docs/PHASE_STATUS.md`. Current accepted/working gate remains unchanged.

## Relationship To Apply Slice 1

- Apply Slice 1 defined future live snapshot readiness only.
- Apply Slice 1 did not authorize live snapshot reads.
- Apply Slice 2 defines future restore point, lock, and DB apply record readiness only.
- Apply Slice 2 depends on the same non-authorizing boundary.
- Apply Slice 2 must not mark Apply Slice 1 accepted.
- Apply Slice 2 must not create acceptance evidence for Apply Slice 1.

## Why Restore/Lock/DB Apply Record Readiness Exists

Future apply safety requires deterministic recovery, overlap prevention, and auditable apply lifecycle evidence.

## Future Restore Point Entry Criteria

- separate accepted gate in docs/PHASE_STATUS.md
- explicit operator approval
- live snapshot read gate already accepted later, if needed
- time synchronization fixed and evidenced
- python -m pytest -q passes
- bash scripts/verify_current_phase_gate.sh passes
- mpf --version matches repository version
- mpf phase-status matches docs/PHASE_STATUS.md Current State
- mpf config validate OK
- mpf doctor OK
- mpf db status OK
- mpf proxy doctor OK
- backend external exposure = NO
- backend internal reachability = OK
- no customer NAT redirects before gate
- no customer firewall rules before gate
- no MPF/customer firewall references before gate
- firewall.apply_mode remains plan_only until explicit accepted gate changes it
- proxy.runtime_activation_allowed remains false until explicit accepted gate changes it
- production traffic remains none
- restore point metadata contract is defined
- restore point checksum/integrity expectations are defined
- restore point failure blocks future apply
- restore point must never be guessed after apply

## Future Lock Entry Criteria

- separate accepted gate in docs/PHASE_STATUS.md
- lock scope documented
- lock owner identity documented
- lock timeout policy documented
- stale lock handling documented
- failure to acquire lock blocks future apply
- lock release behavior documented
- lock must cover apply and rollback
- lock must prevent overlap with jobs and manual operations
- no lock acquisition is allowed in this documentation step

## Future DB Apply Record Entry Criteria

- separate accepted gate in docs/PHASE_STATUS.md
- DB record schema already exists or future migration is separately accepted
- no migration is introduced by this PR
- apply record lifecycle states are defined
- failure states are defined
- rollback references are defined
- correlation_id requirements are defined
- operator identity requirements are defined
- plan_json/hash/payload references are defined
- DB write failure blocks future apply success reporting
- no DB apply writes are allowed in this documentation step

## Future Apply Ordering Contract

Future ordering only (non-implementing contract):

1. validate config
2. validate DB state
3. load desired model
4. obtain live snapshot only after future accepted live snapshot gate
5. generate plan
6. reject plan with errors
7. create restore point only after future accepted restore point gate
8. acquire lock only after future accepted lock gate
9. create DB apply record only after future accepted DB write gate
10. render payload
11. apply atomically only after future accepted apply gate
12. verify only after future accepted verify gate
13. update apply record
14. create event/audit
15. release lock

This ordering is a future contract only. No step above is authorized now if it requires live reads/writes, DB writes, locks, restore points, iptables-save, iptables-restore, real adapters, or runtime mutation.

## Failure Behavior For Future Restore/Lock/DB Record Steps

- restore point failure must block future apply
- lock acquisition failure must block future apply
- DB apply record creation failure must block future apply
- DB apply record update failure must not falsely report success
- no destructive cleanup may run after restore/lock/record failure
- rollback guidance must not guess from current DB state
- partial future failure must be operator-visible and auditable once the relevant gate exists

## Integrity And Idempotency Requirements

- restore point checksum required later
- payload hash required later
- source snapshot hash required later
- apply attempt must have correlation_id later
- duplicate apply attempts must not produce ambiguous success later
- stale restore artifacts must not be used silently later
- operator-visible evidence must be reproducible later

## No-Write Boundary For This Step

- no restore point row is written
- no firewall_snapshot row is written
- no firewall_apply row is written
- no scheduler_lock row is written
- no event/audit row is written
- no filesystem restore artifact is written
- no lock file is created
- no subprocess command is called
- no iptables-save or iptables-restore is called
- no schema migration is added

## Operator Approval Requirements

Any future authorization must use explicit named approvers and dated approval scope before runtime mutation is proposed.

## Time Synchronization Requirement

Time synchronization must be fixed and evidenced before any future restore/lock/DB apply-write authorization.

## Backend Exposure Preconditions

Future apply path remains blocked unless `external_backend_exposed = NO` and `internal_backend_reachable = OK` are evidenced.

## Local-only Runtime Preconditions

Current local-only/runtime-limited gate remains mandatory until an explicit accepted gate changes it.

## Customer/NAT Preconditions

No customer NAT redirects and no customer firewall rules may be introduced by this step.

## Safety Stop Conditions

Stop if any change introduces authorization or implementation of runtime mutation before explicit accepted gates.

## Required Evidence Before Any Future Authorization

Future authorization must include gate verification, version alignment, doctor/config/db/proxy checks, backend exposure evidence, no NAT/customer firewall evidence, and production-traffic-none evidence.

## Abuse Invariant Preservation

- normal -> over_tracking -> over_grace -> hard
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed
- abuse automation remains forbidden until Phase 8
- future hard/unhard still requires restore point, policy backup, firewall plan/apply/verify, scoped conntrack flush, event, and audit only after the relevant future gates

## Boundary With Apply Slice 3

- Apply Slice 3 may later define Controlled No-Customer Apply Harness planning/contracts.
- Slice 2 does not authorize no-customer apply.
- Slice 2 does not authorize fake-to-real adapter transition.
- Slice 2 does not authorize customer NAT or customer firewall rules.
- Slice 2 does not authorize production traffic.

## Acceptance Criteria For This Documentation Step

- document exists and is indexed
- status remains planned/documentation-test-only/non-authorizing
- current gate state remains unchanged
- next planned wording points to Apply Slice 2 readiness boundary
- no runtime/firewall/db mutation behavior is introduced
- abuse invariant remains explicit and unchanged
