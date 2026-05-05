# Architecture

## Project role

This server is a forward-only mining customer gateway.

It is not a fee-proxy server.

## Canonical traffic path

```text
customer_port
  -> firewall policy
  -> NAT redirect
  -> lane backend port
  -> simple-forwarder / gost
  -> v2rayA
  -> mining pool
```

## First stable lane

```text
BTC customer ports -> backend 60010 -> forwarder -> v2rayA -> pool
```

## Lane model

Future coins such as ZEC and LTC must be implemented through the same lane model.

Do not clone scripts per coin.

Expected initial lane ports:

```text
btc -> 60010
zec -> 60015
ltc -> 60020
```

## Standard production paths

```text
Code:    /opt/mpf-py
Config:  /etc/mpf/mpf.yaml
Data:    /var/lib/mpf
Logs:    /var/log/mpf
Backups: /var/backups/mpf
CLI:     mpf
```

## Source of truth

PostgreSQL is the source of truth.

SQLite and flat files are not allowed as the primary state store. They may only be used for debug, import/export, or compatibility tooling.

## Application layers

```text
mpf/
  domain/
  services/
  adapters/
  interfaces/
  jobs/
  migrations/
  tests/
```

## Interface model

The same service layer must be used by:

- CLI
- local Web UI
- Telegram bot
- future internal API

Business logic must not be locked inside CLI handlers.

## Early config rule

During early phases:

```yaml
firewall:
  apply_mode: plan_only
```

No live firewall mutation is allowed until the firewall planner phase is complete.
