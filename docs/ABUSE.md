# ABUSE

Status: Draft v1

This document defines mandatory miner-abuse handling for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

## Goal

Every active customer in every enabled lane must be protected by a one-hour miner-abuse state machine.

Abuse handling is a core feature, not a later patch.

Required state flow:

```text
normal
  -> over_tracking
  -> over_grace
  -> hard
```

Hardening must happen only after sustained miner-abuse for about one hour.

## Definitions

### Customer Capacity Fields

Each customer policy has at least:

```text
miners
farms
maxconn
rate_per_min
burst
```

Meaning:

- `miners`: allowed miner/session capacity
- `farms`: allowed farm/IP grouping capacity
- `maxconn`: current firewall connection limit
- `rate_per_min`: hashlimit rate
- `burst`: hashlimit burst

### Miner-Abuse

Miner-abuse means the customer is using more miner/session capacity than allowed.

Primary signal:

```text
hot_sessions > miners
```

Equivalent implementations may use active conntrack/session counts if they are mapped reliably to customer ports.

### Farms-Over

Farms-over means unique source IP/farm count exceeds the allowed `farms` value.

Signal:

```text
unique_source_ips > farms
```

Farms-over alone must never trigger hardening.
It may be reported and audited, but it is not enough for `hard`.

### Worker-Over

Worker-over means detected unique mining workers exceed allowed miner capacity.

Signal:

```text
unique_workers > miners
```

Worker-over is supporting evidence.
It can strengthen diagnostics, but hardening must be based on sustained miner-abuse.

## Required Coverage

The abuse runner must scan:

```text
all active customers
in all enabled lanes
with non-expired policies
unless explicitly exempt
```

Forbidden exclusions:

- customer created by old/import tooling
- customer in a non-BTC enabled lane
- customer without recent usage sample
- customer with missing optional IP whitelist
- customer with manually edited policy

If a customer cannot be evaluated, the job must record a failed/evaluation-missing event.
Silent skipping is forbidden.

## Exemption Rules

A customer may be exempt only when all fields exist:

```text
abuse_exempt = true
abuse_exempt_reason is not empty
abuse_exempt_until is set
abuse_exempt_by is recorded
abuse_exempt_event_id is recorded
```

Expired exemptions must be ignored.

Permanent exemptions are forbidden unless explicitly represented as a reviewed policy decision in docs and DB schema.

## State Machine

### State: normal

Default healthy state.

On miner-abuse:

```text
normal -> over_tracking
```

Record:

- first_seen_over
- last_seen_over
- current_hot
- current_unique_ips
- evidence snapshot
- event: `abuse.entered_over_tracking`

### State: over_tracking

Customer is currently over miner capacity.

If miner-abuse continues:

- update last_seen_over
- update current_hot
- increment consecutive hit counters where useful
- keep original first_seen_over

If elapsed over time reaches threshold:

```text
over_tracking -> hard
```

Threshold default:

```yaml
abuse:
  threshold_sec: 3600
```

If miner-abuse stops before threshold:

```text
over_tracking -> over_grace
```

Record:

- last_recovery_at
- event: `abuse.entered_over_grace`

### State: over_grace

Customer recently recovered from miner-abuse.

If miner-abuse returns during grace:

```text
over_grace -> over_tracking
```

The implementation must preserve enough timing context to avoid resetting the whole one-hour window incorrectly.
Exact policy must be deterministic and tested.

If grace expires without miner-abuse:

```text
over_grace -> normal
```

Default grace:

```yaml
abuse:
  grace_sec: 900
```

Record:

- event: `abuse.recovered_normal`

### State: hard

Customer has been hardened because miner-abuse persisted for about one hour.

Hard state must remain until explicit unhard or policy change through approved service action.

Entering hard requires:

- restore point
- policy backup
- firewall plan
- firewall apply
- conntrack flush for affected customer/port
- event record
- audit record

## Hard Action

Hardening means:

```text
set effective maxconn to miners
preserve rate_per_min
preserve burst
apply firewall safely
flush conntrack for affected customer port
record event/audit
```

Hardening must not delete the customer's original policy.
The original policy must be restorable.

Suggested DB fields:

```text
abuse_states.customer_id
abuse_states.status
abuse_states.first_seen_over
abuse_states.last_seen_over
abuse_states.last_recovery_at
abuse_states.hard_applied_at
abuse_states.current_hot
abuse_states.current_unique_ips
abuse_states.current_unique_workers
abuse_states.policy_backup_id
abuse_states.restore_point_id
abuse_states.updated_at
```

Suggested event types:

```text
abuse.entered_over_tracking
abuse.entered_over_grace
abuse.recovered_normal
abuse.hard_planned
abuse.hard_applied
abuse.hard_failed
abuse.unhard_planned
abuse.unhard_applied
abuse.unhard_failed
abuse.exempt_added
abuse.exempt_expired
abuse.evaluation_failed
```

## Manual Hard and Unhard

### Manual Hard

Manual hard may exist for emergency operations, but it must use the same service path as automatic hard.

Required:

