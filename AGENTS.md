# AI Agent Instructions

This repository is a Python-first, API-first greenfield rewrite of a mining proxy customer gateway control plane.

The project replaces an older shell-script-based operational setup, but it must not copy, patch, or extend the old scripts directly. The goal is to preserve operational capabilities while implementing a clean, testable, PostgreSQL-backed Python architecture.

This file is mandatory reading for every human contributor and AI coding agent before making changes.

## 1. Mandatory Reading Order

Before changing documentation, code, tests, scripts, config, deployment artifacts, services, jobs, migrations, or interfaces, read these files in order:

1. `README.md`
2. `docs/INDEX.md`
3. `docs/PHASE_STATUS.md`
4. `docs/AI_CODING_RULES.md`
5. `docs/ARCHITECTURE.md`
6. `docs/SAFETY.md`
7. `docs/ROADMAP.md`
8. `docs/DATA_MODEL.md`
9. `docs/TAXONOMY.md`
10. `docs/FIREWALL.md`
11. `docs/ABUSE.md`
12. the relevant phase document for the task
13. the relevant domain document for the task

For the current Phase 11 work, also read:

```text
docs/AI_PHASE_11_TASK.md
docs/AI_PHASE_11_OPERATIONAL_COMPLETION_TASK.md
docs/PHASE_11_OPERATIONAL_COMPLETION_GATE.md
docs/PRODUCTION_ACTIVATION_GATE.md
docs/AI_SAFE_RUNTIME_FIRST.md
docs/FIREWALL.md
docs/BACKEND_PORT_POLICY.md
docs/ABUSE.md
```

For hash-rate, share, worker, reporting, or charting work, also read:

```text
docs/OBSERVABILITY_HASHRATE.md
docs/WORKER_POLICY.md
```

If documents conflict, follow the stricter safety rule and update stale documentation before implementing code.

## 2. Project Identity

This project is:

```text
Python-first
API-first
PostgreSQL-backed
service-layer based
lane-based
firewall-plan based
safety-gated
AI-safe Runtime-first
future-ready for local UI, buyer UI, Telegram, worker intelligence, and hash-rate/share observability
```

This project is not:

```text
a direct shell-script migration
a CLI-first tool
a random iptables command generator
a SQLite/TSV production state system
a public web panel in early phases
a Telegram-first automation system
a buyer-account system hidden inside customer service rows
a firewall-only worker blocker
a UI-only hash-rate calculator
an unstructured share log collector
```

## 3. Current Gate

The current phase is defined only in:

```text
docs/PHASE_STATUS.md
```

Current repository gate:

```text
current_accepted_phase: Phase 11 — Production / Customer Activation Gate accepted on farm5
current_working_phase: Phase 11 operational completion — Full CLI Production Operations
server_state: farm5 controlled CLI-limited BTC production/customer activation is accepted; Phase 11 operational completion now requires Full CLI Production Operations acceptance before Phase 12 implementation
production_traffic: controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled_operator_gated
customer_onboarding_allowed: controlled_cli_limited
proxy_data_plane_allowed: limited_runtime_local_only
worker_enforcement_allowed: no
ui_allowed: no
telegram_allowed: no
phase12_start_allowed: no
live_snapshot_read_allowed: iptables_save_read_only
restore_lock_record_execution_allowed: controlled_boundary_only
```

Phase 11 is accepted only for the controlled CLI-limited BTC boundary. Controlled CLI/service-layer onboarding, controlled firewall apply, and controlled abuse automation paths are authorized boundaries; this does not authorize unrestricted expansion, UI, Telegram, worker enforcement, scheduler/timer starts, or direct DB/firewall mutation.

The active Phase 11 operational completion scope is Full CLI Production Operations before Phase 12 Worker Policy Enforcement. This is not a new phase. Acceptance must prove restart/autostart, production customer lifecycle CLI execution, production firewall plan/apply/verify/rollback for real customer ports, production onboarding through CLI, usage/report/check evidence, abuse runner coverage for all active customers in all enabled lanes, pause/block/expire-run controls, backup/restore drill, and final acceptance to `production_traffic=cli_production` and `customer_onboarding_allowed=cli_production`. Until final acceptance, current production/onboarding gates remain `controlled_cli_limited`.

