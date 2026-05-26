#!/usr/bin/env bash
set -Eeuo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
OUT_DIR=""; VIS=""; VIS_SHA=""; COLLECT_ABUSE=0; COLLECT_RESTART=0; RUN_PRECHECK=0; AG=""; AG_SHA=""
while [[ $# -gt 0 ]]; do case "$1" in
  --expected-version) EXPECTED_VERSION="$2"; shift 2;; --out-dir) OUT_DIR="$2"; shift 2;;
  --visibility-bundle-json) VIS="$2"; shift 2;; --visibility-bundle-json-sha256) VIS_SHA="$2"; shift 2;;
  --collect-abuse-evidence) COLLECT_ABUSE=1; shift;; --collect-restart-evidence) COLLECT_RESTART=1; shift;;
  --artifact-gate-json) AG="$2"; shift 2;; --artifact-gate-json-sha256) AG_SHA="$2"; shift 2;;
  --run-precheck) RUN_PRECHECK=1; shift;; *) echo "Unknown arg: $1"; exit 2;; esac; done
[[ -n "$VIS" && -n "$VIS_SHA" ]] || { echo 'visibility bundle args required'; exit 1; }
OUT_DIR="${OUT_DIR:-/tmp/phase11e-abuse-restart-${EXPECTED_VERSION}-$(date -u +%Y%m%dT%H%M%SZ)}"; mkdir -p "$OUT_DIR"
if [[ "$COLLECT_ABUSE" == "1" ]]; then
  mpf production single-customer-abuse-1h-evidence --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-evidence-only --i-understand-no-abuse-automation-enable --i-understand-no-hard-block --i-understand-no-firewall-apply --i-understand-no-db-mutation --i-understand-no-production-traffic --i-understand-no-miner-traffic --out-json "$OUT_DIR/abuse-1h-evidence.json" --output json > /dev/null
  sha256sum "$OUT_DIR/abuse-1h-evidence.json" | awk '{print $1}' > "$OUT_DIR/abuse-1h-evidence.sha256"
fi
if [[ "$COLLECT_RESTART" == "1" ]]; then
  EXTRA=(); [[ -n "$AG" ]] && EXTRA+=(--artifact-gate-json "$AG"); [[ -n "$AG_SHA" ]] && EXTRA+=(--artifact-gate-json-sha256 "$AG_SHA")
  mpf production single-customer-restart-container-order-evidence --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-evidence-only --i-understand-no-restart --i-understand-no-docker-restart --i-understand-no-systemctl-restart --i-understand-no-firewall-apply --i-understand-no-db-mutation --i-understand-no-production-traffic --i-understand-no-miner-traffic --out-json "$OUT_DIR/restart-container-order-evidence.json" "${EXTRA[@]}" --output json > /dev/null
  sha256sum "$OUT_DIR/restart-container-order-evidence.json" | awk '{print $1}' > "$OUT_DIR/restart-container-order-evidence.sha256"
fi
ABUSE_ARGS=(); [[ -f "$OUT_DIR/abuse-1h-evidence.json" ]] && ABUSE_ARGS+=(--abuse-evidence-json "$OUT_DIR/abuse-1h-evidence.json" --abuse-evidence-json-sha256 "$(cat "$OUT_DIR/abuse-1h-evidence.sha256")")
mpf production single-customer-abuse-1h-readiness --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" "${ABUSE_ARGS[@]}" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-abuse-readiness-only --i-understand-no-abuse-automation-enable --i-understand-no-hard-block-automation --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --output json > "$OUT_DIR/abuse-1h-readiness.json"
RESTART_ARGS=(); [[ -f "$OUT_DIR/restart-container-order-evidence.json" ]] && RESTART_ARGS+=(--restart-evidence-json "$OUT_DIR/restart-container-order-evidence.json" --restart-evidence-json-sha256 "$(cat "$OUT_DIR/restart-container-order-evidence.sha256")")
[[ -n "$AG" ]] && RESTART_ARGS+=(--artifact-gate-json "$AG"); [[ -n "$AG_SHA" ]] && RESTART_ARGS+=(--artifact-gate-json-sha256 "$AG_SHA")
mpf production single-customer-restart-container-order-readiness --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" "${RESTART_ARGS[@]}" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-restart-readiness-only --i-understand-no-restart-performed-by-classifier --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --output json > "$OUT_DIR/restart-container-order-readiness.json"
if [[ "$RUN_PRECHECK" == "1" ]]; then
  mpf production single-customer-limited-acceptance-precheck --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --abuse-1h-readiness-json "$OUT_DIR/abuse-1h-readiness.json" --restart-container-order-readiness-json "$OUT_DIR/restart-container-order-readiness.json" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-precheck-only --i-understand-no-customer-activation --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --output json > "$OUT_DIR/limited-acceptance-precheck.json"
fi
EXPECTED_VERSION="$EXPECTED_VERSION" VIS="$VIS" VIS_SHA="$VIS_SHA" AG="$AG" python - <<'PY' "$OUT_DIR"
import json,sys,os
from datetime import datetime, UTC
out=sys.argv[1]
rd=lambda n: json.load(open(os.path.join(out,n))) if os.path.exists(os.path.join(out,n)) else None
a=rd('abuse-1h-readiness.json'); r=rd('restart-container-order-readiness.json'); p=rd('limited-acceptance-precheck.json')
manifest={'expected_version':os.environ['EXPECTED_VERSION'],'generated_at':datetime.now(UTC).isoformat(),'visibility_bundle_json':os.environ['VIS'],'visibility_bundle_sha256':os.environ['VIS_SHA'],'artifact_gate_json':os.environ.get('AG') or None,'abuse_evidence_json':'abuse-1h-evidence.json' if os.path.exists(os.path.join(out,'abuse-1h-evidence.json')) else None,'restart_evidence_json':'restart-container-order-evidence.json' if os.path.exists(os.path.join(out,'restart-container-order-evidence.json')) else None,'abuse_readiness':None if a is None else a.get('final_decision'),'restart_container_order_readiness':None if r is None else r.get('final_decision'),'limited_acceptance_precheck':None if p is None else p.get('final_decision'),'final_summary':{'abuse':'READY' if a and a.get('abuse_1h_coverage_ready') else 'BLOCKED','restart':'READY' if r and r.get('restart_container_order_ready') else 'BLOCKED','precheck':'READY' if p and p.get('limited_acceptance_precheck_ready') else 'BLOCKED'}}
json.dump(manifest,open(os.path.join(out,'manifest.json'),'w'),indent=2)
PY
( cd "$OUT_DIR" && sha256sum * > sha256-manifest.txt )
