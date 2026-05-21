#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_PATH="${1:-/etc/mpf/mpf.yaml}"
APP_DIR="/opt/mpf-py-src"
BACKUP_BASE="/var/backups/mpf"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_BASE}/phase4-1-config-planning-${STAMP}"

section() {
  printf '\n===== %s =====\n' "$1"
}

section "PRECHECK"

if [ "$(id -u)" -ne 0 ]; then
  echo "CRITICAL: run as root"
  exit 1
fi

if [ ! -f "$CONFIG_PATH" ]; then
  echo "CRITICAL: config file not found: $CONFIG_PATH"
  exit 1
fi

if [ ! -d "$APP_DIR" ]; then
  echo "CRITICAL: app dir not found: $APP_DIR"
  exit 1
fi

if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
  echo "CRITICAL: existing venv python missing: $APP_DIR/.venv/bin/python"
  exit 1
fi

if [ ! -f "$APP_DIR/compose/mpf-proxy.compose.yaml" ]; then
  echo "CRITICAL: Phase 4 compose template missing: $APP_DIR/compose/mpf-proxy.compose.yaml"
  exit 1
fi

mkdir -p "$BACKUP_DIR"
cp -a "$CONFIG_PATH" "$BACKUP_DIR/mpf.yaml.before"

echo "CONFIG_PATH=$CONFIG_PATH"
echo "APP_DIR=$APP_DIR"
echo "BACKUP_DIR=$BACKUP_DIR"

section "PATCH CONFIG PLANNING FIELDS"

"$APP_DIR/.venv/bin/python" - "$CONFIG_PATH" <<'PY'
from __future__ import annotations

from pathlib import Path
import sys

import yaml

config_path = Path(sys.argv[1])
data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
if not isinstance(data, dict):
    raise SystemExit("CRITICAL: config must be a YAML object")


def ensure_dict(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if value is None:
        value = {}
        parent[key] = value
    if not isinstance(value, dict):
        raise SystemExit(f"CRITICAL: {key} must be a YAML object")
    return value

firewall = ensure_dict(data, "firewall")
if firewall.get("apply_mode") != "plan_only":
    raise SystemExit("CRITICAL: firewall.apply_mode must remain plan_only")
firewall.setdefault("backend", "iptables")
firewall.setdefault("lock_path", "/run/mpf-firewall.lock")

proxy = ensure_dict(data, "proxy")
proxy["compose_file"] = "/opt/mpf-py-src/compose/mpf-proxy.compose.yaml"
proxy["project_name"] = "mpf-proxy"
proxy["runtime_activation_allowed"] = False

v2raya = ensure_dict(data, "v2raya")
v2raya["ui_bind_host"] = "127.0.0.1"
v2raya["ui_port"] = 2015

lanes = ensure_dict(data, "lanes")
btc = ensure_dict(lanes, "btc")
backend_port = btc.get("backend_port", 60010)
if int(backend_port) != 60010:
    raise SystemExit(f"CRITICAL: btc.backend_port must remain 60010, got {backend_port!r}")
btc.setdefault("enabled", True)
btc["backend_port"] = 60010
btc.setdefault("chain_prefix", "MPFBTC")

forwarder = ensure_dict(btc, "forwarder")
forwarder["service_name"] = "mpf-forwarder-btc"
forwarder["bind_host"] = "127.0.0.1"
forwarder["listen_port"] = 60010
forwarder["upstream_socks"] = "v2raya:20170"

if not isinstance(btc.get("upstreams"), list) or not btc["upstreams"]:
    btc["upstreams"] = [{"host": "bitcoin.viabtc.io", "port": 3333}]

config_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
PY

cp -a "$CONFIG_PATH" "$BACKUP_DIR/mpf.yaml.after"

echo "OK: Phase 4.1 planning fields written to $CONFIG_PATH"
echo "OK: backup written to $BACKUP_DIR"

section "VALIDATE CONFIG AND PROXY DOCTOR"

cd "$APP_DIR"

mpf config validate --config "$CONFIG_PATH"
mpf proxy config-check --config "$CONFIG_PATH"
mpf proxy status --config "$CONFIG_PATH"
mpf proxy doctor --config "$CONFIG_PATH"

section "RUN PHASE 4 PLANNING GATE"

bash "$APP_DIR/scripts/verify_phase4_planning_gate.sh"

section "FINAL VERDICT"

echo "OK: Phase 4.1 server config planning fields are applied."
echo "OK: v2rayA UI operator port is 2015."
echo "OK: Runtime activation is still NOT authorized."
echo "Backup: $BACKUP_DIR"
