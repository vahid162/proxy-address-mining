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

## Firewall Plan

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
