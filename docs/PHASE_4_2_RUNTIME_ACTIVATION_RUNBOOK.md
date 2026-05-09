# Phase 4.2 Runtime Activation Runbook Planning

Status: planning gate for a future runtime activation execution step

This runbook defines the exact future procedure for starting the Phase 4 proxy data-plane safely.
It does **not** authorize immediate runtime activation by itself.

## Purpose

Phase 4.2 prepares the operator procedure for a later explicit runtime activation decision.

The future runtime shape for BTC is:

```text
future customer NAT path, not active yet
  -> BTC backend port 60010
  -> mpf-forwarder-btc / gost
  -> mpf-v2raya / SOCKS bridge
  -> mining pool
```

During Phase 4.2 planning, customer traffic must remain untouched.

## Current Required State

Before this runbook can be used for runtime execution, the server must still show:

```text
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
production_traffic = none
customer_onboarding_allowed = no
firewall_apply_allowed = no
abuse_automation_allowed = no
proxy_data_plane_allowed = planning_only or explicitly upgraded by a later accepted execution task
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

## Phase 4.2 Planning-Only Rule

The commands below are split into two categories:

1. commands allowed now during planning
2. commands documented for a later explicit runtime execution step

Do not run the runtime execution commands until a later task explicitly authorizes runtime activation.

## Commands Allowed Now During Planning

These are read-only or documentation-safe:

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
mpf proxy config-check
mpf proxy status
mpf proxy doctor
bash scripts/verify_phase4_planning_gate.sh
docker compose -f /opt/mpf-py-src/compose/mpf-proxy.compose.yaml --profile phase4-runtime config
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

## Commands Forbidden Until Later Runtime Approval

Do not run during Phase 4.2 planning:

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

## Future Runtime Execution Procedure

The following section documents the exact future procedure. It is not authorized until a later explicit execution task is accepted.

### 1. Pre-run safety snapshot

```bash
sudo bash <<'BASH'
set -Eeuo pipefail

echo '===== PHASE / CONFIG ====='
mpf phase-status
mpf config validate
mpf config show
mpf doctor
mpf proxy config-check
mpf proxy status
mpf proxy doctor

echo '===== DATABASE READONLY ====='
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status

echo '===== DOCKER READONLY ====='
docker ps -a

echo '===== LISTENING PORTS BEFORE RUNTIME ====='
ss -lntup | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true

echo '===== FIREWALL BEFORE RUNTIME ====='
iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010|2014' || true
ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010|2014' || true
BASH
```

Expected before runtime:

```text
no Docker proxy containers
no risky backend/UI ports listening
no MPF firewall/NAT references
firewall.apply_mode = plan_only
proxy.runtime_activation_allowed = false
no customers
no job runs
```

### 2. Backup source/config metadata

```bash
sudo bash <<'BASH'
set -Eeuo pipefail
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="/var/backups/mpf/phase4-2-before-runtime-${STAMP}"
mkdir -p "$BACKUP_DIR"

tar -C /opt --exclude='mpf-py-src/.venv' -czf "$BACKUP_DIR/mpf-py-src-no-venv.tgz" mpf-py-src
cp -a /etc/mpf/mpf.yaml "$BACKUP_DIR/mpf.yaml"
iptables-save > "$BACKUP_DIR/iptables-save.v4"
ip6tables-save > "$BACKUP_DIR/iptables-save.v6"
docker ps -a > "$BACKUP_DIR/docker-ps-a.txt"
ss -lntup > "$BACKUP_DIR/ss-lntup.txt" || true

echo "BACKUP_DIR=$BACKUP_DIR"
BASH
```

### 3. Validate Compose config without starting runtime

```bash
docker compose -f /opt/mpf-py-src/compose/mpf-proxy.compose.yaml --profile phase4-runtime config >/tmp/mpf-phase4-compose-config.out

grep -E '127\.0\.0\.1:2014|127\.0\.0\.1:60010|phase4-runtime|mpf-forwarder-btc|mpf-v2raya' /tmp/mpf-phase4-compose-config.out
```

Expected:

```text
v2rayA UI published on 127.0.0.1:2014 only
BTC backend published on 127.0.0.1:60010 only
services are behind phase4-runtime profile
```

### 4. Future startup command, only after explicit approval

```bash
cd /opt/mpf-py-src
sudo docker compose -f compose/mpf-proxy.compose.yaml --profile phase4-runtime up -d
```

This command is forbidden during Phase 4.2 planning and must not be run until a later explicit runtime activation execution task is accepted.

### 5. Runtime health checks after future startup

```bash
docker compose -p mpf-proxy -f /opt/mpf-py-src/compose/mpf-proxy.compose.yaml ps

