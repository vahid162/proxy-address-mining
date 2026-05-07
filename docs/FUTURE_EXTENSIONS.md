# Future Extensions Contract

Status: future-facing architecture contract

This document reserves architecture boundaries for capabilities that are intentionally not implemented in early phases but must not be blocked by early design choices.

## Scope

Future extensions covered here:

```text
buyer-facing read-only panel
buyer action requests
plans / packages / entitlements
feature flags
notification rules
health verdict snapshots
incident and runbook guidance
config snapshots
secret references
restore drills
maintenance windows
import staging
worker identity timeline
worker block policy
worker enforcement adapter
server profiles and preflight history
retention policy, later
policy simulation, later
API DTO contracts, later
```

These capabilities are future work. Their schema and service boundaries may exist in Phase 2, but production behavior must wait for the appropriate phase gates.

## Phase 2 Rule

In Phase 2, these extensions are allowed only as:

```text
schema representation
service boundary contract
tests that preserve the boundary
documentation
```

Forbidden in Phase 2:

```text
buyer login service
public buyer UI
payment/billing execution
runtime feature flag switching for dangerous behavior
worker enforcement
Stratum-aware production proxy changes
firewall apply
NAT redirects
abuse automation
import directly into production
incident automation
maintenance automation
```

## Buyer UI Boundary

Buyer UI must not be built by reusing operator identity or by treating `customers` as login accounts.

Correct separation:

```text
operators
  -> human/admin/operator identities

buyer_accounts / buyer_users
  -> future buyer-facing identities

customers
  -> service/port allocations

customer_service_links
  -> relation between buyer accounts and customer service records
```

Initial buyer UI must be read-only.

Allowed future buyer views:

```text
service list
service status
expiry
miners/farms/maxconn summary
usage 1h/1d/30d
abuse state
reject reason summary
operator-visible support notes, if explicitly allowed
```

Forbidden buyer UI behavior:

```text
direct customer policy mutation
direct firewall apply
direct abuse hard/unhard
direct block/pause mutation
direct DB writes from UI handlers
public exposure before auth/audit are complete
```

Buyer-initiated changes should go through:

```text
buyer UI
  -> action_request_service.create_request()
  -> operator review
  -> approved service action, later
  -> event/audit
```

## Plans, Packages, and Entitlements

Commercial/buyer-facing structure must not be mixed into raw firewall policy.

Correct separation:

```text
buyer_account
  -> subscription
    -> subscription_item / service_entitlement
      -> customer service / port
        -> customer policy
```

Reserved tables:

```text
plans
plan_versions
subscriptions
subscription_items
service_entitlements
customer_policy_overrides
```

Rules:

```text
- Billing/payment is not implemented in early phases.
- Plans define intended limits; customer policies represent effective operational policy.
- Overrides must be explicit and auditable.
- Plan changes must be simulated before production apply in later phases.
```

## Action Requests and Approval Workflow

User-triggered or risky operator-triggered actions should be requestable before they are executable.

Reserved table:

```text
action_requests
```

Examples:

```text
renew_request
unpause_request
ip_change_request
plan_change_request
support_request
worker_policy_request
```

Rules:

```text
- request creation is not the same as execution
- approval/rejection must be auditable
- dangerous approved actions still go through the relevant service and restore-point rules
```

## Feature Flags

Feature flags let code exist without being active.

Reserved table:

```text
feature_flags
```

Default for sensitive future flags must be disabled:

```text
buyer_ui_enabled = false
telegram_notifications_enabled = false
telegram_actions_enabled = false
worker_block_enabled = false
stratum_inspection_enabled = false
public_api_enabled = false
nftables_backend_enabled = false
```

Feature flags must not bypass phase gates.

## Notification Rules

Notifications should be event-driven, not hardwired to Telegram.

Correct flow:

```text
event
  -> notification_rule
  -> notification_target
  -> notification delivery/history
```

Reserved table:

```text
notification_rules
```

Rules:

```text
- Telegram is only one possible target.
- Throttling is required for repeated noisy events.
- Notification failure must not mutate customer/firewall/abuse state.
```

## Health Verdict and Incident Boundary

Operators and future buyer UI need simple verdicts, not raw counters only.

Reserved tables:

```text
customer_health_snapshots
incidents
incident_events
runbook_steps
```

Example health states:

```text
OK
Warning
Critical
Expired
Paused
Abuse Tracking
Hard
No Traffic
Backend Problem
Firewall Drift
```

Incident examples:

