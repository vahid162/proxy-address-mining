# AI Phase 11 Task — Production / Customer Activation Gate

Status: future task after Phase 10 final acceptance

This file is the implementation contract for AI coding agents when Phase 11 becomes active.

`docs/PHASE_STATUS.md` remains authoritative. This file does not open Phase 11 by itself.

## Goal

Make the server operational for real customers through the standard `mpf` CLI and Python service layer before Local UI, Operator UI Actions, or Telegram work.

Phase 11 is backend-first and CLI-managed:

```text
Phase 10 accepted
  -> Phase 11 Production / Customer Activation Gate
  -> controlled CLI canary customer
  -> limited real customer onboarding
  -> Phase 12 Worker Policy Enforcement
```

## Required Architecture

Implementation must be Python-first and API-first:

```text
CLI / internal API
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

The CLI must stay a thin interface. Business logic belongs in services/domain code.

## Forbidden Patterns

```text
copy legacy shell scripts as runtime backend
run legacy mpf_* scripts from Python
CLI directly edits PostgreSQL
CLI directly runs iptables
UI or Telegram implementation in Phase 11
direct firewall mutation outside planner/apply service
customer NAT outside desired-model planner
unrestricted customer onboarding
production traffic without canary evidence
abuse automation without explicit Phase 11 gate evidence
worker policy enforcement in Phase 11
```

## Legacy Boundary

The uploaded legacy tgz/scripts are reference material only.

Allowed:

```text
map command parity
read old operator workflow
convert behavior into Python services
derive tests and runbooks
```

Forbidden:

```text
copy old implementation
use TSV/SQLite as source of truth
make shell scripts the backend
```

## Required Command Surface

Phase 11 should introduce or finalize report/activation commands similar to:

```text
mpf production readiness --output json
mpf production canary-plan --output json
mpf production canary-acceptance --output json
mpf production final-activation --output json
```

Operational command groups must be service-layer backed:

```text
mpf customer add/edit/renew/delete/list/set-ips/expire-run
mpf firewall doctor/plan/diff/apply/verify/rollback
mpf usage snapshot/report/customer/doctor
mpf abuse status/run/hard/unhard/events/doctor
mpf check <target>
mpf report <target>
mpf monitor summary/port
mpf audit miners-over/farms-over/suspicious
mpf block add-ip/add-port-ip/list/expire-run/remove
mpf pause add/remove/sync/list
mpf backup create/list/restore-plan
mpf jobs status/list/run/doctor
```

## Activation Requirements

Phase 11 must be accepted only with farm5 evidence proving:

```text
fresh GitHub main sync/test evidence
pytest passes on farm5
mpf doctor OK
phase gate OK
server time/NTP OK
restart safety OK
container startup order tested
firewall apply uses planner/lock/backup/verify/rollback path
customer NAT/customer firewall rules generated only through planner
manual canary customer succeeds
usage/reject accounting visible
session/worker evidence visible from Phase 10 surfaces
abuse 1h covers all active customers in enabled lanes
rollback or restore-plan evidence exists
```

## Abuse Invariant

Do not weaken the abuse requirement:

```text
normal -> over_tracking -> over_grace -> hard
```

Required fail-closed behavior:

```text
all active customers in enabled lanes are scanned
no silent skip
missing/stale evidence does not harden
DB failure does not harden
firewall failure does not harden
farms-over alone does not harden
worker-over alone does not harden
sustained miner-abuse hardens after about 3600 seconds
manual unhard is audited
```

## Initial Operational Boundary

Phase 11 may only open controlled states after acceptance evidence:

```text
production_traffic: controlled_cli_canary or controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled
customer_onboarding_allowed: controlled_cli_canary or controlled_cli_limited
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
```

## Acceptance Gate

```text
manual canary customer connects successfully
NAT hit is visible
usage/reject accounting works
check/report returns clear verdict
abuse scanner covers the customer
rollback or restore-plan exists
server restart preserves accepted runtime service
no unrestricted production onboarding exists
```

## Required Tests

At minimum:

```text
production readiness service tests
canary plan service tests
canary acceptance report tests
final activation report tests
CLI calls service layer tests
firewall apply gate still fail-closed without explicit approval
abuse 1h coverage invariant tests
restart/container-order docs tests
legacy shell backend forbidden tests
```
