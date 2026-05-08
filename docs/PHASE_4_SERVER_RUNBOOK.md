# Phase 4 Server Runbook — Compose Forward-only + Proxy Doctor

Status: planning gate for future Phase 4 server execution

This runbook defines the safety boundary and acceptance checks for Phase 4.
It does not authorize immediate proxy runtime activation by itself.

## Purpose

Phase 4 prepares the forward-only proxy data-plane and proxy doctor without creating customer firewall redirects.

Target data-plane shape for BTC:

```text
future customer NAT path
  -> BTC backend port 60010
  -> forwarder/gost
  -> v2rayA / SOCKS bridge
  -> mining pool
```

During Phase 4 planning and repository implementation, customer traffic must remain untouched.

## Current Required State Before Runtime Activation

Before any server runtime activation is attempted, verify:

```text
firewall.apply_mode = plan_only
production_traffic = none
customer_onboarding_allowed = no
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = planning_only or explicitly upgraded by a later accepted task
```

The server must still have:

```text
no customer NAT redirects
no customer firewall rules
no MPF firewall apply
no usage timers
no abuse automation
no block/pause automation
no public UI/API/Telegram service
```

## Allowed Server-Side Checks During Planning

Allowed checks are read-only:

```bash
mpf phase-status
mpf config validate
mpf config show
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
bash scripts/verify_phase4_planning_gate.sh
```

Allowed OS-level inspection:

```bash
docker ps -a
docker compose version
ss -lntup
iptables-save
ip6tables-save
systemctl list-unit-files
systemctl --type=service --type=timer --type=socket --state=active
timedatectl
```

These commands must not start containers, change firewall rules, create NAT redirects, create customers, or enable timers.

## Forbidden Server-Side Actions Until Explicit Runtime Approval

Do not run:

```bash
docker compose up
docker run
systemctl enable mpf-*.service
systemctl start mpf-*.service
systemctl enable v2raya*.service
systemctl start v2raya*.service
iptables
ip6tables
iptables-restore
ip6tables-restore
mpf customer add
mpf customer edit
mpf firewall apply
mpf abuse run
mpf usage snapshot
```

Do not activate:

- v2rayA runtime
- forwarder/gost runtime
- customer NAT redirect
- customer firewall rules
- production customer import
- usage timers
- abuse automation
- block/pause automation
- local UI service
- buyer UI service
- Telegram bot

## Compose Design Requirements

The future Compose design must satisfy:

- v2rayA UI binds only to `127.0.0.1` or a private Unix/local-only path.
- BTC backend service uses backend port `60010`.
- backend port `60010` is not publicly published on `0.0.0.0`.
- required Docker/internal paths remain reachable.
- healthchecks are defined for the proxy path.
- service names are stable and lane-aware.
- secrets are not committed to Git.
- rollback/stop instructions are documented before runtime activation.

## Backend Port Acceptance

Backend ports are internal service ports.

Correct future health split:

```text
internal_backend_reachable = OK
external_backend_exposed = NO
```

Critical failures:

```text
internal_backend_reachable = FAIL
external_backend_exposed = YES
v2raya_ui_public = YES
backend_published_0_0_0_0 = YES
```

Do not fix public exposure by blocking valid local, loopback, Docker, or future MPF-owned NAT paths.

## Proxy Doctor Acceptance Fields

A Phase 4 proxy doctor must report:

```text
compose_file_exists
compose_config_valid
v2raya_ui_local_only
backend_listener_state
backend_internal_reachability
backend_external_exposure
backend_docker_publish_mode
proxy_container_state
healthcheck_state
no_customer_nat_redirects
firewall_apply_mode_plan_only
final_verdict
```

Allowed final verdict values:

```text
OK
WARN
CRITICAL
```

## Planning Gate Verification

The planning gate is accepted only if:

```text
docs/AI_PHASE_4_TASK.md exists
docs/PHASE_4_SERVER_RUNBOOK.md exists
scripts/verify_phase4_planning_gate.sh exists
mpf phase-status shows Phase 3.1 accepted and Phase 4 planning
README points to Phase 3.1 accepted and Phase 4 planning
firewall.apply_mode remains plan_only
Docker proxy runtime is not activated by this planning work
no firewall/NAT/customer/usage/abuse mutation is introduced
```

## Runtime Activation Gate

A later runtime activation task must be created before starting containers.

That future task must include:

```text
exact server commands
backup or restore point plan
compose config validation
container startup command
healthcheck commands
backend internal reachability test
backend external exposure test
v2rayA UI local-only test
stop/rollback commands
confirmation that no customer NAT redirect will be created
confirmation that firewall.apply_mode remains plan_only
post-run evidence checklist
```

Without that later accepted task, Phase 4 remains planning-only.

## Rollback / Stop Plan Requirements For Future Runtime

Before runtime activation, document exact commands to:

```text
stop proxy containers
remove proxy containers if needed
confirm no risky ports are listening
confirm no MPF firewall/NAT rules exist
confirm config remains plan_only
collect logs for diagnosis
```

## Server Evidence To Send Back After Future Runtime Work

When a future approved runtime activation is executed, collect:

```bash
mpf phase-status
mpf doctor
mpf proxy doctor
mpf proxy status
docker ps -a
ss -lntup | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true
iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
timedatectl
```

Do not move to Phase 5 until Phase 4 evidence is reviewed and accepted.
