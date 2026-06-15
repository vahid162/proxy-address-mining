#!/usr/bin/env bash
set -euo pipefail
VERSION="0.1.275"
OUT_DIR="${1:-/tmp/phase11-post-cleanup-restart-persistence-evidence-$(date -u +%Y%m%dT%H%M%SZ)}"
MPF_BIN="${MPF_BIN:-mpf}"
mkdir -p "$OUT_DIR"
run_capture() { local name="$1"; shift; "$@" >"$OUT_DIR/$name" 2>&1 || true; }
extract_target() { python - "$1" <<'PY'
import json, sys
from pathlib import Path
text='\n'.join(line for line in Path(sys.argv[1]).read_text().splitlines() if not line.startswith('#'))
data=json.loads(text); host=data.get('resolved_ipv4') or data.get('target_host'); port=data.get('target_port')
if data.get('status') == 'ok' and host and port: print(f'{host}:{port}')
PY
}
run_capture mpf-version.txt "$MPF_BIN" --version
run_capture phase-status.txt "$MPF_BIN" phase-status
run_capture mpf-doctor.txt "$MPF_BIN" doctor
run_capture proxy-doctor.txt "$MPF_BIN" proxy doctor
run_capture db-status.txt "$MPF_BIN" db status
run_capture docker-ps.txt docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
run_capture docker-compose-ps.txt docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime ps -a
run_capture ss-listeners.txt ss -ltnp
run_capture iptables-save.txt iptables-save
run_capture ip6tables-save.txt ip6tables-save
run_capture controlled-backend-target.json "$MPF_BIN" production controlled-backend-target --expected-version "$VERSION" --output json
EXPECTED_BACKEND_TARGET="$(extract_target "$OUT_DIR/controlled-backend-target.json" 2>/dev/null || true)"
if [ -z "$EXPECTED_BACKEND_TARGET" ]; then echo expected_backend_target_required >"$OUT_DIR/expected-backend-target.txt"; exit 2; fi
printf '%s\n' "$EXPECTED_BACKEND_TARGET" >"$OUT_DIR/expected-backend-target.txt"
run_capture current-controlled-artifact-gate.json "$MPF_BIN" production current-controlled-artifact-gate --expected-version "$VERSION" --expected-backend-target "$EXPECTED_BACKEND_TARGET" --iptables-save-file "$OUT_DIR/iptables-save.txt" --ip6tables-save-file "$OUT_DIR/ip6tables-save.txt" --output json
run_capture controlled-artifact-persistence-plan.json "$MPF_BIN" production controlled-artifact-persistence-plan --expected-version "$VERSION" --output json
run_capture restart-autostart-persistence-diagnosis.json "$MPF_BIN" production restart-autostart-persistence-diagnosis --expected-version "$VERSION" --output json
run_capture restart-autostart-proof.json "$MPF_BIN" production restart-autostart-proof --output json
run_capture phase11-operational-completion-gap-inventory.json "$MPF_BIN" production phase11-operational-completion-gap-inventory --output json
run_capture summary.json "$MPF_BIN" production phase11-post-cleanup-restart-persistence-evidence --expected-version "$VERSION" --output json
cat >"$OUT_DIR/mutation-flags.json" <<'JSON'
{"mutation_performed":false,"db_mutation_performed":false,"firewall_apply_performed":false,"conntrack_flush_performed":false,"docker_restart_performed":false,"systemd_restart_performed":false,"customer_onboarding_performed":false,"abuse_runner_executed":false,"worker_enforcement_performed":false,"phase12_started":false}
JSON
python - <<PY >"$OUT_DIR/manifest.json"
import json, pathlib
root=pathlib.Path('$OUT_DIR')
summary=json.loads((root/'summary.json').read_text() or '{}') if (root/'summary.json').exists() else {}
print(json.dumps({"component":"phase11_post_cleanup_restart_persistence_evidence_bundle","repository_version":"$VERSION","evidence_dir":"$OUT_DIR","expected_backend_target":"$EXPECTED_BACKEND_TARGET","files":sorted(p.name for p in root.iterdir()),"mutation_performed":False,"next_required_step":summary.get('next_required_step','collect_real_restart_autostart_evidence_after_operator_restart_or_reboot')}, indent=2))
PY
cat "$OUT_DIR/summary.json"
printf '\nEvidence directory: %s\n' "$OUT_DIR"
