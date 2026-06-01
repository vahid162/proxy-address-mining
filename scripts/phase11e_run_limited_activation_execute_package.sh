#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"
MPF_BIN="${MPF_BIN:-}"
if [ -z "$MPF_BIN" ]; then
  if [ -x /opt/mpf-py/.venv/bin/mpf ]; then MPF_BIN=/opt/mpf-py/.venv/bin/mpf
  elif [ -x .venv/bin/mpf ]; then MPF_BIN=.venv/bin/mpf
  else MPF_BIN=mpf
  fi
fi
EXPECTED_VERSION= DECISION_JSON= DECISION_SHA= EXECUTION_JSON= EXECUTION_SHA= ROLLBACK_JSON= ROLLBACK_SHA= ARTIFACT_JSON= ARTIFACT_SHA= OUT_DIR= OPERATOR= REASON=
EXECUTE=false
COLLECT_POST_EVIDENCE=false
OPERATOR_CONFIRMED=false
UNDERSTAND_MUTATION=false
UNDERSTAND_LIMITED_ONLY=false
UNDERSTAND_CANARY=false
UNDERSTAND_NO_FIREWALL=false
UNDERSTAND_NO_UNRESTRICTED_PRODUCTION=false
UNDERSTAND_NO_MINER_EXPANSION=false
UNDERSTAND_NO_ABUSE=false
UNDERSTAND_PHASE11_NOT_ACCEPTED=false
REVIEWED_ROLLBACK=false
REVIEWED_POST_EVIDENCE=false
UNDERSTAND_POST_EVIDENCE_ONLY=false
UNDERSTAND_NO_DB_MUTATION=false
UNDERSTAND_NO_PRODUCTION_EXPANSION=false
while [ "$#" -gt 0 ]; do
 case "$1" in
  --expected-version) EXPECTED_VERSION="$2"; shift 2;; --decision-json) DECISION_JSON="$2"; shift 2;; --decision-json-sha256) DECISION_SHA="$2"; shift 2;;
  --execution-package-json) EXECUTION_JSON="$2"; shift 2;; --execution-package-json-sha256) EXECUTION_SHA="$2"; shift 2;;
  --rollback-package-json) ROLLBACK_JSON="$2"; shift 2;; --rollback-package-json-sha256) ROLLBACK_SHA="$2"; shift 2;;
  --artifact-gate-json) ARTIFACT_JSON="$2"; shift 2;; --artifact-gate-json-sha256) ARTIFACT_SHA="$2"; shift 2;;
  --out-dir) OUT_DIR="$2"; shift 2;; --operator) OPERATOR="$2"; shift 2;; --reason) REASON="$2"; shift 2;;
  --execute) EXECUTE=true; shift;; --collect-post-evidence) COLLECT_POST_EVIDENCE=true; shift;;
  --operator-confirmed) OPERATOR_CONFIRMED=true; shift;;
  --i-understand-this-mutates-limited-customer-db-state) UNDERSTAND_MUTATION=true; shift;;
  --i-understand-limited-btc-001-only) UNDERSTAND_LIMITED_ONLY=true; shift;;
  --i-understand-canary-must-be-preserved) UNDERSTAND_CANARY=true; shift;;
  --i-understand-no-firewall-apply) UNDERSTAND_NO_FIREWALL=true; shift;;
  --i-understand-no-unrestricted-production) UNDERSTAND_NO_UNRESTRICTED_PRODUCTION=true; shift;;
  --i-understand-no-production-traffic-expansion) UNDERSTAND_NO_PRODUCTION_EXPANSION=true; shift;;
  --i-understand-no-miner-traffic-expansion) UNDERSTAND_NO_MINER_EXPANSION=true; shift;;
  --i-understand-no-abuse-automation) UNDERSTAND_NO_ABUSE=true; shift;;
  --i-understand-phase11-not-accepted) UNDERSTAND_PHASE11_NOT_ACCEPTED=true; shift;;
  --i-have-reviewed-rollback-package) REVIEWED_ROLLBACK=true; shift;;
  --i-have-reviewed-post-evidence-command) REVIEWED_POST_EVIDENCE=true; shift;;
  --i-understand-post-evidence-only) UNDERSTAND_POST_EVIDENCE_ONLY=true; shift;;
  --i-understand-no-db-mutation) UNDERSTAND_NO_DB_MUTATION=true; shift;;
  *) echo "unknown argument: $1" >&2; exit 2;; esac
