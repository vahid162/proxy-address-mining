#!/usr/bin/env bash
set -euo pipefail
VERSION="0.1.279"
OUT_DIR="${1:-/tmp/phase11-restart-autostart-proof-after-persistence-fix-$(date -u +%Y%m%dT%H%M%SZ)}"
MPF_BIN="${MPF_BIN:-mpf}"
mkdir -p "$OUT_DIR"
run_capture() { local name="$1"; shift; echo "===== $name ====="; "$@" >"$OUT_DIR/$name" 2>&1 || true; cat "$OUT_DIR/$name"; }
extract_target() { python - "$1" <<'PY'
import json, sys
from pathlib import Path
text='\n'.join(line for line in Path(sys.argv[1]).read_text().splitlines() if not line.startswith('#'))
data=json.loads(text); host=data.get('resolved_ipv4') or data.get('target_host'); port=data.get('target_port')
if data.get('status') == 'ok' and host and port: print(f'{host}:{port}')
PY
}
date -Is | tee "$OUT_DIR/date_is.txt"; hostname | tee "$OUT_DIR/hostname.txt"
run_capture mpf-version.txt "$MPF_BIN" --version
run_capture mpf-phase-status.txt "$MPF_BIN" phase-status
run_capture mpf-config-validate.txt "$MPF_BIN" config validate
run_capture mpf-proxy-status.txt "$MPF_BIN" proxy status
run_capture mpf-proxy-doctor.txt "$MPF_BIN" proxy doctor
run_capture docker-ps-a.txt docker ps -a
run_capture docker-compose-ps-a.txt docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime ps -a
run_capture ss-ltnp.txt ss -ltnp
run_capture iptables-save.txt iptables-save
run_capture ip6tables-save.txt ip6tables-save
run_capture controlled-backend-target.json "$MPF_BIN" production controlled-backend-target --expected-version "$VERSION" --output json
EXPECTED_TARGET="$(extract_target "$OUT_DIR/controlled-backend-target.json" || true)"
printf '%s\n' "$EXPECTED_TARGET" | tee "$OUT_DIR/expected-backend-target.txt"
run_capture current-controlled-artifact-gate.json "$MPF_BIN" production current-controlled-artifact-gate --expected-version "$VERSION" --expected-backend-target "$EXPECTED_TARGET" --iptables-save-file "$OUT_DIR/iptables-save.txt" --ip6tables-save-file "$OUT_DIR/ip6tables-save.txt" --output json
run_capture restart-autostart-proof.json "$MPF_BIN" production restart-autostart-proof --evidence-dir "$OUT_DIR" --output json
cat >"$OUT_DIR/mutation-flags.json" <<'JSON'
{"mutation_performed":false,"db_mutation_performed":false,"firewall_apply_performed":false,"conntrack_flush_performed":false,"docker_restart_performed":false,"systemd_restart_performed":false}
JSON
find "$OUT_DIR" -type f -maxdepth 1 -print0 | sort -z | xargs -0 sha256sum >"$OUT_DIR/SHA256SUMS.txt"
printf 'Restart/autostart proof after persistence fix evidence: %s\n' "$OUT_DIR"
