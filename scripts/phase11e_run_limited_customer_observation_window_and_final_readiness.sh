#!/usr/bin/env bash
set -euo pipefail
# For database.url=postgresql:///mpf local-peer installs, run DB-reading mpf commands as sudo -u mpf, not root.
MPF_BIN=${MPF_BIN:-mpf}; MPF_PYTHON=${MPF_PYTHON:-python3}
EXPECTED_VERSION= OBSERVATION_JSON= OBSERVATION_SHA= REVIEW_JSON= REVIEW_SHA= SOURCE_JSON= SOURCE_SHA= ROLLBACK_JSON= ROLLBACK_SHA= ARTIFACT_JSON= ARTIFACT_SHA= OUT_DIR= OPERATOR= REASON= WINDOW_SECONDS= SAMPLE_INTERVAL= MIN_SAMPLES=
while [ "$#" -gt 0 ]; do
 case "$1" in
  --expected-version) EXPECTED_VERSION=$2;; --observation-json) OBSERVATION_JSON=$2;; --observation-json-sha256) OBSERVATION_SHA=$2;;
  --acceptance-review-json) REVIEW_JSON=$2;; --acceptance-review-json-sha256) REVIEW_SHA=$2;; --source-evidence-json) SOURCE_JSON=$2;; --source-evidence-json-sha256) SOURCE_SHA=$2;;
  --rollback-package-json) ROLLBACK_JSON=$2;; --rollback-package-json-sha256) ROLLBACK_SHA=$2;; --artifact-gate-json) ARTIFACT_JSON=$2;; --artifact-gate-json-sha256) ARTIFACT_SHA=$2;;
  --out-dir) OUT_DIR=$2;; --operator) OPERATOR=$2;; --reason) REASON=$2;; --window-seconds) WINDOW_SECONDS=$2;; --sample-interval-seconds) SAMPLE_INTERVAL=$2;; --min-samples) MIN_SAMPLES=$2;;
  *) echo "unknown argument: $1" >&2; exit 2;; esac; shift 2
done
for value in EXPECTED_VERSION OBSERVATION_JSON OBSERVATION_SHA REVIEW_JSON REVIEW_SHA SOURCE_JSON SOURCE_SHA ROLLBACK_JSON ROLLBACK_SHA ARTIFACT_JSON ARTIFACT_SHA OUT_DIR OPERATOR REASON WINDOW_SECONDS SAMPLE_INTERVAL MIN_SAMPLES; do [ -n "${!value}" ] || { echo "missing required argument: $value" >&2; exit 2; }; done
check_sha() { [ -f "$1" ] && printf '%s  %s\n' "$2" "$1" | sha256sum --check --status -; }
check_sha "$OBSERVATION_JSON" "$OBSERVATION_SHA"; check_sha "$REVIEW_JSON" "$REVIEW_SHA"; check_sha "$SOURCE_JSON" "$SOURCE_SHA"; check_sha "$ROLLBACK_JSON" "$ROLLBACK_SHA"; check_sha "$ARTIFACT_JSON" "$ARTIFACT_SHA"
mkdir -p "$OUT_DIR"
WINDOW_START=$(date -u +%Y-%m-%dT%H:%M:%SZ); WINDOW_END=$(date -u -d "+$WINDOW_SECONDS seconds" +%Y-%m-%dT%H:%M:%SZ)
WINDOW_OUT="$OUT_DIR/limited-customer-observation-window.json"; WINDOW_OUT_SHA="$OUT_DIR/limited-customer-observation-window.sha256"
FINAL_OUT="$OUT_DIR/phase11-final-acceptance-readiness-planning.json"; FINAL_OUT_SHA="$OUT_DIR/phase11-final-acceptance-readiness-planning.sha256"
"$MPF_BIN" production phase11e-limited-customer-observation-window --expected-version "$EXPECTED_VERSION" --observation-json "$OBSERVATION_JSON" --observation-json-sha256 "$OBSERVATION_SHA" --acceptance-review-json "$REVIEW_JSON" --acceptance-review-json-sha256 "$REVIEW_SHA" --source-evidence-json "$SOURCE_JSON" --source-evidence-json-sha256 "$SOURCE_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --window-start "$WINDOW_START" --window-end "$WINDOW_END" --sample-interval-seconds "$SAMPLE_INTERVAL" --min-samples "$MIN_SAMPLES" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-observation-window-only --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-production-traffic-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --i-understand-phase11-not-accepted --out-json "$WINDOW_OUT" --output json
"$MPF_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["final_decision"] == "PHASE11E_LIMITED_CUSTOMER_OBSERVATION_WINDOW_READY"' "$WINDOW_OUT"
sha256sum "$WINDOW_OUT" | awk '{print $1}' > "$WINDOW_OUT_SHA"
"$MPF_BIN" production phase11-final-acceptance-readiness-planning --expected-version "$EXPECTED_VERSION" --observation-window-json "$WINDOW_OUT" --observation-window-json-sha256 "$(cat "$WINDOW_OUT_SHA")" --acceptance-review-json "$REVIEW_JSON" --acceptance-review-json-sha256 "$REVIEW_SHA" --rollback-package-json "$ROLLBACK_JSON" --rollback-package-json-sha256 "$ROLLBACK_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-readiness-planning-only --i-understand-no-current-state-change --i-understand-no-production-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --i-understand-no-ui-telegram --i-understand-phase11-not-accepted --out-json "$FINAL_OUT" --output json
"$MPF_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["final_decision"] == "PHASE11_FINAL_ACCEPTANCE_READINESS_PLANNING_READY"' "$FINAL_OUT"
sha256sum "$FINAL_OUT" | awk '{print $1}' > "$FINAL_OUT_SHA"
"$MPF_PYTHON" - <<'PY' "$OUT_DIR/manifest.json" "$EXPECTED_VERSION" "$OBSERVATION_JSON" "$REVIEW_JSON" "$SOURCE_JSON" "$ROLLBACK_JSON" "$ARTIFACT_JSON" "$WINDOW_OUT" "$FINAL_OUT"
import json,sys
from pathlib import Path
keys=("observation_json","acceptance_review_json","source_evidence_json","rollback_package_json","artifact_gate_json","observation_window_json","final_readiness_planning_json")
paths=dict(zip(keys,sys.argv[3:]))
paths.update({"observation_window_sha256":str(Path(paths["observation_window_json"]).with_suffix(".sha256")),"final_readiness_planning_sha256":str(Path(paths["final_readiness_planning_json"]).with_suffix(".sha256")),"manifest_json":sys.argv[1],"sha256_manifest":str(Path(sys.argv[1]).with_name("sha256-manifest.txt"))})
Path(sys.argv[1]).write_text(json.dumps({"component":"phase11e_limited_customer_observation_window_and_final_readiness_helper","expected_version":sys.argv[2],"mutation_performed":False,"paths":paths}, separators=(",",":"))+"\n", encoding="utf-8")
PY
( cd "$OUT_DIR" && sha256sum limited-customer-observation-window.json limited-customer-observation-window.sha256 phase11-final-acceptance-readiness-planning.json phase11-final-acceptance-readiness-planning.sha256 manifest.json ) > "$OUT_DIR/sha256-manifest.txt"