```text
backend_public_exposure
firewall_apply_failed
abuse_job_failed
backup_failed
proxy_down
postgres_unavailable
high_reject_rate
```

Rules:

```text
- incident/runbook entries guide the operator; they do not auto-apply dangerous fixes in early phases.
- runbook command hints must remain reviewable by a human.
```

## Config Snapshots and Secret References

Config changes and secret dependencies must be traceable.

Reserved tables:

```text
config_snapshots
secret_references
```

Rules:

```text
- config text may be snapshotted for audit/restore.
- raw secrets must not be stored in Git or DB.
- secret_references store path/name/status only, not secret values.
```

## Backup Verification and Restore Drills

Backup is not accepted until restore is tested.

Reserved table:

```text
restore_drills
```

Rules:

```text
- backups record creation
- restore_drills record whether restore was tested
- failed restore drill is an operational warning
```

## Maintenance Windows

Maintenance windows prevent planned work from looking like unexplained failure.

Reserved table:

```text
maintenance_windows
```

Allowed scopes:

```text
system
lane
customer
```

Example behaviors:

```text
read_only
pause_forwarding
suppress_notifications
```

Automation must not use maintenance windows to silently bypass abuse coverage unless a later phase explicitly defines and tests that behavior.

## Import Staging

Greenfield does not mean unsafe direct import. Old data must be staged first.

Reserved tables:

```text
import_batches
import_staged_customers
import_validation_errors
```

Correct flow:

```text
read old data
  -> validate
  -> stage
  -> show report
  -> operator confirms
  -> create through services
  -> firewall plan later
```

Rules:

```text
- import must not directly create firewall rules
- import must not bypass abuse coverage
- import must not write production state without validation and confirmation
```

## Worker Blocking Boundary

Worker names are observed inside Stratum-layer traffic. Firewall rules alone cannot reliably enforce worker-name policy.

Supported future stages:

```text
1. observe workers
2. map workers to customer/session/IP evidence
3. report worker identity and mismatches
4. define worker policy/block rules
5. enforce through a suitable adapter, later
```

Worker block must not be implemented as only an IP block. IP blocks may be a fallback action, but the worker policy must remain explicit.

Required future components:

```text
worker_identities
worker_policies
worker_blocks
worker_enforcement_events
worker_policy_service
worker_enforcement_adapter
```

Possible enforcement adapters:

```text
detection_only
stratum_proxy
manual_operator_action
```

Strict worker rejection requires Stratum-aware data-plane support. It must not be assumed available in firewall phases.

## Server Profile and Preflight History

Because target servers may have no GitHub/internet access, server state must be recorded and reviewed.

Reserved tables:

```text
server_profiles
preflight_runs
preflight_findings
```

Rules:

```text
- do not guess server capabilities
- preflight must happen before bootstrap or risky upgrades
- findings should guide runbooks and phase acceptance
```

## Retention Policy, Policy Simulation, and DTO Contracts

These are important but can stay documented until the relevant implementation phase.

Future reserved concepts:

```text
retention_policies
retention_runs
policy_simulations
firewall_plan_previews
abuse_simulations
service command objects / DTO contracts
```

Rules:

```text
- large tables need explicit retention before long-term production use
- dangerous policy changes should be simulated before apply
- CLI/UI/Telegram/API must share service command objects instead of duplicating logic
```

## Roadmap Placement

Buyer UI is after local read-only UI foundations:

```text
Phase 11: local Web UI read-only
Future: buyer-safe read-only reporting
Future: buyer action requests with operator review
```

Worker block enforcement is after session/worker timeline and evidence exist:

```text
Phase 10: session / worker / policy timeline
Future: worker policy reporting
Future: worker enforcement adapter
```

Plan/entitlement, feature flags, notification rules, config snapshots, server profiles, and restore drills may be modeled in Phase 2 but are not runtime features until later phase gates.

## Acceptance Requirements Before Implementation

Before buyer UI implementation:

```text
local UI auth boundary exists
buyer accounts are separate from operators and customers
buyer reports use service layer
read-only access is tested
no direct mutation path exists
```

Before worker block implementation:

```text
worker evidence quality is known
worker-to-session mapping is tested
policy service exists
adapter failure behavior is documented
operator-visible evidence is available
no firewall-only worker block assumption exists
```

Before import implementation:

```text
staging tables exist
validation report exists
operator confirmation exists
service-layer creation path exists
firewall plan is separate from import
```

Before notification rules are active:

```text
targets are configured without raw secrets
throttle is tested
failed notification is non-mutating
```
