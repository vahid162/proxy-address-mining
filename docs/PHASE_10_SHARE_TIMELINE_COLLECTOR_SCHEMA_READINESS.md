# Phase 10 Share Timeline + Collector Schema Readiness

This document is schema-readiness only. No production DB execution is authorized in this PR.

## Proposed tables
- share_timeline_events
- share_timeline_rollups
- collector_dry_run_events
- collector_job_contract (or job_runs integration)

## share_timeline_events
Columns: share_event_id (pk), customer_id, lane_id, session_id nullable, worker_identity_id nullable, customer_port, src_ip nullable, worker_name nullable, share_status, reject_reason nullable, share_difficulty nullable, pool_difficulty nullable, pool_latency_ms nullable, observed_at, source, evidence_ref nullable, idempotency_key, created_at.
Indexes: (customer_id,lane_id,observed_at), (share_status,observed_at), (source,observed_at).
Idempotency: unique(idempotency_key).

## share_timeline_rollups
Columns: rollup_id (pk), customer_id, lane_id, window_start, window_end, accepted_count, rejected_count, stale_count, synthetic_count, accepted_difficulty, rejected_difficulty, created_at.
Indexes: (customer_id,lane_id,window_start), (window_end).

## collector_dry_run_events
Columns: dry_run_event_id (pk), collector_name, input_source, sample_size, validation_ok, failure_count, report_json, created_at.
Indexes: (collector_name,created_at), (validation_ok,created_at).

## collector_job_contract / job_runs integration
Collector dry-run execution must integrate with scheduler_locks + job_runs contracts before runtime phases. In this phase it remains contract-only.

## Retention + high-volume guard
- share_timeline_events: short retention with partition-ready design.
- rollups: longer retention.
- high-volume guard: ingestion thresholds and truncation/skip reporting are required before runtime.

## Future migration gate requirement
Any real migration must be gated by explicit accepted phase authorization and dedicated operator evidence.
