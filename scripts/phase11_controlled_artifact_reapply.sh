#!/usr/bin/env bash
set -euo pipefail

MODE="package"
PACKAGE_JSON=""
PACKAGE_SHA256=""
PACKAGE_ID=""
OPERATOR=""
REASON=""
OUT_DIR="${OUT_DIR:-./phase11-controlled-artifact-reapply-evidence}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan"; shift ;;
    --package) MODE="package"; shift ;;
    --verify) MODE="verify"; PACKAGE_JSON="${2:-}"; shift 2 ;;
    --execute) MODE="execute"; shift ;;
    --package-json) PACKAGE_JSON="${2:-}"; shift 2 ;;
    --package-sha256) PACKAGE_SHA256="${2:-}"; shift 2 ;;
    --package-id) PACKAGE_ID="${2:-}"; shift 2 ;;
    --operator) OPERATOR="${2:-}"; shift 2 ;;
    --reason) REASON="${2:-}"; shift 2 ;;
    --out-dir) OUT_DIR="${2:-}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUT_DIR"
case "$MODE" in
  plan)
    mpf production controlled-artifact-reapply-plan --output json | tee "$OUT_DIR/controlled-artifact-reapply-plan.json"
    ;;
  package)
    mpf production controlled-backend-target --output json | tee "$OUT_DIR/controlled-backend-target.json" >/dev/null
    mpf production controlled-artifact-reapply-plan --output json | tee "$OUT_DIR/controlled-artifact-reapply-plan.json" >/dev/null
    mpf production controlled-artifact-reapply-package --output json | tee "$OUT_DIR/controlled-artifact-reapply-package.json"
    sha256sum "$OUT_DIR"/*.json > "$OUT_DIR/manifest.sha256"
    ;;
  verify)
    [[ -n "$PACKAGE_JSON" ]] || { echo "--package-json is required for verify" >&2; exit 2; }
    mpf production controlled-artifact-reapply-verify --package-json "$PACKAGE_JSON" --output json
    ;;
  execute)
    [[ -n "$PACKAGE_JSON" && -n "$PACKAGE_SHA256" && -n "$PACKAGE_ID" && -n "$OPERATOR" && -n "$REASON" ]] || {
      echo "execute requires --package-json, --package-sha256, --package-id, --operator, and --reason" >&2; exit 2;
    }
    mpf production controlled-artifact-reapply-verify --package-json "$PACKAGE_JSON" --output json | tee "$OUT_DIR/pre-execute-verify.json" >/dev/null
    if ! python - "$OUT_DIR/pre-execute-verify.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
sys.exit(0 if p.get('final_decision') == 'CONTROLLED_ARTIFACT_REAPPLY_VERIFY_READY' else 1)
PY
    then
      echo "verify did not pass; refusing execute" >&2
      exit 1
    fi
    mpf production controlled-artifact-reapply-execute --package-json "$PACKAGE_JSON" --package-sha256 "$PACKAGE_SHA256" --package-id "$PACKAGE_ID" --operator "$OPERATOR" --reason "$REASON" --execute --yes --output json
    ;;
  *) echo "unsupported mode: $MODE" >&2; exit 2 ;;
esac
