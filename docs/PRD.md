# Product Requirements Document

Status: Canonical product contract

## Authority

This PRD defines static product scope and success criteria. Current runtime permissions, phase state, gates, and operational authorization are only in [`docs/PHASE_STATUS.md`](PHASE_STATUS.md).

## Product objective

`proxy-address-mining` is a Python-first mining customer gateway control plane.

## Primary operator outcome

Operators can safely manage customer-facing mining ports through CLI workflows that call service-layer contracts, produce auditable evidence, and avoid direct runtime mutation from interfaces.

## Product boundaries

- Forward-only customer gateway.
- PostgreSQL source of truth for customer, policy, usage, abuse, event, and audit state.
- Lane-based architecture for coins and backend routing.
- Local configuration in controlled config files, not mutable runtime state.
- Audited control plane where decisions, side effects, and restore paths are recorded.

## Required core capabilities

- Lane model.
- Customer lifecycle.
- Policy versioning.
- Firewall plan, diff, apply, verify, and rollback.
- Backend exposure guard.
- Usage, report, and check workflows.
- Block and pause controls.
- Backup and restore points.
- Event and audit records.
- One-hour miner-abuse state machine.

## Abuse product invariant

Every active customer in every enabled lane must be evaluated. The intended state machine is `normal -> over_tracking -> over_grace -> hard`. Hardening is only for sustained miner-abuse of approximately one hour. Farms-over alone must not cause hardening.

## Non-goals

- Direct legacy shell migration.
- Public web panel.
- Public API.
- Unrestricted production expansion.
- Worker enforcement before its explicit future phase.
- Telegram write actions.
- Billing.
- Multi-server dashboard.
- Direct nftables migration.

## Product success criteria

- Operators can understand intended customer, lane, policy, firewall, usage, abuse, and restore behavior from canonical documents.
- Interfaces remain thin and route behavior through services, repositories, adapters, events, and audit.
- Runtime-affecting workflows have planner, verifier, restore-point, evidence, event, audit, and rollback contracts.
- Static contracts do not duplicate dynamic phase snapshots or operational authorization.
- Historical documents, release notes, and archived evidence remain context only and are not treated as runtime authority.
