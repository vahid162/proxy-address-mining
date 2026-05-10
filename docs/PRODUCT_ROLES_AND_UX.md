# Product Roles and UX Journey Contract

Status: Phase 5-F2 contract (documentation-only)

## Scope and phase gate

Phase 5 is **DB-only**: `current_working_phase: Phase 5 — Customer CRUD in DB Only`.

This document defines the future product roles, UI/Telegram boundaries, action journey, and operator-facing UX contract for `proxy-address-mining`.
It does **not** authorize UI runtime, Telegram runtime, public API exposure, firewall/NAT changes, collectors, automation, or DB mutations in Phase 5.

Runtime impact: none.
Firewall impact: none.
Database migration impact: none.
UI impact: none.
Telegram impact: none.
Production traffic impact: none.

Strictly forbidden in Phase 5:

```text
no UI service
no buyer UI service
no Telegram bot
no public API binding
no direct DB write from UI/API/Telegram
no direct firewall apply
no direct abuse hard/unhard
no direct block/pause mutation
no shell command execution from Telegram
no migration
no model changes
no collector
no systemd timer
no production customer traffic
```

## Purpose

The project already defines technical contracts for customer lifecycle, troubleshooting evidence, worker policy, control rules, and future observability.
This document adds the missing product/UX contract so future CLI, local Web UI, buyer UI, Telegram, and API surfaces use the same role model, action states, confirmation rules, and safety gates.

Future user-facing surfaces must not invent separate business logic.
They must use service-layer command objects and response DTOs.

Required interaction boundary:

```text
CLI / local Web UI / buyer Web UI / Telegram / future API
  -> request DTO or command object
  -> service layer
  -> repository / adapter
  -> event + audit
  -> response DTO / verdict DTO
```

Forbidden permanently:

```text
UI directly updates tables
Telegram directly runs shell commands
buyer UI directly mutates customer policy
buyer UI directly applies firewall
Telegram directly applies firewall
operator UI bypasses service validation
surface-specific business logic that diverges from CLI behavior
```

## Common UX states

All future surfaces should normalize customer/service state into the same safe vocabulary.

Recommended status/verdict labels:

```text
OK
Pending First Connect
No Recent Traffic
Paused
Expired
Deleted
High Reject Rate
Wrong Source IP
Worker Mismatch
Abuse Tracking
Abuse Grace
Hard Limited
Backend Problem
Pool Problem
Firewall Drift
Needs Operator Review
Action Pending
Action Approved
Action Rejected
Action Executed
```

Buyer-safe surfaces may show simplified labels and must hide dangerous internal details where appropriate.
Operator and technician surfaces may show full evidence, event, audit, and plan context.

## Action safety classes

Every future action exposed through CLI, UI, Telegram, or API must be classified before implementation.

```text
read_only
request_only
operator_confirmed
plan_required
dangerous_with_restore_point
forbidden
```

Rules:

```text
read_only: returns state only, no mutation.
request_only: creates an action request, not execution.
operator_confirmed: requires authenticated operator confirmation and event/audit.
plan_required: must show preview/plan before execution.
dangerous_with_restore_point: requires restore point, plan, confirmation, event/audit, and rollback guidance.
forbidden: must not be exposed on that role/surface.
```

Dangerous actions include at least:

```text
firewall apply
firewall rollback
abuse hard
manual unhard
block/unblock
pause/unpause
bulk policy change
worker enforcement
runtime collector activation
public exposure change
```

## Role contract matrix

Every role section below must define needs, allowed information, forbidden information, allowed actions, request-only actions, dangerous actions, required confirmation, required event/audit, and future phase placement.

### 1. buyer/customer

Needs:

```text
see service status
see assigned host/port/lane summary
see expiry and renewal state
see whether service is active, paused, expired, or pending first-connect
see simple usage/report health when later available
understand connection problems in buyer-safe language
request renewal
request IP whitelist change
request support
```

Allowed information:

```text
own service list
own customer_key or buyer-facing service key
assigned port and lane display name
expiry and lifecycle status
buyer-safe health verdict
buyer-safe usage summary after Phase 7/9
buyer-safe reject summary after Phase 7/9
buyer-safe abuse status without internal hardening internals
support/action request status
```

Forbidden information:

```text
other customers
raw firewall rules
raw iptables output
internal backend ports as public connection targets
other buyers
operator audit internals
secrets
raw Telegram/API tokens
raw restore artifacts
unsafe shell commands
```

