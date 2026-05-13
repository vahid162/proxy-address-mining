# Phase 6 Live Snapshot Read Gate Proposal

Status: planned, documentation/test-only, non-authorizing (proposal only; non-authorizing)

## A. Purpose

Define the first future live read-only boundary needed before any apply/verify/rollback work.

## B. Non-Authorization

This PR does not authorize live firewall read or `iptables-save`. It only defines the future gate proposal.

It does **not** authorize:

- live firewall read
- `iptables-save`
- firewall write
- `iptables-restore`
- apply
- rollback
- verify that mutates state
- restore point write
- lock acquisition
- DB apply write
- DB apply record
- customer NAT redirects
- customer firewall rules
- production traffic
- usage automation
- abuse automation
- UI
- Telegram

## C. Future Gate Entry Criteria

A future live snapshot read gate may be proposed only when all criteria are met:

- separate acceptance in `docs/PHASE_STATUS.md`
- explicit operator approval
- farm5 evidence included
- `python -m pytest -q` passing
- current phase safety gate OK
- `mpf config validate` OK
- `mpf doctor` OK
- `mpf db status` OK
- `mpf proxy doctor` OK
- `firewall.apply_mode` remains `plan_only` before authorization
- `proxy.runtime_activation_allowed` remains `false`
- `production_traffic` remains `none`
- no customer NAT redirects
- no customer firewall rules
- no MPF/customer firewall references
- backend external exposure = NO
- backend internal reachability = OK
- time synchronization fixed, or explicitly treated as a blocker for production-dependent phases

## D. Future Allowed Operation If Accepted Later

If and only if a later gate is accepted in `docs/PHASE_STATUS.md`, the allowed boundary is:

- one explicit read-only live firewall snapshot operation
- controlled read of live firewall state through an approved adapter
- `iptables-save` only if explicitly accepted later in `docs/PHASE_STATUS.md`
- no parsing fallback to empty firewall
- no guessed firewall state
- no mutation of firewall/runtime/DB state
- output must be human-readable and JSON
- errors must be fail-closed
- live snapshot failure must not be treated as clean/empty firewall
- result feeds planner/diff only
- final decision remains BLOCKED for apply until a later apply gate

## E. Stop Conditions

Stop and block if any of the following occurs:

- Current State changes unexpectedly
- `firewall_apply_allowed` becomes `yes`
- `production_traffic` is enabled
- live write/apply/rollback/verify appears
- `iptables-restore` appears
- customer NAT/customer firewall rules appear
- backend external exposure appears
- backend internal reachability breaks
- tests fail
- operator evidence is missing

## F. Next Step After This Proposal

After this proposal is merged, the next implementation PR may add read-only live snapshot service/adapter scaffolding only if `docs/PHASE_STATUS.md` remains non-authorizing and the implementation is fail-closed. It must still not execute live read unless a later gate explicitly accepts it.

## G. Abuse Invariant

Keep unchanged:

- `normal -> over_tracking -> over_grace -> hard`
- sustained miner-abuse hardens after about 3600 seconds
- farms-over alone must not harden
- worker-over alone must not harden
- all active customers in enabled lanes must be covered
- no silent skip is allowed
- abuse automation remains forbidden until Phase 8
