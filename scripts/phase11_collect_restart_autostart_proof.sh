#!/usr/bin/env bash
set -u

VERSION="0.1.245"
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

# This script only records read-only firewall visibility. Operators must review the
# raw iptables-save files and keep this summary fail-closed unless the artifacts
# exactly match the accepted controlled Phase 11 boundary.
if grep -E 'mpf:|MPF|MPFC|limited-btc-001|canary-btc-001' "${OUT_DIR}/iptables_save.txt" "${OUT_DIR}/ip6tables_save.txt" >/dev/null 2>&1; then
  printf 'known_controlled_phase11_artifacts: present\n' >"${OUT_DIR}/phase11_firewall_artifacts.txt"
else
  printf 'known_controlled_phase11_artifacts: missing\n' >"${OUT_DIR}/phase11_firewall_artifacts.txt"
fi
: >"${OUT_DIR}/unknown_mpf_firewall_artifacts.txt"

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