Allowed actions:

```text
view own service status
view own report
view own expiry
create support request
create renewal request
create IP change request
acknowledge notifications
```

Request-only actions:

```text
renewal
IP whitelist change
unpause request
plan change request
support request
worker policy request
```

Dangerous actions:

```text
none for direct execution
```

Required confirmation:

```text
confirm request submission only; buyer confirmation is not execution confirmation
```

Required event/audit:

```text
action request creation
support request creation
notification acknowledgement where supported
operator review and execution later
```

Future phase placement:

```text
Phase 12: buyer-safe read-only reporting
Phase 13+: buyer action requests with operator review where accepted
Phase 14+: Telegram buyer read-only/request-only commands where accepted
```

### 2. seller/operator

Needs:

```text
create customer service records
renew service
update customer policy intent
update IP whitelist intent
view expiring and expired services
view policy history
view buyer/service mapping later
preview plan impact before dangerous changes
approve or reject buyer requests
```

Allowed information:

```text
customer CRUD state
policy history
lifecycle reports
events and audit for owned operations
future buyer account/service mapping
future action request queue
future plan preview and execution status
```

Forbidden information:

```text
raw secrets
unsafe shell command suggestions as executable buttons
direct DB credentials in UI
unreviewed firewall apply shortcuts
```

Allowed actions:

```text
DB-only customer create/update/renew/disable/delete in Phase 5 through service layer
review customer policy history
review events/audit
review lifecycle reports
approve/reject future action requests
```

Request-only actions:

```text
firewall-affecting changes before Phase 6 acceptance
runtime-affecting changes before the relevant phase
worker enforcement before Phase 15+
public exposure changes
```

Dangerous actions:

```text
firewall apply
firewall rollback
bulk policy changes
manual unhard
block/unblock
pause/unpause
worker enforcement
production import execution
```

Required confirmation:

```text
operator confirmation for every mutation
plan confirmation for firewall-affecting actions
restore-point confirmation for dangerous actions
```

Required event/audit:

```text
customer mutation
policy mutation
lifecycle mutation
approval/rejection
firewall plan/apply/rollback
block/pause
manual unhard
import execution
```

Future phase placement:

```text
Phase 5: DB-only customer operations
Phase 6: firewall planning/apply workflow
Phase 7: usage/reject report review
Phase 8: abuse state review/manual controls where accepted
Phase 13: UI actions with confirmation
Phase 14: restricted Telegram actions with confirmation
```

### 3. technician/support

Needs:

```text
quickly diagnose cannot-connect cases
see customer status and policy
see assigned port and lane
see backend/proxy health
see future NAT/firewall/reject/session/worker evidence
see clear next operator action
create support notes
escalate safely
```

Allowed information:

```text
customer status and policy summary
operator-safe diagnostic verdicts
troubleshooting evidence
flow/session/worker timeline after accepted phases
event and audit references needed for support
runbook guidance
```

Forbidden information:

```text
raw secrets
unmasked credentials
direct shell mutation commands
customer data outside assigned scope if RBAC exists later
buyer-private information not needed for support
```

Allowed actions:

```text
read diagnostics
run read-only checks
add support notes later through service layer
create action request or escalation
acknowledge incident/runbook step later
```

Request-only actions:

```text
customer policy changes
IP whitelist changes
pause/unpause
block/unblock
manual unhard
firewall apply
```

Dangerous actions:

```text
none unless technician is also an authorized operator and the relevant phase permits it
```

Required confirmation:

```text
support note confirmation
escalation confirmation
action request confirmation
operator confirmation for any execution path
```

Required event/audit:

```text
support notes
action requests
escalations
runbook acknowledgements
operator-executed fixes
```

Future phase placement:

```text
Phase 9: check/report/diagnostic verdicts
Phase 10: timeline/evidence pack
Phase 11: local read-only UI
Phase 13: operator-confirmed action execution
```

### 4. Telegram admin/operator

Needs:

```text
receive critical notifications
run safe read-only status checks
acknowledge incidents
review pending action requests
approve restricted actions only when allowed later
avoid noisy repeated alerts
```

Allowed information:

```text
operator-safe status summaries
critical event notifications
pending action request summaries
safe diagnostic verdicts
links or IDs to review in local UI/CLI
```

Forbidden information:

