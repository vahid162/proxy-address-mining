# AI Phase 6-A1 Codex Task — Firewall Planner Domain + Dry-Run Plan

Status: ready for Codex implementation

This task is the first implementation slice after the Phase 6 cleanup gate.

## Current Gate

Authoritative source:

```text
docs/PHASE_STATUS.md
```

Current state:

```text
accepted phase: Phase 5 — Customer CRUD in DB Only accepted on farm5
working phase: Phase 6 — Firewall Planner
sub-step: Phase 6-A1 — Firewall planner domain, desired model, diff model, and dry-run rendering
production traffic: none
live firewall apply: not allowed
customer NAT redirects: not allowed
customer firewall rules: not allowed
abuse automation: not allowed
```

## Goal

Implement the first safe firewall planner foundation.

This task must produce a model-driven firewall plan from config/DB-shaped inputs and render it in both human-readable and JSON-friendly forms.

Phase 6-A1 must not mutate the live firewall, run `iptables-restore`, create customer NAT redirects, create live firewall rules, start timers, or activate production traffic.

## Mandatory Reading Before Coding

Read these files first:

```text
AGENTS.md
README.md
docs/INDEX.md
docs/PHASE_STATUS.md
docs/AI_CODING_RULES.md
docs/AI_PHASE_6_TASK.md
docs/FIREWALL.md
docs/BACKEND_PORT_POLICY.md
docs/SAFETY.md
docs/DATA_MODEL.md
docs/TAXONOMY.md
docs/ABUSE.md
```

## Allowed Scope

Allowed implementation:

```text
firewall desired-state domain dataclasses or Pydantic DTOs
firewall plan/diff result objects
pure planner service that accepts config/DB-shaped records and optional live-state input
human-readable plan renderer
JSON-serializable plan output
planner errors/warnings model
unit tests for planner behavior
CLI read-only commands only if thin and service-backed
```

Allowed CLI commands for this task, if implemented:

```text
mpf firewall plan
mpf firewall diff
```

These commands must be read-only and dry-run only.

## Forbidden Scope

Do not implement, run, or activate:

```text
mpf firewall apply
mpf firewall rollback
mpf firewall verify as live mutation
iptables-restore
live firewall mutation
customer NAT redirects
customer firewall rules in the live system
conntrack flush
usage timers
hash-rate/share collectors
abuse runner automation
block/pause automation
UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

It is acceptable to define future enum values or placeholder DTO fields for applyability, but no production apply path may exist.

## Required Design

Use the existing project boundary:

```text
CLI/API -> request DTO -> service -> domain/planner -> response DTO
```

Do not put business logic inside `mpf/interfaces/cli.py`.

Suggested files:

```text
mpf/domain/firewall.py
mpf/services/firewall_planner_service.py
tests/test_phase6_firewall_planner_domain.py
tests/test_phase6_firewall_planner_service.py
tests/test_phase6_firewall_cli.py   # only if CLI commands are added
```

Use different file names if they fit the existing style better, but preserve the service/domain/interface boundary.

## Desired Model Requirements

The desired model should represent intent only.

It should include at least:

```text
backend: iptables
apply_mode: plan_only
tables referenced, at minimum filter and nat as planned model names
chain intents
rule intents
lane backend coverage
customer coverage
customer policy references
backend guard intent
warnings
errors
applyable boolean
```

## Plan/Diff Requirements

The plan result must distinguish:

```text
create
keep
update
delete
warning
error
```

For Phase 6-A1, live-state input may be a simple in-memory structure, fixture, or empty-live-state object.

Do not shell out to `iptables-save` yet unless implemented as a strictly read-only adapter with tests and no dependency on live system state.

## Required Safety Behavior

Planner result must become non-applyable when errors exist.

At minimum, tests must cover:

```text
empty active customer set produces a valid no-customer plan
active customer produces desired customer rule intents without mutating firewall
plan output includes firewall_change: planned_only or equivalent
plan output includes nat_change: planned_only or equivalent
plan output includes runtime_change: no
plan with backend exposure error is not applyable
plan with customer port collision is not applyable
plan with lane backend collision is not applyable
JSON output is stable and serializable
human output is readable and includes warnings/errors
```

## Customer and Lane Rules

Use existing DB/config concepts:

```text
lane.name
lane.enabled
lane.backend_port
lane.chain_prefix
customer.id
customer.customer_key
customer.port
customer.status
customer.lane
customer policy: miners, farms, maxconn, rate_per_min, burst, ips_mode
```

Deleted customers must not generate active desired firewall intents.

Paused/expired status behavior may be represented as warnings or future placeholders if the exact firewall behavior is not finalized yet.

## Backend Port Policy

Preserve this invariant:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Do not block loopback, Docker/internal paths, or the future MPF-owned NAT redirect path just to hide backend ports externally.

Docker-managed local-only DNAT for `127.0.0.1:2015` and `127.0.0.1:60010` in the accepted Phase 4 runtime is informational and must not be treated as customer NAT.

## Version and Changelog

Because this task adds code, update:

```text
mpf/__init__.py
pyproject.toml
CHANGELOG.md
```

Use the next patch version after the current repository version.

The changelog entry must explicitly say this is planner-only and introduces no live firewall/NAT/runtime mutation.

## Acceptance Commands

Codex must leave the repo passing:

```bash
python -m pytest -q
```

After syncing to farm5, the operator will run:

```bash
cd /opt/mpf-py-src
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db status
mpf proxy doctor
./.venv/bin/python -m pytest -q
bash scripts/verify_current_phase_gate.sh
```

Expected server invariants after sync:

```text
production_traffic: none
firewall_apply_allowed: no
abuse_automation_allowed: no
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: false
no MPF/customer firewall references
no customer NAT redirects
limited runtime listeners remain local-only
```

## Stop Conditions

Stop and revise if any change introduces:

```text
live firewall apply
iptables-restore
customer NAT redirect creation
customer firewall rule creation in live system
traffic-changing behavior
usage timer
abuse automation
backend public exposure
backend internal reachability failure
business logic inside CLI handlers
production TSV/SQLite source of truth
worker blocking as firewall-only
```

## Final Output Expected From Codex

Codex should produce one focused patch that includes:

```text
firewall planner domain model
planner service
human and JSON plan rendering
unit tests
optional thin CLI dry-run plan/diff commands
version/changelog update
no runtime firewall/NAT/apply behavior
```
