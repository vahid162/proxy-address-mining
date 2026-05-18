# AI Phase 10 Task — Session / Worker / Policy / Share Timeline

Status: Current / Planning-Readiness / Backend-Readiness

## Current boundary
- Phase 10A/10B/10C readiness contracts are implemented in this PR as safe, non-mutating backend-readiness surfaces.
- Current accepted phase remains Phase 9 — Check / Report / Diagnostics accepted on farm5.
- Current working phase remains Phase 10 — Session / Worker / Policy / Share Timeline planning/readiness.
- Fresh farm5 0.1.132 sync/test evidence is recorded for this implementation package.
- After this PR is merged, fresh farm5 0.1.133 sync/test evidence is required before accepting Phase 10D/10E work.

## Implemented report-only outputs
- `mpf phase10 readiness --output json`
- `mpf phase10 session-readiness --output json`
- `mpf phase10 worker-policy-readiness --output json`
- `mpf phase10 share-timeline-readiness --output json`
- `mpf phase10 enforcement-boundary --output json`
- `mpf phase10 session-model-readiness --output json`
- `mpf phase10 worker-identity-readiness --output json`
- `mpf phase10 worker-policy-contract-readiness --output json`
- `mpf phase10 implementation-readiness --output json`

## Next target
- Phase 10D — Share Timeline readiness.
- Phase 10E — Collector dry-run gate readiness.
- Do not create another evidence-only PR unless it is required to record a post-merge farm5 sync/test boundary.
- Do not jump directly to UI, Telegram, worker enforcement, or production/customer activation.
- Controlled CLI canary remains in Phase 11 after Phase 10 final acceptance.

## Forbidden in the current Phase 10 boundary
No real worker runtime, no background worker loop, no scheduler/timer, no collector daemon, no live share ingestion, no production DB execution, no enforcement, no firewall apply, no iptables-restore, no customer NAT/customer firewall rules, no hard/soft block, no pause automation, no production traffic, no UI, no Telegram.

## Abuse invariant preservation
normal -> over_tracking -> over_grace -> hard remains mandatory.
Sustained hardening remains about 3600s.
farms-over alone / worker-over alone / missing-stale evidence / DB-firewall failure must not harden.
No silent skip is allowed.
This PR must not start or authorize abuse automation.

## Phase 10A/10B/10C implementation note
- This PR is not evidence-only.
- It implements Phase 10A/10B/10C readiness contracts.
- It does not authorize runtime.
- It does not authorize scheduler/timer.
- It does not authorize collector daemon.
- It does not authorize production traffic.
- It does not authorize firewall apply.
- It does not authorize worker enforcement.
- It does not authorize customer NAT/customer firewall rules.
- It does not authorize abuse automation.