```text
raw secrets
raw tokens
full sensitive audit dumps in chat
shell command execution
automatic firewall apply without plan
public backend exposure controls without confirmation
buyer data outside scope
```

Allowed actions:

```text
read-only status commands after Phase 14 stage 2
notification acknowledgement
action request review after restricted-action phase
```

Request-only actions:

```text
firewall apply until local plan/confirmation path is accepted
block/pause until restricted action path is accepted
manual unhard until restricted action path is accepted
customer policy mutation unless explicitly accepted later
```

Dangerous actions:

```text
firewall apply
rollback
block/unblock
pause/unpause
manual unhard
worker enforcement
public exposure change
```

Required confirmation:

```text
two-step confirmation for restricted actions
explicit target summary
plan/reference ID where applicable
short expiry on confirmation token
```

Required event/audit:

```text
notification delivery
acknowledgement
command invocation
approval/rejection
execution request
final execution result
```

Future phase placement:

```text
Phase 14 stage 1: notifications only
Phase 14 stage 2: read-only commands
Phase 14 stage 3: restricted actions with allowlist and confirmation
```

### 5. Telegram buyer

Needs:

```text
see own service status
see expiry
receive safe service notifications
request renewal
request IP change
request support
receive action request updates
```

Allowed information:

```text
own services only
buyer-safe verdicts
expiry and lifecycle state
safe usage/report summary after accepted phases
support request status
```

Forbidden information:

```text
other customers
operator audit internals
raw firewall/NAT details
backend internal ports as connection instructions
raw worker evidence from other buyers
shell commands
```

Allowed actions:

```text
read own status
acknowledge own notifications
create support request
create renewal request
create IP change request
```

Request-only actions:

```text
renewal
IP whitelist change
unpause
plan change
support
```

Dangerous actions:

```text
none
```

Required confirmation:

```text
confirm request submission
confirm notification acknowledgement
```

Required event/audit:

```text
request creation
notification delivery/acknowledgement
operator review result later
```

Future phase placement:

```text
Phase 14 stage 1+: notifications where allowed
Phase 14 stage 2+: read-only buyer commands where allowed
Phase 14 stage 3+: request-only buyer actions where allowed
```

### 6. local Web UI operator

Needs:

```text
dashboard overview
customer list
customer detail
lifecycle reports
policy history
events/audit
health verdicts
future usage/session/worker timelines
safe action panels
confirmation modals
plan previews
```

Allowed information:

```text
operator-visible customers
policy and lifecycle history
events and audit
future firewall plans and apply history
future abuse state and evidence
future usage/session/worker evidence
runbook guidance
```

Forbidden information:

```text
raw secrets
unmasked tokens
direct DB credentials
unsafe shell execution buttons
unconfirmed dangerous execution paths
```

Allowed actions:

```text
read-only dashboard before action phases
DB-only customer mutations when Phase 13 accepts UI actions
review plan previews
approve or reject action requests
add notes where accepted
```

Request-only actions:

```text
any action before its accepted phase
firewall-affecting action before Phase 6 and Phase 13 acceptance
worker enforcement before Phase 15+
```

Dangerous actions:

```text
firewall apply/rollback
block/unblock
pause/unpause
manual unhard
bulk policy change
public exposure change
worker enforcement
```

Required confirmation:

```text
confirmation modal for every mutation
plan preview for firewall-affecting changes
restore-point warning for dangerous actions
explicit target, before/after summary, and reason field
```

Required event/audit:

```text
all mutations
all approvals/rejections
all dangerous plans and executions
all failed dangerous actions
```

Future phase placement:

```text
Phase 11: local Web UI read-only
Phase 13: local operator UI actions with confirmation
```

### 7. buyer-safe Web UI user

Needs:

```text
service list
service detail
expiry
safe status
safe usage/report summary
support/action request creation
support/action request history
```

Allowed information:

```text
own buyer account
own linked services
buyer-safe customer detail
buyer-safe usage/report summary
buyer-safe abuse status
support/action request status
```

Forbidden information:

```text
other buyers
operator-only audit internals
raw firewall rules
raw backend exposure internals
dangerous action buttons
direct policy mutation
secret references
```

Allowed actions:

```text
read own reports
create action requests
acknowledge notifications
update buyer profile only after auth/user phase is accepted
```

Request-only actions:

```text
renewal
IP change
unpause
support
plan/service change
```

Dangerous actions:

```text
none
```

