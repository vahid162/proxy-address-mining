# Phase 4 Runtime Activation Execution Task — Limited Proxy Runtime Startup

Status: approved execution task for a limited Phase 4 proxy runtime startup

This task authorizes only the limited proxy runtime activation described here.
It does not authorize production customer traffic, customer NAT redirects, firewall apply, usage timers, abuse automation, UI, Telegram, or customer mutation.

## Pre-approval Review

The current repository path was checked against:

- `docs/PHASE_STATUS.md`
- `docs/ROADMAP.md`
- `docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md`
- uploaded scenario/checklist context

The path is consistent with the roadmap Phase 4 goal: start the proxy data-plane without customer firewall redirects.

The target data-plane remains:

```text
future customer_port, not active yet
  -> firewall policy, not active yet
  -> NAT redirect, not active yet
  -> BTC backend port 60010
  -> mpf-forwarder-btc / gost
  -> mpf-v2raya
  -> mining pool
```

## Scope Approved Now

Allowed by this task:

```text
start mpf-v2raya and mpf-forwarder-btc only through Docker Compose profile phase4-runtime
validate v2rayA UI is bound on the host to 127.0.0.1:2015 only
validate v2rayA UI maps to container port 2017 for the current image
validate BTC backend is bound to 127.0.0.1:60010 only
validate BTC backend is internally reachable from the server
validate BTC backend is not exposed on 0.0.0.0 or ::
confirm no MPF customer NAT redirects exist
confirm no MPF customer firewall chains exist
collect post-run evidence
provide stop/rollback command
```

## Still Forbidden

Still forbidden in this task:

```text
customer CRUD mutation
customer NAT redirects
customer firewall rules
firewall apply
iptables-restore
usage timers
hash-rate/share collectors
abuse automation
block/pause automation
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
public v2rayA UI exposure
public backend exposure
```

## Required Safety Invariants

These must remain true:

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
customer_onboarding_allowed = no
firewall_apply_allowed = no
abuse_automation_allowed = no
customers = 0
job_runs = 0
```

`proxy.runtime_activation_allowed` stays false because this task authorizes a one-time operator-controlled Docker Compose execution path only; it does not enable general app/API/CLI runtime mutation.

## Approved Server Script

The approved execution script is:

```bash
sudo bash /opt/mpf-py-src/scripts/phase4_runtime_activation_execute.sh start
```

Evidence-only inspection after startup:

```bash
sudo bash /opt/mpf-py-src/scripts/phase4_runtime_activation_execute.sh status
```

Rollback / stop:

```bash
sudo bash /opt/mpf-py-src/scripts/phase4_runtime_activation_execute.sh stop
```

## Expected Possible Failure

The server has no GitHub/internet path. If the Docker images are not already present locally, the startup may fail safely because the script uses:

```text
docker compose up --pull never
```

If that happens, do not use internet on the server. The next task must prepare an offline Docker image transfer/import procedure.

## Required Evidence After Execution

Send the complete script output back for review.

The expected successful state is:

```text
mpf config validate OK
mpf doctor OK
mpf proxy config-check final_verdict OK
mpf-v2raya container exists and is healthy
mpf-forwarder-btc container exists and is healthy
127.0.0.1:2015 listener exists for host/operator v2rayA UI access
127.0.0.1:60010 listener exists for BTC backend
no 0.0.0.0:2015 listener
no 0.0.0.0:60010 listener
no [::]:2015 listener
no [::]:60010 listener
no MPF customer NAT redirects
no MPF customer firewall chains
firewall.apply_mode remains plan_only
proxy.runtime_activation_allowed remains false
```

If any critical check fails, stop the runtime immediately with the approved stop command and send the output for review.
