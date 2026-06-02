#!/usr/bin/env bash
set -Eeuo pipefail
# Read-only Phase 11 final acceptance helper. For local-peer postgresql:///mpf DB-reading commands, run as sudo -u mpf, not root.
MPF_BIN="${MPF_BIN:-mpf}"
fail(){ echo "ERROR: $*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
check(){ [ -f "$1" ] || fail "missing file: $1"; [ "$(sha "$1")" = "$2" ] || fail "hash mismatch: $1"; }
while [ $# -gt 0 ]; do case "$1" in
 --expected-version) VERSION=$2;; --final-acceptance-pr-readiness-json) READINESS=$2;; --final-acceptance-pr-readiness-json-sha256) READINESS_SHA=$2;; --controlled-boundary-decision-json) DECISION=$2;; --controlled-boundary-decision-json-sha256) DECISION_SHA=$2;; --controlled-boundary-package-json) PACKAGE=$2;; --controlled-boundary-package-json-sha256) PACKAGE_SHA=$2;; --artifact-gate-json) ARTIFACT=$2;; --artifact-gate-json-sha256) ARTIFACT_SHA=$2;; --out-dir) OUT=$2;; --operator) OPERATOR=$2;; --reason) REASON=$2;; *) fail "unknown argument: $1";; esac; shift 2; done
: "${VERSION:?}" "${READINESS:?}" "${READINESS_SHA:?}" "${DECISION:?}" "${DECISION_SHA:?}" "${PACKAGE:?}" "${PACKAGE_SHA:?}" "${ARTIFACT:?}" "${ARTIFACT_SHA:?}" "${OUT:?}" "${OPERATOR:?}" "${REASON:?}"
check "$READINESS" "$READINESS_SHA"; check "$DECISION" "$DECISION_SHA"; check "$PACKAGE" "$PACKAGE_SHA"; check "$ARTIFACT" "$ARTIFACT_SHA"; mkdir -p "$OUT"
FINAL="$OUT/phase11-final-acceptance.json"; POST="$OUT/phase11-post-acceptance-verification.json"
"$MPF_BIN" production phase11-final-acceptance --expected-version "$VERSION" --final-acceptance-pr-readiness-json "$READINESS" --final-acceptance-pr-readiness-json-sha256 "$READINESS_SHA" --controlled-boundary-decision-json "$DECISION" --controlled-boundary-decision-json-sha256 "$DECISION_SHA" --controlled-boundary-package-json "$PACKAGE" --controlled-boundary-package-json-sha256 "$PACKAGE_SHA" --operator "$OPERATOR" --reason "$REASON" --out-json "$FINAL" --output json --operator-confirmed --i-understand-phase11-final-acceptance --i-understand-controlled-cli-limited-only --i-understand-phase12-is-next --i-understand-worker-enforcement-remains-disabled --i-understand-ui-telegram-remain-disabled --i-understand-no-unrestricted-production-expansion --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change
[ "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["final_decision"])' "$FINAL")" = PHASE11_FINAL_ACCEPTANCE_ACCEPTED ] || fail 'final acceptance blocked'
sha "$FINAL" > "$OUT/phase11-final-acceptance.sha256"
"$MPF_BIN" production phase11-post-acceptance-verification --expected-version "$VERSION" --final-acceptance-json "$FINAL" --final-acceptance-json-sha256 "$(cat "$OUT/phase11-final-acceptance.sha256")" --artifact-gate-json "$ARTIFACT" --artifact-gate-json-sha256 "$ARTIFACT_SHA" --operator "$OPERATOR" --reason "$REASON" --out-json "$POST" --output json --operator-confirmed --i-understand-post-acceptance-verification-only --i-understand-no-db-mutation --i-understand-no-firewall-apply --i-understand-no-runtime-change --i-understand-ui-telegram-remain-disabled --i-understand-worker-enforcement-remains-disabled
[ "$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["final_decision"])' "$POST")" = PHASE11_POST_ACCEPTANCE_VERIFICATION_READY ] || fail 'post verification blocked'
sha "$POST" > "$OUT/phase11-post-acceptance-verification.sha256"
python - "$OUT" "$READINESS" "$DECISION" "$PACKAGE" "$ARTIFACT" <<'PY'
import json,sys
out,readiness,decision,package,artifact=sys.argv[1:]
json.dump({"component":"phase11_final_acceptance_and_post_verification_manifest","inputs":{"final_acceptance_pr_readiness_json":readiness,"controlled_boundary_decision_json":decision,"controlled_boundary_package_json":package,"artifact_gate_json":artifact},"outputs":{"final_acceptance_json":f"{out}/phase11-final-acceptance.json","post_acceptance_verification_json":f"{out}/phase11-post-acceptance-verification.json"},"mutation_performed":False,"db_mutation_performed":False,"firewall_apply_performed":False,"docker_restart_performed":False,"systemd_restart_performed":False},open(f"{out}/manifest.json","w"),indent=2)
PY
( cd "$OUT" && sha256sum phase11-final-acceptance.json phase11-post-acceptance-verification.json manifest.json > sha256-manifest.txt )
