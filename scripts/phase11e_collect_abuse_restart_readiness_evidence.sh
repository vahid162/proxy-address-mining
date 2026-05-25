#!/usr/bin/env bash
set -Eeuo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
OUT_DIR=""; VIS=""; VIS_SHA=""
while [[ $# -gt 0 ]]; do case "$1" in --expected-version) EXPECTED_VERSION="$2"; shift 2;; --out-dir) OUT_DIR="$2"; shift 2;; --visibility-bundle-json) VIS="$2"; shift 2;; --visibility-bundle-json-sha256) VIS_SHA="$2"; shift 2;; *) echo "Unknown arg: $1"; exit 2;; esac; done
[[ -n "$EXPECTED_VERSION" ]] || exit 1
[[ -n "$VIS" && -n "$VIS_SHA" ]] || { echo 'visibility bundle args required'; exit 1; }
OUT_DIR="${OUT_DIR:-/tmp/phase11e-abuse-restart-${EXPECTED_VERSION}-$(date -u +%Y%m%dT%H%M%SZ)}"; mkdir -p "$OUT_DIR"
mpf --version > "$OUT_DIR/mpf-version.txt" || true
mpf phase-status > "$OUT_DIR/phase-status.txt" || true
mpf doctor > "$OUT_DIR/mpf-doctor.txt" || true
mpf db status > "$OUT_DIR/db-status.txt" || true
mpf proxy doctor > "$OUT_DIR/proxy-doctor.txt" || true
bash "$REPO_ROOT/scripts/verify_current_phase_gate.sh" > "$OUT_DIR/verify-current-phase-gate.txt" || true
docker ps > "$OUT_DIR/docker-ps.txt" 2>&1 || true
if [[ -f "$REPO_ROOT/docker-compose.yml" || -f "$REPO_ROOT/compose.yml" ]]; then docker compose ps > "$OUT_DIR/docker-compose-ps.txt" 2>&1 || true; fi
mpf production single-customer-abuse-1h-readiness --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-abuse-readiness-only --i-understand-no-abuse-automation-enable --i-understand-no-hard-block-automation --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --output json > "$OUT_DIR/abuse-1h-readiness.json"
mpf production single-customer-restart-container-order-readiness --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-restart-readiness-only --i-understand-no-restart-performed-by-classifier --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --output json > "$OUT_DIR/restart-container-order-readiness.json"
EXPECTED_VERSION="$EXPECTED_VERSION" VIS="$VIS" VIS_SHA="$VIS_SHA" python - <<'PY' "$OUT_DIR"
import json,sys,os,datetime
out=sys.argv[1]
expected_version=os.environ.get('EXPECTED_VERSION')
visibility_bundle_json=os.environ.get('VIS')
visibility_bundle_sha256=os.environ.get('VIS_SHA')
a=json.load(open(os.path.join(out,'abuse-1h-readiness.json')))
r=json.load(open(os.path.join(out,'restart-container-order-readiness.json')))
manifest={'expected_version': expected_version,'generated_at': datetime.datetime.utcnow().isoformat()+'Z', 'visibility_bundle_json': visibility_bundle_json, 'visibility_bundle_sha256': visibility_bundle_sha256, 'note':'this helper currently produces BLOCKED readiness unless external abuse/restart evidence files are added in later steps', 'abuse_readiness':a.get('final_decision'),'restart_container_order_readiness':r.get('final_decision'),'limited_acceptance_precheck':'BLOCKED','final_summary':{'abuse':'READY' if a.get('abuse_1h_coverage_ready') else 'BLOCKED','restart':'READY' if r.get('restart_container_order_ready') else 'BLOCKED','precheck':'BLOCKED'}}
json.dump(manifest,open(os.path.join(out,'manifest.json'),'w'),indent=2)
PY
( cd "$OUT_DIR" && sha256sum * > sha256-manifest.txt )
echo "abuse readiness: $(python -c "import json;print('READY' if json.load(open('$OUT_DIR/abuse-1h-readiness.json')).get('abuse_1h_coverage_ready') else 'BLOCKED')")"
echo "restart/container-order readiness: $(python -c "import json;print('READY' if json.load(open('$OUT_DIR/restart-container-order-readiness.json')).get('restart_container_order_ready') else 'BLOCKED')")"
echo "limited acceptance precheck: BLOCKED"
