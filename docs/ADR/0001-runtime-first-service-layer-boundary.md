# 0001: Runtime-first service-layer boundary

## Status: Accepted

## Context

The control plane manages customer-facing mining gateway behavior where direct interface mutations can affect firewall policy, database state, customer availability, auditability, and rollback safety. Future interfaces must not become separate backends with duplicated business logic.

## Decision

Business logic lives in services and domain modules. Repositories own PostgreSQL persistence. Adapters own external I/O. CLI, API, UI, and Telegram are thin interfaces over the service layer. Runtime mutations remain subject to active-gate authorization and the safety workflow. Future interfaces cannot bypass service, audit, restore-point, or evidence boundaries.

## Consequences

- Shared behavior is implemented once in services/domain.
- Persistence is isolated in repositories.
- Firewall, Docker, conntrack, systemd, network, and notification effects are isolated in adapters.
- Interfaces can evolve without weakening safety or audit requirements.
- Runtime work remains reviewable, gated, and rollback-aware.

## Alternatives considered

- Interface-owned business logic: rejected because CLI/UI/Telegram behavior would diverge and bypass auditability.
- Direct SQL or firewall commands in handlers: rejected because it bypasses validation, restore points, and verification.
- Legacy shell migration as the core architecture: rejected because it preserves unsafe coupling instead of creating a testable Python control plane.

## Compliance expectations

New code must keep interfaces thin, route decisions through services/domain, use repositories for PostgreSQL, use adapters for external I/O, and preserve planner, verifier, restore-point, evidence, event, audit, and rollback boundaries for runtime-affecting workflows.
