# Hash-rate and Share Observability

Status: future capability contract

This document reserves the architecture for accepted/rejected hash-rate reporting per device and future charts.

It is a planning contract only. It does not activate collectors, packet capture, proxy parsing, UI charts, or production traffic.

## Goal

The system must eventually report, per customer and per mining device:

```text
accepted share count
rejected share count
accepted difficulty
rejected difficulty
accepted hash-rate
rejected hash-rate
reject ratio
recent trend
chartable time-series
```

## Why This Must Be Planned Early

Hash-rate and share data can become high-volume time-series data.
If it is added later as ad-hoc logs or UI-only calculations, the project will become hard to scale and hard to maintain.

The correct approach is:

```text
Stratum/share evidence
  -> normalized raw or near-raw share events
  -> aggregate samples
  -> report service
  -> API/CLI/UI charts
```

## Device Identity

A device is not always a guaranteed physical ASIC identity.

In early implementations, device identity may be derived from:

```text
customer_id
lane_id
normalized_worker_name
src_ip
session evidence
```

Worker name alone must not be treated as a guaranteed physical device.
Multiple devices may share a worker name. One device may change IP. The model must preserve evidence and confidence.

## Future Data Model

The following tables should be added when the matching phase is approved.
They are not required in the current Phase 3.1 server migration.

### `mining_devices`

Purpose: stable observed device identity derived from worker/session evidence.

Suggested fields:

```text
id
customer_id
lane_id
worker_identity_id
normalized_worker_name
last_src_ip
first_seen_at
last_seen_at
status
identity_confidence
metadata_json
created_at
updated_at
```

### `share_events`

Purpose: raw or near-raw share evidence.

Suggested fields:

```text
id
customer_id
lane_id
mining_device_id
flow_session_id
worker_name
src_ip
share_result          accepted / rejected / stale / duplicate / invalid / unknown
difficulty
job_id
reject_reason
seen_at
evidence_json
created_at
```

Raw share events may be high volume. They require retention and partitioning review before production collection.

### `device_hashrate_samples`

Purpose: chartable aggregate time-series per mining device.

Suggested fields:

```text
id
customer_id
lane_id
mining_device_id
window_start
window_end
accepted_shares
rejected_shares
accepted_difficulty
rejected_difficulty
accepted_hashrate_hps
rejected_hashrate_hps
reject_ratio
source
confidence
created_at
```

### `customer_hashrate_samples`

Purpose: chartable aggregate time-series per customer.

Suggested fields:

```text
id
customer_id
lane_id
window_start
window_end
accepted_shares
rejected_shares
accepted_difficulty
rejected_difficulty
accepted_hashrate_hps
rejected_hashrate_hps
reject_ratio
source
confidence
created_at
```

## Aggregation Rule

UI charts must use aggregate samples, not raw high-volume share events.

Recommended flow:

```text
share_events or Stratum parser evidence
  -> aggregation job
  -> device_hashrate_samples / customer_hashrate_samples
  -> report service
  -> API DTO
  -> UI chart
```

## Retention Rule

Retention must be defined before high-volume collection starts.

Suggested policy:

```text
share_events: short retention, partitioned by time
hashrate_samples: longer retention, downsampled as needed
chart API: reads samples only
```

Exact retention should be decided before Phase 10 or before any Stratum/share collector is activated.

## Phase Placement

The feature should be implemented in stages:

```text
Phase 3.1: documentation and architecture contract only
Phase 7: make usage/accounting model compatible with future hash-rate samples
Phase 10: session/worker/share evidence and aggregation foundations
Phase 11+: read-only UI charts from aggregate samples
Later: advanced device identity and confidence improvements
```

No runtime share capture should be activated before data-plane, retention, and privacy/safety contracts are accepted.

## Service Boundaries

Suggested future services:

```text
share_observation_service
hashrate_aggregation_service
hashrate_report_service
```

Suggested future repositories:

```text
share_event_repo
mining_device_repo
hashrate_sample_repo
```

Interfaces must not compute business meaning directly.
CLI/API/UI should ask report services for normalized output.

## Test Requirements

Before production acceptance:

```text
accepted share aggregation works
rejected share aggregation works
reject_ratio handles zero-share windows safely
worker name alone is not treated as guaranteed device identity
samples are tied to customer and lane
chart queries read aggregate samples, not raw share_events
retention/partition assumptions are tested or documented
aggregation job is idempotent per time window
```

## Stop Conditions

Stop and revise if a patch introduces:

```text
raw share collection without retention policy
UI charts reading raw share_events directly
hash-rate stored only in logs
worker name treated as a guaranteed physical device
high-volume polling without job_runs/scheduler_locks
collector bypassing service/repository boundaries
share parser coupled directly to UI or Telegram
```
