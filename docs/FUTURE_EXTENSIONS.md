# Future Extensions Contract

Status: future-facing architecture contract

This document reserves the architecture boundaries for capabilities that are intentionally not implemented in early phases but must not be blocked by early design choices.

## Scope

Future extensions covered here:

```text
buyer-facing read-only panel
buyer action requests
worker identity timeline
worker block policy
worker enforcement adapter
```

These capabilities are future work. Their schema and service boundaries may exist in Phase 2, but production behavior must wait for the appropriate phase gates.

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

## Phase Safety

In Phase 2, only schema and contracts are allowed.

Forbidden in Phase 2:

```text
buyer login service
public buyer UI
worker enforcement
Stratum-aware production proxy changes
firewall apply
NAT redirects
abuse automation
```

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
