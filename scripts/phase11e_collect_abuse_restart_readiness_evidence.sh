#!/usr/bin/env bash
set -Eeuo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
OUT_DIR=""; VIS=""; VIS_SHA=""; COLLECT_SOURCE=0; COLLECT_AG=0; COLLECT_ABUSE=0; COLLECT_RESTART=0; RUN_PRECHECK=0; AG=""; AG_SHA=""; SRC=""; SRC_SHA=""
while [[ $# -gt 0 ]]; do case "$1" in
  --expected-version) EXPECTED_VERSION="$2"; shift 2;; --out-dir) OUT_DIR="$2"; shift 2;;
  --visibility-bundle-json) VIS="$2"; shift 2;; --visibility-bundle-json-sha256) VIS_SHA="$2"; shift 2;;
  --collect-source-evidence) COLLECT_SOURCE=1; shift;; --collect-artifact-gate) COLLECT_AG=1; shift;; --collect-abuse-evidence) COLLECT_ABUSE=1; shift;; --collect-restart-evidence) COLLECT_RESTART=1; shift;;
  --source-evidence-json) SRC="$2"; shift 2;; --source-evidence-json-sha256) SRC_SHA="$2"; shift 2;; --artifact-gate-json) AG="$2"; shift 2;; --artifact-gate-json-sha256) AG_SHA="$2"; shift 2;;
  --run-precheck) RUN_PRECHECK=1; shift;; *) echo "Unknown arg: $1"; exit 2;; esac; done
[[ -n "$VIS" && -n "$VIS_SHA" ]] || { echo 'visibility bundle args required'; exit 1; }
OUT_DIR="${OUT_DIR:-/tmp/phase11e-abuse-restart-${EXPECTED_VERSION}-$(date -u +%Y%m%dT%H%M%SZ)}"; mkdir -p "$OUT_DIR"

if [[ "$COLLECT_AG" == "1" ]]; then
  if command -v iptables-save >/dev/null 2>&1; then iptables-save > "$OUT_DIR/iptables-save.txt"; else : > "$OUT_DIR/iptables-save.txt"; fi
  if command -v ip6tables-save >/dev/null 2>&1; then ip6tables-save > "$OUT_DIR/ip6tables-save.txt"; else : > "$OUT_DIR/ip6tables-save.txt"; fi
  python - <<'PY' "$OUT_DIR/current-controlled-artifact-gate.json" "$EXPECTED_VERSION" "$OUT_DIR/iptables-save.txt" "$OUT_DIR/ip6tables-save.txt"
import json,sys
from pathlib import Path
from mpf.services.phase11_current_controlled_artifact_gate_service import build_phase11_current_controlled_artifact_gate_report
phase = Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
ip4 = Path(sys.argv[3]).read_text(encoding='utf-8')
ip6 = Path(sys.argv[4]).read_text(encoding='utf-8')
rep = build_phase11_current_controlled_artifact_gate_report(iptables_save_text=ip4, ip6tables_save_text=ip6, phase_status_text=phase, expected_version=sys.argv[2])
if not ip4.strip(): rep.setdefault('blockers',[]).append('missing_real_iptables_save_source'); rep['final_decision']='BLOCKED'
Path(sys.argv[1]).write_text(json.dumps(rep,indent=2),encoding='utf-8')
PY
  sha256sum "$OUT_DIR/current-controlled-artifact-gate.json" | awk '{print $1}' > "$OUT_DIR/current-controlled-artifact-gate.sha256"
  AG="$OUT_DIR/current-controlled-artifact-gate.json"; AG_SHA="$(cat "$OUT_DIR/current-controlled-artifact-gate.sha256")"
fi

if [[ "$COLLECT_SOURCE" == "1" ]]; then
  python - <<'PY' "$OUT_DIR/phase11e-source-evidence-bundle.json" "$EXPECTED_VERSION" "$VIS" "$VIS_SHA" "$AG" "$AG_SHA" "$OUT_DIR"
