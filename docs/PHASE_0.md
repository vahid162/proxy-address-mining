# PHASE 0 — Architecture Freeze

Status: Draft v1

This document defines Phase 0 for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

Phase 0 is documentation-only.
No server mutation, package installation, service activation, firewall change, customer onboarding, or automation activation is allowed in this phase.

## 0. Purpose

Freeze architecture, scope, safety boundaries, data model, abuse requirements, and phase gates before any implementation or server bootstrap.

The goal is to prevent uncontrolled migration from old shell scripts and ensure the new system starts as a clean, testable, API-first Python project.

## 1. Fixed Project Decisions

The following decisions are frozen for the initial implementation:

```text
project type: greenfield rewrite
server role: forward-only customer gateway
source of truth: local PostgreSQL
configuration: /etc/mpf/mpf.yaml
code path: /opt/mpf-py
data path: /var/lib/mpf
log path: /var/log/mpf
backup path: /var/backups/mpf
CLI name: mpf
first lane: BTC
BTC backend port: 60010
firewall backend: iptables first
firewall apply mechanism: iptables-save / iptables-restore
scheduler: systemd timers
initial firewall mode: plan_only
UI/API binding: local-only
Telegram: future notification-first integration
```

## 2. In Scope for Phase 0

Allowed work:

1. Review old system behavior and operational capabilities.
2. Define target architecture.
3. Define API-first boundaries.
4. Define safety guardrails.
5. Define firewall lifecycle.
6. Define abuse state machine.
7. Define PostgreSQL data model contract.
8. Define roadmap and phase gates.
9. Define Phase 1 preflight checklist.
10. Update AI agent instructions.
11. Prepare documentation-only pull request.

## 3. Out of Scope for Phase 0

Forbidden work:

1. Install packages.
2. Create system users.
3. Create directories on production server.
4. Create PostgreSQL database/user.
5. Create Python virtual environment.
6. Run Docker or Docker Compose.
7. Start v2rayA, forwarder, or any proxy service.
8. Create customer records.
9. Create firewall rules.
10. Create NAT redirects.
11. Apply iptables or nftables changes.
12. Enable abuse runner.
13. Enable block/pause automation.
14. Enable UI or Telegram.
15. Onboard production traffic.

## 4. Required Phase 0 Documents

Phase 0 is complete only when these documents exist and agree with each other:

```text
docs/ARCHITECTURE.md
docs/SAFETY.md
docs/ABUSE.md
docs/FIREWALL.md
docs/DATA_MODEL.md
docs/ROADMAP.md
docs/PHASE_0.md
docs/PHASE_1.md
AGENTS.md
README.md
```

## 5. Architecture Acceptance

The architecture is accepted only if it documents:

1. API-first service boundary.
2. PostgreSQL as source of truth.
3. Lane model from day one.
4. BTC backend `60010`.
5. Firewall plan/diff/apply/verify/rollback lifecycle.
6. Abuse 1h state machine.
7. Event/audit requirement.
8. Restore point requirement.
9. Local-only UI/API rule.
10. Telegram future path without direct DB/firewall access.

## 6. API-First Acceptance

The following boundary must be documented and enforced in later phases:

```text
CLI / API / UI / Telegram / jobs
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Forbidden future patterns must be documented:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly writes DB
Telegram directly runs shell commands
job bypasses service validation
```

## 7. Firewall Acceptance

Firewall documentation must specify:

1. desired model generation
2. live firewall snapshot
3. human-readable plan
4. JSON plan
5. restore point before apply
6. live firewall backup
7. lock before apply
8. atomic apply through `iptables-restore`
9. verify after apply
10. rollback from stored artifact
11. backend exposure guard
12. drift detection
13. no one-off production iptables mutation

## 8. Abuse Acceptance

Abuse documentation must specify:

```text
normal -> over_tracking -> over_grace -> hard
```

And these rules:

1. All active customers in all enabled lanes are scanned.
2. No silent skip is allowed.
3. Exemption requires reason and expiry.
4. Farms-over alone does not harden.
5. Sustained miner-abuse hardens after about 3600 seconds.
6. Hard creates restore point.
7. Hard creates policy backup.
8. Hard uses firewall plan/apply/verify path.
9. Hard flushes affected conntrack scope.
10. Manual unhard is audited.

## 9. Data Model Acceptance

Data model documentation must represent:

1. lanes
2. lane upstreams
3. customers
4. versioned customer policies
5. customer IP pins
6. events
7. audit log
8. firewall applies
9. firewall snapshots
10. restore points
11. usage samples
12. policy events
13. flow/session records
14. worker events
15. abuse states
16. abuse events
17. job runs
18. scheduler locks
19. blocks
20. pauses
21. backups
22. notification targets
23. API tokens for future local API/UI/Telegram

## 10. Roadmap Acceptance

Roadmap must define numbered phases and gates:

```text
0. Architecture Freeze
1. Preflight + Bootstrap Without Traffic Changes
2. PostgreSQL + Config + Domain Model
3. CLI + Internal API Foundation
4. Compose Forward-only + Proxy Doctor
5. Customer CRUD in DB Only
6. Firewall Planner + Apply/Verify/Rollback
7. Usage + Policy/Reject Accounting
8. Abuse 1h Core
9. Check / Report / Diagnostics
10. Session / Worker / Policy Timeline
11. Local Web UI Read-only
12. UI Actions With Confirmation
13. Telegram Notifications, Read-only Commands, Restricted Actions
```

## 11. Required Stop Conditions

Phase 0 output must define stop conditions for later phases, including:

1. Firewall apply introduced before Phase 6.
2. Abuse automation introduced before Phase 8.
3. UI writes directly to DB.
4. Telegram runs shell commands.
5. Customer rules created during Phase 1.
6. NAT redirects created during Phase 1.
7. Backend becomes publicly exposed.
8. `apply_mode=plan_only` is bypassed.
9. TSV/SQLite becomes production source of truth.
10. Customer is excluded from abuse without valid exemption.

## 12. Phase 0 Review Checklist

Before Phase 0 is accepted, verify:

```text
[ ] README matches the roadmap.
[ ] AGENTS.md points AI agents to required docs.
[ ] Architecture doc states API-first boundaries.
[ ] Safety doc defines forbidden actions.
[ ] Firewall doc forbids ad-hoc production mutations.
[ ] Abuse doc preserves one-hour hardening rule.
[ ] Data model doc includes restore points and job_runs.
[ ] Roadmap defines gates and stop conditions.
[ ] Phase 1 doc contains preflight and smoke tests.
[ ] No implementation files were introduced by mistake.
[ ] No server commands are required by Phase 0.
```

## 13. Phase 0 Deliverable

Expected deliverable:

```text
documentation-only pull request
```

The pull request must include:

1. summary of architecture freeze
2. safety rules
3. phase roadmap
4. explicit statement that no production runtime behavior changed

## 14. Phase 0 Completion Criteria

Phase 0 is complete only when:

```text
all required docs exist
all docs agree on core decisions
AI agent instructions are updated
review confirms no runtime/server changes
Phase 1 preflight is ready
```

## 15. Transition to Phase 1

After Phase 0 is accepted, Phase 1 may start with server preflight.

Phase 1 must not assume server state.
It must inspect first, then decide exact bootstrap commands based on real output.
