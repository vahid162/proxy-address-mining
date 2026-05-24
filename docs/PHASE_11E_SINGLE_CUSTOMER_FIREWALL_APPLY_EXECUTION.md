# Phase 11E single-customer firewall apply execution

Purpose: controlled execution path for exact candidate `limited-btc-001 / btc / 20101 / 172.18.0.3:60010`.

Prerequisites: 0.1.203 sync/test pass, 0.1.203 apply-gate READY evidence, exact hashes.

Hard boundaries: dry-run default, explicit execute flags+env only, no production/miner traffic acceptance, no Phase 11 acceptance, preserve canary 20001, only 20101 scope.

Dry-run command: `mpf production single-customer-firewall-apply-execute --apply-gate-json <file> ... --no-execute --output json`

Execute example needs env vars:
- `MPF_PHASE11_SINGLE_CUSTOMER_APPLY_EXECUTION=allow`
- `MPF_PHASE11_SINGLE_CUSTOMER_APPLY_TARGET=limited-btc-001:btc:20101:172.18.0.3:60010`
- `MPF_PHASE11_SINGLE_CUSTOMER_APPLY_I_UNDERSTAND_HOST_FIREWALL_MUTATION=allow`

Required pre-apply artifacts: pre-apply snapshot, restore point, operator lock, rollback artifact.
Required post-apply evidence: post-apply snapshot, 20101 verify, canary-preservation verify, runtime-path evidence.
Rollback/review is mandatory on any failure or partial-apply suspicion. Production/miner traffic remains not accepted until post-apply runtime evidence PR.


Boundary clarification (0.1.204):
- This package primarily validates/applies exact 20101 NAT redirect and preserves existing 20001 canary artifact.
- MPFC_20101 rules are scoped customer filter primitives unless/until a later verified hook/enforcement step proves traffic-path attachment.
- This PR does not claim full filter-enforcement acceptance without explicit post-apply hook/path evidence.
