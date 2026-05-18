# Phase 10 Session/Worker/Policy Schema Readiness

This document defines additive schema readiness only. It does not authorize production DB execution.

## Proposed tables
- session_observations
- worker_identities
- worker_policy_contracts
- worker_policy_events

## session_observations
Columns: session_id (pk), customer_id, lane_id, customer_port, src_ip, src_port, worker_identity_id nullable, opened_at, closed_at nullable, last_seen_at, state, source, evidence_ref nullable, created_at.
Indexes: (customer_id,lane_id,last_seen_at), (src_ip,src_port,last_seen_at).
Idempotency: unique(session_id).
Retention: time-based retention, partition-ready.

## worker_identities
Columns: worker_identity_id (pk), customer_id, lane_id, worker_name, normalized_worker_name, first_seen_at, last_seen_at, source, status, evidence_ref nullable, created_at.
Indexes: (customer_id,lane_id,normalized_worker_name), (last_seen_at).
Idempotency: unique(customer_id,lane_id,normalized_worker_name).
Retention: active + historical evidence retention policy required before runtime enablement.

## worker_policy_contracts
Columns: policy_id (pk), customer_id, lane_id, mode, allowed_workers jsonb, denied_workers jsonb, max_workers nullable, violation_action, enforcement_enabled false-by-default, created_at, updated_at.
Indexes: (customer_id,lane_id,updated_at).
Idempotency: unique(customer_id,lane_id,mode,updated_at).

## worker_policy_events
Columns: event_id (pk), policy_id, customer_id, lane_id, event_type, payload_json, created_at.
Indexes: (policy_id,created_at), (customer_id,lane_id,created_at).

## Future migration gate requirement
Any production migration execution requires explicit accepted phase gate and dedicated operator evidence. This document is planning/readiness only.
