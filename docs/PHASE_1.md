# PHASE 1 — Preflight + Bootstrap Without Traffic Changes

Status: Draft v1

This document defines Phase 1 for `proxy-address-mining`.
It is an implementation contract for humans and AI coding agents.

Phase 1 prepares the server and Python project skeleton without touching production traffic.

## 0. Purpose

Prepare the target server for the MPF Python project while keeping the system safe.

Phase 1 must not create customer firewall rules, NAT redirects, abuse automation, block automation, or UI/Telegram actions.

The phase starts with inspection, not assumptions.

## 1. Phase 1 Principle

```text
inspect first
bootstrap second
smoke test third
no traffic changes
```

No command may be recommended as final unless the current server state is known from preflight output.

## 2. Allowed Work

Allowed in Phase 1:

1. inspect OS, kernel, timezone, hostname
2. inspect network interfaces, routes, DNS
3. inspect firewall backend and nft/legacy status
4. inspect Docker availability
5. inspect PostgreSQL availability
6. inspect Python availability
7. inspect required tools
8. install base packages
9. create standard directories
10. create local PostgreSQL user/database
11. create Python virtual environment
12. create minimal project skeleton
13. create initial `/etc/mpf/mpf.yaml`
14. create minimal `mpf` CLI smoke commands
15. run smoke tests
16. document server state

## 3. Forbidden Work

Forbidden in Phase 1:

1. create production customers
2. create customer firewall rules
3. create NAT redirects
4. expose backend ports publicly
5. start customer traffic path
6. enable abuse automation
7. enable block automation
8. enable pause automation
9. enable UI actions
10. expose UI publicly
11. activate Telegram bot
12. run firewall apply for customer state
13. import production customers as active firewall state
14. switch `firewall.apply_mode` away from `plan_only`

## 4. Required Preflight

Preflight must collect:

```text
OS and version
kernel
hostname
timezone
uptime
network interfaces
routes
DNS resolvers
iptables version
iptables backend alternative
ip6tables version
nft availability
ufw/firewalld status, if present
Docker version/status
Docker Compose version
PostgreSQL version/status
Python version
pip/venv availability
disk capacity
RAM/swap
internet reachability
package repository availability
required tool list
```

Required tools to check:

```text
python3
pip3
git
curl
wget
jq
docker
conntrack
tcpdump
ipset
sqlite3
psql
ss
iptables
ip6tables
nft
```

## 5. Preflight Script

The operator may run a read-only preflight script similar to:

```bash
sudo bash <<'BASH'
set -Eeuo pipefail

echo '===== BASIC ====='
date -Is
hostname
cat /etc/os-release
uname -a
timedatectl || true
uptime
echo

echo '===== NETWORK ====='
ip -br addr
echo
ip route
echo
cat /etc/resolv.conf
echo

echo '===== FIREWALL STACK ====='
iptables --version || true
ip6tables --version || true
update-alternatives --display iptables 2>/dev/null || true
nft --version 2>/dev/null || true
ufw status verbose 2>/dev/null || true
firewall-cmd --state 2>/dev/null || true
echo

echo '===== TOOLS ====='
for x in python3 pip3 git curl wget jq docker conntrack tcpdump ipset sqlite3 psql ss iptables ip6tables nft; do
  if command -v "$x" >/dev/null 2>&1; then
    echo "OK   $x -> $(command -v "$x")"
    "$x" --version 2>/dev/null | head -n 1 || true
  else
    echo "MISS $x"
  fi
done
echo

echo '===== DOCKER ====='
systemctl is-active docker 2>/dev/null || true
docker version 2>/dev/null || true
docker compose version 2>/dev/null || true
echo

echo '===== POSTGRESQL ====='
systemctl is-active postgresql 2>/dev/null || true
psql --version 2>/dev/null || true
echo

echo '===== CAPACITY ====='
df -h /
echo
free -h
echo
swapon --show || true
echo

echo '===== APT / REACHABILITY ====='
apt-cache policy docker.io docker-ce docker-compose-plugin postgresql python3 python3-venv 2>/dev/null || true
echo
getent hosts github.com || true
getent hosts download.docker.com || true
getent hosts archive.ubuntu.com || true
echo
timeout 8 bash -lc 'curl -I -4 -sS https://github.com >/dev/null && echo OK_github || echo FAIL_github' || true
timeout 8 bash -lc 'curl -I -4 -sS https://download.docker.com >/dev/null && echo OK_docker || echo FAIL_docker' || true
timeout 8 bash -lc 'curl -I -4 -sS https://archive.ubuntu.com >/dev/null && echo OK_archive || echo FAIL_archive' || true
BASH
```

The output must be reviewed before writing final bootstrap commands.

## 6. Bootstrap Package Set

Exact packages depend on preflight result and OS family.

Typical Ubuntu/Debian package groups:

```text
base:
  ca-certificates
  curl
  wget
  git
  jq
  gnupg
  lsb-release

python:
  python3
  python3-venv
  python3-pip

postgresql:
  postgresql
  postgresql-client

network/firewall tools:
  iptables
  iptables-persistent or distro equivalent
  conntrack
  tcpdump
  ipset
  nftables
  iproute2

container:
  docker-ce or docker.io
  docker-compose-plugin
```

Do not install or pin package versions blindly.
Use preflight and current OS repository availability.

## 7. Standard Paths

Create these paths:

```text
/opt/mpf-py
/etc/mpf
/etc/mpf/secrets.d
/var/lib/mpf
/var/log/mpf
/var/backups/mpf
/run/mpf, created by systemd/tmpfiles if needed
```

Recommended ownership:

