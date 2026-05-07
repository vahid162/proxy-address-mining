#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="/opt/mpf-py-src"
RUNTIME_LINK="/usr/local/bin/mpf"
BACKUP_ROOT="/var/backups/mpf"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_ROOT}/phase3-runtime-promote-${STAMP}"

section() {
  printf '\n===== %s =====\n' "$1"
}

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo 'This script must run as root because it updates /usr/local/bin/mpf and creates backups.'
    exit 1
  fi
}

require_root

section 'PRECHECK'
if [ ! -d "$SOURCE_DIR" ]; then
  echo "CRITICAL: source directory not found: $SOURCE_DIR"
  exit 1
fi
if [ ! -x "$SOURCE_DIR/.venv/bin/python" ]; then
  echo "CRITICAL: missing executable: $SOURCE_DIR/.venv/bin/python"
  exit 1
fi
if [ ! -f "$SOURCE_DIR/mpf/interfaces/cli.py" ]; then
  echo "CRITICAL: missing Phase 3 CLI module: $SOURCE_DIR/mpf/interfaces/cli.py"
  exit 1
fi
if ! grep -q "apply_mode: plan_only" /etc/mpf/mpf.yaml; then
  echo 'CRITICAL: /etc/mpf/mpf.yaml must remain apply_mode: plan_only'
  exit 1
fi

section 'BACKUP CURRENT RUNTIME'
install -d -m 0750 -o mpf -g mpf "$BACKUP_DIR"
if [ -e "$RUNTIME_LINK" ] || [ -L "$RUNTIME_LINK" ]; then
  cp -a "$RUNTIME_LINK" "$BACKUP_DIR/mpf.current"
  readlink -f "$RUNTIME_LINK" > "$BACKUP_DIR/mpf.current.realpath" || true
fi
if [ -d /opt/mpf-py ]; then
  tar -C /opt -czf "$BACKUP_DIR/opt-mpf-py-before.tar.gz" mpf-py
fi
cp -a /etc/mpf "$BACKUP_DIR/etc-mpf" 2>/dev/null || true
chown -R mpf:mpf "$BACKUP_DIR"

echo "backup_dir: $BACKUP_DIR"

section 'INSTALL OFFICIAL MPF WRAPPER'
cat > /usr/local/bin/mpf <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
export PYTHONPATH="/opt/mpf-py-src${PYTHONPATH:+:${PYTHONPATH}}"
exec /opt/mpf-py-src/.venv/bin/python -m mpf.interfaces.cli "$@"
EOF
chmod 0755 /usr/local/bin/mpf

section 'VERIFY PHASE 3 COMMANDS'
mpf --version
mpf phase-status
mpf config validate
mpf doctor
mpf db ping
mpf db status
mpf lanes list
mpf customer list
mpf jobs status

section 'VERIFY TESTS AND MIGRATION'
cd "$SOURCE_DIR"
.venv/bin/python -m pytest -q
sudo -u mpf .venv/bin/alembic current
sudo -u mpf .venv/bin/alembic heads

section 'VERIFY NO TRAFFIC CHANGE'
docker ps -a
if iptables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
  echo 'CRITICAL: MPF/backend reference appeared in iptables after runtime promotion'
  iptables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
  exit 1
fi
if ip6tables-save | grep -Eiq 'MPF|MPFBTC|MPFC_|MPFO_|60010'; then
  echo 'CRITICAL: MPF/backend reference appeared in ip6tables after runtime promotion'
  ip6tables-save | grep -Ei 'MPF|MPFBTC|MPFC_|MPFO_|60010' || true
  exit 1
fi
ss -lntup | grep -E ':(60010|2014|20170|20171|20172|22070|22071|22072)\b' || true

echo 'OK: Phase 3 runtime promotion completed without traffic-changing behavior.'
echo "Backup saved at: $BACKUP_DIR"
