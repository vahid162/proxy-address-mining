#!/usr/bin/env bash
set -u

VERSION="0.1.246"
OUT_DIR="${1:-/tmp/phase11-restart-autostart-proof-${VERSION}}"
mkdir -p "${OUT_DIR}"

run_capture() {
  local name="$1"
  shift
  {
    echo "# command: $*"
    echo "# captured_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$@"
  } >"${OUT_DIR}/${name}" 2>&1 || true
}

printf '%s\n' "${VERSION}" >"${OUT_DIR}/repository_version.txt"
run_capture mpf_version.txt mpf --version
# Strip helper comments from exact version evidence if mpf is available.
if command -v mpf >/dev/null 2>&1; then
  mpf --version >"${OUT_DIR}/mpf_version.txt" 2>&1 || true
fi

run_capture phase_status.txt mpf phase-status
run_capture db_ping.txt mpf db ping
if [ -s "${OUT_DIR}/db_ping.txt" ] && grep -q '^OK$' "${OUT_DIR}/db_ping.txt"; then
  printf 'OK\n' >"${OUT_DIR}/db_ping.txt"
fi
run_capture db_status.txt mpf db status
run_capture lanes.txt mpf lanes list
run_capture customers.txt mpf customer list --include-deleted

if command -v docker >/dev/null 2>&1; then
  run_capture docker_ps.txt docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
else
  printf 'docker command not found\n' >"${OUT_DIR}/docker_ps.txt"
fi

if command -v ss >/dev/null 2>&1; then
  run_capture listeners.txt ss -ltnp
else
  printf 'ss command not found\n' >"${OUT_DIR}/listeners.txt"
fi

{
  echo "Phase 11 restart/autostart expected dependency order (read-only evidence):"
  echo "1. PostgreSQL reachable before mpf DB-backed CLI checks."
  echo "2. v2rayA local UI listener must be local-only on 127.0.0.1:2015."
  echo "3. BTC forwarder/backend listener must be local-only on 127.0.0.1:60010."
  echo "4. Accepted limited BTC proxy containers should be visible/running before customer traffic evidence is accepted."
  echo
  echo "docker_ps excerpt:"
  cat "${OUT_DIR}/docker_ps.txt"
  echo
  echo "listeners excerpt:"
  cat "${OUT_DIR}/listeners.txt"
} >"${OUT_DIR}/container_listener_order.txt"

if command -v iptables-save >/dev/null 2>&1; then
  run_capture iptables_save.txt iptables-save
else
  printf 'iptables-save command not found\n' >"${OUT_DIR}/iptables_save.txt"
fi
if command -v ip6tables-save >/dev/null 2>&1; then
  run_capture ip6tables_save.txt ip6tables-save
else
  printf 'ip6tables-save command not found\n' >"${OUT_DIR}/ip6tables_save.txt"
fi

# Classify firewall evidence through the official read-only controlled artifact gate.
# The restart/autostart proof must never synthesize an empty unknown-artifact file.
mpf production current-controlled-artifact-gate \
  --expected-version "${VERSION}" \
  --iptables-save-file "${OUT_DIR}/iptables_save.txt" \
  --ip6tables-save-file "${OUT_DIR}/ip6tables_save.txt" \
  --output json >"${OUT_DIR}/current_controlled_artifact_gate.json" 2>"${OUT_DIR}/current_controlled_artifact_gate.stderr" || true

python - "${OUT_DIR}/current_controlled_artifact_gate.json" "${OUT_DIR}/phase11_firewall_artifacts.txt" "${OUT_DIR}/unknown_mpf_firewall_artifacts.txt" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])
known_path = Path(sys.argv[2])
unknown_path = Path(sys.argv[3])

try:
    report = json.loads(json_path.read_text(encoding="utf-8"))
except Exception as exc:  # noqa: BLE001 - helper evidence must fail closed.
    known_path.write_text("known_controlled_phase11_artifacts: missing\n", encoding="utf-8")
    unknown_path.write_text(f"artifact_gate_parse_failed: {exc}\n", encoding="utf-8")
    raise SystemExit(0)

if report.get("known_controlled_artifacts_present") is True:
    known_path.write_text("known_controlled_phase11_artifacts: present\n", encoding="utf-8")
else:
    known_path.write_text("known_controlled_phase11_artifacts: missing\n", encoding="utf-8")

unknown = report.get("unknown_mpf_artifacts")
if unknown == []:
    unknown_path.write_text("unknown_mpf_firewall_artifacts: []\n", encoding="utf-8")
elif isinstance(unknown, list):
    unknown_path.write_text("".join(f"{item}\n" for item in unknown), encoding="utf-8")
else:
    unknown_path.write_text("unknown_mpf_artifacts_missing_or_invalid\n", encoding="utf-8")
PY

cat >"${OUT_DIR}/mutation_flags.json" <<'JSON'
{
  "mutation_performed": false,
  "db_mutation_performed": false,
  "firewall_apply_performed": false,
  "conntrack_flush_performed": false,
  "docker_restart_performed": false,
  "systemd_restart_performed": false
}
JSON

run_capture proof_report.json mpf production restart-autostart-proof --evidence-dir "${OUT_DIR}" --output json

cat >"${OUT_DIR}/OPERATOR_NEXT_STEPS.txt" <<EOF
Phase 11 restart/autostart proof helper completed read-only collection in:
${OUT_DIR}

Manual workflow reminder:
1. Before any manual restart/reboot, capture this pre-restart evidence directory.
2. Perform any restart/reboot manually outside this helper only if the operator has approved it.
3. After the system returns, run this helper again.
4. Review proof_report.json and run:
   mpf production restart-autostart-proof --evidence-dir ${OUT_DIR} --output json

This helper did not reboot, did not restart Docker, did not restart systemd services,
did not mutate PostgreSQL, did not apply firewall changes, and did not flush conntrack.
EOF

printf 'Phase 11 restart/autostart proof evidence directory: %s\n' "${OUT_DIR}"
printf 'Review %s/proof_report.json and %s/OPERATOR_NEXT_STEPS.txt\n' "${OUT_DIR}" "${OUT_DIR}"
