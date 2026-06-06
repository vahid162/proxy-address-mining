# FIREWALL

Status: Draft v1

This document defines the firewall model and safety contract for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

## Goal

The firewall system must safely expose customer ports, enforce customer policy, redirect allowed traffic to lane backend ports, account for usage/rejects, and prevent direct backend exposure.

The target data path is:

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

The first lane is BTC:

```text
BTC customer ports -> backend 60010
```

## Core Rule

Firewall changes must be model-driven.

Forbidden production pattern:

```text
run one iptables command directly for each customer action
```

Required production pattern:

```text
read DB/config
  -> build desired firewall model
  -> compare desired with live firewall
  -> generate plan
  -> show human diff
  -> show JSON diff
  -> create restore point
  -> backup live firewall
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event
  -> rollback or rollback-plan on failure
```


## Phase 6-E2 Isolated Harness Evidence Package / Boundary Planning (Isolated/Non-Production Only)

Phase 6-E2 is evidence package and boundary planning only via `docs/PHASE_6_E2_ISOLATED_HARNESS_EVIDENCE_PACKAGE.md`.

- it does not authorize live apply
- it does not authorize live firewall read/write
- it does not authorize `iptables-save` or `iptables-restore`
- it does not authorize real iptables adapters
- it does not authorize DB apply writes
- it does not authorize lock acquisition
- it does not authorize restore point writes
- it does not authorize customer NAT redirects
- it does not authorize customer firewall rules

## Phase 6-D1 Live-Apply Boundary Contract (Documentation/Test-Only)

Phase 6-D1 only defines boundaries via `docs/PHASE_6_D1_LIVE_APPLY_BOUNDARY.md`.

- live apply remains forbidden.
- iptables-save and iptables-restore remain forbidden before explicit gate acceptance.
- D1 is non-authorizing and documentation/test-only.

## Phase 6-C0 Note (Readiness Contract + Manual Canary Runbook Only)

Phase 6-C0 adds a live apply gate readiness contract and manual canary runbook only.

- it does not implement apply
- it does not implement rollback
- it does not implement verify
- it does not execute `iptables-save`
- it does not execute `iptables-restore`
- it does not acquire locks
- it does not write restore points
- it does not change firewall/NAT/runtime state
- live apply remains forbidden until a dedicated apply gate is explicitly accepted

## Phase 6-B6 Note (Offline Acceptance Evidence Bundle Only)

Phase 6-B6 adds a single inspection-only acceptance evidence bundle via `mpf firewall evidence`.

- summarizes planner, diff/doctor contract status, restore artifact, apply contract, package, optional rollback artifact, and preflight
- remains artifact-only and inspection-only
- does not permit live apply or live rollback
- does not execute `iptables-save` or `iptables-restore`
- does not acquire locks
- does not write restore points, rollback files, or database rows
- final verdict remains `BLOCKED` while current phase forbids live apply

## Phase 6-B1/B2 Note (Offline Artifact/Contract Only)

Phase 6-B2 adds offline contracts for restore point, lock, verify, rollback, and apply-readiness inspection only.

- live firewall apply remains forbidden
- `iptables-save` execution remains forbidden
- `iptables-restore` execution remains forbidden
- apply/rollback/verify execution commands are not exposed in this phase

## Phase 6-B1 Note (Offline Artifact Only)

Phase 6-B starts apply-contract design only.

- renderer output is offline artifact-only (`mpf firewall render-restore`)
- live firewall apply remains forbidden
- `iptables-restore` execution remains forbidden
- this step does not change firewall/NAT/runtime live state

## Supported Backend

Initial backend:

```text
iptables
```

Allowed apply mechanism:

```text
iptables-save
iptables-restore
```

Future backend:

```text
nftables
```

Do not start direct nftables support until iptables planner is stable and tested.

## No Direct Mutation Rule

Interfaces and jobs must never directly mutate firewall state.

Forbidden:

```text
CLI -> iptables -A ...
CLI -> iptables -D ...
UI -> iptables command
Telegram -> shell command
abuse job -> direct maxconn chain edit
customer service -> direct subprocess iptables call
```

Allowed:

```text
interface/job
  -> service layer
  -> firewall_service
  -> firewall planner
  -> firewall adapter
```

Direct `iptables` commands may be used only for diagnostics, isolated tests, or generated emergency restore scripts.

## Apply Modes

Config:

```yaml
firewall:
  backend: iptables
  apply_mode: plan_only
```

Allowed values:

```text
plan_only
manual_apply
atomic_apply
```

### plan_only

- Generate plans and diffs only.
- No live mutation.
- Required for Phase 0 and Phase 1.

### manual_apply

- Generate restore/apply artifacts.
- Operator may apply generated artifact manually.
- Useful for first canary and review.

