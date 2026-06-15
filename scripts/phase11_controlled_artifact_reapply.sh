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
OUT_DIR_EXPLICIT="false"
YES="false"

usage_error() {
  echo "$1" >&2
  exit 2
}

write_manifest() {
  local dir="$1"
  find "$dir" -maxdepth 1 -type f -name '*.json' -print0 | sort -z | xargs -0 sha256sum > "$dir/manifest.sha256"
}

validate_json_decision() {
  local report_path="$1"
  local expected_decision="$2"
  python - "$report_path" "$expected_decision" <<'PY'
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
expected = sys.argv[2]
try:
    report = json.loads(report_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"malformed JSON in {report_path}: {exc}", file=sys.stderr)
    sys.exit(1)
final_decision = report.get("final_decision")
if not final_decision:
    print(f"missing final_decision in {report_path}", file=sys.stderr)
    sys.exit(1)
blockers = report.get("blockers", [])
def diag():
    fields = {
        "final_decision": final_decision,
        "blockers": blockers,
        "error": report.get("error"),
        "error_stage": report.get("error_stage"),
        "backup": report.get("backup"),
        "raw_snapshot_drift_warnings": report.get("raw_snapshot_drift_warnings"),
    }
    print(f"decision diagnostics for {report_path}: " + json.dumps(fields, sort_keys=True), file=sys.stderr)
if blockers:
    diag()
    sys.exit(1)
if final_decision != expected:
    diag()
    sys.exit(1)
PY
}

require_execute_common_args() {
  [[ -n "$PACKAGE_JSON" && -n "$PACKAGE_SHA256" && -n "$PACKAGE_ID" && -n "$OPERATOR" && -n "$REASON" ]] || {
    usage_error "$MODE requires --package-json, --package-sha256, --package-id, --operator, and --reason"
  }
  [[ "$OUT_DIR_EXPLICIT" == "true" && -n "$OUT_DIR" ]] || usage_error "$MODE requires explicit --out-dir"
}

prepare_execute_out_dir() {
  umask 077
  mkdir -p "$OUT_DIR"
}

validate_package_sha() {
  local actual_sha
  actual_sha="$(sha256sum "$PACKAGE_JSON" | awk '{print $1}')"
  [[ "$actual_sha" == "$PACKAGE_SHA256" ]] || usage_error "package sha256 mismatch"
}

run_execution_gate_preflight() {
  local report="$OUT_DIR/controlled-artifact-reapply-execution-gate-preflight.json"
  mpf production controlled-artifact-reapply-execution-gate-preflight \
    --package-json "$PACKAGE_JSON" \
    --package-sha256 "$PACKAGE_SHA256" \
    --package-id "$PACKAGE_ID" \
    --operator "$OPERATOR" \
    --reason "$REASON" \
    --output json > "$report"
  validate_json_decision "$report" "READY_CONTROLLED_ARTIFACT_REAPPLY_EXECUTION_GATE_PREFLIGHT"
  write_manifest "$OUT_DIR"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan"; shift ;;
    --package) MODE="package"; shift ;;
    --readiness) MODE="readiness"; shift ;;
    --live-ready-package) MODE="live-ready-package"; shift ;;
    --verify) MODE="verify"; PACKAGE_JSON="${2:-}"; shift 2 ;;
    --execute-preflight) MODE="execute-preflight"; shift ;;
    --rollback-test) MODE="rollback-test"; shift ;;
    --rollback-apply) MODE="rollback-apply"; shift ;;
    --execute) MODE="execute"; shift ;;
    --yes) YES="true"; shift ;;
    --package-json) PACKAGE_JSON="${2:-}"; shift 2 ;;
    --package-sha256) PACKAGE_SHA256="${2:-}"; shift 2 ;;
    --package-id) PACKAGE_ID="${2:-}"; shift 2 ;;
    --operator) OPERATOR="${2:-}"; shift 2 ;;
    --reason) REASON="${2:-}"; shift 2 ;;
    --out-dir) OUT_DIR="${2:-}"; OUT_DIR_EXPLICIT="true"; shift 2 ;;
    --packet-path-evidence-dir) PACKET_PATH_EVIDENCE_DIR="${2:-}"; shift 2 ;;
    *) usage_error "unknown argument: $1" ;;
  esac
done