Required confirmation:

```text
request submission confirmation
clear non-execution wording for request-only actions
```

Required event/audit:

```text
buyer login/access later
request creation
notification acknowledgement
operator review result
```

Future phase placement:

```text
Phase 12: buyer-safe read-only reporting
Phase 13+: request flow integration where accepted
```

## Journey contract matrix

Every future UI, Telegram, API, or CLI workflow must map to one of these journeys or extend this contract first.

### customer onboarding

Primary role: seller/operator.
Future surfaces: CLI, local Web UI.
Phase placement: Phase 5 DB-only now; traffic reachability only after Phase 6+ acceptance.
Required states: draft/preview, created DB-only, future firewall eligible, future live after plan/apply.
Safety: must show `firewall_change: no`, `nat_change: no`, `runtime_change: no` in Phase 5 dry-run outputs.
Event/audit: customer.created, audit entry.

### service renewal

Primary role: seller/operator; buyer may request only.
Future surfaces: CLI, local Web UI, buyer UI request, Telegram request.
Phase placement: Phase 5 DB-only renewal now; buyer request later.
Safety: buyer request is not execution.
Event/audit: customer.renewed or action_request.created/reviewed.

### first-connect activation

Primary role: customer; technician/operator observe later.
Future surfaces: reports, timeline, UI, Telegram status.
Phase placement: runtime evidence later only; Phase 5 stores intent only.
Safety: no first-connect runtime detector in Phase 5.
Event/audit: future activation event and evidence link.

### IP whitelist change request

Primary role: buyer/customer request, seller/operator approval.
Future surfaces: buyer UI, Telegram buyer, local UI operator, CLI.
Phase placement: DB-only IP pin changes in Phase 5 by operator; buyer request later.
Safety: buyer cannot directly mutate whitelist.
Event/audit: action_request.created, operator approval/rejection, customer.ip_pins_changed.

### customer cannot connect

Primary role: technician/support.
Future surfaces: `mpf check`, `mpf diag`, local UI, Telegram read-only status.
Phase placement: Phase 9/10 consumes troubleshooting evidence.
Safety: diagnosis is read-only unless operator separately executes approved action.
Event/audit: support note/action request where created.

### customer expired

Primary role: customer/buyer, seller/operator.
Future surfaces: lifecycle reports, buyer UI, Telegram notification.
Phase placement: Phase 5 DB-only reports; automation later only.
Safety: no auto-expire timer in Phase 5.
Event/audit: renewal request, renewal execution, future expiry event.

### customer paused

Primary role: seller/operator, technician/support, buyer view.
Future surfaces: local UI, buyer-safe UI, Telegram notification.
Phase placement: pause runtime later; Phase 5 status/lifecycle only.
Safety: buyer can request unpause but cannot unpause directly.
Event/audit: pause/unpause action and reason.

### abuse warning / hard state

Primary role: operator/technician; buyer-safe view later.
Future surfaces: check/report/UI/Telegram notifications.
Phase placement: Phase 8 for abuse runtime, Phase 9/10 for verdict/timeline.
Safety: all active customers remain abuse-evaluable; farms-over or worker-over alone must not harden.
Event/audit: abuse state transitions, hard/unhard audit, restore point.

### worker mismatch

Primary role: technician/support; buyer-safe summary later.
Future surfaces: worker timeline, report, local UI, Telegram read-only alert.
Phase placement: Phase 10 detection, Phase 15+ enforcement.
Safety: worker enforcement is future-only and not firewall-only.
Event/audit: worker evidence and action request if operator action is needed.

### high reject rate

Primary role: technician/support, operator, buyer-safe report.
Future surfaces: usage report, policy event report, UI charts, Telegram notification.
Phase placement: Phase 7/9, chart surfaces later.
Safety: high-volume evidence requires retention policy first.
Event/audit: notification and operator action if taken.

### backend/pool issue

Primary role: technician/operator.
Future surfaces: proxy doctor, diag, local UI health card, Telegram notification.
Phase placement: Phase 4/6/9 depending on evidence source.
Safety: backend internal reachability must remain allowed; public exposure must remain denied.
Event/audit: incident/runbook acknowledgement later.

### seller creates service

Primary role: seller/operator.
Future surfaces: CLI now, local UI later.
Phase placement: Phase 5 DB-only; live reachability after firewall plan/apply phase.
Safety: no customer NAT/firewall in Phase 5.
Event/audit: customer.created and audit entry.

