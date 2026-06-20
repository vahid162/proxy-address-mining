# WORKER POLICY

Status: future architecture contract
Runtime impact: none
Firewall impact: none
Production traffic impact: none
Database migration impact: none in the current phase

This document defines the future worker policy and worker routing boundary for `proxy-address-mining`.
It exists so AI coding agents do not accidentally implement worker behavior as unsafe firewall-only logic or premature automation.

## Contract boundary

Historical note: this contract was introduced during an earlier phase. Current phase, runtime authorization, and next required step are defined only in `docs/PHASE_STATUS.md`.

This document does **not** authorize worker runtime behavior.

Contract clarity: **worker enforcement is future-only** until the required evidence and adapter phases are accepted.

Forbidden now:

```text
worker scanner
worker guard
worker route enforcement
worker block enforcement
worker session kill
tcpdump job
conntrack job
systemd timer
firewall mutation
NAT redirect
production traffic
```

## Worker Identity Rule

Worker names are Stratum-layer identities.

They are not firewall-layer identities.

A firewall can reason about:

```text
source IP
source port
destination port
protocol
connection state
packet counters
```

A firewall cannot reliably reason about:

```text
worker name
normalized worker name
mining account string
Stratum authorize identity
share submit identity
```

Therefore worker blocking, worker routing, and worker policy must not be modeled as firewall-only rules.

## Required Future Flow

Future worker policy must follow this flow:

```text
worker observation
  -> worker identity normalization
  -> session/flow evidence
  -> worker policy service
  -> worker enforcement adapter, later
  -> event/audit/evidence
```

Required future data boundaries already represented or planned in the project include:

```text
worker_events
worker_identities
worker_policies
worker_blocks
worker_enforcement_events
flow_sessions
flow_events
customer_workers
policy_events
events
audit_log
```

## Evidence First

Strict worker enforcement is forbidden until evidence exists.

Minimum evidence requirements before enforcement:

```text
customer_id
lane_id
customer port
source IP
session evidence
worker_name
normalization result
confidence score
seen_at timestamp
evidence_json
```

Worker name alone is insufficient to identify a physical device.

Recommended early identity model:

```text
customer + lane + normalized_worker_name + src_ip + session evidence
```

## Worker Routing Contract

A future table may be introduced after explicit phase approval:

```text
worker_routing_rules
```

Purpose:

```text
Represent intent such as: this worker pattern should only appear on this customer port or lane.
```

Suggested fields:

```text
id
customer_id
worker_match_type
worker_pattern
required_lane_id
required_port
violation_action
starts_at
expires_at
status
reason
created_at
created_by
metadata_json
correlation_id
```

Recommended `worker_match_type` values:

```text
exact
prefix
regex
```

Recommended `violation_action` values:

```text
observe
notify
block_port_ip
reject_later
kill_session_later
```

The default safe mode must be:

```text
observe
```

Any action stronger than observe/notify requires later phase approval, evidence tests, adapter tests, event/audit, and rollback or operator recovery guidance.

## Allowed Future Modes

Worker policy enforcement modes:

```text
detection_only
manual_operator_action
stratum_proxy
```

### detection_only

Allowed after the session/worker evidence phase is accepted.

Behavior:

```text
observe violations
record evidence
report to operator
send notification later if enabled
no automatic reject
no automatic kill
no firewall mutation
```

### manual_operator_action

Allowed only after operator action paths are implemented with confirmation and audit.

Behavior:

```text
operator reviews evidence
operator creates block/pause/action request through service layer
event/audit is recorded
firewall changes, if any, go through firewall planner
```

### stratum_proxy

Allowed only after a Stratum-aware enforcement adapter exists and is tested.

Behavior:

```text
adapter can understand worker identity
adapter can reject or disconnect at protocol level
adapter records evidence
actions are audited
failure behavior is documented
```

## Forbidden Patterns

Forbidden permanently:

```text
worker block implemented only as IP firewall block
worker route implemented by guessing iptables rules
CLI parsing tcpdump output and mutating DB directly
Telegram running shell commands for worker control
UI writing worker policy tables directly
worker enforcement without event/audit
worker enforcement without evidence_json
worker enforcement before retention policy
```

## Relationship With Control Rules

Worker policy may later integrate with `docs/CONTROL_RULES.md`.

Possible future mapping:

```text
worker_blocks
  -> control_rules(rule_type=worker_block, scope_type=worker)

worker_routing_rules
  -> control_rules(rule_type=worker_route, scope_type=worker_port)
```

This mapping is future-only and must not introduce runtime behavior during Phase 5.

## Abuse Interaction

Worker-over may support diagnostics, but it must not replace miner-abuse detection.

Rules:

```text
farms-over alone must not harden
worker-over alone must not harden
sustained miner-abuse after about 3600 seconds is required for automatic hardening
all active customers in all enabled lanes must remain covered by abuse evaluation
```

A worker policy patch that weakens the one-hour abuse requirement must be rejected.

## Phase Placement

### Phase 5 — Customer CRUD in DB Only

Allowed:

```text
documentation only
future contract only
customer validation awareness
no worker runtime
```

### Phase 10 — Session / Worker / Policy / Share Timeline

Allowed after acceptance:

```text
worker observation
worker evidence
worker identity confidence
worker reporting
detection-only policy output
```

### Phase 15 or Later — Worker Policy Enforcement

Allowed after acceptance:

```text
worker block enforcement
worker route enforcement
session kill or reject adapter behavior
strict policy actions
```

## Acceptance Criteria for This Contract

This contract is accepted only when:

```text
pytest passes
Phase 5 remains DB-only
no worker runtime is added
no tcpdump/conntrack job is added
no firewall/NAT path is added
worker enforcement remains future-only
worker blocking is not modeled as firewall-only
abuse 1h coverage is preserved
```

A patch that adds worker enforcement before evidence and adapter support must be rejected.