```text
/opt/mpf-py       root:root or mpf:mpf depending deployment model
/etc/mpf          root:mpf
/etc/mpf/secrets.d root:mpf, mode 0750
/var/lib/mpf      mpf:mpf
/var/log/mpf      mpf:mpf
/var/backups/mpf  root:mpf or mpf:mpf
```

Secrets must be mode `0600` where practical.

## 8. PostgreSQL Bootstrap

Create local PostgreSQL objects:

```text
database: mpf
user: mpf
access: local-only
```

Phase 1 may create the empty database and verify connection.

Phase 1 must not deploy the full production schema unless Phase 2 has started.

Allowed Phase 1 DB checks:

```bash
mpf db ping
psql connection test
```

## 9. Python Skeleton

Create minimal skeleton:

```text
/opt/mpf-py/
  pyproject.toml
  README.md
  mpf/
    __init__.py
    interfaces/
      __init__.py
      cli.py
    config.py
    db.py
  tests/
    test_smoke.py
```

Allowed smoke commands:

```bash
mpf --help
mpf doctor
mpf config validate
mpf config show
mpf db ping
```

Forbidden in Phase 1 CLI:

```text
mpf customer add
mpf firewall apply
mpf abuse run
mpf block expire-run
mpf pause sync
```

These commands may exist only as documented future commands or stubs that fail closed with a clear message.

## 10. Initial Config

Create `/etc/mpf/mpf.yaml` with safe defaults:

```yaml
server:
  name: farm-new-1
  timezone: Europe/Berlin

paths:
  app: /opt/mpf-py
  data: /var/lib/mpf
  logs: /var/log/mpf
  backups: /var/backups/mpf

database:
  url: postgresql:///mpf

firewall:
  backend: iptables
  apply_mode: plan_only
  lock_path: /run/mpf-firewall.lock

lanes:
  btc:
    enabled: true
    backend_port: 60010
    chain_prefix: MPFBTC
    upstreams:
      - host: bitcoin.viabtc.io
        port: 3333

  zec:
    enabled: false
    backend_port: 60015
    chain_prefix: MPFZEC
    upstreams: []

  ltc:
    enabled: false
    backend_port: 60020
    chain_prefix: MPFLTC
    upstreams: []

abuse:
  enabled: true
  threshold_sec: 3600
  grace_sec: 900
```

Important:

```text
firewall.apply_mode must stay plan_only during Phase 1.
```

## 11. Systemd Scope

Allowed in Phase 1:

- optional read-only doctor service
- tmpfiles definition for `/run/mpf`

Forbidden in Phase 1:

- abuse timer
- usage timer
- block expiry timer
- pause sync timer
- backup timer that mutates state
- UI service
- Telegram service
- customer firewall apply service

## 12. Docker Scope

Phase 1 may verify Docker installation.

Phase 1 must not start production proxy data-plane.

Forbidden in Phase 1:

```text
v2rayA service activation
v2raya bridge activation
simple-forwarder activation
customer backend activation
public port publishing
```

Docker Compose data-plane starts in Phase 4.

## 13. Firewall Scope

Allowed in Phase 1:

- read iptables version
- read iptables backend
- read current rules for diagnostics
- save diagnostic snapshots, if needed

Forbidden in Phase 1:

- add chain
- delete chain
- add rule
- delete rule
- NAT redirect
- DOCKER-USER mutation
- backend guard mutation

## 14. Smoke Tests

Phase 1 acceptance commands:

```bash
mpf --help
mpf doctor
mpf config validate
mpf config show
mpf db ping
python -m pytest
systemctl status postgresql
docker version
docker compose version
conntrack -V
iptables --version
```

`mpf doctor` in Phase 1 should report:

```text
config: OK or actionable error
postgresql: OK or actionable error
paths: OK or actionable error
python env: OK or actionable error
docker: OK/WARN depending availability
firewall backend: OK/WARN depending availability
traffic changes: none
apply_mode: plan_only
```

## 15. Phase 1 Acceptance Gate

Phase 1 is accepted only when:

```text
[ ] preflight output is reviewed
[ ] required tools are installed or missing tools are documented
[ ] standard paths exist
[ ] PostgreSQL service is active
[ ] local mpf DB connection works
[ ] Python virtual environment exists
[ ] mpf CLI smoke commands work
[ ] config validates
[ ] tests pass
[ ] firewall.apply_mode remains plan_only
[ ] no customer firewall rules were created
[ ] no NAT redirects were created
[ ] no backend public exposure was introduced
[ ] no abuse/block/pause automation was enabled
[ ] no UI or Telegram service was enabled
```

## 16. Failure Handling

If preflight shows unsupported OS or missing repositories:

```text
stop and update bootstrap plan
```

If iptables backend is unclear:

```text
stop and document legacy/nft status before continuing
```

If PostgreSQL cannot start:

```text
stop before Python DB work
```

If config validation fails:

```text
fix config before any later phase
```

If any traffic-changing artifact appears:

```text
stop, rollback/remove artifact, document incident
```

## 17. Transition to Phase 2

Phase 2 may start only after Phase 1 acceptance gate passes.

Required handoff to Phase 2:

```text
preflight report
installed package list
path ownership/mode report
PostgreSQL connection result
mpf.yaml content
pytest output
known warnings
```

Phase 2 then implements schema, migrations, and domain model.

## 18. AI Coding Agent Rules for Phase 1

AI agents must not generate Phase 1 code or scripts that:

1. apply firewall changes
2. create customer rules
3. create NAT redirects
4. start abuse automation
5. start block/pause automation
6. expose UI/API publicly
7. start Telegram
8. bypass `plan_only`
9. assume OS/package state without preflight
10. hide failed commands with broad `|| true` except in read-only diagnostic collection

A Phase 1 patch that changes traffic behavior must be rejected.
