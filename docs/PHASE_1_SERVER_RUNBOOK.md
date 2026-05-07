# Phase 1 Server Runbook

Status: Phase 1 server execution record and operator runbook

This document records the safe Phase 1 bootstrap path for the target server and defines how to verify that no production traffic behavior was introduced.

## Target Server Summary

Observed target server:

```text
hostname: farm5
OS: Ubuntu 24.04.4 LTS
kernel family: Ubuntu 6.8 generic
architecture: x86_64
timezone: Asia/Tehran
firewall userspace: iptables v1.8.10 nf_tables
nftables: available
```

Network details are intentionally not recorded in this public repository. Future firewall/customer phases must explicitly decide which interface and address are customer-facing. Phase 1 does not create customer rules or NAT redirects.

## Phase 1 Result

Phase 1 bootstrap was executed successfully on `farm5`.

Installed or verified base components:

```text
Python 3.12
pip
pytest
PyYAML
PostgreSQL 16
Docker 28
Docker Compose v2
containerd
conntrack
ipset
tcpdump
sqlite3
iptables/nftables tools
```

Created local state:

```text
system user: mpf
database: mpf
PostgreSQL role: mpf
config: /etc/mpf/mpf.yaml
app path: /opt/mpf-py
data path: /var/lib/mpf
log path: /var/log/mpf
backup path: /var/backups/mpf
secrets directory: /etc/mpf/secrets.d
CLI symlink: /usr/local/bin/mpf -> /opt/mpf-py/mpf_cli.py
```

Phase 1 config safety:

```yaml
firewall:
  backend: iptables
  apply_mode: plan_only

lanes:
  btc:
    enabled: true
    backend_port: 60010

abuse:
  threshold_sec: 3600
  grace_sec: 900
```

## Accepted Smoke Checks

The following checks passed on `farm5`:

```bash
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db ping
python -m pytest
systemctl is-active postgresql
systemctl is-active docker
systemctl is-active containerd
docker version
docker compose version
conntrack -V
iptables --version
```

Observed test result:

```text
5 passed
```

Observed Docker state:

```text
No containers exist.
```

Observed firewall state:

```text
No MPF-owned firewall chains or rules exist.
No customer NAT redirect exists.
No backend 60010 MPF state exists.
```

## Current Safety Status

```text
Phase 1 bootstrap: accepted
production traffic: none
customer firewall rules: none
NAT redirects: none
backend listener: none
Docker containers: none
abuse automation: none
block/pause automation: none
UI service: none
Telegram service: none
```

The server is not production-ready yet. It is only prepared for Phase 2 planning and implementation.

## NTP Warning

Current time synchronization status requires follow-up before production.

Observed:

```text
systemd-timesyncd: active
System clock synchronized: no
Packet count: 0
public Ubuntu NTP replies timed out
```

This is not a Phase 1 blocker, but it must be fixed before production traffic and before the abuse runner is activated. The one-hour abuse state machine depends on reliable timestamps.

Recommended next investigation:

```bash
timedatectl timesync-status || true
systemctl status systemd-timesyncd --no-pager || true
resolvectl status || true
```

Possible fixes, to be selected only after network policy is known:

```text
- allow outbound UDP/123
- configure an internal NTP server
- configure a provider-approved NTP endpoint
```

Do not guess or hardcode a time server without confirming the network policy.

## Re-run Verification

Use a read-only verification after any Phase 1 maintenance:

```bash
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db ping
cd /opt/mpf-py && python -m pytest
docker ps -a
ss -lntup
iptables-save | grep -E 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
timedatectl || true
```

Expected:

```text
pytest passes
mpf db ping OK
no Docker containers
no MPF firewall rules
firewall.apply_mode=plan_only
PostgreSQL local-only
```

## What Must Not Be Done Yet

Do not run or implement these on the server until the appropriate later phases:

```text
customer add/edit/delete/renew
PostgreSQL production migrations
firewall planner/apply
NAT redirects
v2rayA or forwarder containers
usage timers
abuse runner automation
block/pause automation
UI service
Telegram bot
production customer import
```

## Next Phase

The next safe project step is Phase 2 planning and implementation in the repository:

```text
Phase 2 — PostgreSQL + Config + Domain Model
```

Phase 2 must still not apply firewall rules or start customer traffic.
