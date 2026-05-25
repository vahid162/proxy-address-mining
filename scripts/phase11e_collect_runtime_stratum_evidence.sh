#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_VERSION="0.1.212"
FORWARDER_CONTAINER="mpf-forwarder"
BRIDGE_CONTAINER="mpf-v2raya-socks-bridge"
OUT_DIR=""
WAIT_FOR_TRANSCRIPT_SECONDS=300
CAPTURE_DELAY_SECONDS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --operator) OPERATOR="$2"; shift 2 ;;
    --reason) REASON="$2"; shift 2 ;;
    --post-apply-evidence-json) POST_APPLY_JSON="$2"; shift 2 ;;
    --post-apply-evidence-json-sha256) POST_APPLY_SHA="$2"; shift 2 ;;
    --transcript-json) TRANSCRIPT_JSON="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --forwarder-container) FORWARDER_CONTAINER="$2"; shift 2 ;;
    --bridge-container) BRIDGE_CONTAINER="$2"; shift 2 ;;
    --expected-version) EXPECTED_VERSION="$2"; shift 2 ;;
    --wait-for-transcript-seconds) WAIT_FOR_TRANSCRIPT_SECONDS="$2"; shift 2 ;;
    --capture-delay-seconds) CAPTURE_DELAY_SECONDS="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

: "${OPERATOR:?--operator required}"
: "${REASON:?--reason required}"
: "${POST_APPLY_JSON:?--post-apply-evidence-json required}"
: "${POST_APPLY_SHA:?--post-apply-evidence-json-sha256 required}"
: "${TRANSCRIPT_JSON:?--transcript-json required}"
command -v conntrack >/dev/null 2>&1 || { echo "CRITICAL: conntrack not installed"; exit 1; }

OUT_DIR="${OUT_DIR:-/tmp/phase11e-runtime-stratum-${EXPECTED_VERSION}-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$OUT_DIR"

write_manifest() {
  OUT_DIR="$OUT_DIR" EXPECTED_VERSION="$EXPECTED_VERSION" OPERATOR="$OPERATOR" REASON="$REASON" WAIT_FOR_TRANSCRIPT_SECONDS="$WAIT_FOR_TRANSCRIPT_SECONDS" python - <<'PY'
import datetime, glob, hashlib, json, os
out = os.environ['OUT_DIR']
arts = {os.path.basename(p): p for p in glob.glob(out+'/*') if os.path.isfile(p)}
sha = {k: hashlib.sha256(open(v,'rb').read()).hexdigest() for k,v in arts.items()}

def decision(name):
    p = os.path.join(out, name)
    if not os.path.exists(p):
        return 'NOT_RUN'
    try:
        return json.load(open(p)).get('final_decision','UNKNOWN')
    except Exception:
        return 'INVALID_JSON'

manifest = {
    'version': os.environ['EXPECTED_VERSION'],
    'timestamp': datetime.datetime.utcnow().isoformat()+'Z',
    'operator': os.environ['OPERATOR'],
    'reason': os.environ['REASON'],
    'artifact_paths': arts,
    'sha256': sha,
    'final_decisions': {
        'current_controlled_artifact_gate': decision('current-controlled-artifact-gate.json'),
        'runtime_probe_diagnostics': decision('runtime-probe-diagnostics.json'),
        'runtime_path_evidence': decision('runtime-path-evidence.json'),
        'stratum_transcript_evidence': decision('stratum-transcript-evidence.json'),
        'visibility_bundle': decision('visibility-bundle.json'),
    },
    'no_activation_performed': True,
    'external_probe_required': True,
    'transcript_wait_seconds': int(os.environ['WAIT_FOR_TRANSCRIPT_SECONDS']),
    'next_required_step': 'review_evidence_and_submit_pr',
}
json.dump(manifest, open(os.path.join(out, 'manifest.json'),'w'), indent=2)
PY
}

if (( CAPTURE_DELAY_SECONDS > 0 )); then
  sleep "$CAPTURE_DELAY_SECONDS"
fi

iptables-save > "$OUT_DIR/live-iptables-save.txt"
if command -v ip6tables-save >/dev/null 2>&1; then ip6tables-save > "$OUT_DIR/live-ip6tables-save.txt"; else : > "$OUT_DIR/live-ip6tables-save.txt"; fi

gate_json="$OUT_DIR/current-controlled-artifact-gate.json"
mpf production current-controlled-artifact-gate --expected-version "$EXPECTED_VERSION" --iptables-save-file "$OUT_DIR/live-iptables-save.txt" --ip6tables-save-file "$OUT_DIR/live-ip6tables-save.txt" --output json > "$gate_json"
GATE_DECISION="$(python -c 'import json,sys;print(json.load(open(sys.argv[1])).get("final_decision",""))' "$gate_json")"
if [[ "$GATE_DECISION" == BLOCKED_* ]]; then
  write_manifest
  echo "CRITICAL: blocked by artifact gate: $GATE_DECISION"
  exit 1
fi
[[ "$GATE_DECISION" == "PASS_WITH_KNOWN_CONTROLLED_PHASE11_ARTIFACTS" || "$GATE_DECISION" == "PASS_NO_CUSTOMER_ARTIFACTS" ]] || { write_manifest; echo "CRITICAL: blocked by artifact gate: $GATE_DECISION"; exit 1; }