### atomic_apply

- Application may run atomic apply through the firewall adapter.
- Requires all safety gates and tests.

## Chain Model

Initial iptables model should use explicit MPF-owned chains.

Recommended chain naming:

```text
MPF_INPUT
MPF_CUSTOMERS
MPF_GUARD
MPF_ACCT_IN
MPF_ACCT_OUT
MPF_NAT_PRE
MPF_NAT_POST
MPFC_<port>
MPFO_<port>
MPFL_<lane>
```

Meaning:

- `MPF_INPUT`: top-level filter entrypoint
- `MPF_CUSTOMERS`: customer dispatch chain
- `MPF_GUARD`: backend exposure guard
- `MPF_ACCT_IN`: incoming accounting
- `MPF_ACCT_OUT`: outgoing accounting, if needed
- `MPF_NAT_PRE`: NAT prerouting entrypoint
- `MPF_NAT_POST`: NAT postrouting entrypoint, if needed
- `MPFC_<port>`: per-customer filter chain
- `MPFO_<port>`: per-customer owner/policy chain
- `MPFL_<lane>`: per-lane dispatch or common lane chain

The exact chain structure may evolve, but ownership and verification rules must remain explicit.

## Customer Policy Rules

Each active customer may require:

- port accept/dispatch rule
- optional IP whitelist rules
- connlimit rule
- hashlimit rule
- pause reject rule
- block reject rule
- accounting rules
- NAT redirect rule to lane backend

Policy fields:

```text
lane
port
miners
farms
maxconn
rate_per_min
burst
ips_mode
ip_whitelist
status
expires_at
```

## NAT Rules

Allowed customer traffic must be redirected:

```text
customer_port -> lane.backend_port
```

For BTC:

```text
customer_port -> 60010
```

NAT must be generated from desired model.
Manual NAT edits are forbidden.

## Backend Exposure Guard

Backend ports must not be publicly reachable.

Required detection:

- backend port has public listener
- backend port is reachable from external interface
- Docker published backend port is not localhost-protected
- missing `DOCKER-USER` or equivalent guard
- raw/filter chain bypass exists

Required behavior:

- `mpf firewall doctor` reports backend exposure as critical
- apply is blocked if exposure would be introduced
- canary validation checks backend exposure

## v2rayA and UI Guard

v2rayA UI must bind only locally.

Allowed:

```text
127.0.0.1:<ui_port>
Unix socket, if implemented
```

Forbidden:

```text
0.0.0.0:<ui_port>
public_ip:<ui_port>
Docker published UI without localhost bind
```

## Firewall

0.1.249 controlled artifact reapply note: the only newly implemented Phase 11 mutation-capable path is an operator-gated, exact two-customer, `iptables-restore --test --noflush` then `iptables-restore --noflush` package executor. Plan/package/verify/evidence defaults remain read-only, stale/unknown/duplicate/public artifacts fail closed, and no farm5 mutation was performed by the PR.
 Plan

`mpf firewall plan` must produce:

- human-readable summary
- machine-readable JSON
- list of tables touched
- list of chains created/changed/deleted
- list of rules added/removed/changed
- collision warnings
- exposure warnings
- drift summary
- estimated affected customers

Plan JSON should include stable object types, for example:

```json
{
  "mode": "plan_only",
  "backend": "iptables",
  "tables": ["filter", "nat", "raw"],
  "actions": [
    {
      "action": "create_chain",
      "table": "filter",
      "chain": "MPF_CUSTOMERS"
    }
  ],
  "warnings": [],
  "errors": []
}
```

A plan with errors must not be applyable.

## Firewall Diff

`mpf firewall diff` compares desired model with live firewall state.

It must detect:

- missing chain
- unexpected chain
- missing rule
- unexpected rule
- duplicated rule
- changed rule order where order matters
- stale customer rule
- missing NAT redirect
- missing accounting rule
- backend exposure drift

## Apply Lifecycle

`mpf firewall apply --yes` must execute this sequence:

```text
1. validate config
2. validate DB state
3. load desired model
4. load live firewall snapshot
5. generate plan
6. reject plan with errors
7. create restore point
8. save live firewall snapshot
9. acquire firewall lock
10. render full iptables-restore payload
11. apply atomically
12. verify live state
13. write firewall apply record
14. write event/audit record
15. release lock
```

If verification fails:

```text
record failure
produce rollback plan
restore automatically only if configured and safe
report affected customers
```

## Rollback Lifecycle

`mpf firewall rollback <apply_id> --yes` must:

- load restore point
- validate snapshot integrity
- acquire firewall lock
- apply rollback atomically
- verify
- record rollback event
- record affected customers

Rollback must not rely on guessing old rules from current DB state.
It must use stored restore artifacts.