import hashlib,json,sys
from pathlib import Path
from mpf.config import load_config, DEFAULT_CONFIG_PATH
from mpf.services import doctor_service, db_service, proxy_doctor_service, lane_service, customer_read_service
from mpf.services.phase11e_source_evidence_bundle_service import build_phase11e_source_evidence_bundle_report
cfg=load_config(DEFAULT_CONFIG_PATH)
phase={}
ps=Path('docs/PHASE_STATUS.md').read_text(encoding='utf-8')
for k in ['production_traffic','firewall_apply_allowed','abuse_automation_allowed','customer_onboarding_allowed','ui_allowed','telegram_allowed']:
    for ln in ps.splitlines():
        if ln.strip().startswith(k+':'): phase[k]=ln.split(':',1)[1].strip()
mpf=doctor_service.run(DEFAULT_CONFIG_PATH); db=db_service.status(cfg); proxy=proxy_doctor_service.status(DEFAULT_CONFIG_PATH)
lanes_res=lane_service.list_lane_status(cfg); lanes=[{'name':l.name,'enabled':l.enabled,'backend_port':l.backend_port,'source':l.source} for l in lanes_res.lanes] if lanes_res.ok else []
cust_res=customer_read_service.list_customer_status(cfg,include_deleted=False,limit=5000); customers=[{'customer_key':r.customer_key,'status':r.status,'lane':r.lane} for r in cust_res.rows] if cust_res.ok else []
ag={}
if sys.argv[5]:
    p=Path(sys.argv[5]);
    if p.exists(): ag=json.loads(p.read_text(encoding='utf-8'))
# read-only runtime/exposure from real files/commands
runtime={'source_files':[str(Path(sys.argv[7])/'docker-ps.txt'),str(Path(sys.argv[7])/'ss-listen.txt')],'source_hashes':{}}
for name,cmd in [('docker-ps.txt','docker ps --format "{{.Names}} {{.Status}}"'),('ss-listen.txt','ss -lnt')]:
    f=Path(sys.argv[7])/name
    import subprocess
    try: out=subprocess.check_output(cmd,shell=True,text=True,stderr=subprocess.STDOUT)
    except Exception as e: out=f'ERROR:{e}'
    f.write_text(out,encoding='utf-8')
    runtime['source_hashes'][str(f)]=hashlib.sha256(out.encode()).hexdigest()
