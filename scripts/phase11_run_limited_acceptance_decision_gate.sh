#!/usr/bin/env bash
set -euo pipefail
# For database.url=postgresql:///mpf local-peer installs, run DB-reading mpf commands as sudo -u mpf, not root.
MPF_BIN=${MPF_BIN:-mpf}; MPF_PYTHON=${MPF_PYTHON:-python3}
EXPECTED_VERSION= OBSERVATION_WINDOW_JSON= OBSERVATION_WINDOW_SHA= FINAL_READINESS_JSON= FINAL_READINESS_SHA= ARTIFACT_JSON= ARTIFACT_SHA= OUT_DIR= OPERATOR= REASON=
while [ "$#" -gt 0 ]; do
 case "$1" in
  --expected-version) EXPECTED_VERSION=$2;; --observation-window-json) OBSERVATION_WINDOW_JSON=$2;; --observation-window-json-sha256) OBSERVATION_WINDOW_SHA=$2;;
  --final-readiness-planning-json) FINAL_READINESS_JSON=$2;; --final-readiness-planning-json-sha256) FINAL_READINESS_SHA=$2;; --artifact-gate-json) ARTIFACT_JSON=$2;; --artifact-gate-json-sha256) ARTIFACT_SHA=$2;;
  --out-dir) OUT_DIR=$2;; --operator) OPERATOR=$2;; --reason) REASON=$2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; shift 2
done
for value in EXPECTED_VERSION OBSERVATION_WINDOW_JSON OBSERVATION_WINDOW_SHA FINAL_READINESS_JSON FINAL_READINESS_SHA ARTIFACT_JSON ARTIFACT_SHA OUT_DIR OPERATOR REASON; do [ -n "${!value}" ] || { echo "missing required argument: $value" >&2; exit 2; }; done
check_sha() { [ -f "$1" ] && printf '%s  %s\n' "$2" "$1" | sha256sum --check --status -; }
check_sha "$OBSERVATION_WINDOW_JSON" "$OBSERVATION_WINDOW_SHA"; check_sha "$FINAL_READINESS_JSON" "$FINAL_READINESS_SHA"; check_sha "$ARTIFACT_JSON" "$ARTIFACT_SHA"
mkdir -p "$OUT_DIR"
OUT_JSON="$OUT_DIR/phase11-limited-acceptance-decision-gate.json"; OUT_SHA="$OUT_DIR/phase11-limited-acceptance-decision-gate.sha256"
"$MPF_BIN" production phase11-limited-acceptance-decision-gate --expected-version "$EXPECTED_VERSION" --observation-window-json "$OBSERVATION_WINDOW_JSON" --observation-window-json-sha256 "$OBSERVATION_WINDOW_SHA" --final-readiness-planning-json "$FINAL_READINESS_JSON" --final-readiness-planning-json-sha256 "$FINAL_READINESS_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-limited-acceptance-decision-only --i-understand-no-current-state-change --i-understand-no-phase11-final-acceptance --i-understand-no-production-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-ui-telegram --out-json "$OUT_JSON" --output json
"$MPF_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["final_decision"] == "PHASE11_LIMITED_ACCEPTANCE_DECISION_GATE_READY"' "$OUT_JSON"
sha256sum "$OUT_JSON" | awk '{print $1}' > "$OUT_SHA"
"$MPF_PYTHON" - <<'PY' "$OUT_DIR/manifest.json" "$EXPECTED_VERSION" "$OBSERVATION_WINDOW_JSON" "$OBSERVATION_WINDOW_SHA" "$FINAL_READINESS_JSON" "$FINAL_READINESS_SHA" "$ARTIFACT_JSON" "$ARTIFACT_SHA" "$OUT_JSON" "$OUT_SHA"
import json,sys
from pathlib import Path
keys=("observation_window_json","observation_window_json_sha256","final_readiness_planning_json","final_readiness_planning_json_sha256","artifact_gate_json","artifact_gate_json_sha256","decision_gate_json","decision_gate_json_sha256")
paths=dict(zip(keys,sys.argv[3:]))
paths.update({"manifest_json":sys.argv[1],"sha256_manifest":str(Path(sys.argv[1]).with_name("sha256-manifest.txt"))})
Path(sys.argv[1]).write_text(json.dumps({"component":"phase11_limited_acceptance_decision_gate_helper","expected_version":sys.argv[2],"mutation_performed":False,"paths":paths}, separators=(",",":"))+"\n", encoding="utf-8")
PY
( cd "$OUT_DIR" && sha256sum phase11-limited-acceptance-decision-gate.json phase11-limited-acceptance-decision-gate.sha256 manifest.json ) > "$OUT_DIR/sha256-manifest.txt"