## Required Locks

Firewall apply and rollback require:

```text
/run/mpf-firewall.lock
```

Database-backed lock is also required so recurring jobs do not overlap with manual operations.

## Drift Handling

Drift means live firewall state differs from desired DB/config model.

Drift must be visible in:

```text
mpf firewall doctor
mpf firewall diff
mpf check <customer>
```

Severe drift blocks apply unless the operator explicitly chooses a reviewed reconciliation path.

Examples of severe drift:

- backend exposure
- missing customer chain for active customer
- NAT redirect to wrong backend
- duplicated conflicting connlimit rule
- orphan chain that still receives traffic

## Accounting Rules

Every active customer must have accounting coverage.

Accounting must support:

- usage snapshot
- usage delta
- reject counters
- customer report
- abuse evidence, where applicable

`mpf usage doctor` and `mpf firewall doctor` must report missing accounting rules.

## Reject Events

The firewall model should support reject accounting for:

- connlimit reject
- hashlimit reject
- pause reject
- block reject
- whitelist reject, if applicable
- expired/deleted customer reject, if applicable

Rejects must be explainable by `mpf check`.

## Customer Status Behavior

### active

Customer receives normal policy and NAT redirect.

### paused

Customer receives pause reject behavior and no normal forwarding.

### expired

Customer should not be forwarded unless policy explicitly allows grace.

### deleted

Customer rules should be removed from desired model after safe deletion process.

## Lane Behavior

Lane is part of desired firewall model.

Each enabled lane has:

```text
name
backend_port
chain_prefix
upstreams, outside firewall but referenced by doctor
```

A disabled lane must not create active customer forwarding rules.

Port collision rules:

- customer port must be unique across all active customers
- lane backend port must not collide with customer ports
- backend ports must be unique across enabled lanes

## API-First Boundary

Allowed service calls:

```text
firewall_service.plan()
firewall_service.diff()
firewall_service.apply()
firewall_service.verify()
firewall_service.rollback()
firewall_service.doctor()
```

Interfaces must not build firewall rules themselves.

Forbidden:

```text
CLI renders iptables rules
UI builds iptables-restore payload
abuse job edits firewall chains directly
customer service runs iptables command directly
```

## Commands

Required CLI commands:

```bash
mpf firewall doctor
mpf firewall plan
mpf firewall diff
mpf firewall apply --yes
mpf firewall verify
mpf firewall rollback <apply_id> --yes
```

Useful future commands:

```bash
mpf firewall export-desired
mpf firewall export-live
mpf firewall explain <customer|port>
mpf firewall guard-check
```

## Doctor Requirements

`mpf firewall doctor` must check:

- iptables backend
- required tools installed
- required chains exist
- desired/live drift
- backend exposure
- v2rayA UI exposure
- missing accounting rules
- NAT redirect coverage
- customer port collisions
- lane backend collisions
- orphan MPF chains
- stale deleted/expired customer rules
- Docker interaction risks

Doctor output must have a final verdict:

```text
OK
WARN
CRITICAL
```

## Failure Behavior

If DB is unavailable:

- plan may fail
- apply is forbidden
- rollback from local artifact may be allowed only through explicit emergency procedure

If config is invalid:

- apply is forbidden

If live firewall cannot be read:

- apply is forbidden

If restore point cannot be created:

- apply is forbidden

If verify fails after apply:

- record failure
- produce rollback plan
- do not report success

## Tests Required

Minimum unit tests:

- desired model generation for active customer
- paused customer does not forward normally
- expired customer does not forward normally
- deleted customer is absent from desired rules
- lane backend port collision is detected
- customer port collision is detected
- backend exposure is detected
- missing accounting rule is detected
- orphan chain is detected
- duplicate rule is detected
- plan with errors cannot be applied

Minimum integration tests:

- render valid iptables-restore payload
- apply in isolated namespace or test fixture
- verify expected rules exist after apply
- rollback restores previous snapshot
- failed verify creates failure record
- abuse hard uses firewall service path
- customer add/edit/delete changes desired model only until apply

## Acceptance Checklist

Firewall implementation is accepted only when:

- no interface directly mutates firewall state
- plan output is human-readable and JSON
- apply creates restore point and firewall snapshot
- apply uses lock
- apply uses atomic restore
- verify is mandatory
- rollback has been tested
- backend exposure is detected and blocks unsafe apply
- every active customer has NAT and accounting coverage
- drift is visible and actionable
- tests cover planner, apply, verify, rollback, and failure cases

A patch that adds ad-hoc production firewall mutation must be rejected.


## Phase 6-B3 Offline Apply Package (Inspection Only)

