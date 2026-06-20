# SAFETY

Status: Canonical safety contract

## Authority

[`docs/PHASE_STATUS.md`](PHASE_STATUS.md) alone controls current runtime authorization. Architecture-stage or historical examples in this safety contract do not authorize current work or any runtime mutation.

## Historical preservation

Detailed legacy safety rationale and historical phase examples are preserved as non-authorizing context in [`docs/history/SAFETY_LEGACY_0.1.301.md`](history/SAFETY_LEGACY_0.1.301.md). Do not use that archive as current runtime authorization.

## Safety goal

The project manages customer-facing mining gateway traffic and firewall policy. Mistakes can disconnect customers, expose backend ports, or block valid traffic. The default posture is fail-closed and evidence-backed.

## Non-negotiable constraints

- PostgreSQL is the source of truth.
- `/etc/mpf/mpf.yaml` is configuration, not mutable runtime state.
- CLI, UI, buyer UI, Telegram, and future API must use the same service layer.
- Business logic must not live in CLI handlers.
- No interface may directly write DB tables.
- No interface may directly run iptables commands.
- No recurring job may bypass service validation.
- No customer firewall mutation may happen while config says plan-only.
- No destructive action may run without an event record.
- No dangerous action may run without a restore point.
- Secrets must not be committed to the repository.
- Backend ports must not be publicly exposed.
- v2rayA UI must not be publicly exposed.
- Early Web UI must not be publicly exposed.
- Buyer UI must be read-only first.
- Buyer accounts must remain separate from customer service/port records.
- Worker block must not be modeled as firewall-only.
- Feature flags must not bypass phase gates.
- Phase 12, worker enforcement, UI, Telegram, unrestricted onboarding, and unrestricted production expansion are governed only by current dynamic state in `docs/PHASE_STATUS.md`.

## Required side-effect workflow

All external side effects must pass:

```text
plan -> backup/restore point -> lock -> atomic apply -> verify -> event/audit -> rollback path
```

A failed verify must produce a fail-closed result and a rollback path. It must never silently leave an unverified partial state.

## API-first safety boundary

Correct pattern:

```text
CLI / API / UI / Buyer UI / Telegram
  -> request DTO / command object
  -> service layer
  -> repository / adapter
  -> event + audit
  -> response DTO
```

Forbidden pattern:

```text
CLI -> subprocess("iptables ...")
UI -> direct SQL update
Buyer UI -> direct customer/firewall/policy/abuse mutation
Telegram -> shell command
job -> direct table mutation without service validation
```

The service layer owns validation, state transitions, audit, and side-effect ordering.

## Firewall safety

All firewall changes must go through `firewall_service` and firewall adapters. Required detection before apply includes port collision, lane backend collision, customer chain collision, orphan chain, backend direct exposure, drift, missing accounting rules, missing NAT redirect, duplicated rules, and unsupported backend conditions.

Direct one-off production mutations such as `iptables -A`, `iptables -D`, `iptables -I`, or `iptables -F` are forbidden from interfaces and operator shortcuts.

## Database safety

Production database mutation must go through services and repositories with explicit transaction boundaries, event/audit consistency, and active-gate authorization. Direct database mutation from CLI/UI/API/Telegram handlers is forbidden.

## Buyer, UI, Telegram, and public exposure safety

Buyer-facing, UI, and Telegram features are future gated interfaces. They must not directly mutate customer policy, firewall, abuse, block, pause, or database state. Backend ports, UI surfaces, and APIs must not be publicly exposed unless current dynamic state explicitly authorizes the exact exposure.

## Worker safety

Worker names are Stratum-layer identities, not firewall-layer identities. Worker enforcement requires worker/session evidence, approved adapters, service-layer decisions, and event/audit records. Production worker enforcement remains governed only by current dynamic state.

## Extension safety

Extension-ready schema or documentation does not mean runtime activation. Feature flags must default sensitive capabilities to disabled, notification rules must not hardwire Telegram as the only target, import staging must not directly create live customers or firewall rules, config snapshots must not store raw secrets, and restore drills are required before backup strategy is trusted.