conntrack -L > "$OUT_DIR/conntrack.txt"
docker logs --since 15m "$FORWARDER_CONTAINER" > "$OUT_DIR/forwarder.log" || echo "WARN: forwarder log collection failed" > "$OUT_DIR/forwarder.log.warn"
docker logs --since 15m "$BRIDGE_CONTAINER" > "$OUT_DIR/bridge.log" || echo "WARN: bridge log collection failed" > "$OUT_DIR/bridge.log.warn"

for f in "$OUT_DIR"/*; do [[ -f "$f" ]] && sha256sum "$f" > "$f.sha256"; done

transcript_ok=false
for ((i=0; i<=WAIT_FOR_TRANSCRIPT_SECONDS; i++)); do
  if [[ -f "$TRANSCRIPT_JSON" ]] && python -c 'import json,sys;json.load(open(sys.argv[1]));print("ok")' "$TRANSCRIPT_JSON" >/dev/null 2>&1; then
    transcript_ok=true
    break
  fi
  sleep 1
done

if [[ "$transcript_ok" != "true" ]]; then
  write_manifest
  OUT_DIR="$OUT_DIR" python - <<'PY'
import json, os
p=os.path.join(os.environ['OUT_DIR'],'manifest.json')
m=json.load(open(p))
m['final_decisions']['stratum_transcript_evidence']='BLOCKED_TRANSCRIPT_MISSING_OR_INVALID'
m['next_required_step']='provide_valid_transcript_and_rerun'
json.dump(m, open(p,'w'), indent=2)
PY
  echo "CRITICAL: transcript missing or invalid after wait window"
  exit 1
fi

cp "$TRANSCRIPT_JSON" "$OUT_DIR/stratum-transcript.json"
sha256sum "$OUT_DIR/stratum-transcript.json" > "$OUT_DIR/stratum-transcript.json.sha256"

mpf production single-customer-runtime-probe-diagnostics --expected-version "$EXPECTED_VERSION" --post-apply-evidence-json "$POST_APPLY_JSON" --post-apply-evidence-json-sha256 "$POST_APPLY_SHA" --live-snapshot-file "$OUT_DIR/live-iptables-save.txt" --live-snapshot-sha256 "$(cut -d' ' -f1 "$OUT_DIR/live-iptables-save.txt.sha256")" --conntrack-snapshot-file "$OUT_DIR/conntrack.txt" --conntrack-snapshot-sha256 "$(cut -d' ' -f1 "$OUT_DIR/conntrack.txt.sha256")" --forwarder-log-file "$OUT_DIR/forwarder.log" --forwarder-log-sha256 "$(test -f "$OUT_DIR/forwarder.log.sha256" && cut -d' ' -f1 "$OUT_DIR/forwarder.log.sha256" || echo missing)" --bridge-log-file "$OUT_DIR/bridge.log" --bridge-log-sha256 "$(test -f "$OUT_DIR/bridge.log.sha256" && cut -d' ' -f1 "$OUT_DIR/bridge.log.sha256" || echo missing)" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-probe-diagnostics-only --i-understand-no-runtime-acceptance --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --i-confirm-stratum-transcript-required --i-confirm-visibility-bundle-required --i-confirm-abuse-1h-required-before-customer-traffic --i-confirm-restart-container-order-required-before-limited-acceptance --output json > "$OUT_DIR/runtime-probe-diagnostics.json"

mpf production single-customer-runtime-path-evidence --expected-version "$EXPECTED_VERSION" --post-apply-evidence-json "$POST_APPLY_JSON" --post-apply-evidence-json-sha256 "$POST_APPLY_SHA" --live-snapshot-file "$OUT_DIR/live-iptables-save.txt" --conntrack-snapshot-file "$OUT_DIR/conntrack.txt" --forwarder-log-file "$OUT_DIR/forwarder.log" --bridge-log-file "$OUT_DIR/bridge.log" --operator "$OPERATOR" --reason "$REASON" --operator-confirmed --i-understand-runtime-evidence-only --i-understand-no-production-traffic-acceptance --i-understand-no-miner-traffic-acceptance --i-understand-no-db-activation --i-confirm-stratum-transcript-required --i-confirm-visibility-bundle-required --i-confirm-abuse-1h-required-before-customer-traffic --i-confirm-restart-container-order-required-before-limited-acceptance --output json > "$OUT_DIR/runtime-path-evidence.json"

mpf production single-customer-stratum-transcript-evidence --transcript-json "$OUT_DIR/stratum-transcript.json" --output json > "$OUT_DIR/stratum-transcript-evidence.json"

READY_PATH="$(python -c 'import json,sys;print(str(json.load(open(sys.argv[1])).get("runtime_path_evidence_ready",False)).lower())' "$OUT_DIR/runtime-path-evidence.json")"
READY_TX="$(python -c 'import json,sys;print(str(json.load(open(sys.argv[1])).get("stratum_transcript_ready",False)).lower())' "$OUT_DIR/stratum-transcript-evidence.json")"
if [[ "$READY_PATH" == "true" && "$READY_TX" == "true" ]]; then
  mpf production single-customer-visibility-bundle --runtime-path-evidence-json "$OUT_DIR/runtime-path-evidence.json" --runtime-path-evidence-json-sha256 "$(sha256sum "$OUT_DIR/runtime-path-evidence.json" | cut -d' ' -f1)" --stratum-transcript-evidence-json "$OUT_DIR/stratum-transcript-evidence.json" --stratum-transcript-evidence-json-sha256 "$(sha256sum "$OUT_DIR/stratum-transcript-evidence.json" | cut -d' ' -f1)" --output json > "$OUT_DIR/visibility-bundle.json"
fi

write_manifest

echo "OK: evidence directory: $OUT_DIR"