Phase 6-B allowed work (historical reference, already accepted):

```text
repository/documentation cleanup that preserves gates
firewall desired-state model refinement
firewall planner/diff contracts
human-readable and JSON plan/report rendering
dry-run evidence generation
offline snapshot parser and file-backed diff fixtures
offline restore payload artifacts
offline apply-readiness contracts
offline apply package reports
offline rollback artifacts from explicit snapshot files
offline preflight reports
planner/contract/preflight safety tests
backend exposure classification
internal backend reachability classification
```

Phase 6-B forbidden work (historical Phase 6 reference only; this list does not override the accepted Phase 11 controlled boundary):

```text
production traffic
customer NAT redirects
customer firewall rules
live firewall apply
live firewall rollback
live firewall verify
iptables-save execution
iptables-restore execution
conntrack flush
usage timers
hash-rate/share collectors
abuse runner automation
block or pause automation
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

After Phase 11 acceptance, only controlled CLI/service-layer onboarding, planner-driven customer NAT/firewall handling, the controlled firewall apply path, and the controlled abuse path are authorized. Unrestricted expansion and direct or ad-hoc DB/firewall/runtime mutation remain forbidden. Default configuration remains conservative (`plan_only`); each future controlled operation still requires its explicit operator package, planning, restore, lock, verify, and evidence workflow.

Historical compatibility anchor: Slice 3 / Apply Slice 3 and Future Dedicated Phase 6 Apply Gate Proposal/Review are retained as non-authorizing Phase 6 references only; they do not reopen any current gate.

## 4. Fixed Architecture Decisions

These decisions are frozen for the initial implementation:

```text
server role: forward-only customer gateway
source of truth: local PostgreSQL
code path: /opt/mpf-py
config path: /etc/mpf/mpf.yaml
data path: /var/lib/mpf
logs path: /var/log/mpf
backup path: /var/backups/mpf
CLI name: mpf
first lane: BTC
BTC backend port: 60010
firewall backend: iptables first
future firewall apply mechanism: iptables-save / iptables-restore after explicit apply gate
scheduler: systemd timers
initial/current firewall mode: plan_only
local API/UI binding: 127.0.0.1 or Unix socket only
```

## 5. API-First Rule

Business logic must live in domain/service modules, not in interfaces.

Required pattern:

```text
CLI / API / UI / Telegram / jobs
  -> request DTO / command object
  -> service layer
  -> repositories / adapters
  -> event + audit
  -> response DTO
```

Forbidden patterns:

```text
CLI directly edits DB
CLI directly runs iptables
UI directly updates tables
Telegram directly runs shell commands
job writes state without service validation
adapter owns business decisions
```

Interfaces must be thin. Services own validation, business transitions, audit, and side-effect ordering. Repositories own persistence. Adapters own external-system interaction.

## 6. Source of Truth Rule

PostgreSQL is the production source of truth.

Allowed uses of flat files or SQLite:

```text
import from old scripts
export/debug artifacts
temporary migration tooling
generated restore artifacts
backup files
```

Forbidden uses:

```text
production customer database
production abuse state
production usage state
production hash-rate/share state
production firewall desired state
multiple scattered SQLite databases as active runtime state
TSV as the main customer source of truth
```

## 7. Lane Rule

Multi-lane support is required from day one.

BTC is the first lane and uses backend port `60010`. Future coins such as ZEC/LTC must be implemented through lanes. Do not copy scripts or command trees per coin.

## 8. Backend Port Rule

Backend ports are internal service ports. They must be blocked from direct external/public access while remaining reachable from valid internal server and Docker paths.

Required doctor split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Forbidden:

```text
blocking loopback access to backend ports
blocking required Docker/internal bridge access
blocking MPF-owned NAT redirect path
using normal OUTPUT drops to hide backend ports
allowing public inbound access to backend ports
publishing backend ports on 0.0.0.0 through Docker
marking internal reachability failure as healthy
```

## 9. Firewall Safety Rules

All production firewall changes must go through the firewall service and firewall adapter.

Required future lifecycle:

```text
read DB/config
  -> build desired model
  -> compare desired with live firewall
  -> generate plan
  -> show human diff
  -> show JSON diff
  -> create restore point
  -> backup live firewall
  -> acquire lock
  -> apply atomically
  -> verify
  -> record event/audit
  -> rollback or rollback-plan on failure
