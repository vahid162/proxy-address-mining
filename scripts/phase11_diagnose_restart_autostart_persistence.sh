#!/usr/bin/env bash
set -euo pipefail

VERSION="0.1.246"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-/tmp/mpf-phase11-restart-autostart-persistence-$(date -u +%Y%m%dT%H%M%SZ)}"
COMPOSE_FILE="${MPF_PROXY_COMPOSE_FILE:-${REPO_ROOT}/compose/mpf-proxy.compose.yaml}"
PROJECT_NAME="${MPF_PROXY_PROJECT_NAME:-mpf-proxy}"

mkdir -p "${OUT_DIR}"

run_capture_cmd() {
  local name="$1"
  shift
  {
    printf '$'
    for arg in "$@"; do printf ' %q' "$arg"; done
    printf '\n'
    "$@"
  } >"${OUT_DIR}/${name}" 2>&1 || true
}

run_capture_cmd mpf_phase_status.txt mpf phase-status
run_capture_cmd mpf_proxy_status.txt mpf proxy status
run_capture_cmd mpf_proxy_doctor.txt mpf proxy doctor
run_capture_cmd docker_ps_a.txt docker ps -a
run_capture_cmd docker_compose_ps_a.txt docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps -a
run_capture_cmd ss_ltnp.txt ss -ltnp
run_capture_cmd iptables_save.txt iptables-save
run_capture_cmd ip6tables_save.txt ip6tables-save
run_capture_cmd current_controlled_artifact_gate.json mpf production current-controlled-artifact-gate \
  --expected-version "${VERSION}" \
  --iptables-save-file "${OUT_DIR}/iptables_save.txt" \
  --ip6tables-save-file "${OUT_DIR}/ip6tables_save.txt" \
  --output json
run_capture_cmd restart_autostart_proof.json mpf production restart-autostart-proof --output json
run_capture_cmd restart_autostart_persistence_diagnosis.json mpf production restart-autostart-persistence-diagnosis --expected-version "${VERSION}" --output json

cat >"${OUT_DIR}/README.txt" <<EOF
Phase 11 restart/autostart persistence diagnosis bundle (${VERSION}).
This helper is read-only evidence collection only. It captures MPF status, Docker listings,
listener state, iptables-save snapshots, controlled artifact gate output, restart/autostart proof,
and the post-reboot persistence diagnosis. It intentionally does not perform runtime/service,
database, firewall, restore, or connection-table mutation.
EOF

printf 'Phase 11 restart/autostart persistence diagnosis evidence directory: %s\n' "${OUT_DIR}"
