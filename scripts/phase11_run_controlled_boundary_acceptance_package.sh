#!/usr/bin/env bash
set -euo pipefail
# For database.url=postgresql:///mpf local-peer installs, run DB-reading mpf commands as sudo -u mpf, not root.
MPF_BIN=${MPF_BIN:-mpf}; MPF_PYTHON=${MPF_PYTHON:-python3}
EXPECTED_VERSION= DECISION_JSON= DECISION_SHA= ARTIFACT_JSON= ARTIFACT_SHA= SOURCE_JSON= SOURCE_SHA= ABUSE_JSON= ABUSE_SHA= RESTART_JSON= RESTART_SHA= OUT_DIR= OPERATOR= REASON=
while [ "$#" -gt 0 ]; do
 case "$1" in
  --expected-version) EXPECTED_VERSION=$2;; --limited-acceptance-decision-json) DECISION_JSON=$2;; --limited-acceptance-decision-json-sha256) DECISION_SHA=$2;;
  --artifact-gate-json) ARTIFACT_JSON=$2;; --artifact-gate-json-sha256) ARTIFACT_SHA=$2;; --source-evidence-json) SOURCE_JSON=$2;; --source-evidence-json-sha256) SOURCE_SHA=$2;;
  --abuse-readiness-json) ABUSE_JSON=$2;; --abuse-readiness-json-sha256) ABUSE_SHA=$2;; --restart-readiness-json) RESTART_JSON=$2;; --restart-readiness-json-sha256) RESTART_SHA=$2;;
  --out-dir) OUT_DIR=$2;; --operator) OPERATOR=$2;; --reason) REASON=$2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; shift 2
done
for value in EXPECTED_VERSION DECISION_JSON DECISION_SHA ARTIFACT_JSON ARTIFACT_SHA SOURCE_JSON SOURCE_SHA ABUSE_JSON ABUSE_SHA RESTART_JSON RESTART_SHA OUT_DIR OPERATOR REASON; do [ -n "${!value}" ] || { echo "missing required argument: $value" >&2; exit 2; }; done
check_sha() { [ -f "$1" ] && printf '%s  %s\n' "$2" "$1" | sha256sum --check --status -; }
check_sha "$DECISION_JSON" "$DECISION_SHA"; check_sha "$ARTIFACT_JSON" "$ARTIFACT_SHA"; check_sha "$SOURCE_JSON" "$SOURCE_SHA"; check_sha "$ABUSE_JSON" "$ABUSE_SHA"; check_sha "$RESTART_JSON" "$RESTART_SHA"
mkdir -p "$OUT_DIR"
OUT_JSON="$OUT_DIR/phase11-controlled-boundary-acceptance-package.json"; OUT_SHA="$OUT_DIR/phase11-controlled-boundary-acceptance-package.sha256"
"$MPF_BIN" production phase11-controlled-boundary-acceptance-package --expected-version "$EXPECTED_VERSION" --limited-acceptance-decision-json "$DECISION_JSON" --limited-acceptance-decision-json-sha256 "$DECISION_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --source-evidence-json "$SOURCE_JSON" --source-evidence-json-sha256 "$SOURCE_SHA" --abuse-readiness-json "$ABUSE_JSON" --abuse-readiness-json-sha256 "$ABUSE_SHA" --restart-readiness-json "$RESTART_JSON" --restart-readiness-json-sha256 "$RESTART_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-controlled-boundary-package-only --i-understand-no-current-state-change --i-understand-no-phase11-final-acceptance --i-understand-no-production-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation-enable --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-ui-telegram --out-json "$OUT_JSON" --output json
"$MPF_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["final_decision"] == "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_PACKAGE_READY"' "$OUT_JSON"
sha256sum "$OUT_JSON" | awk '{print $1}' > "$OUT_SHA"
"$MPF_PYTHON" - <<'PY' "$OUT_DIR/manifest.json" "$EXPECTED_VERSION" "$DECISION_JSON" "$DECISION_SHA" "$ARTIFACT_JSON" "$ARTIFACT_SHA" "$SOURCE_JSON" "$SOURCE_SHA" "$ABUSE_JSON" "$ABUSE_SHA" "$RESTART_JSON" "$RESTART_SHA" "$OUT_JSON" "$OUT_SHA"
import json,sys
from pathlib import Path
keys=("limited_acceptance_decision_json","limited_acceptance_decision_json_sha256","artifact_gate_json","artifact_gate_json_sha256","source_evidence_json","source_evidence_json_sha256","abuse_readiness_json","abuse_readiness_json_sha256","restart_readiness_json","restart_readiness_json_sha256","controlled_boundary_acceptance_package_json","controlled_boundary_acceptance_package_json_sha256")
paths=dict(zip(keys,sys.argv[3:])); paths.update({"manifest_json":sys.argv[1],"sha256_manifest":str(Path(sys.argv[1]).with_name("sha256-manifest.txt"))})
Path(sys.argv[1]).write_text(json.dumps({"component":"phase11_controlled_boundary_acceptance_package_helper","expected_version":sys.argv[2],"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"runtime_change_performed":False,"paths":paths}, separators=(",",":"))+"\n", encoding="utf-8")
PY
( cd "$OUT_DIR" && sha256sum phase11-controlled-boundary-acceptance-package.json phase11-controlled-boundary-acceptance-package.sha256 manifest.json ) > "$OUT_DIR/sha256-manifest.txt"