docker ps -a --filter name=mpf-v2raya --filter name=mpf-forwarder-btc

mpf proxy status
mpf proxy doctor
```

### 6. v2rayA UI local-only check

```bash
ss -lntup | grep -E ':2014\b' || true
curl -fsS http://127.0.0.1:2014 >/dev/null && echo OK_V2RAYA_UI_LOCAL || echo WARN_V2RAYA_UI_LOCAL_NOT_READY
```

Expected:

```text
listener is 127.0.0.1:2014 only
no 0.0.0.0:2014 listener
```

### 7. BTC backend internal reachability check

```bash
ss -lntup | grep -E ':60010\b' || true
nc -zv 127.0.0.1 60010
```

Expected:

```text
internal_backend_reachable = OK
listener is local/internal only
```

### 8. BTC backend external exposure check

From the server, inspect listener binding:

```bash
ss -lntup | grep -E ':60010\b' || true
```

Critical failure:

```text
0.0.0.0:60010
public_ip:60010
```

Expected:

```text
external_backend_exposed = NO
```

If an external client is available later, test from outside the server:

```bash
nc -zv <server_public_ip> 60010
```

Expected result from outside:

```text
connection refused or timeout
```

### 9. Confirm no customer NAT redirects

```bash
iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
```

Expected during Phase 4 runtime activation:

```text
no customer NAT redirects
no customer firewall rules
no MPF customer chains
```

A local Docker listener on `127.0.0.1:60010` is acceptable. MPF-owned NAT/customer rules are not acceptable yet.

### 10. Confirm plan_only remains active

```bash
mpf config show | grep -E 'firewall.apply_mode|proxy.runtime_activation_allowed'
```

Expected:

```text
firewall.apply_mode: plan_only
proxy.runtime_activation_allowed: False
```

### 11. Stop / rollback commands

```bash
cd /opt/mpf-py-src
sudo docker compose -f compose/mpf-proxy.compose.yaml --profile phase4-runtime down

docker ps -a
ss -lntup | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true
mpf proxy status
mpf proxy doctor
```

Expected after stop:

```text
no proxy project containers running
no risky backend/UI ports listening
firewall.apply_mode remains plan_only
no customer NAT redirects
```

## Evidence To Send Back After Future Runtime Execution

After a later approved runtime execution, collect and send:

```bash
sudo bash <<'BASH'
set -Eeuo pipefail

echo '===== PHASE ====='
mpf phase-status
mpf config validate
mpf config show
mpf doctor

echo '===== PROXY ====='
mpf proxy config-check
mpf proxy status
mpf proxy doctor

echo '===== DOCKER ====='
docker ps -a
docker compose -p mpf-proxy -f /opt/mpf-py-src/compose/mpf-proxy.compose.yaml ps -a

echo '===== PORTS ====='
ss -lntup | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true

echo '===== FIREWALL ====='
iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010|2014' || true
ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010|2014' || true

echo '===== TIME ====='
timedatectl || true
BASH
```

## Acceptance Criteria For Later Runtime Execution

A later runtime activation can be accepted only if:

```text
mpf config validate OK
mpf doctor OK
mpf proxy config-check OK
proxy containers started only through explicit phase4-runtime profile
v2rayA UI is local-only
BTC backend 60010 is internally reachable
BTC backend 60010 is not externally/publicly exposed
no customer NAT redirect exists
no customer firewall rule exists
firewall.apply_mode remains plan_only
proxy.runtime_activation_allowed remains false unless a later task explicitly changes it
no usage timer exists
no abuse automation exists
stop/rollback command works
post-run evidence is sent back and reviewed
```

## Still Forbidden After Phase 4 Runtime Activation

Even after a later approved proxy runtime startup, these remain forbidden until later phases:

```text
customer CRUD mutation
customer firewall rules
customer NAT redirects
firewall apply
usage timers
hash-rate/share collectors
abuse runner automation
block/pause automation
local UI service
buyer UI service
Telegram bot
production customer import
worker enforcement
public API binding
```

Do not move to Phase 5 until Phase 4 runtime evidence is reviewed and accepted.
