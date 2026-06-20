# ROADMAP

Status: Canonical long-term product roadmap

## Authority

Runtime-first work, when current dynamic state names it, is routed through [`docs/AI_SAFE_RUNTIME_FIRST.md`](AI_SAFE_RUNTIME_FIRST.md).

This roadmap describes product evolution only. It does not define current runtime permissions, current gates, customer authorization, production traffic state, or next required work. [`docs/PHASE_STATUS.md`](PHASE_STATUS.md) is the only current-state authority.

## Ordering principles

- Build stable architecture and safety foundations before runtime expansion.
- Keep interfaces thin and service-layer backed.
- Advance from local, auditable control-plane capabilities toward future interfaces only after explicit gates.
- Treat Phase 12, worker enforcement, UI, and Telegram as future gated stages, not present authorization.

## 1. Architecture and foundations

Define product scope, safety rules, architecture boundaries, data ownership, local configuration, migrations, versioning, testing, and documentation contracts.

## 2. Control plane

Implement Python-first CLI/service workflows backed by PostgreSQL, repositories, adapters, event records, audit records, locks, restore points, and explicit diagnostics.

## 3. Data plane

Model the forward-only gateway path:

```text
customer_port -> firewall policy -> NAT redirect -> lane backend -> forwarder -> v2rayA -> pool
```

Keep backend exposure guarded and lane routing explicit.

## 4. Customer lifecycle

Support customer create, renew, pause, block, expire, restore, and report flows through service-layer validation and audit.

## 5. Firewall

Provide plan, diff, package, apply, verify, rollback, drift detection, backend exposure checks, and fail-closed diagnostics through firewall services and adapters.

## 6. Usage

Expose usage, report, and check workflows that let operators verify customer-facing behavior without bypassing service boundaries.

## 7. Abuse

Implement the one-hour miner-abuse state machine for all active customers in all enabled lanes. Farms-over alone must not harden a customer.

## 8. Diagnostics

Provide doctor, readiness, evidence, and validator commands that make operator decisions reproducible without mutating runtime state unexpectedly.

## 9. Timeline and observability

Build session, worker, policy, share, and hash-rate observability as first-class evidence layers rather than UI-only calculations.

## 10. Future UI

Future UI is a local, gated interface over existing services. It must not directly write the database, mutate firewall state, or expose untrusted HTML unsafely.

## 11. Future Telegram

Future Telegram support is a gated interface over services. Write actions remain forbidden until explicitly authorized by current dynamic state and safety contracts.

## 12. Future worker enforcement

Worker enforcement is a future gated stage requiring session/worker evidence, approved adapters, service-layer decisions, event/audit records, and rollback/disable paths.
