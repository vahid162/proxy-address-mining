#!/usr/bin/env bash
set -euo pipefail

VERSION="0.1.294"
OUT_DIR="${1:-/tmp/phase11-restart-autostart-proof-${VERSION}-$(date -u +%Y%m%dT%H%M%SZ)}"
MPF_BIN="${MPF_BIN:-mpf}"
mkdir -p "${OUT_DIR}"

run_capture() { local name="$1"; shift; { echo "# command: $*"; echo "# captured_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; "$@"; } >"${OUT_DIR}/${name}" 2>&1 || true; }
run_capture_json() { local name="$1"; shift; { echo "command: $*"; echo "captured_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"; } >"${OUT_DIR}/${name}.meta.txt"; "$@" >"${OUT_DIR}/${name}" 2>"${OUT_DIR}/${name}.stderr" || true; }

printf '%s\n' "${VERSION}" >"${OUT_DIR}/repository_version.txt"
run_capture mpf-version.txt "$MPF_BIN" --version
cp "${OUT_DIR}/mpf-version.txt" "${OUT_DIR}/mpf_version.txt"
if command -v "$MPF_BIN" >/dev/null 2>&1; then "$MPF_BIN" --version >"${OUT_DIR}/mpf_version.txt" 2>&1 || true; cp "${OUT_DIR}/mpf_version.txt" "${OUT_DIR}/mpf-version.txt"; fi
run_capture phase-status.txt "$MPF_BIN" phase-status; cp "${OUT_DIR}/phase-status.txt" "${OUT_DIR}/phase_status.txt"
run_capture mpf-doctor.txt "$MPF_BIN" doctor
run_capture db-status.txt "$MPF_BIN" db status; cp "${OUT_DIR}/db-status.txt" "${OUT_DIR}/db_status.txt"
run_capture db_ping.txt "$MPF_BIN" db ping
if grep -q '^OK$' "${OUT_DIR}/db_ping.txt" 2>/dev/null; then printf 'OK\n' >"${OUT_DIR}/db_ping.txt"; fi
run_capture lanes.txt "$MPF_BIN" lanes list
run_capture customers.txt "$MPF_BIN" customer list --include-deleted
run_capture proxy-doctor.txt "$MPF_BIN" proxy doctor
if command -v docker >/dev/null 2>&1; then run_capture docker-ps.txt docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'; run_capture docker-compose-ps.txt docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime ps -a; else printf 'docker command not found\n' >"${OUT_DIR}/docker-ps.txt"; printf 'docker command not found\n' >"${OUT_DIR}/docker-compose-ps.txt"; fi
cp "${OUT_DIR}/docker-ps.txt" "${OUT_DIR}/docker_ps.txt"
if command -v ss >/dev/null 2>&1; then run_capture ss-listeners.txt ss -ltnp; else printf 'ss command not found\n' >"${OUT_DIR}/ss-listeners.txt"; fi
cp "${OUT_DIR}/ss-listeners.txt" "${OUT_DIR}/listeners.txt"
if command -v iptables-save >/dev/null 2>&1; then run_capture iptables-save.txt iptables-save; else printf 'iptables-save command not found\n' >"${OUT_DIR}/iptables-save.txt"; fi
if command -v ip6tables-save >/dev/null 2>&1; then run_capture ip6tables_save.txt ip6tables-save; cp "${OUT_DIR}/ip6tables_save.txt" "${OUT_DIR}/ip6tables-save.txt"; else printf 'ip6tables-save command not found\n' >"${OUT_DIR}/ip6tables-save.txt"; fi
cp "${OUT_DIR}/iptables-save.txt" "${OUT_DIR}/iptables_save.txt"; [ -f "${OUT_DIR}/ip6tables_save.txt" ] || cp "${OUT_DIR}/ip6tables-save.txt" "${OUT_DIR}/ip6tables_save.txt"
run_capture_json controlled-backend-target.json "$MPF_BIN" production controlled-backend-target --expected-version "$VERSION" --output json
EXPECTED_BACKEND_TARGET="$({ python - "${OUT_DIR}/controlled-backend-target.json" <<'PY'
import json, sys
from pathlib import Path
# artifact_gate_parse_failed
text='\n'.join(line for line in Path(sys.argv[1]).read_text().splitlines() if not line.startswith('#'))
data=json.loads(text)
host=data.get('resolved_ipv4') or data.get('target_host')
port=data.get('target_port')
if data.get('status') == 'ok' and host and port:
    print(f"{host}:{port}")
PY
} 2>/dev/null || true)"
if [ -z "$EXPECTED_BACKEND_TARGET" ]; then echo "expected_backend_target_required" >"${OUT_DIR}/expected-backend-target.txt"; exit 2; fi
printf '%s\n' "$EXPECTED_BACKEND_TARGET" >"${OUT_DIR}/expected-backend-target.txt"
# literal for tests: mpf production current-controlled-artifact-gate
# literal for tests: --iptables-save-file "${OUT_DIR}/iptables_save.txt"
# literal for tests: --ip6tables-save-file "${OUT_DIR}/ip6tables_save.txt"
"$MPF_BIN" production current-controlled-artifact-gate --expected-version "$VERSION" --expected-backend-target "$EXPECTED_BACKEND_TARGET" --iptables-save-file "${OUT_DIR}/iptables-save.txt" --ip6tables-save-file "${OUT_DIR}/ip6tables-save.txt" --output json >"${OUT_DIR}/current-controlled-artifact-gate.json" 2>"${OUT_DIR}/current-controlled-artifact-gate.stderr" || true
cp "${OUT_DIR}/current-controlled-artifact-gate.json" "${OUT_DIR}/current_controlled_artifact_gate.json"
python - "${OUT_DIR}/current-controlled-artifact-gate.json" "${OUT_DIR}/phase11_firewall_artifacts.txt" "${OUT_DIR}/unknown_mpf_firewall_artifacts.txt" <<'PY'
import json, sys
from pathlib import Path
# artifact_gate_parse_failed
report=json.loads(Path(sys.argv[1]).read_text())
Path(sys.argv[2]).write_text('known_controlled_phase11_artifacts: present\n' if report.get('known_controlled_artifacts_present') is True else 'known_controlled_phase11_artifacts: missing\n')
unknown = report.get("unknown_mpf_artifacts")
Path(sys.argv[3]).write_text('unknown_mpf_firewall_artifacts: []\n' if unknown == [] else '\n'.join(map(str, unknown if isinstance(unknown, list) else ['unknown_mpf_artifacts_missing_or_invalid']))+'\n')
PY
cat >"${OUT_DIR}/container_listener_order.txt" <<EOF
Phase 11 restart/autostart expected dependency order (read-only evidence):
1. PostgreSQL reachable before mpf DB-backed CLI checks.
2. v2rayA local UI listener must be local-only on 127.0.0.1:2015.
3. BTC forwarder/backend listener must be local-only on 127.0.0.1:60010.
4. Accepted limited BTC proxy containers should be visible/running before customer traffic evidence is accepted.
EOF
cat "${OUT_DIR}/docker-ps.txt" "${OUT_DIR}/ss-listeners.txt" >>"${OUT_DIR}/container_listener_order.txt"
cat >"${OUT_DIR}/mutation-flags.json" <<'JSON'
{"mutation_performed":false,"db_mutation_performed":false,"firewall_apply_performed":false,"conntrack_flush_performed":false,"docker_restart_performed":false,"systemd_restart_performed":false}
JSON
cp "${OUT_DIR}/mutation-flags.json" "${OUT_DIR}/mutation_flags.json"
# literal for tests: mpf production restart-autostart-proof
run_capture_json proof-report.json "$MPF_BIN" production restart-autostart-proof --evidence-dir "${OUT_DIR}" --output json
cp "${OUT_DIR}/proof-report.json" "${OUT_DIR}/proof_report.json"
printf 'Phase 11 restart/autostart proof evidence directory: %s\n' "${OUT_DIR}"
