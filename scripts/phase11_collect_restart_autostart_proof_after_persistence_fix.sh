#!/usr/bin/env bash
set -euo pipefail
VERSION="0.1.299"
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
EXPECTED_BACKEND_TARGET="$(extract_target "$OUT_DIR/controlled-backend-target.json" 2>/dev/null || true)"
if [ -z "$EXPECTED_BACKEND_TARGET" ]; then echo expected_backend_target_required >"$OUT_DIR/expected-backend-target.txt"; exit 2; fi
printf '%s\n' "$EXPECTED_BACKEND_TARGET" >"$OUT_DIR/expected-backend-target.txt"
run_capture current-controlled-artifact-gate.json "$MPF_BIN" production current-controlled-artifact-gate --expected-version "$VERSION" --expected-backend-target "$EXPECTED_BACKEND_TARGET" --iptables-save-file "$OUT_DIR/iptables-save.txt" --ip6tables-save-file "$OUT_DIR/ip6tables-save.txt" --output json
run_capture controlled-artifact-persistence-plan.json "$MPF_BIN" production controlled-artifact-persistence-plan --expected-version "$VERSION" --output json
run_capture restart-autostart-persistence-diagnosis.json "$MPF_BIN" production restart-autostart-persistence-diagnosis --expected-version "$VERSION" --output json
run_capture restart-autostart-persistence-fix-plan.json "$MPF_BIN" production restart-autostart-persistence-fix-plan --expected-version "$VERSION" --output json
run_capture restart-autostart-proof.json "$MPF_BIN" production restart-autostart-proof --output json
run_capture phase11-operational-completion-gap-inventory.json "$MPF_BIN" production phase11-operational-completion-gap-inventory --output json
cat >"$OUT_DIR/mutation-flags.json" <<'JSON'
{"mutation_performed":false,"db_mutation_performed":false,"firewall_apply_performed":false,"conntrack_flush_performed":false,"docker_restart_performed":false,"systemd_restart_performed":false}
JSON
python - <<PY | tee "$OUT_DIR/manifest.json"
import json
print(json.dumps({"component":"phase11_restart_autostart_proof_after_persistence_fix_collection","repository_version":"$VERSION","mutation_performed":False,"evidence_dir":"$OUT_DIR","expected_backend_target":"$EXPECTED_BACKEND_TARGET"}, indent=2))
PY
