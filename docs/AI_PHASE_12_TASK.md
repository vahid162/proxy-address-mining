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
```
