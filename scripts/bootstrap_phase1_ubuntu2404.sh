#!/usr/bin/env bash
set -Eeuo pipefail

# MPF Phase 1 bootstrap for Ubuntu 24.04.
# This script mutates the host only within the Phase 1 bootstrap boundary:
# - installs base packages
# - creates the mpf system user and standard paths
# - enables PostgreSQL and creates an empty local mpf database
# - enables Docker service only, without starting any containers
# - writes a safe /etc/mpf/mpf.yaml with firewall.apply_mode=plan_only
# - installs a minimal Phase 1 smoke CLI and tests
#
# Forbidden here:
# - customer firewall rules
# - NAT redirects
# - backend exposure
# - proxy data-plane containers
# - abuse/block/pause automation
# - UI or Telegram services

export DEBIAN_FRONTEND=noninteractive

echo '===== MPF PHASE 1 BOOTSTRAP: START ====='

if [[ ${EUID} -ne 0 ]]; then
  echo 'ERROR: run as root or with sudo' >&2
  exit 1
fi

if [[ -r /etc/os-release ]]; then
  . /etc/os-release
else
  echo 'ERROR: /etc/os-release not found' >&2
  exit 1
fi

if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
  echo "ERROR: this bootstrap is pinned to Ubuntu 24.04; found ID=${ID:-unknown} VERSION_ID=${VERSION_ID:-unknown}" >&2
  exit 1
fi

echo
echo '===== 1) APT UPDATE ====='
apt-get update

echo
echo '===== 2) INSTALL BASE PACKAGES ====='
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  wget \
  git \
  jq \
  python3 \
  python3-venv \
  python3-pip \
  python-is-python3 \
  python3-yaml \
  python3-pytest \
  postgresql \
  postgresql-client \
  docker.io \
  docker-compose-v2 \
  conntrack \
  tcpdump \
  ipset \
  sqlite3 \
  iptables \
  nftables \
  iproute2

echo
echo '===== 3) CREATE MPF SYSTEM USER AND PATHS ====='
if ! id -u mpf >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/mpf --shell /usr/sbin/nologin mpf
fi

install -d -m 0755 /opt/mpf-py
install -d -m 0755 /etc/mpf
install -d -m 0750 -o mpf -g mpf /var/lib/mpf
install -d -m 0750 -o mpf -g mpf /var/log/mpf
install -d -m 0750 -o mpf -g mpf /var/backups/mpf
install -d -m 0750 -o root -g mpf /etc/mpf/secrets.d

echo
echo '===== 4) START POSTGRESQL AND CREATE LOCAL DB ====='
systemctl enable --now postgresql

sudo -u postgres psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mpf') THEN
    CREATE ROLE mpf LOGIN;
  END IF;
END
$$;

SELECT 'CREATE DATABASE mpf OWNER mpf'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'mpf')\gexec
SQL

echo
echo '===== 5) WRITE SAFE PHASE 1 CONFIG ====='
cat > /etc/mpf/mpf.yaml <<'YAML'
server:
  name: farm5
  timezone: Asia/Tehran

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
YAML
chmod 0644 /etc/mpf/mpf.yaml

echo
echo '===== 6) INSTALL SAFE PHASE 1 MPF CLI SKELETON ====='
cat > /opt/mpf-py/mpf_cli.py <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import yaml

VERSION = "0.1.0-phase1"
DEFAULT_CONFIG = Path("/etc/mpf/mpf.yaml")


def load_config(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"config must be a YAML object: {path}")
    return data


def validate_config(path: Path) -> tuple[bool, str]:
    try:
        cfg = load_config(path)

        db_url = cfg.get("database", {}).get("url", "")
        if not str(db_url).startswith(("postgresql://", "postgresql+psycopg://", "postgresql:///")):
            return False, "database.url must be PostgreSQL"

        firewall = cfg.get("firewall", {})
        if firewall.get("backend") != "iptables":
            return False, "Phase 1 supports only firewall.backend=iptables"
        if firewall.get("apply_mode") != "plan_only":
            return False, "Phase 1 requires firewall.apply_mode=plan_only"

        lanes = cfg.get("lanes", {})
        btc = lanes.get("btc")
        if not isinstance(btc, dict):
            return False, "btc lane is required"
        if btc.get("backend_port") != 60010:
            return False, "btc.backend_port must be 60010"

        enabled_ports: dict[int, str] = {}
        for lane_name, lane in lanes.items():
            if not isinstance(lane, dict) or not lane.get("enabled"):
                continue
            port = lane.get("backend_port")
            if port in enabled_ports:
                return False, f"enabled lane port collision: {enabled_ports[port]} and {lane_name}"
            enabled_ports[port] = lane_name

        abuse = cfg.get("abuse", {})
        if int(abuse.get("threshold_sec", 0)) < 3600:
            return False, "abuse.threshold_sec must be >= 3600"

    except Exception as exc:
        return False, str(exc)

    return True, "OK"


