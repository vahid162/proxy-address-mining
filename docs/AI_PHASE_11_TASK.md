# AI Phase 11 Task — Production / Customer Activation Gate

Status: future task after Phase 10 final acceptance

This file is the implementation contract for AI coding agents when Phase 11 becomes active.

`docs/PHASE_STATUS.md` remains authoritative. This file does not open Phase 11 by itself.

## Goal

Make the server operational for real customers through the standard `mpf` CLI and Python service layer before Local UI, Operator UI Actions, or Telegram work.

Phase 11 is backend-first, CLI-managed, and AI-safe Runtime-first:

```text
Phase 10 accepted
  -> Phase 11 Production / Customer Activation Gate
  -> controlled CLI canary customer
  -> limited real customer onboarding
  -> Phase 12 Worker Policy Enforcement
```

Read `docs/AI_SAFE_RUNTIME_FIRST.md` before changing Phase 11 code, tests, services, jobs, scripts, or runbooks. Runtime-first means moving toward real controlled runtime evidence in small accepted steps; it does not authorize bypassing phase gates, planner/service-layer boundaries, rollback evidence, or operator approval.

## Required Sub-step Execution Model

Phase 11 must be implemented like earlier phases: small PRs, clear gates, evidence-first, fail-closed, and no fabricated server evidence.

Do not implement Phase 11 as one large production-enabling PR.

Required sequence:

```text
Phase 11A — Production readiness inventory
Phase 11B — CLI canary plan/report only
Phase 11C — Controlled firewall/customer activation harness
Phase 11D — Manual canary customer acceptance
Phase 11E — Limited real customer onboarding
Phase 11F — Phase 11 final acceptance report
```

### Phase 11A — Production readiness inventory

Allowed:

```text
report-only services and CLI
server preflight contract
restart/container-order checklist
fresh farm5 sync/test evidence requirements
current gate verification
```

Forbidden:

```text
production traffic
firewall apply
customer NAT/customer firewall rules
abuse automation runner
real customer onboarding
```

Acceptance evidence:

```text
mpf production readiness --output json
pytest on GitHub
farm5 sync/test evidence after merge
mpf doctor OK
phase gate OK
```

### Phase 11B — CLI canary plan/report only

Allowed:

```text
canary customer intent model
canary plan renderer
firewall desired-model preview
rollback/restore-plan preview
operator checklist
```

Forbidden:

```text
actual customer NAT
actual firewall apply
actual abuse automation
production customer traffic
```

Acceptance evidence:

```text
mpf production canary-plan --output json
plan is human-readable and JSON
plan is fail-closed by default
```

### Phase 11C — Controlled firewall/customer activation harness

Allowed only after prior sub-steps are accepted:

```text
controlled apply harness
planner/lock/backup/verify/rollback path
explicit operator confirmation
single canary boundary
```

Forbidden:

```text
unrestricted onboarding
UI actions
Telegram actions
worker enforcement
background automation without an explicit accepted runner gate
```

Acceptance evidence:

```text
restore point exists before apply
iptables-save backup exists before apply
lock acquired before apply
verify runs after apply
rollback or rollback-plan exists
```

### Phase 11D — Manual canary customer acceptance

Allowed:

```text
one explicit canary customer
controlled CLI activation
usage/reject/session/worker visibility checks
abuse coverage check
check/report final verdict
```

Acceptance evidence:

```text
canary customer connects successfully
NAT hit is visible
usage/reject accounting works
abuse scanner covers the customer
rollback or restore-plan evidence exists
```

### Phase 11E — Limited real customer onboarding

Allowed only after canary acceptance:

```text
limited real customer onboarding through CLI
controlled customer_onboarding_allowed transition
controlled production_traffic transition
operator-visible audit/events
```

Forbidden:

```text
unrestricted production onboarding
UI/Telegram mutation paths
direct DB/firewall mutation
```

Acceptance evidence:

```text
small limited customer set works
restart safety remains OK
abuse 1h coverage remains OK
check/report remains clear
rollback/restore-plan remains available
```

### Phase 11F — Phase 11 final acceptance report

Required output:

```text
mpf production final-activation --output json
```

Final acceptance must explicitly record which controlled gates are open and which remain closed.

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

By final Phase 11 acceptance, the target is controlled real customer sales through CLI/service-layer workflows, not UI/Telegram and not unrestricted onboarding.

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
sub-step gate ordering tests
AI-safe Runtime-first boundary tests
```
