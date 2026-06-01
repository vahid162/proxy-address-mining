#!/usr/bin/env bash
set -euo pipefail
# Read-only helper. For local-peer database.url=postgresql:///mpf, run DB-reading mpf commands as sudo -u mpf, not root.
MPF_BIN=${MPF_BIN:-mpf}; MPF_PYTHON=${MPF_PYTHON:-python}
EXPECTED_VERSION=; PACKAGE_JSON=; PACKAGE_SHA=; OUT_DIR=; OPERATOR=; REASON=
while [ $# -gt 0 ]; do
  case "$1" in
    --expected-version) EXPECTED_VERSION=$2; shift 2;;
    --controlled-boundary-package-json) PACKAGE_JSON=$2; shift 2;;
    --controlled-boundary-package-json-sha256) PACKAGE_SHA=$2; shift 2;;
    --out-dir) OUT_DIR=$2; shift 2;;
    --operator) OPERATOR=$2; shift 2;;
    --reason) REASON=$2; shift 2;;
    *) echo "unknown argument: $1" >&2; exit 2;;
  esac
done
[ -n "$EXPECTED_VERSION" ] && [ -n "$PACKAGE_JSON" ] && [ -n "$PACKAGE_SHA" ] && [ -n "$OUT_DIR" ] && [ -n "$OPERATOR" ] && [ -n "$REASON" ] || { echo "missing required argument" >&2; exit 2; }
check_sha() { [ -f "$1" ] && printf '%s  %s\n' "$2" "$1" | sha256sum --check --status -; }
check_sha "$PACKAGE_JSON" "$PACKAGE_SHA"
mkdir -p "$OUT_DIR"
DECISION_JSON="$OUT_DIR/phase11-controlled-boundary-acceptance-decision.json"; DECISION_SHA="$OUT_DIR/phase11-controlled-boundary-acceptance-decision.sha256"
READINESS_JSON="$OUT_DIR/phase11-final-acceptance-pr-readiness.json"; READINESS_SHA="$OUT_DIR/phase11-final-acceptance-pr-readiness.sha256"
"$MPF_BIN" production phase11-controlled-boundary-acceptance-decision --expected-version "$EXPECTED_VERSION" --controlled-boundary-package-json "$PACKAGE_JSON" --controlled-boundary-package-json-sha256 "$PACKAGE_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-controlled-boundary-decision-only --i-understand-no-current-state-change --i-understand-no-phase11-final-acceptance --i-understand-no-production-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation-enable --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-ui-telegram --out-json "$DECISION_JSON" --output json
"$MPF_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["final_decision"] == "PHASE11_CONTROLLED_BOUNDARY_ACCEPTANCE_DECISION_READY"' "$DECISION_JSON"
sha256sum "$DECISION_JSON" | awk '{print $1}' > "$DECISION_SHA"
"$MPF_BIN" production phase11-final-acceptance-pr-readiness --expected-version "$EXPECTED_VERSION" --controlled-boundary-decision-json "$DECISION_JSON" --controlled-boundary-decision-json-sha256 "$(cat "$DECISION_SHA")" --controlled-boundary-package-json "$PACKAGE_JSON" --controlled-boundary-package-json-sha256 "$PACKAGE_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-final-acceptance-readiness-only --i-understand-no-current-state-change --i-understand-phase11-not-accepted-by-this-command --i-understand-no-production-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-ui-telegram --out-json "$READINESS_JSON" --output json
"$MPF_PYTHON" -c 'import json,sys; assert json.load(open(sys.argv[1], encoding="utf-8"))["final_decision"] == "PHASE11_FINAL_ACCEPTANCE_PR_READINESS_READY"' "$READINESS_JSON"
sha256sum "$READINESS_JSON" | awk '{print $1}' > "$READINESS_SHA"
"$MPF_PYTHON" - <<'PY' "$OUT_DIR/manifest.json" "$EXPECTED_VERSION" "$PACKAGE_JSON" "$PACKAGE_SHA" "$DECISION_JSON" "$DECISION_SHA" "$READINESS_JSON" "$READINESS_SHA"
import json,sys
from pathlib import Path
keys=("controlled_boundary_package_json","controlled_boundary_package_json_sha256","controlled_boundary_acceptance_decision_json","controlled_boundary_acceptance_decision_json_sha256","phase11_final_acceptance_pr_readiness_json","phase11_final_acceptance_pr_readiness_json_sha256")
paths=dict(zip(keys,sys.argv[3:])); paths.update({"manifest_json":sys.argv[1],"sha256_manifest":str(Path(sys.argv[1]).with_name("sha256-manifest.txt"))})
Path(sys.argv[1]).write_text(json.dumps({"component":"phase11_controlled_boundary_decision_and_final_readiness_helper","expected_version":sys.argv[2],"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"runtime_change_performed":False,"paths":paths}, separators=(",",":"))+"\n", encoding="utf-8")
PY
( cd "$OUT_DIR" && sha256sum phase11-controlled-boundary-acceptance-decision.json phase11-controlled-boundary-acceptance-decision.sha256 phase11-final-acceptance-pr-readiness.json phase11-final-acceptance-pr-readiness.sha256 manifest.json ) > "$OUT_DIR/sha256-manifest.txt"