### seller renews service

Primary role: seller/operator.
Future surfaces: CLI now, local UI later.
Phase placement: Phase 5 DB-only renewal; buyer request later.
Safety: no lifecycle timer in Phase 5.
Event/audit: customer.renewed and audit entry.

### technician diagnoses issue

Primary role: technician/support.
Future surfaces: check/report/diag/timeline/local UI.
Phase placement: Phase 9/10.
Safety: diagnosis must be read-only by default.
Event/audit: support note, action request, operator execution later.

### buyer opens support request

Primary role: buyer/customer.
Future surfaces: buyer UI, Telegram buyer.
Phase placement: Phase 12/14+.
Safety: request-only, no direct mutation.
Event/audit: action_request.created or support_request.created.

### operator approves action request

Primary role: seller/operator.
Future surfaces: local UI, CLI, restricted Telegram later.
Phase placement: Phase 13/14+ depending on surface and action.
Safety: approval is separate from dangerous execution when plan/restore is required.
Event/audit: approved/rejected/executed states.

### UI dangerous action confirmation

Primary role: operator.
Future surfaces: local Web UI.
Phase placement: Phase 13+.
Safety: target summary, plan preview, reason, confirmation, restore point where required.
Event/audit: confirmation, execution, result.

### Telegram notification and acknowledgement

Primary role: operator or buyer depending on target.
Future surfaces: Telegram.
Phase placement: Phase 14.
Safety: notifications first, read-only commands second, restricted actions third.
Event/audit: delivery, acknowledgement, command/action record.

## Surface contract

### CLI

CLI remains the reference operational interface before UI/Telegram.
It must stay thin and use services.
CLI output should use the same DTO/verdict vocabulary that UI and Telegram will consume later.

### Local Web UI

Local Web UI starts read-only.
It must bind only to `127.0.0.1` or Unix socket.
It must not write DB directly.
It must not execute shell commands directly.
It must not apply firewall directly.

Recommended initial pages:

```text
Dashboard
Customers
Customer detail
Lifecycle reports
Events/audit
Diagnostics/check result
Usage/reject reports later
Session/worker timeline later
Action requests later
Runbook/incident view later
```

### Buyer Web UI

Buyer Web UI starts read-only and buyer-safe.
Buyer account identity must remain separate from customer service rows.
Buyer action buttons create requests, not execution.

Recommended initial pages:

```text
My services
Service detail
Expiry/renewal state
Buyer-safe health report
Usage summary later
Support/action requests
Notification history later
```

### Telegram

Telegram starts as notification-only.
Read-only commands may be added later.
Restricted actions may be added only after allowlist, confirmation, event/audit, and service-layer execution paths exist.

Forbidden Telegram behavior:

```text
shell command execution
raw firewall apply
direct DB write
unsafe token exposure
buyer direct mutation
unconfirmed dangerous action
```

### Future API

Future API must expose DTOs/services, not table-shaped direct mutations.
Public API binding is forbidden in early phases.
Local-only API surfaces must preserve the same action safety classes.

## Phase placement

```text
Phase 5:
  Product/UX contract only, DB-only customer operation contracts, no UI/Telegram runtime.

Phase 6:
  Firewall plan/apply evidence and plan previews for operator surfaces.

Phase 7:
  Usage and policy/reject summaries for reports.

Phase 8:
  Abuse runtime state and operator-safe/manual controls where accepted.

Phase 9:
  Check/report/diagnostic verdict DTOs.

Phase 10:
  Session/worker/policy timeline and evidence packs.

Phase 11:
  Local Web UI read-only.

Phase 12:
  Buyer-safe read-only reporting.

Phase 13:
  Local operator UI actions with confirmation.

Phase 14:
  Telegram notifications, read-only commands, restricted actions.

Phase 15+:
  Worker enforcement after evidence and adapter acceptance.
```

## Acceptance criteria for this contract

This contract is accepted only when:

```text
pytest passes
Phase 5 remains DB-only
no UI runtime is added
no Telegram runtime is added
no public API binding is added
no migration/model change is added
no direct DB write path is added
no firewall/NAT path is added
no systemd timer is added
no collector is added
role boundaries are documented
journeys are documented
request-only vs execution actions are documented
confirmation/audit requirements are documented
```

A patch that turns this document into runtime behavior before the relevant accepted phase must be rejected.
