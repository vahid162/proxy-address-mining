# Phase 4.1 Server Result — Compose Template + Server Config Planning

Status: accepted server evidence

Server: `farm5`

Timestamp from evidence:

```text
2026-05-09T10:27:18+03:30
```

## Scope

Phase 4.1 completed repository/server planning alignment for the proxy Compose template and server config fields.

This result does not authorize runtime activation.

## Accepted Server Evidence

```text
GitHub main ZIP synced successfully
server source aligned with GitHub ZIP
pytest passed: 60 passed
mpf config validate OK
mpf proxy config-check final_verdict: OK
mpf proxy status final_verdict: WARN
mpf proxy doctor final_verdict: WARN
Phase 4 planning gate passed
Runtime activation is still NOT authorized
```

## Config Planning Applied

The server config `/etc/mpf/mpf.yaml` was updated through:

```bash
sudo bash /opt/mpf-py-src/scripts/apply_phase4_1_config_planning.sh /etc/mpf/mpf.yaml
```

The script created a backup at:

```text
/var/backups/mpf/phase4-1-config-planning-20260509T065705Z
```

The source ZIP sync created a backup at:

```text
/var/backups/mpf/source-before-zip-sync-20260509T065647Z
```

The applied planning fields include:

```yaml
proxy:
  compose_file: /opt/mpf-py-src/compose/mpf-proxy.compose.yaml
  project_name: mpf-proxy
  runtime_activation_allowed: false

v2raya:
  ui_bind_host: 127.0.0.1
  ui_port: 2014

lanes:
  btc:
    forwarder:
      service_name: mpf-forwarder-btc
      bind_host: 127.0.0.1
      listen_port: 60010
      upstream_socks: v2raya:22070
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
no customer NAT redirects
no customer firewall rules
no customer onboarding
no usage timers
no abuse automation
no UI or Telegram runtime
```

## Expected Remaining Warning

The only expected proxy doctor warning after Phase 4.1 is:

```text
lane.btc.backend_internal_reachability: WARN
```

Reason: backend internal reachability cannot be checked until an explicit later runtime activation runbook starts the proxy containers.

This warning is expected and is not a Phase 4.1 blocker.

## Next Step

The next repository step is:

```text
Phase 4.2 — Runtime Activation Runbook Planning
```

Phase 4.2 must prepare an explicit runtime activation task/runbook before any container is started.

The future runtime activation runbook must include:

```text
backup/restore point plan
docker compose config validation
exact container startup command with explicit profile
healthcheck commands
backend internal reachability test
backend external exposure test
v2rayA UI local-only test
stop/rollback commands
confirmation that no customer NAT redirect will be created
confirmation that firewall.apply_mode remains plan_only
post-run evidence checklist
```

## Still Forbidden

Do not run or activate yet:

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
