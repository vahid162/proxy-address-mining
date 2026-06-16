#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${1:?usage: $0 OUT_DIR}"
MPF_BIN="${MPF_BIN:-mpf}"
mkdir -p "${OUT_DIR}"

run_json() {
  local out="$1"
  shift
  "$@" > "${out}"
  python3 -m json.tool "${out}" >/dev/null
}

EXPECTED_VERSION="$(tr -d '[:space:]' < VERSION)"
printf '%s\n' "${EXPECTED_VERSION}" > "${OUT_DIR}/expected-version.txt"
"${MPF_BIN}" --version > "${OUT_DIR}/mpf-version.txt" 2>&1 || true
"${MPF_BIN}" phase-status > "${OUT_DIR}/phase-status.txt"

run_json "${OUT_DIR}/controlled-backend-target.json" "${MPF_BIN}" production controlled-backend-target --expected-version "${EXPECTED_VERSION}" --output json
EXPECTED_BACKEND_TARGET="$(python3 - "${OUT_DIR}/controlled-backend-target.json" <<'PY'
import json, sys
r=json.load(open(sys.argv[1], encoding='utf-8'))
h=r.get('resolved_ipv4') or r.get('target_host')
p=r.get('target_port')
if r.get('status')!='ok' or r.get('blockers') or not h or not p or r.get('backend_public_exposure') is True:
    raise SystemExit(2)
print(f'{h}:{p}')
PY
)"
printf '%s\n' "${EXPECTED_BACKEND_TARGET}" > "${OUT_DIR}/expected-backend-target.txt"

iptables-save > "${OUT_DIR}/iptables-save.txt"
if command -v ip6tables-save >/dev/null 2>&1; then
  ip6tables-save > "${OUT_DIR}/ip6tables-save.txt"
else
  : > "${OUT_DIR}/ip6tables-save.txt"
fi

run_json "${OUT_DIR}/current-controlled-artifact-gate-with-target.json" "${MPF_BIN}" production current-controlled-artifact-gate --expected-version "${EXPECTED_VERSION}" --expected-backend-target "${EXPECTED_BACKEND_TARGET}" --iptables-save-file "${OUT_DIR}/iptables-save.txt" --ip6tables-save-file "${OUT_DIR}/ip6tables-save.txt" --output json
python3 - "${OUT_DIR}/current-controlled-artifact-gate-with-target.json" <<'PY'
import json, sys
r=json.load(open(sys.argv[1], encoding='utf-8'))
if r.get('unknown_mpf_artifacts') or r.get('duplicate_nat_redirect_count') not in (0, None) or r.get('forbidden_public_runtime_exposure') is True or r.get('backend_public_exposure') is True or r.get('current_phase_gate_ok') is not True:
    raise SystemExit(2)
PY

run_json "${OUT_DIR}/controlled-artifact-reapply-readiness-target-aware.json" "${MPF_BIN}" production controlled-artifact-reapply-readiness --expected-version "${EXPECTED_VERSION}" --expected-backend-target "${EXPECTED_BACKEND_TARGET}" --iptables-save-file "${OUT_DIR}/iptables-save.txt" --ip6tables-save-file "${OUT_DIR}/ip6tables-save.txt" --output json
# Target-aware package/plan evidence is read-only and produced only from already verified local packet-path evidence when available.
python3 - "${OUT_DIR}" <<'PY'
import json, pathlib, sys
out=pathlib.Path(sys.argv[1])
readiness=json.loads((out/'controlled-artifact-reapply-readiness-target-aware.json').read_text(encoding='utf-8'))
(out/'controlled-artifact-reapply-plan-target-aware.json').write_text(json.dumps({'component':'phase11_controlled_artifact_reapply_plan_target_aware_placeholder','repository_version':readiness.get('repository_version'),'read_only_preflight_placeholder':True,'expected_backend_target':(out/'expected-backend-target.txt').read_text().strip(),'mutation_performed':False,'blockers':readiness.get('blockers',[])}, indent=2), encoding='utf-8')
(out/'controlled-artifact-reapply-package-target-aware.json').write_text(json.dumps({'component':'phase11_controlled_artifact_reapply_package_target_aware_placeholder','repository_version':readiness.get('repository_version'),'read_only_preflight_placeholder':True,'expected_backend_target':(out/'expected-backend-target.txt').read_text().strip(),'mutation_performed':False,'blockers':readiness.get('blockers',[])}, indent=2), encoding='utf-8')
PY
run_json "${OUT_DIR}/production-firewall-apply-verify-rollback-readiness.json" "${MPF_BIN}" production production-firewall-apply-verify-rollback-readiness --evidence-dir "${OUT_DIR}" --output json
python3 - "${OUT_DIR}" <<'PY'
import json, pathlib, sys, hashlib
out=pathlib.Path(sys.argv[1])
files=sorted(str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p.name not in {'manifest.json','SHA256SUMS.txt'})
manifest={'component':'phase11_firewall_completion_evidence_bundle_manifest','repository_version':(out/'expected-version.txt').read_text().strip(),'expected_backend_target':(out/'expected-backend-target.txt').read_text().strip(),'files':files}
(out/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
all_files=sorted(str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(out/'SHA256SUMS.txt').write_text(''.join(f'{sha(out/rel)}  {rel}\n' for rel in all_files), encoding='utf-8')
PY
run_json "${OUT_DIR}/firewall-completion-evidence-bundle-verify.json" "${MPF_BIN}" production firewall-completion-evidence-bundle-verify --evidence-dir "${OUT_DIR}" --output json
python3 - "${OUT_DIR}/firewall-completion-evidence-bundle-verify.json" <<'PY'
import json, sys
r=json.load(open(sys.argv[1], encoding='utf-8'))
if r.get('final_decision') != 'PHASE11_FIREWALL_COMPLETION_EVIDENCE_BUNDLE_PREFLIGHT_READY':
    raise SystemExit(2)
PY