done
for value in EXPECTED_VERSION DECISION_JSON DECISION_SHA EXECUTION_JSON EXECUTION_SHA ROLLBACK_JSON ROLLBACK_SHA ARTIFACT_JSON ARTIFACT_SHA OUT_DIR OPERATOR REASON; do [ -n "${!value}" ] || { echo "missing required argument: $value" >&2; exit 2; }; done
mkdir -p "$OUT_DIR"
check_sha() { printf '%s  %s\n' "$2" "$1" | sha256sum --check --status -; }
check_sha "$DECISION_JSON" "$DECISION_SHA"; check_sha "$EXECUTION_JSON" "$EXECUTION_SHA"; check_sha "$ROLLBACK_JSON" "$ROLLBACK_SHA"; check_sha "$ARTIFACT_JSON" "$ARTIFACT_SHA"
EXECUTION_OUT="$OUT_DIR/limited-activation-execution.json"; POST_OUT="$OUT_DIR/post-activation-evidence.json"
if [ "$EXECUTE" != true ]; then
 printf '{"component":"phase11e_limited_activation_execute_helper","execute_requested":false,"mutation_performed":false,"next_required_step":"rerun_with_explicit_execute_after_operator_review"}\n' > "$EXECUTION_OUT"
else
 for confirmation in OPERATOR_CONFIRMED UNDERSTAND_MUTATION UNDERSTAND_LIMITED_ONLY UNDERSTAND_CANARY UNDERSTAND_NO_FIREWALL UNDERSTAND_NO_UNRESTRICTED_PRODUCTION UNDERSTAND_NO_MINER_EXPANSION UNDERSTAND_NO_ABUSE UNDERSTAND_PHASE11_NOT_ACCEPTED REVIEWED_ROLLBACK REVIEWED_POST_EVIDENCE; do
  [ "${!confirmation}" = true ] || { echo "missing required execute confirmation: $confirmation" >&2; exit 2; }
 done
 "$MPF_BIN" production phase11e-limited-activation-execute --expected-version "$EXPECTED_VERSION" --limited-activation-decision-json "$DECISION_JSON" --limited-activation-decision-json-sha256 "$DECISION_SHA" --limited-activation-execution-package-json "$EXECUTION_JSON" --limited-activation-execution-package-json-sha256 "$EXECUTION_SHA" --limited-activation-rollback-package-json "$ROLLBACK_JSON" --limited-activation-rollback-package-json-sha256 "$ROLLBACK_SHA" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-this-mutates-limited-customer-db-state --i-understand-limited-btc-001-only --i-understand-canary-must-be-preserved --i-understand-no-firewall-apply --i-understand-no-unrestricted-production --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --i-understand-phase11-not-accepted --i-have-reviewed-rollback-package --i-have-reviewed-post-evidence-command --out-json "$EXECUTION_OUT" --output json
fi
sha256sum "$EXECUTION_OUT" | awk '{print $1}' > "$OUT_DIR/limited-activation-execution.sha256"
if [ "$COLLECT_POST_EVIDENCE" = true ]; then
 [ "$EXECUTE" = true ] || { echo '--collect-post-evidence requires --execute' >&2; exit 2; }
 for confirmation in OPERATOR_CONFIRMED UNDERSTAND_POST_EVIDENCE_ONLY UNDERSTAND_NO_DB_MUTATION UNDERSTAND_NO_FIREWALL UNDERSTAND_NO_PRODUCTION_EXPANSION UNDERSTAND_NO_MINER_EXPANSION UNDERSTAND_NO_ABUSE; do
  [ "${!confirmation}" = true ] || { echo "missing required post-evidence confirmation: $confirmation" >&2; exit 2; }
 done
 "$MPF_BIN" production phase11e-limited-activation-post-evidence-collect --expected-version "$EXPECTED_VERSION" --activation-execution-json "$EXECUTION_OUT" --activation-execution-json-sha256 "$(cat "$OUT_DIR/limited-activation-execution.sha256")" --artifact-gate-json "$ARTIFACT_JSON" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-post-evidence-only --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-production-traffic-expansion --i-understand-no-miner-traffic-expansion --i-understand-no-abuse-automation --out-json "$POST_OUT" --output json
 sha256sum "$POST_OUT" | awk '{print $1}' > "$OUT_DIR/post-activation-evidence.sha256"
fi
printf '{"component":"phase11e_limited_activation_execute_helper","expected_version":"%s","execute_requested":%s,"collect_post_evidence_requested":%s,"mutation_performed_by_helper":false}\n' "$EXPECTED_VERSION" "$EXECUTE" "$COLLECT_POST_EVIDENCE" > "$OUT_DIR/manifest.json"
if [ "$COLLECT_POST_EVIDENCE" = true ]; then
 ( cd "$OUT_DIR" && sha256sum limited-activation-execution.json manifest.json post-activation-evidence.json ) > "$OUT_DIR/sha256-manifest.txt"
else
 ( cd "$OUT_DIR" && sha256sum limited-activation-execution.json manifest.json ) > "$OUT_DIR/sha256-manifest.txt"
fi
