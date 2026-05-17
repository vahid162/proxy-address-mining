# Production / Customer Activation Gate

Status: planned gate after Phase 10 final acceptance

This document defines the required gate for making the server operational for real customers through terminal commands before Local UI, Buyer UI, or Telegram phases.

This gate is not open now. It is a future explicit acceptance gate.

## Purpose

After Phase 10 is accepted, the next operational target is CLI-managed production activation:

```text
Phase 10 accepted
  -> Production / Customer Activation Gate
  -> controlled CLI customer activation
  -> manual canary customer
  -> limited real customer onboarding
  -> later UI / Telegram surfaces reuse the same services
```

The goal is to make `mpf` usable as the standard terminal operator interface for real customer operations while preserving the Python/API-first architecture.

## Legacy Compatibility Boundary

The uploaded legacy inventory/tgz and existing production shell scripts are reference material only.

They define operational capabilities and command parity expectations, not implementation source code.

Allowed use:

```text
read legacy command behavior
map legacy capabilities to new service-layer commands
preserve operator workflows where safe
write tests and runbooks from observed behavior
```

Forbidden use:

```text
copy old shell scripts into the new runtime
keep SQLite/TSV as production source of truth
run legacy mpf_* scripts as the implementation backend
let Telegram or UI call shell scripts directly
bypass PostgreSQL/service-layer/audit/firewall-plan gates
```

## Required CLI Operational Surface

The activation gate must provide terminal-first operations equivalent to the safe production needs of the legacy MPF setup.

Required command groups:

```text
mpf doctor
mpf status
mpf customer add/edit/renew/delete/list/set-ips/expire-run
mpf firewall doctor/plan/diff/apply/verify/rollback
mpf usage snapshot/report/customer/doctor
mpf abuse status/run/hard/unhard/events/doctor
mpf check <target>
mpf report <target>
mpf monitor summary/port
mpf audit miners-over/farms-over/suspicious
mpf block add-ip/add-port-ip/list/expire-run/remove
mpf pause add/remove/sync/list
mpf note add/latest
mpf events latest
mpf backup create/list/restore-plan
mpf jobs status/list/run/doctor
```

Every command must call service-layer code. The CLI must stay a thin interface.

## Required Activation Gates

The gate must not be accepted until all items below are true and evidenced on farm5.

### 1. Fresh server evidence

```text
latest GitHub main version synced to farm5
pytest passes on farm5
mpf doctor OK
mpf phase-status aligned
scripts/verify_current_phase_gate.sh passes before opening new gates
```

### 2. Time and restart safety

```text
system clock synchronized: yes
NTP active
all enabled MPF systemd services restart correctly
after server restart, accepted runtime comes back automatically
container startup order is documented and tested
```

### 3. Firewall activation boundary

```text
firewall desired model built from PostgreSQL/config only
customer NAT/customer firewall rules are generated only through planner
manual canary apply is reviewed before general apply
iptables-save backup exists before apply
restore point exists before apply
lock is acquired before apply
verify runs after apply
rollback or rollback-plan is available on failure
backend public exposure remains blocked
```

### 4. Customer onboarding transition

Current state is:

```text
customer_onboarding_allowed: db_only
```

The production activation gate may move this only to a controlled CLI mode, for example:

```text
customer_onboarding_allowed: controlled_cli_canary
```

Then, after canary evidence:

```text
customer_onboarding_allowed: controlled_cli_limited
```

It must not jump directly to unrestricted production onboarding.

### 5. Abuse 1h runtime activation

The abuse invariant remains mandatory:

```text
normal -> over_tracking -> over_grace -> hard
```

Required activation behavior:

```text
all active customers in all enabled lanes are scanned
no silent skip
missing/stale evidence does not harden
DB failure does not harden
firewall failure does not harden
farms-over alone does not harden
worker-over alone does not harden
sustained miner-abuse hardens after about 3600 seconds
hard creates restore point and policy backup
hard uses firewall plan/apply/verify path after the relevant gate
manual unhard is audited
```

### 6. Usage, policy, session, and worker visibility

Before real customers are added, the operator must be able to see:

```text
usage counters
reject counters
active/recent sessions
unique IPs
unique workers
abuse state
final check/report verdict
```

Phase 10 evidence surfaces should feed this gate.

### 7. Manual canary customer

Before paid/real customer onboarding, the gate requires one manual canary customer with explicit evidence:

```text
customer created through mpf CLI
firewall plan reviewed
apply performed only through accepted path
customer connects successfully
NAT hit is visible
usage/reject accounting works
check/report returns clear verdict
abuse scanner covers the customer
rollback path is tested or restore-plan is generated
```

### 8. UI and Telegram reuse rule

After CLI activation, Web UI and Telegram may be added only as interfaces over the same service layer.

Forbidden future patterns:

```text
Telegram -> shell command
Telegram -> direct DB write
UI -> direct DB write
UI -> direct firewall command
bot-specific business logic fork
```

Required future pattern:

```text
UI / Telegram
  -> request DTO / command object
  -> same service layer used by CLI
  -> repositories/adapters
  -> event/audit
  -> response DTO
```

## Acceptance Output

The gate must produce a final report similar to:

```text
mpf production readiness --output json
mpf production canary-plan --output json
mpf production canary-acceptance --output json
mpf production final-activation --output json
```

All reports must be fail-closed by default.

## Initial Operational Boundary

The first production state should be limited, not unrestricted:

```text
production_traffic: controlled_cli_canary or controlled_cli_limited
firewall_apply_allowed: controlled
abuse_automation_allowed: controlled
customer_onboarding_allowed: controlled_cli_canary or controlled_cli_limited
ui_allowed: no
telegram_allowed: no
```

UI, Buyer UI, Telegram, and worker enforcement remain later phases unless a future explicit gate changes the roadmap.