def config_show(path: Path) -> int:
    cfg = load_config(path)
    print(f"server.name: {cfg['server']['name']}")
    print(f"server.timezone: {cfg['server']['timezone']}")
    print(f"database.url: {cfg['database']['url']}")
    print(f"firewall.backend: {cfg['firewall']['backend']}")
    print(f"firewall.apply_mode: {cfg['firewall']['apply_mode']}")
    for name, lane in sorted(cfg["lanes"].items()):
        print(
            f"lane.{name}: enabled={lane['enabled']} "
            f"backend_port={lane['backend_port']} chain_prefix={lane['chain_prefix']}"
        )
    print(f"abuse.enabled: {cfg['abuse']['enabled']}")
    print(f"abuse.threshold_sec: {cfg['abuse']['threshold_sec']}")
    print(f"abuse.grace_sec: {cfg['abuse']['grace_sec']}")
    return 0


def db_ping() -> int:
    cmd = ["psql", "-d", "mpf", "-tAc", "select 1"]
    if os.geteuid() == 0:
        cmd = ["sudo", "-u", "mpf", *cmd]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stderr.strip() or result.stdout.strip() or "db ping failed")
        return 1
    if result.stdout.strip() == "1":
        print("OK")
        return 0
    print(f"unexpected db result: {result.stdout.strip()!r}")
    return 1


def doctor(path: Path) -> int:
    ok, msg = validate_config(path)
    print("MPF Phase 1 doctor")
    print(f"config_path: {path}")
    print(f"config: {'OK' if ok else 'ERROR'}")
    if not ok:
        print(f"config_error: {msg}")
        return 1
    cfg = load_config(path)
    print(f"apply_mode: {cfg['firewall']['apply_mode']}")
    print("traffic_changes: none")
    print("firewall_mutation: disabled")
    print("abuse_automation: disabled")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mpf",
        description="MPF Phase 1 safe CLI skeleton. No production traffic mutation.",
    )
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("command", nargs="?")
    parser.add_argument("subcommand", nargs="?")
    args = parser.parse_args()

    path = Path(args.config)

    if args.version:
        print(VERSION)
        return 0

    if args.command == "phase-status":
        print("current_accepted_phase: Phase 0 — Architecture Freeze")
        print("current_working_phase: Phase 1 — Bootstrap Without Traffic Changes")
        print("firewall_apply_allowed: no")
        print("abuse_automation_allowed: no")
        print("customer_onboarding_allowed: no")
        return 0

    if args.command == "doctor":
        return doctor(path)

    if args.command == "config" and args.subcommand == "validate":
        ok, msg = validate_config(path)
        print("OK" if ok else msg)
        return 0 if ok else 1

    if args.command == "config" and args.subcommand == "show":
        return config_show(path)

    if args.command == "db" and args.subcommand == "ping":
        return db_ping()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod 0755 /opt/mpf-py/mpf_cli.py
ln -sf /opt/mpf-py/mpf_cli.py /usr/local/bin/mpf

mkdir -p /opt/mpf-py/tests
cat > /opt/mpf-py/tests/test_phase1_safety.py <<'PY'
from pathlib import Path

import yaml

CONFIG = Path("/etc/mpf/mpf.yaml")


def load_config():
    with CONFIG.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_config_exists():
    assert CONFIG.exists()


def test_firewall_stays_plan_only():
    cfg = load_config()
    assert cfg["firewall"]["apply_mode"] == "plan_only"


def test_btc_backend_port_is_frozen():
    cfg = load_config()
    assert cfg["lanes"]["btc"]["backend_port"] == 60010


def test_database_is_postgresql():
    cfg = load_config()
    assert cfg["database"]["url"].startswith("postgresql")


def test_abuse_threshold_is_one_hour_minimum():
    cfg = load_config()
    assert int(cfg["abuse"]["threshold_sec"]) >= 3600
PY

chown -R root:root /opt/mpf-py
chmod -R go-w /opt/mpf-py

echo
echo '===== 7) ENABLE DOCKER SERVICE ONLY; DO NOT RUN CONTAINERS ====='
systemctl enable --now docker

echo
echo '===== 8) PHASE 1 SMOKE TESTS ====='
mpf --help
mpf --version
mpf phase-status
mpf config validate
mpf config show
mpf doctor
mpf db ping

cd /opt/mpf-py
python -m pytest

systemctl status postgresql --no-pager
docker version
docker compose version || true
conntrack -V
iptables --version

echo
echo '===== 9) CONFIRM NO PRODUCTION MPF TRAFFIC STATE ====='
echo 'Checking listening ports:'
ss -lntup || true

echo
echo 'Checking MPF-like iptables names:'
iptables-save | grep -E 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true

echo
echo '===== MPF PHASE 1 BOOTSTRAP: COMPLETE ====='
echo 'Send the full output to review before moving forward.'
