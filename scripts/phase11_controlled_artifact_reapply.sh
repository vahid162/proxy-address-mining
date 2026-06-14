#!/usr/bin/env bash
set -euo pipefail

MODE="package"
PACKAGE_JSON=""
PACKAGE_SHA256=""
PACKAGE_ID=""
OPERATOR=""
REASON=""
PACKET_PATH_EVIDENCE_DIR=""
OUT_DIR="${OUT_DIR:-./phase11-controlled-artifact-reapply-evidence}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan"; shift ;;
    --package) MODE="package"; shift ;;
    --readiness) MODE="readiness"; shift ;;
    --live-ready-package) MODE="live-ready-package"; shift ;;
    --verify) MODE="verify"; PACKAGE_JSON="${2:-}"; shift 2 ;;
    --execute) MODE="execute"; shift ;;
    --package-json) PACKAGE_JSON="${2:-}"; shift 2 ;;
    --package-sha256) PACKAGE_SHA256="${2:-}"; shift 2 ;;
    --package-id) PACKAGE_ID="${2:-}"; shift 2 ;;
    --operator) OPERATOR="${2:-}"; shift 2 ;;
    --reason) REASON="${2:-}"; shift 2 ;;
    --out-dir) OUT_DIR="${2:-}"; shift 2 ;;
    --packet-path-evidence-dir) PACKET_PATH_EVIDENCE_DIR="${2:-}"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUT_DIR"
case "$MODE" in
  plan)
    mpf production controlled-artifact-reapply-plan --output json | tee "$OUT_DIR/controlled-artifact-reapply-plan.json"
    ;;
  readiness)
    mpf production controlled-artifact-reapply-readiness --output json | tee "$OUT_DIR/controlled-artifact-reapply-readiness.json"
    sha256sum "$OUT_DIR"/*.json > "$OUT_DIR/manifest.sha256"
    ;;
  live-ready-package)
    [[ -n "$PACKET_PATH_EVIDENCE_DIR" ]] || { echo "--packet-path-evidence-dir is required for live-ready-package" >&2; exit 2; }
    mpf production live-ready-controlled-artifact-reapply-package --packet-path-evidence-dir "$PACKET_PATH_EVIDENCE_DIR" --output-dir "$OUT_DIR" --output json | tee "$OUT_DIR/live-ready-controlled-artifact-reapply-package.json"
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
    [[ "${MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY:-}" == "allow" && "${MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE:-}" == "allow" ]] || { echo "required environment gates are missing" >&2; exit 2; }
    actual_sha="$(sha256sum "$PACKAGE_JSON" | awk '{print $1}')"
    [[ "$actual_sha" == "$PACKAGE_SHA256" ]] || { echo "package sha256 mismatch" >&2; exit 2; }
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
    echo "About to run controlled mutation command:" >&2
    EXEC_CMD="controlled-artifact-reapply-${MODE}"
    echo "mpf production $EXEC_CMD --package-json $PACKAGE_JSON --package-sha256 $PACKAGE_SHA256 --package-id $PACKAGE_ID --operator $OPERATOR --reason <redacted> --execute --yes --output json" >&2
    mpf production "$EXEC_CMD" --package-json "$PACKAGE_JSON" --package-sha256 "$PACKAGE_SHA256" --package-id "$PACKAGE_ID" --operator "$OPERATOR" --reason "$REASON" --execute --yes --output json
    ;;
  *) echo "unsupported mode: $MODE" >&2; exit 2 ;;
esac
