#!/usr/bin/env bash
set -Eeuo pipefail

ZIP_PATH="${1:-/tmp/proxy-address-mining-main.zip}"
APP_DIR="/opt/mpf-py-src"
BACKUP_BASE="/var/backups/mpf"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_BASE}/source-before-zip-sync-${STAMP}"

section() {
  printf '\n===== %s =====\n' "$1"
}

section "PRECHECK"

if [ "$(id -u)" -ne 0 ]; then
  echo "CRITICAL: run as root"
  exit 1
fi

if [ ! -f "$ZIP_PATH" ]; then
  echo "CRITICAL: zip file not found: $ZIP_PATH"
  exit 1
fi

if [ ! -d "$APP_DIR" ]; then
  echo "CRITICAL: app dir not found: $APP_DIR"
  exit 1
fi

if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
  echo "CRITICAL: existing venv python missing: $APP_DIR/.venv/bin/python"
  echo "Server has no GitHub/internet path, so dependencies will not be installed."
  exit 1
fi

command -v python3 >/dev/null 2>&1 || {
  echo "CRITICAL: python3 not found"
  exit 1
}

mkdir -p "$BACKUP_DIR"

echo "ZIP_PATH=$ZIP_PATH"
echo "APP_DIR=$APP_DIR"
echo "BACKUP_DIR=$BACKUP_DIR"

section "BACKUP CURRENT SOURCE"

tar -C /opt --exclude='mpf-py-src/.venv' -czf "$BACKUP_DIR/mpf-py-src-no-venv.tgz" mpf-py-src

if [ -f /etc/mpf/mpf.yaml ]; then
  cp -a /etc/mpf/mpf.yaml "$BACKUP_DIR/mpf.yaml"
fi

if [ -f /usr/local/bin/mpf ]; then
  cp -a /usr/local/bin/mpf "$BACKUP_DIR/usr-local-bin-mpf"
fi

echo "OK: backup created at $BACKUP_DIR"

section "EXTRACT ZIP"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 - "$ZIP_PATH" "$TMP_DIR" <<'PY'
import sys
import zipfile
from pathlib import Path

zip_path = Path(sys.argv[1])
target = Path(sys.argv[2])

with zipfile.ZipFile(zip_path) as zf:
    zf.extractall(target)
PY

NEW_SRC="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d -name 'proxy-address-mining-*' | head -n 1 || true)"

if [ -z "$NEW_SRC" ]; then
  echo "CRITICAL: extracted source directory not found"
  find "$TMP_DIR" -maxdepth 2 -type d -print
  exit 1
fi

echo "NEW_SRC=$NEW_SRC"

section "SANITY CHECK NEW SOURCE"

required_files=(
  pyproject.toml
  README.md
  AGENTS.md
  docs/INDEX.md
  docs/PHASE_STATUS.md
  docs/AI_PHASE_4_TASK.md
  docs/PHASE_4_SERVER_RUNBOOK.md
  docs/OFFLINE_SYNC_RUNBOOK.md
  scripts/verify_phase4_planning_gate.sh
  scripts/sync_main_zip_on_server.sh
  mpf/config.py
  mpf/interfaces/cli.py
  mpf/services/proxy_doctor_service.py
  mpf/domain/health.py
  mpf/adapters/docker_compose.py
  mpf/adapters/socket_inspector.py
  tests/test_cli_phase_status.py
  tests/test_smoke.py
  tests/test_phase4_proxy.py
)

for file in "${required_files[@]}"; do
  if [ ! -f "$NEW_SRC/$file" ]; then
    echo "CRITICAL: required file missing in zip: $file"
    exit 1
  fi
  echo "OK: $file"
done

if ! grep -q 'current_accepted_phase: Phase 3.1' "$NEW_SRC/docs/PHASE_STATUS.md"; then
  echo "CRITICAL: new PHASE_STATUS does not show Phase 3.1 accepted"
  exit 1
fi

if ! grep -q 'current_working_phase: Phase 4' "$NEW_SRC/docs/PHASE_STATUS.md"; then
  echo "CRITICAL: new PHASE_STATUS does not show Phase 4 planning"
  exit 1
fi

if ! grep -q 'proxy_data_plane_allowed: planning_only' "$NEW_SRC/docs/PHASE_STATUS.md"; then
  echo "CRITICAL: new PHASE_STATUS does not keep proxy_data_plane_allowed as planning_only"
  exit 1
fi

if ! grep -q 'runtime_activation_allowed: false' "$NEW_SRC/configs/mpf.example.yaml"; then
  echo "CRITICAL: example config does not keep proxy runtime activation disabled"
  exit 1
fi

section "SYNC SOURCE WITHOUT TOUCHING VENV"

find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name '.venv' -exec rm -rf {} +

cp -a "$NEW_SRC"/. "$APP_DIR"/

chmod +x "$APP_DIR"/scripts/*.sh 2>/dev/null || true

echo "OK: source synced to $APP_DIR"
echo "OK: existing venv preserved"

section "INSTALL SAFE MPF WRAPPER"

cat > /usr/local/bin/mpf <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/mpf-py-src
exec /opt/mpf-py-src/.venv/bin/python -c 'from mpf.interfaces.cli import app; app()' "$@"
EOF

chmod 0755 /usr/local/bin/mpf

echo "OK: /usr/local/bin/mpf updated"

section "VERIFY PHASE STATUS"

cd "$APP_DIR"

mpf --version
mpf phase-status

if ! mpf phase-status | grep -q 'current_accepted_phase: Phase 3.1'; then
  echo "CRITICAL: mpf phase-status still not aligned with Phase 3.1"
  exit 1
fi

if ! mpf phase-status | grep -q 'current_working_phase: Phase 4'; then
  echo "CRITICAL: mpf phase-status still not aligned with Phase 4 planning"
  exit 1
fi

if ! mpf phase-status | grep -q 'proxy_data_plane_allowed: planning_only'; then
  echo "CRITICAL: mpf phase-status does not show planning_only"
  exit 1
fi

section "RUN PYTEST WITH VENV"

"$APP_DIR/.venv/bin/python" -m pytest -q

section "RUN SAFE SMOKE CHECKS"

mpf config validate
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status
mpf proxy config-check
mpf proxy status
mpf proxy doctor

section "RUN PHASE 4 PLANNING GATE"

bash "$APP_DIR/scripts/verify_phase4_planning_gate.sh"

section "FINAL VERDICT"

echo "OK: GitHub main zip synced successfully."
echo "OK: server source is aligned with GitHub zip."
echo "OK: Phase 4 planning gate is installed and verified."
echo "OK: Runtime activation is still NOT authorized."
echo "Backup: $BACKUP_DIR"