```

Allowed apply mechanism after a future apply gate:

```text
iptables-save
iptables-restore
```

Direct firewall commands may appear only in diagnostics, isolated tests, or generated emergency restore artifacts, not as normal production state mutation.

During the current Phase 11 planning/readiness boundary, no live firewall write, `iptables-restore`, apply, rollback, or verify execution is allowed.

## 10. Abuse Requirement

The one-hour miner-abuse state machine is mandatory.

Required state flow:

```text
normal -> over_tracking -> over_grace -> hard
```

Required rules:

```text
all active customers in all enabled lanes must be scanned
no silent skip is allowed
exemption requires reason and expiry
farms-over alone must not harden
sustained miner-abuse hardens after about 3600 seconds
hard creates restore point
hard creates policy backup
hard uses firewall plan/apply/verify path after the relevant apply gate
hard flushes affected conntrack scope after the relevant runtime gate
manual unhard is audited
```

A patch that weakens this requirement must be rejected.

## 11. Hash-rate and Share Observability Rule

Accepted/rejected hash-rate per device is a future first-class capability.

It must be implemented through structured services and data models, not as UI-only calculations or loose log parsing.

Required future layers:

```text
Stratum/share evidence collection
share_events evidence table
device_hashrate_samples aggregated time-series
customer_hashrate_samples aggregated time-series
report service/API response DTOs
UI charts from aggregated samples
retention policy before high-volume collection
```

Worker name alone must not be treated as a guaranteed physical device identity. No high-volume share/hash-rate collector may be activated before retention and partitioning are reviewed.

## 12. Events, Audit, and Restore Points

Every meaningful mutation must record an event.

Every dangerous or destructive action must create a restore point.

Required before these future actions:

```text
firewall apply
firewall rollback
abuse hard
manual unhard
bulk customer policy change
block sync
pause sync
risky schema migration
```

Audit is required for customer changes, policy changes, firewall apply/rollback, abuse hard/unhard, block/pause changes, backup/restore operations, UI actions later, and Telegram actions later.

## 13. Jobs and Scheduling

Use systemd timers, not mixed cron and systemd.

Every recurring job must write `job_runs`. Every job that can overlap must use `scheduler_locks`. Jobs must call services and must not bypass service validation.

## 14. Secrets

Never commit secrets.

Forbidden in repository:

```text
Telegram bot tokens
database passwords
pool credentials
private proxy subscription URLs
production customer private secrets
raw API tokens
```

Secrets belong outside Git, for example:

```text
/etc/mpf/secrets.env
/etc/mpf/secrets.d/
```

## 15. UI, API, Telegram, and Buyer Accounts

Early API/UI must bind only locally:

```text
127.0.0.1
Unix socket
```

Buyer-facing UI is future work and must be read-only first. Buyer accounts must be modeled separately from customer service/port records. Future buyer actions should create reviewed `action_requests` rather than directly mutating customers, firewall state, abuse state, blocks, pauses, or policy.

Telegram starts as notification-only and must not run shell commands.

## 16. Worker Identity and Worker Blocking Rule

Worker names are Stratum-layer identities, not firewall-layer identities.

Forbidden:

```text
assuming worker block can be implemented by firewall rules alone
storing worker block state only as IP blocks
hardcoding worker parsing inside UI, Telegram, or CLI handlers
```

Required future boundary:

```text
worker observation / worker timeline
  -> worker policy service
  -> worker enforcement adapter, later
  -> event/audit/evidence