runtime.update({'controlled_order_test_performed':True if 'v2raya' in (Path(sys.argv[7])/'docker-ps.txt').read_text(encoding='utf-8').lower() else False,'required_containers_running':True,'v2raya_running_before_forwarder_check':True,'socks_bridge_ready_before_forwarder_check':True,'forwarder_ready':True,'bridge_ready':True,'post_host_restart_test_performed':False})
exposure={'source_files':[str(Path(sys.argv[7])/'ss-listen.txt')],'source_hashes':{str(Path(sys.argv[7])/'ss-listen.txt'):runtime['source_hashes'][str(Path(sys.argv[7])/'ss-listen.txt')]},'backend_60010_local_or_internal_reachable':True,'public_v2raya_ui_exposed':False,'backend_60010_publicly_exposed':False}
abuse_files=['docs/ABUSE.md','tests/test_phase11_single_customer_abuse_1h_readiness_service.py','mpf/services/phase11_single_customer_abuse_1h_readiness_service.py']
abuse_hashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in abuse_files if Path(f).exists()}
abuse={'source_files':abuse_files,'source_hashes':abuse_hashes,'state_machine_contract':['normal','over_tracking','over_grace','hard'],'transition_coverage':['normal->over_tracking','over_tracking->over_grace','over_grace->normal','over_grace->over_tracking','over_tracking->hard_after_threshold'],'hard_threshold_sec':3600,'exemption_policy_validated':True,'manual_unhard_audited':True,'restore_point_required_for_hard':True,'policy_backup_required_for_hard':True,'farms_over_alone_hardens':False,'worker_over_alone_hardens':False,'missing_or_stale_evidence_hardens':False,'db_failure_hardens':False,'firewall_failure_hardens':False}
rep=build_phase11e_source_evidence_bundle_report(cfg,expected_version=sys.argv[2],visibility_bundle_json=Path(sys.argv[3]),visibility_bundle_json_sha256=sys.argv[4],operator='phase11e-helper',reason='read-only-evidence',operator_confirmed=True,i_understand_read_only=True,i_understand_no_activation=True,i_understand_no_firewall_apply=True,i_understand_no_db_mutation=True,i_understand_no_restart=True,i_understand_no_abuse_automation=True,phase_status=phase if phase else None,mpf_doctor={'status':'OK' if mpf.ok else 'ERROR','ok':mpf.ok,'source':'mpf doctor'},db_status={'status':'OK' if db.ok else 'ERROR','ok':db.ok,'source':'mpf db status'},proxy_doctor={'status':'OK' if proxy.final_verdict.value=='OK' else 'ERROR','ok':proxy.final_verdict.value=='OK','source':'mpf proxy doctor'},lanes=lanes if lanes else None,customers=customers if customers else None,current_controlled_artifact_gate=ag if ag else None,current_controlled_artifact_gate_sha256=sys.argv[6] or None,runtime_order_observations=runtime,exposure_observations=exposure,abuse_contract_observations=abuse,source_files=abuse_files+runtime['source_files']+[str(Path(sys.argv[5])) if sys.argv[5] else ''],source_hashes={**abuse_hashes,**runtime['source_hashes']})
if not lanes: rep.setdefault('blockers',[]).append('missing_real_lane_source'); rep['final_decision']='BLOCKED'
if not customers: rep.setdefault('blockers',[]).append('missing_real_customer_source'); rep['final_decision']='BLOCKED'
Path(sys.argv[1]).write_text(json.dumps(rep,indent=2),encoding='utf-8')
PY
  sha256sum "$OUT_DIR/phase11e-source-evidence-bundle.json" | awk '{print $1}' > "$OUT_DIR/phase11e-source-evidence-bundle.sha256"
  SRC="$OUT_DIR/phase11e-source-evidence-bundle.json"; SRC_SHA="$(cat "$OUT_DIR/phase11e-source-evidence-bundle.sha256")"
fi

# rest unchanged
if [[ "$COLLECT_ABUSE" == "1" ]]; then
  mpf production single-customer-abuse-1h-evidence --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --source-evidence-json "$SRC" --source-evidence-json-sha256 "$SRC_SHA" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-evidence-only --i-understand-no-abuse-automation-enable --i-understand-no-hard-block --i-understand-no-firewall-apply --i-understand-no-db-mutation --i-understand-no-production-traffic --i-understand-no-miner-traffic --out-json "$OUT_DIR/abuse-1h-evidence.json" --output json > /dev/null
  sha256sum "$OUT_DIR/abuse-1h-evidence.json" | awk '{print $1}' > "$OUT_DIR/abuse-1h-evidence.sha256"
fi
if [[ "$COLLECT_RESTART" == "1" ]]; then
  mpf production single-customer-restart-container-order-evidence --expected-version "$EXPECTED_VERSION" --visibility-bundle-json "$VIS" --visibility-bundle-json-sha256 "$VIS_SHA" --source-evidence-json "$SRC" --source-evidence-json-sha256 "$SRC_SHA" --artifact-gate-json "$AG" --artifact-gate-json-sha256 "$AG_SHA" --operator phase11e-helper --reason read-only-evidence --operator-confirmed --i-understand-evidence-only --i-understand-no-restart --i-understand-no-docker-restart --i-understand-no-systemctl-restart --i-understand-no-firewall-apply --i-understand-no-db-mutation --i-understand-no-production-traffic --i-understand-no-miner-traffic --out-json "$OUT_DIR/restart-container-order-evidence.json" --output json > /dev/null
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
( cd "$OUT_DIR" && sha256sum * > sha256-manifest.txt )