- operator identity
- reason
- restore point
- policy backup
- firewall plan/apply/verify
- event/audit record

### Manual Unhard

Manual unhard must restore or set a reviewed policy.

Required:

- operator identity
- reason
- restore point
- target policy after unhard
- firewall plan/apply/verify
- event/audit record

Unhard must not silently restore stale policy if the customer was edited after hardening.
Conflict handling must be explicit.

## Evidence Sources

Allowed evidence sources:

- conntrack snapshot
- firewall counters
- usage samples
- flow/session ledger
- worker events
- policy/reject events

The first production implementation may rely primarily on conntrack and firewall/accounting counters.
Worker evidence can be added after session/worker timeline matures.

## Evaluation Algorithm

Reference behavior:

```text
for each enabled lane:
  load active customers
  for each customer:
    if valid exemption exists:
      record/skip as exempt
      continue

    collect current evidence
    if evidence missing:
      record evaluation_failed
      continue

    miner_over = hot_sessions > customer.miners
    farms_over = unique_source_ips > customer.farms
    worker_over = unique_workers > customer.miners, if available

    update audit/evidence fields

    if state == normal:
      if miner_over: enter over_tracking

    elif state == over_tracking:
      if miner_over and elapsed(first_seen_over) >= threshold_sec:
        harden
      elif miner_over:
        keep over_tracking
      else:
        enter over_grace

    elif state == over_grace:
      if miner_over:
        return to over_tracking using deterministic timing policy
      elif elapsed(last_recovery_at) >= grace_sec:
        return to normal
      else:
        keep over_grace

    elif state == hard:
      keep hard until approved unhard or policy action
```

Farms-over and worker-over should appear in reports and events, but farms-over alone must not call `harden`.

## Timing Rules

Default values:

```yaml
abuse:
  enabled: true
  threshold_sec: 3600
  grace_sec: 900
```

Recommended runner interval:

```text
60s to 300s
```

The one-hour threshold should be implemented using timestamps, not by assuming a fixed number of job runs.

Reason:

- jobs can be delayed
- server can reboot
- scheduler can skip a run
- manual execution can happen

## Conntrack Flush

After hardening, active abusive connections for the affected customer port should be flushed so the new policy takes effect.

Flush must be scoped to the affected customer/port where possible.

Forbidden:

```text
flush all conntrack entries globally without documented emergency reason
```

## API-First Boundary

Allowed entrypoints:

```text
mpf abuse run
mpf abuse status
mpf abuse hard <target> --yes
mpf abuse unhard <target> --yes
future API endpoint
future UI action
future Telegram command
```

All entrypoints must call:

```text
abuse_service
```

Interfaces must not implement the state machine.

Forbidden:

```text
CLI computes abuse transition directly
UI updates abuse_states directly
Telegram runs shell command to change maxconn
job writes hard state without firewall service
```

## Reports and Operator Output

`mpf abuse status` must show:

- customer name
- lane
- port
- miners
- farms
- maxconn
- current hot sessions
- current unique IPs
- current unique workers, if available
- state
- first_seen_over
- last_seen_over
- elapsed over time
- hard_applied_at
- exemption status
- latest event

`mpf audit miners-over` must show customers where miner-abuse is active or recent.

`mpf audit farms-over` must show farms-over without hardening them automatically.

## Failure Handling

If evidence collection fails:

- do not harden
- record `abuse.evaluation_failed`
- mark job as degraded or failed depending on coverage

If firewall plan fails:

- do not harden
- record `abuse.hard_failed`

If firewall apply fails:

- do not mark hard as applied
- record failure
- produce rollback/restore guidance

If conntrack flush fails after successful firewall apply:

- keep hard state if firewall is verified
- record warning event
- report to operator

## Tests Required

Minimum unit tests:

- normal remains normal when within limits
- normal enters over_tracking on miner-over
- farms-over alone does not harden
- worker-over alone does not harden
- over_tracking continues while miner-over persists
- over_tracking enters over_grace when miner-over stops
- over_grace returns to normal after grace expires
- over_grace returns to over_tracking if miner-over returns
- sustained miner-over for about 3600s enters hard
- hard creates restore point
- hard creates policy backup
- hard calls firewall service
- hard records event
- manual unhard records event
- exemption requires reason and expiry
- expired exemption is ignored
- all active customers in enabled lanes are scanned

Minimum integration tests:

- abuse runner scans multi-lane active customers
- evidence-missing customer records evaluation failure
- firewall failure prevents hard-applied state
- verified hard action changes effective maxconn
- unhard conflict is detected when policy changed after hard

## Acceptance Checklist

Abuse implementation is accepted only when:

- all active customers in all enabled lanes are covered
- no silent skip exists
- exemption requires reason and expiry
- farms-over alone never hardens
- sustained miner-abuse hardens after about one hour
- hard creates restore point and policy backup
- hard uses firewall planner/apply/verify path
- conntrack flush is scoped and audited
- manual unhard is audited
- test suite covers state machine and failure cases

A patch that weakens the one-hour abuse requirement must be rejected.