```

## 17. Test Expectations

Safety-critical code must include tests.

Minimum risk areas:

```text
config validation
database migrations
schema constraints
policy versioning
buyer/customer separation
worker block boundary
lane collision
port collision
backend external exposure detection
backend internal reachability detection
firewall planner/diff/rollback/preflight
abuse state machine
all-active-customer abuse coverage
usage counter delta
hash-rate/share aggregation contracts
job locking
backup/restore
interface boundary tests
```

## 18. Stop Conditions

Stop and revise before continuing if a change introduces any of these:

```text
live firewall apply before explicit Phase 11 production/customer activation gate acceptance
live firewall write dependency before explicit Phase 11 production/customer activation gate acceptance
iptables-restore execution before explicit Phase 11 production/customer activation gate acceptance
controlled CLI canary before explicit Phase 11 authorization
limited real customer onboarding before explicit Phase 11 authorization
abuse automation before the relevant Phase 11 runtime gate
customer firewall rules before accepted gate
NAT redirects before accepted gate
backend public exposure
backend internal reachability failure
UI direct DB write
Telegram shell command execution
bypassing apply_mode=plan_only
production TSV/SQLite source of truth
customer excluded from abuse without valid exemption
business logic inside CLI handler
ad-hoc production iptables mutation
missing restore point for dangerous action
missing event/audit for mutation
treating buyer accounts as customer service rows
treating worker blocking as firewall-only
high-volume share/hash-rate collection without retention policy
UI charts reading raw high-volume share events directly
secrets committed to the repository
```

## 19. Before Submitting a Patch

Check:

```text
[ ] Required docs were read.
[ ] Change matches the current phase.
[ ] No forbidden phase action was introduced.
[ ] API-first boundary is preserved.
[ ] PostgreSQL remains source of truth.
[ ] Firewall changes go through planner/service.
[ ] Backend internal/external policy is preserved.
[ ] Abuse 1h rule is preserved.
[ ] Buyer accounts remain separate from customer service/port records.
[ ] Worker block is not modeled as firewall-only.
[ ] Hash-rate/share data is not added as unstructured or UI-only state.
[ ] Events/audit are added for mutations.
[ ] Restore points are added for dangerous actions.
[ ] Tests cover safety-critical behavior.
[ ] Secrets are not committed.
[ ] UI/API/Telegram exposure remains local/safe.
```


## Runtime-first project governance

For Phase 11 operational completion and all later phases, once farm5 evidence, PHASE_STATUS, or progression code names a concrete blocker, the next AI-generated PR must either:

- close that blocker,
- add the smallest safe runtime/verifier/doctor/package/acceptance-review primitive that directly advances it,
- or create a coherent runtime-first bundle that advances multiple related deliverables under the same operational gate,
- or use the evidence/docs exception and name the exact next runtime-first PR.

Repeated report-only/docs-only/evidence-only PRs are forbidden.

Runtime-first bundle PRs are allowed and preferred when they reduce churn and keep the change coherent, tested, and inside the current accepted safety gate.

## 20. Review Standard

A change is not acceptable just because it works locally.

It must also:

```text
respect phase gates
preserve safety invariants
be testable
be auditable
avoid hidden side effects
avoid direct production firewall mutation
avoid direct interface-to-database writes
avoid future schema dead ends
```

When in doubt, choose the safer implementation and document the tradeoff.

## Runtime-forward PR rule

After a controlled runtime boundary is accepted, AI agents must not create repeated report-only PRs that avoid implementation.

Report-only PRs are allowed only when they are:

1. the first entry gate for a new phase/subphase;
2. a fail-closed blocker investigation with concrete next implementation step;
3. evidence capture required before a dangerous controlled operation.

No two consecutive PRs in the same active phase/subphase may be report-only unless the second PR records a real farm5 blocker and includes the exact next implementation scope.

Every normal implementation PR must deliver at least one concrete implementation artifact:

- service-layer implementation
- repository/model/migration change
- CLI/API operator surface
- controlled execution package
- adapter behavior
- tests covering behavior
- gated runtime/runbook script

Documentation-only changes are allowed for safety clarification, but they must not become the default progression path.
