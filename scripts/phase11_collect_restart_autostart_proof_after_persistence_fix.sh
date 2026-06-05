#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-/tmp/phase11-restart-autostart-proof-after-persistence-fix-$(date +%Y%m%dT%H%M%S%z)}"
MPF_BIN="${MPF_BIN:-mpf}"
mkdir -p "$OUT_DIR"

run_capture() {
  local name="$1"; shift
  echo "===== $name ====="
  "$@" >"$OUT_DIR/$name" 2>&1 || true
  cat "$OUT_DIR/$name"
}

date -Is | tee "$OUT_DIR/date_is.txt"
hostname | tee "$OUT_DIR/hostname.txt"
run_capture mpf_version.txt "$MPF_BIN" --version
run_capture mpf_phase_status.txt "$MPF_BIN" phase-status
run_capture mpf_config_validate.txt "$MPF_BIN" config validate
run_capture mpf_proxy_status.txt "$MPF_BIN" proxy status
run_capture mpf_proxy_doctor.txt "$MPF_BIN" proxy doctor
run_capture docker_ps_a.txt docker ps -a
run_capture docker_compose_ps_a.txt docker compose -p mpf-proxy -f compose/mpf-proxy.compose.yaml --profile phase4-runtime ps -a
run_capture ss_ltnp.txt ss -ltnp
run_capture iptables_save.txt iptables-save
run_capture ip6tables_save.txt ip6tables-save
run_capture current_controlled_artifact_gate.json "$MPF_BIN" production current-controlled-artifact-gate --output json
run_capture controlled_artifact_persistence_plan.json "$MPF_BIN" production controlled-artifact-persistence-plan --output json
run_capture restart_autostart_persistence_diagnosis.json "$MPF_BIN" production restart-autostart-persistence-diagnosis --output json
run_capture restart_autostart_persistence_fix_plan.json "$MPF_BIN" production restart-autostart-persistence-fix-plan --output json
run_capture restart_autostart_proof.json "$MPF_BIN" production restart-autostart-proof --output json
run_capture phase11_operational_completion_gap_inventory.json "$MPF_BIN" production phase11-operational-completion-gap-inventory --output json

python - <<PY | tee "$OUT_DIR/manifest.json"
import json
print(json.dumps({"component":"phase11_restart_autostart_proof_after_persistence_fix_collection","mutation_performed":False,"evidence_dir":"$OUT_DIR"}, indent=2))
PY
