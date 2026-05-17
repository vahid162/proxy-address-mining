# AI Phase 12 Task — Worker Policy Enforcement

Status: future task after Phase 11 acceptance

This file is the implementation contract for AI coding agents when Phase 12 becomes active.

`docs/PHASE_STATUS.md` remains authoritative. This file does not open Phase 12 by itself.

## Goal

Enforce worker policy only after both conditions are true:

```text
Phase 10 worker/session/share evidence is accepted
Phase 11 controlled production/customer activation is accepted
```

Phase 12 must not be implemented before reliable worker evidence and a controlled production path exist.

## Required Sub-step Execution Model

Phase 12 must be implemented like earlier phases: small PRs, clear gates, evidence-first, fail-closed, and no fabricated server evidence.

Do not implement strict worker enforcement as one large PR.

Required sequence:

```text
Phase 12A — Worker evidence and mapping readiness
Phase 12B — Worker policy service in detection_only mode
Phase 12C — Manual operator enforcement action planning
Phase 12D — Adapter capability and failure-mode readiness
Phase 12E — Controlled enforcement canary, if adapter support is accepted
Phase 12F — Phase 12 final acceptance report
```

### Phase 12A — Worker evidence and mapping readiness

Allowed:

```text
report-only readiness services
worker identity normalization contract
worker-to-session mapping confidence model
evidence freshness/staleness checks
```

Forbidden:

```text
strict enforcement
firewall-only worker block
adapter mutation
UI/Telegram enforcement
```

Acceptance evidence:

```text
worker evidence exists from Phase 10
session evidence exists from Phase 10
mapping confidence is reported
missing/stale evidence fails closed
```

### Phase 12B — Worker policy service in detection_only mode

Allowed:

```text
worker policy service
repository methods
detection-only reports
events/audit for detection
operator-visible violations
```

Forbidden:

```text
automatic blocking
automatic disconnect
automatic firewall mutation
strict enforcement
```

Acceptance evidence:

```text
detection_only is default
violations are visible
audit/events are created where appropriate
no customer traffic is interrupted by detection-only logic
```

### Phase 12C — Manual operator enforcement action planning

Allowed:

```text
manual action plan generation
operator confirmation contract
dry-run manual enforcement report
rollback/disable plan
```

Forbidden:

```text
automatic enforcement without operator confirmation
UI/Telegram action paths before their own phases
```

Acceptance evidence:

```text
operator can inspect evidence before action
manual action plan is JSON and human-readable
manual action is audited
safe no-op path exists
```

### Phase 12D — Adapter capability and failure-mode readiness

Allowed:

```text
adapter capability report
stratum_proxy readiness contract
failure-mode simulation
fallback to detection_only
```

Forbidden:

```text
strict adapter-backed enforcement without tested adapter behavior
silent enforcement on adapter failure
enforcement when evidence is stale or missing
```

Acceptance evidence:

```text
adapter capabilities are explicit
adapter failures fall back to detection_only
DB failure results in no enforcement
firewall failure results in no enforcement
```

### Phase 12E — Controlled enforcement canary

Allowed only after prior Phase 12 sub-steps are accepted:

```text
single controlled canary enforcement scenario
operator-approved strict mode where supported
clear rollback/disable path
```

Forbidden:

```text
general strict enforcement
firewall-only worker-name block
unreviewed customer impact
```

Acceptance evidence:

```text
canary enforcement outcome is recorded
affected customer/session/worker evidence is recorded
rollback/disable works
detection_only fallback works
```

### Phase 12F — Phase 12 final acceptance report

Required output:

```text
mpf worker-policy final-acceptance --output json
```

Final acceptance must explicitly record selected enforcement mode, evidence quality, adapter support, fallback behavior, and which gates remain closed.

## Required Architecture

Implementation must be Python-first and API-first:

```text
CLI / internal API
  -> request DTO / command object
  -> worker policy service
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

The CLI is only an interface. Enforcement decisions belong in domain/services code.

## Allowed Enforcement Modes

```text
detection_only
manual_operator_action
stratum_proxy, only after adapter is implemented and tested
```

Default mode must be fail-closed and safe. Detection-only is the safest initial mode.

## Forbidden Patterns

```text
firewall-only worker-name blocking
iptables rule based only on worker name
strict enforcement without reliable worker-to-session mapping
strict enforcement without adapter tests
strict enforcement when evidence is missing or stale
enforcement that bypasses event/audit
enforcement from UI or Telegram before their own accepted phases
legacy shell script enforcement backend
```

## Required Work

```text
worker-to-session mapping confidence model
worker identity normalization
worker policy service
worker policy repository methods
operator-visible enforcement plan
detection-only report
manual operator action report
adapter capability report
adapter failure behavior
safe fallback to detection_only
worker enforcement event/audit records
worker enforcement readiness/final-acceptance reports
```

## Evidence Requirements

Before any strict enforcement can be considered:

```text
worker evidence exists from Phase 10
session evidence exists from Phase 10
customer production path exists from Phase 11
adapter behavior is tested
failure behavior is documented
rollback or disable path exists
operator can inspect evidence before action
```

## Safety Requirements

```text
missing evidence -> no strict enforcement
stale evidence -> no strict enforcement
mapping confidence below threshold -> detection_only
adapter failure -> detection_only
DB failure -> no enforcement
firewall failure -> no enforcement
manual operator action must be audited
strict mode must not rely on firewall-only worker names
```

## Abuse Boundary

Worker Policy Enforcement must not weaken abuse 1h behavior.

```text
worker-over alone does not harden
farms-over alone does not harden
miner-abuse sustained about 3600 seconds is still the hardening trigger
```

## Acceptance Gate

```text
worker-to-session mapping is reliable enough for selected mode
worker policy service is tested
adapter behavior is tested
detection-only mode is safe
manual/operator enforcement is audited
strict enforcement does not rely on firewall-only worker names
safe fallback to detection_only is proven
no UI/Telegram bypass exists
```

## Required Tests

At minimum:

```text
worker identity normalization tests
worker-to-session confidence tests
worker policy service tests
detection-only report tests
manual operator action report tests
adapter failure behavior tests
fallback-to-detection-only tests
missing/stale evidence fail-closed tests
no firewall-only worker block tests
event/audit tests
CLI uses service-layer tests
sub-step gate ordering tests
```
