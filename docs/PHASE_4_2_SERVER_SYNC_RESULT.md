# Phase 4.2 Server Sync Result — Runtime Activation Runbook Planning

Status: accepted server evidence

Server: `farm5`

Timestamp from evidence:

```text
2026-05-09T12:06:53+03:30
```

## Scope

Phase 4.2 repository planning artifacts were synced to the server and verified.

This result does not authorize runtime activation.

## Accepted Server Evidence

```text
GitHub main ZIP synced successfully
server source aligned with GitHub ZIP
mpf phase-status reports Phase 4.1 accepted / Phase 4.2 working
pytest passed: 60 passed
mpf config validate OK
mpf doctor OK
mpf db ping OK
mpf db status OK
mpf lanes list OK and read-only
mpf customer list OK and read-only
mpf jobs status OK and read-only
mpf proxy config-check final_verdict: OK
mpf proxy status final_verdict: WARN
mpf proxy doctor final_verdict: WARN
Phase 4.2 planning gate passed
Runtime activation is still NOT authorized
```

## Backup Artifact

The server source sync created this backup:

```text
/var/backups/mpf/source-before-zip-sync-20260509T083643Z
```

## Planning Files Verified On Server

```text
docs/AI_PHASE_4_2_TASK.md
docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md
docs/PHASE_4_1_SERVER_RESULT.md
scripts/sync_main_zip_on_server.sh
scripts/verify_phase4_planning_gate.sh
```

## Safety Evidence

```text
firewall.apply_mode remains plan_only
proxy.runtime_activation_allowed remains false
Docker has no proxy runtime containers
v2rayA UI port is not listening during planning
BTC backend port 60010 is not listening during planning
no MPF/backend IPv4 firewall references detected
no MPF/backend IPv6 firewall references detected
no risky backend/UI ports listening
no customers
no job runs
no customer NAT redirects
no customer firewall rules
no customer onboarding
no usage timers
no abuse automation
no UI or Telegram runtime
```

## Expected Remaining Warning

The expected proxy doctor warning remains:

```text
lane.btc.backend_internal_reachability: WARN
```

Reason: backend internal reachability cannot be checked until a later explicitly approved runtime activation execution step starts the proxy containers.

This warning is expected and is not a Phase 4.2 blocker.

## Current Server Warning

Time synchronization has previously been reported as not confirmed on `farm5`:

```text
System clock synchronized: no
NTP service: active
```

This is not a Phase 4.2 planning blocker, but it must be fixed before production traffic, usage accuracy, hash-rate time-series collection, expiry automation, job automation that depends on reliable time, or abuse automation.

## Next Step

The next step is an explicit operator decision about whether to proceed to a limited Phase 4 runtime activation execution step.

That future step may start only proxy runtime containers through the documented `phase4-runtime` profile, and still must not create customer NAT redirects, customer firewall rules, usage timers, abuse automation, UI, Telegram, or production customer onboarding.

## Still Forbidden

Do not run or activate yet without the next explicit execution approval:

```text
docker compose up
docker run
v2rayA runtime
forwarder/gost runtime
customer NAT redirects
customer firewall rules
firewall apply
customer CRUD mutation
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
```
