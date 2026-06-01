#!/usr/bin/env bash
set -euo pipefail
MPF_BIN=${MPF_BIN:-mpf}; MPF_PYTHON=${MPF_PYTHON:-python3}
EXPECTED_VERSION= ACTIVATION_JSON= ACTIVATION_SHA= POST_JSON= POST_SHA= SOURCE_JSON= SOURCE_SHA= ROLLBACK_JSON= ROLLBACK_SHA= ARTIFACT_JSON= ARTIFACT_SHA= OUT_DIR= OPERATOR= REASON=
while [ "$#" -gt 0 ]; do
 case "$1" in
  --expected-version) EXPECTED_VERSION=$2;; --activation-execution-json) ACTIVATION_JSON=$2;; --activation-execution-json-sha256) ACTIVATION_SHA=$2;;
  --post-activation-evidence-json) POST_JSON=$2;; --post-activation-evidence-json-sha256) POST_SHA=$2;; --source-evidence-json) SOURCE_JSON=$2;; --source-evidence-json-sha256) SOURCE_SHA=$2;;
  --rollback-package-json) ROLLBACK_JSON=$2;; --rollback-package-json-sha256) ROLLBACK_SHA=$2;; --artifact-gate-json) ARTIFACT_JSON=$2;; --artifact-gate-json-sha256) ARTIFACT_SHA=$2;;
  --out-dir) OUT_DIR=$2;; --operator) OPERATOR=$2;; --reason) REASON=$2;; *) echo "unknown argument: $1" >&2; exit 2;; esac; shift 2
done
for value in EXPECTED_VERSION ACTIVATION_JSON ACTIVATION_SHA POST_JSON POST_SHA SOURCE_JSON SOURCE_SHA ROLLBACK_JSON ROLLBACK_SHA ARTIFACT_JSON ARTIFACT_SHA OUT_DIR OPERATOR REASON; do [ -n "${!value}" ] || { echo "missing required argument: $value" >&2; exit 2; }; done
check_sha() { printf '%s  %s\n' "$2" "$1" | sha256sum --check --status -; }
check_sha "$ACTIVATION_JSON" "$ACTIVATION_SHA"; check_sha "$POST_JSON" "$POST_SHA"; check_sha "$SOURCE_JSON" "$SOURCE_SHA"; check_sha "$ROLLBACK_JSON" "$ROLLBACK_SHA"; check_sha "$ARTIFACT_JSON" "$ARTIFACT_SHA"
mkdir -p "$OUT_DIR"
OBS="$OUT_DIR/limited-activation-observation.json"; REVIEW="$OUT_DIR/limited-activation-acceptance-review.json"
"$MPF_BIN" production phase11e-limited-activation-observation-collect --expected-version "$EXPECTED_VERSION" --activation-execution-json "$ACTIVATION_JSON" --activation-execution-json-sha256 "$ACTIVATION_SHA" --post-activation-evidence-json "$POST_JSON" --post-activation-evidence-json-sha256 "$POST_SHA" --source-evidence-json "$SOURCE_JSON" --source-evidence-json-sha256 "$SOURCE_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-observation-only --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-production-traffic-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --i-understand-phase11-not-accepted --out-json "$OBS" --output json
sha256sum "$OBS" | awk '{print $1}' > "$OUT_DIR/limited-activation-observation.sha256"
"$MPF_BIN" production phase11e-limited-activation-acceptance-review --expected-version "$EXPECTED_VERSION" --activation-execution-json "$ACTIVATION_JSON" --activation-execution-json-sha256 "$ACTIVATION_SHA" --post-activation-evidence-json "$POST_JSON" --post-activation-evidence-json-sha256 "$POST_SHA" --observation-json "$OBS" --observation-json-sha256 "$(cat "$OUT_DIR/limited-activation-observation.sha256")" --limited-activation-rollback-package-json "$ROLLBACK_JSON" --limited-activation-rollback-package-json-sha256 "$ROLLBACK_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-review-only --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-no-production-traffic-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --i-understand-phase11-not-accepted --i-understand-limited-acceptance-is-not-phase11-final --out-json "$REVIEW" --output json
sha256sum "$REVIEW" | awk '{print $1}' > "$OUT_DIR/limited-activation-acceptance-review.sha256"
"$MPF_PYTHON" - <<'PY' "$OUT_DIR/manifest.json" "$EXPECTED_VERSION"
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({"component":"phase11e_limited_activation_observation_and_review_helper","expected_version":sys.argv[2],"mutation_performed":False,"outputs":["limited-activation-observation.json","limited-activation-acceptance-review.json"]}, separators=(",",":"))+"\n", encoding="utf-8")
PY
( cd "$OUT_DIR" && sha256sum limited-activation-observation.json limited-activation-observation.sha256 limited-activation-acceptance-review.json limited-activation-acceptance-review.sha256 manifest.json ) > "$OUT_DIR/sha256-manifest.txt"