- Added `mpf firewall package` as an offline inspection-only report.
- The package combines planner output, restore payload contract, and apply-readiness contract.
- It remains artifact-only and inspection-only (`applyable=false`, `live_apply_allowed=false`, `readiness=blocked_for_live_apply`).
- It does not execute `iptables-save` or `iptables-restore`.
- It does not acquire locks, write restore points, write files, or write database rows.
- Live firewall apply remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.


## Phase 6-B4 Offline Rollback Artifact Renderer

- Added offline rollback artifact contract/renderer only (`mpf firewall render-rollback`).
- Input must be explicit operator-provided offline snapshot file (`--snapshot-file`).
- Inspection-only artifact: no live rollback/apply execution is allowed.
- Does not execute `iptables-save` or `iptables-restore`.
- Does not acquire locks, write restore points, write rollback files, write DB rows, or write filesystem artifacts.
- Does not guess rollback from DB desired plan; artifact is derived only from supplied offline snapshot content.
- Live apply/rollback remains forbidden until a dedicated Phase 6 apply gate is explicitly accepted.


## Phase 6-B5 Offline Preflight

`mpf firewall preflight` is inspection-only and artifact-only. It combines planner output with restore/apply/package contracts and optional rollback artifact status from an explicit offline snapshot file only. It does not permit live apply/rollback, does not run iptables-save/iptables-restore, does not acquire locks, and does not write restore points, rollback files, DB rows, or filesystem artifacts. Final verdict remains `BLOCKED` while live apply is forbidden by phase gate.


## Phase 6-C1 Note

Phase 6-C1 adds risk matrix and operator approval checklist only.

- It does not implement apply.
- It does not implement rollback.
- It does not implement verify.
- It does not execute iptables-save.
- It does not execute iptables-restore.
- It does not acquire locks.
- It does not write restore points.
- It does not change firewall/NAT/runtime state.
- Live apply remains forbidden until a dedicated apply gate is explicitly accepted.


## Phase 6-C2 — Offline Apply Gate Review Report

Phase 6-C2 adds `mpf firewall gate-review` as an offline, inspection-only report.

It summarizes evidence bundle, risk matrix, checklist, rollback readiness, canary readiness, and abuse requirement preservation.

It does **not** authorize live apply, rollback, or verify. It does **not** execute `iptables-save` or `iptables-restore`, does not acquire locks, does not write restore points/rollback files/database rows, and does not guess live state.

Final decision remains `BLOCKED` while `firewall_apply_allowed: no` in the current phase gate.

## Phase 6-C3 Closure Note

Phase 6-C3 adds acceptance evidence and closure docs only.

- Phase 6-C is accepted as offline/contract/review-only.
- It does not implement apply.
- It does not implement rollback.
- It does not implement verify.
- It does not execute iptables-save.
- It does not execute iptables-restore.
- It does not acquire locks.
- It does not write restore points.
- It does not change firewall/NAT/runtime state.

Live apply remains forbidden until a dedicated apply gate is explicitly accepted.


## Phase 6-E0 Isolated Harness Boundary

Phase 6-E0 is fake/no-op isolated harness planning/contracts only. It does not authorize host production firewall mutation. Real live apply, live rollback, live verify, live firewall read/write, iptables-save, and iptables-restore remain forbidden until a dedicated apply gate is accepted.


## Phase 6-E0 Acceptance Note

Phase 6-E0 is accepted as fake/no-op isolated harness contracts only (`docs/PHASE_6_E0_ACCEPTANCE_EVIDENCE.md`).
Reference: `docs/PHASE_6_E1_ISOLATED_HARNESS_HARDENING.md`.
Phase 6-E1 may only harden isolated harness contracts/tests.
Host production firewall mutation remains forbidden.
Real live apply remains forbidden.


Phase 6-G is accepted as controlled live apply gate planning / pre-apply review only, documentation/test-only and non-authorizing.
Future dedicated Phase 6 apply gate remains not accepted and not authorized.
Phase 6-G is controlled live apply gate planning / pre-apply review only and does not authorize live apply/read/write, iptables-save, iptables-restore, real adapters, DB apply writes, lock acquisition, restore point writes, customer NAT redirects, or customer firewall rules.


Phase 6-G is accepted as planning/pre-apply review only (documentation/test-only, non-authorizing).
Next planned documentation/test-only step is Phase 6-H — Dedicated Apply Gate Entry Criteria / Authorization Boundary.
Future dedicated apply gate remains not accepted and not authorized.


Phase 6-H is accepted as documentation/test-only and non-authorizing. Future dedicated Phase 6 apply gate remains not accepted and not authorized. No live apply/read/write, iptables-save, iptables-restore, real adapters, DB writes, locks, restore points, NAT/customer firewall rules, production traffic, usage automation, abuse automation, UI, or Telegram are allowed.