case "$MODE" in
  plan)
    mkdir -p "$OUT_DIR"
    mpf production controlled-artifact-reapply-plan --output json | tee "$OUT_DIR/controlled-artifact-reapply-plan.json"
    ;;
  readiness)
    mkdir -p "$OUT_DIR"
    mpf production controlled-artifact-reapply-readiness --output json | tee "$OUT_DIR/controlled-artifact-reapply-readiness.json"
    sha256sum "$OUT_DIR"/*.json > "$OUT_DIR/manifest.sha256"
    ;;
  live-ready-package)
    mkdir -p "$OUT_DIR"
    [[ -n "$PACKET_PATH_EVIDENCE_DIR" ]] || usage_error "--packet-path-evidence-dir is required for live-ready-package"
    mpf production live-ready-controlled-artifact-reapply-package --packet-path-evidence-dir "$PACKET_PATH_EVIDENCE_DIR" --output-dir "$OUT_DIR" --output json | tee "$OUT_DIR/live-ready-controlled-artifact-reapply-package.json"
    ;;
  package)
    mkdir -p "$OUT_DIR"
    mpf production controlled-backend-target --output json | tee "$OUT_DIR/controlled-backend-target.json" >/dev/null
    mpf production controlled-artifact-reapply-plan --output json | tee "$OUT_DIR/controlled-artifact-reapply-plan.json" >/dev/null
    mpf production controlled-artifact-reapply-package --output json | tee "$OUT_DIR/controlled-artifact-reapply-package.json"
    sha256sum "$OUT_DIR"/*.json > "$OUT_DIR/manifest.sha256"
    ;;
  verify)
    [[ -n "$PACKAGE_JSON" ]] || usage_error "--package-json is required for verify"
    mpf production controlled-artifact-reapply-verify --package-json "$PACKAGE_JSON" --output json
    ;;
  execute-preflight)
    require_execute_common_args
    prepare_execute_out_dir
    validate_package_sha
    run_execution_gate_preflight
    ;;
  rollback-test)
    [[ -n "$PACKAGE_JSON" && -n "$OPERATOR" && -n "$REASON" ]] || usage_error "rollback-test requires --package-json, --operator, and --reason"
    prepare_execute_out_dir
    rollback_report="$OUT_DIR/controlled-artifact-reapply-rollback.json"
    mpf production controlled-artifact-reapply-rollback \
      --package-json "$PACKAGE_JSON" \
      --operator "$OPERATOR" \
      --reason "$REASON" \
      --output json > "$rollback_report"
    validate_json_decision "$rollback_report" "CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK_TEST_READY"
    write_manifest "$OUT_DIR"
    ;;
  rollback-apply)
    [[ -n "$PACKAGE_JSON" && -n "$OPERATOR" && -n "$REASON" ]] || usage_error "rollback-apply requires --package-json, --operator, and --reason"
    [[ "$YES" == "true" ]] || usage_error "rollback-apply requires script-level --yes"
    [[ "${MPF_PHASE11_CONTROLLED_ARTIFACT_ROLLBACK:-}" == "allow" ]] || usage_error "required rollback environment gate is missing"
    prepare_execute_out_dir
    rollback_report="$OUT_DIR/controlled-artifact-reapply-rollback.json"
    mpf production controlled-artifact-reapply-rollback \
      --package-json "$PACKAGE_JSON" \
      --operator "$OPERATOR" \
      --reason "$REASON" \
      --apply \
      --yes \
      --output json > "$rollback_report"
    validate_json_decision "$rollback_report" "CONTROLLED_ARTIFACT_REAPPLY_ROLLBACK_APPLIED_PENDING_REVIEW"
    write_manifest "$OUT_DIR"
    ;;
  execute)
    require_execute_common_args
    [[ "$YES" == "true" ]] || usage_error "execute requires script-level --yes"
    [[ "${MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY:-}" == "allow" && "${MPF_PHASE11_CONTROLLED_ARTIFACT_REAPPLY_EXECUTE:-}" == "allow" ]] || usage_error "required environment gates are missing"
    prepare_execute_out_dir
    validate_package_sha
    run_execution_gate_preflight
    execute_report="$OUT_DIR/controlled-artifact-reapply-execute.json"
    mpf production controlled-artifact-reapply-execute \
      --package-json "$PACKAGE_JSON" \
      --package-sha256 "$PACKAGE_SHA256" \
      --package-id "$PACKAGE_ID" \
      --operator "$OPERATOR" \
      --reason "$REASON" \
      --execute \
      --yes \
      --output json > "$execute_report"
    validate_json_decision "$execute_report" "CONTROLLED_ARTIFACT_REAPPLY_EXECUTED_PENDING_FARM5_EVIDENCE_REVIEW"
    write_manifest "$OUT_DIR"
    ;;
  *) usage_error "unsupported mode: $MODE" ;;
esac
