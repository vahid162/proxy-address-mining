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

fail() {
  echo "CRITICAL: $*"
  exit 1
}

section "PRECHECK"

[ "$(id -u)" -eq 0 ] || fail "run as root"
[ -f "$ZIP_PATH" ] || fail "zip file not found: $ZIP_PATH"
[ -d "$APP_DIR" ] || fail "app dir not found: $APP_DIR"
[ -x "$APP_DIR/.venv/bin/python" ] || fail "existing venv python missing: $APP_DIR/.venv/bin/python"
command -v python3 >/dev/null 2>&1 || fail "python3 not found"

mkdir -p "$BACKUP_DIR"
echo "ZIP_PATH=$ZIP_PATH"
echo "APP_DIR=$APP_DIR"
echo "BACKUP_DIR=$BACKUP_DIR"

section "BACKUP CURRENT SOURCE"
tar -C /opt --exclude='mpf-py-src/.venv' -czf "$BACKUP_DIR/mpf-py-src-no-venv.tgz" mpf-py-src
[ -f /etc/mpf/mpf.yaml ] && cp -a /etc/mpf/mpf.yaml "$BACKUP_DIR/mpf.yaml"
[ -f /usr/local/bin/mpf ] && cp -a /usr/local/bin/mpf "$BACKUP_DIR/usr-local-bin-mpf"
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
[ -n "$NEW_SRC" ] || fail "extracted source directory not found"
echo "NEW_SRC=$NEW_SRC"

section "SANITY CHECK NEW SOURCE"
required_files=(
  pyproject.toml
  README.md
  AGENTS.md
  compose/mpf-proxy.compose.yaml
  docs/INDEX.md
  docs/PHASE_STATUS.md
  docs/AI_CODING_RULES.md
  docs/AI_PHASE_4_TASK.md
  docs/AI_PHASE_4_2_TASK.md
  docs/AI_PHASE_5_TASK.md
  docs/PHASE_4_SERVER_RUNBOOK.md
  docs/PHASE_4_1_SERVER_RESULT.md
  docs/PHASE_4_2_SERVER_SYNC_RESULT.md
  docs/PHASE_4_2_RUNTIME_ACTIVATION_RUNBOOK.md
  docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_REVIEW.md
  docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_TASK.md
  docs/PHASE_4_RUNTIME_ACTIVATION_SERVER_RESULT.md
  docs/OFFLINE_SYNC_RUNBOOK.md
  docs/MIGRATION_POLICY.md
  scripts/verify_phase4_planning_gate.sh
  scripts/sync_main_zip_on_server.sh
  scripts/phase4_runtime_activation_execute.sh
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
  [ -f "$NEW_SRC/$file" ] || fail "required file missing in zip: $file"
  echo "OK: $file"
done

grep -q 'current_accepted_phase: Phase 4 Runtime Activation' "$NEW_SRC/docs/PHASE_STATUS.md" || fail "new PHASE_STATUS does not show accepted Phase 4 runtime activation"
grep -q 'current_working_phase: Phase 5' "$NEW_SRC/docs/PHASE_STATUS.md" || fail "new PHASE_STATUS does not show Phase 5 working phase"
grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' "$NEW_SRC/docs/PHASE_STATUS.md" || fail "new PHASE_STATUS does not keep proxy data-plane limited local-only"
grep -q 'customer_onboarding_allowed: db_only_after_phase5_gate' "$NEW_SRC/docs/PHASE_STATUS.md" || fail "new PHASE_STATUS does not keep Phase 5 DB-only customer boundary"
grep -q 'runtime_activation_allowed: false' "$NEW_SRC/configs/mpf.example.yaml" || fail "example config does not keep proxy runtime activation disabled"
grep -q 'phase4_runtime_activation_execute.sh' "$NEW_SRC/docs/PHASE_4_RUNTIME_ACTIVATION_EXECUTION_TASK.md" || fail "runtime execution task does not reference approved script"
grep -q -- '--pull never' "$NEW_SRC/scripts/phase4_runtime_activation_execute.sh" || fail "runtime execution script must use --pull never"

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
mpf phase-status | grep -q 'current_accepted_phase: Phase 4 Runtime Activation' || fail "mpf phase-status is not aligned with accepted Phase 4 runtime"
mpf phase-status | grep -q 'current_working_phase: Phase 5' || fail "mpf phase-status is not aligned with Phase 5"
mpf phase-status | grep -q 'proxy_data_plane_allowed: limited_runtime_local_only' || fail "mpf phase-status does not show limited_runtime_local_only"

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

section "RUN PHASE 5 SAFETY GATE"
bash "$APP_DIR/scripts/verify_phase4_planning_gate.sh"

section "FINAL VERDICT"
echo "OK: GitHub main zip synced successfully."
echo "OK: server source is aligned with GitHub zip."
echo "OK: accepted Phase 4 runtime / Phase 5 DB-only gate is installed and verified."
echo "OK: Runtime remains limited local-only; production customer traffic is still disabled."
echo "Backup: $BACKUP_DIR"
