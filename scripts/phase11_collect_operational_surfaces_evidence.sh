#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${1:?usage: $0 OUT_DIR}"
FIREWALL_COMPLETION_EVIDENCE_DIR="${MPF_FIREWALL_COMPLETION_EVIDENCE_DIR:-}"
export FIREWALL_COMPLETION_EVIDENCE_DIR
LIFECYCLE_EXECUTION_EVIDENCE_JSON="${MPF_LIFECYCLE_EXECUTION_EVIDENCE_JSON:-${2:-}}"
MPF_BIN="${MPF_BIN:-mpf}"
RESTART_DIR="${OUT_DIR}/restart-autostart-proof"
mkdir -p "${OUT_DIR}" "${RESTART_DIR}"

LIFECYCLE_EVIDENCE_ARG=()
if [[ -n "${LIFECYCLE_EXECUTION_EVIDENCE_JSON}" ]]; then
  if [[ ! -f "${LIFECYCLE_EXECUTION_EVIDENCE_JSON}" ]]; then
    echo "lifecycle execution evidence not found: ${LIFECYCLE_EXECUTION_EVIDENCE_JSON}" >&2
    exit 2
  fi
  cp "${LIFECYCLE_EXECUTION_EVIDENCE_JSON}" "${OUT_DIR}/production-customer-lifecycle-execution-evidence.json"
  sha256sum "${OUT_DIR}/production-customer-lifecycle-execution-evidence.json" | awk '{print $1}' > "${OUT_DIR}/production-customer-lifecycle-execution-evidence.sha256"
  LIFECYCLE_EVIDENCE_ARG=(--lifecycle-execution-evidence-json "${OUT_DIR}/production-customer-lifecycle-execution-evidence.json")
fi

run_json() {
  local out="$1"
  shift
  "$@" > "${out}"
  python3 -m json.tool "${out}" >/dev/null
}

write_collector_metadata() {
  python3 - "${OUT_DIR}" <<'PY'
import json, pathlib, sys
out=pathlib.Path(sys.argv[1])
flag_keys=('mutation_performed','phase12_start_allowed','worker_enforcement_enabled','ui_enabled','telegram_enabled')
def collect_flags(paths):
    flags={}
    for p in paths:
        try:
            data=json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        if isinstance(data, dict):
            for k,v in data.items():
                if k.endswith('_performed') or k in flag_keys:
                    flags[f'{p.relative_to(out)}:{k}']=v
    return flags
source_names={'production-customer-lifecycle-execution-evidence.json'}
json_files=list(out.rglob('*.json'))
flags=collect_flags([p for p in json_files if str(p.relative_to(out)) not in source_names and p.name not in {'mutation-flags.json','source-evidence-mutation-flags.json'}])
(out/'mutation-flags.json').write_text(json.dumps(flags, indent=2, sort_keys=True), encoding='utf-8')
source_flags=collect_flags([out/name for name in source_names if (out/name).exists()])
source_report={'classification':'historical_source_evidence_not_current_collector_run', 'mutation_flags': source_flags}
(out/'source-evidence-mutation-flags.json').write_text(json.dumps(source_report, indent=2, sort_keys=True), encoding='utf-8')
lifecycle_evidence={}
if (out/'production-customer-lifecycle-execution-evidence.json').exists():
    lifecycle_evidence={
        'path':'production-customer-lifecycle-execution-evidence.json',
        'sha256':(out/'production-customer-lifecycle-execution-evidence.sha256').read_text(encoding='utf-8').strip(),
    }
manifest={
    'expected_version':(out/'expected-version.txt').read_text(encoding='utf-8').strip(),
    'expected_backend_target':(out/'expected-backend-target.txt').read_text(encoding='utf-8').strip(),
    'restart_autostart_evidence_dir':'restart-autostart-proof',
    'lifecycle_execution_evidence': lifecycle_evidence,
    'firewall_completion_evidence_dir': __import__('os').environ.get('FIREWALL_COMPLETION_EVIDENCE_DIR') or None,
    'firewall_completion_evidence_dir_original': __import__('os').environ.get('FIREWALL_COMPLETION_EVIDENCE_DIR_ORIGINAL') or None,
    'firewall_completion_evidence_dir_resolved': __import__('os').environ.get('FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED') or None,
    'firewall_completion_readiness_source': __import__('os').environ.get('FIREWALL_COMPLETION_READINESS_SOURCE') or None,
    'firewall_completion_evidence_manifest': 'firewall-completion-evidence-manifest.json' if (out/'firewall-completion-evidence-manifest.json').exists() else None,
    'firewall_completion_readiness': 'production-firewall-apply-verify-rollback-readiness.json' if (out/'production-firewall-apply-verify-rollback-readiness.json').exists() else None,
    'backup_restore_drill_readiness': 'backup-restore-drill-readiness.json' if (out/'backup-restore-drill-readiness.json').exists() else None,
    'mutation_flags': 'mutation-flags.json',
    'source_evidence_mutation_flags': 'source-evidence-mutation-flags.json',
    'sha256s': 'SHA256SUMS.txt',
    'firewall_completion_evidence_sha256s': 'firewall-completion-evidence-SHA256SUMS.txt' if (out/'firewall-completion-evidence-SHA256SUMS.txt').exists() else None,
    'firewall_completion_evidence_manifest_sha256': 'firewall-completion-evidence-manifest.sha256' if (out/'firewall-completion-evidence-manifest.sha256').exists() else None,
    'files':sorted(str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()),
}
(out/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')
PY
  (cd "${OUT_DIR}" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
}

EXPECTED_VERSION="$(tr -d '[:space:]' < VERSION)"
printf '%s\n' "${EXPECTED_VERSION}" > "${OUT_DIR}/expected-version.txt"
"${MPF_BIN}" --version > "${OUT_DIR}/mpf-version.txt" 2>&1 || true
"${MPF_BIN}" phase-status > "${OUT_DIR}/phase-status.txt"

run_json "${OUT_DIR}/controlled-backend-target.json" "${MPF_BIN}" production controlled-backend-target --expected-version "${EXPECTED_VERSION}" --output json
EXPECTED_BACKEND_TARGET="$(python3 - "${OUT_DIR}/controlled-backend-target.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1], encoding='utf-8'))
h=r.get('resolved_ipv4') or r.get('target_host')
p=r.get('target_port')
if r.get('status')!='ok' or r.get('blockers') or not h or not p or r.get('backend_public_exposure') is True:
    raise SystemExit(1)
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

set +e
bash scripts/verify_current_phase_gate.sh > "${OUT_DIR}/verify-current-phase-gate.txt" 2>&1
printf '%s\n' "$?" > "${OUT_DIR}/verify-current-phase-gate.rc"
set -e

run_json "${OUT_DIR}/customer-lifecycle-doctor.json" "${MPF_BIN}" customer lifecycle-doctor --output json
run_json "${OUT_DIR}/firewall-apply-rollback-operational-surface.json" "${MPF_BIN}" production firewall-apply-rollback-operational-surface --expected-backend-target "${EXPECTED_BACKEND_TARGET}" --output json
run_json "${OUT_DIR}/usage-report-check-operational-surface.json" "${MPF_BIN}" production usage-report-check-operational-surface --output json

MPF_BIN="${MPF_BIN}" bash scripts/phase11_collect_restart_autostart_proof.sh "${RESTART_DIR}"
python3 -m json.tool "${RESTART_DIR}/proof-report.json" > "${OUT_DIR}/restart-autostart-proof-report.pretty.json"

run_json "${OUT_DIR}/production-customer-lifecycle-execution-readiness.json" env MPF_EXPECTED_BACKEND_TARGET="${EXPECTED_BACKEND_TARGET}" "${MPF_BIN}" production production-customer-lifecycle-execution-readiness --evidence-dir "${RESTART_DIR}" --expected-backend-target "${EXPECTED_BACKEND_TARGET}" "${LIFECYCLE_EVIDENCE_ARG[@]}" --output json
FIREWALL_COMPLETION_EVIDENCE_ARG=()
FIREWALL_COMPLETION_EVIDENCE_DIR_ORIGINAL="${FIREWALL_COMPLETION_EVIDENCE_DIR}"
FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED=""
FIREWALL_COMPLETION_READINESS_SOURCE=""
validate_or_fail_closed_firewall_readiness() {
  local src="$1"
  local out="$2"
  python3 - "${src}" "${out}" <<'PY'
import json, pathlib, sys
src=pathlib.Path(sys.argv[1])
out=pathlib.Path(sys.argv[2])
fail_decision='BLOCKED_PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE'
def fail(blocker, detail=None):
    blockers=[blocker] if detail is None else [blocker, str(detail)]
    out.write_text(json.dumps({
        'component':'phase11_production_firewall_apply_verify_rollback_readiness',
        'production_firewall_apply_verify_rollback':'missing_or_partial',
        'phase12_start_allowed':False,
        'mutation_performed':False,
        'db_mutation_performed':False,
        'firewall_apply_performed':False,
        'conn'+'track_flush_performed':False,
        'docker_restart_performed':False,
        'systemd_restart_performed':False,
        'blockers':blockers,
        'final_decision':fail_decision,
        'next_required_step':'production_firewall_apply_verify_rollback',
    }, indent=2, sort_keys=True), encoding='utf-8')
    return 1
try:
    data=json.loads(src.read_text(encoding='utf-8'))
except Exception as exc:
    raise SystemExit(fail('firewall_completion_readiness_json_invalid', exc))
if not isinstance(data, dict):
    raise SystemExit(fail('firewall_completion_readiness_json_invalid'))
safe_decisions={
 'PRODUCTION_FIREWALL_ALREADY_APPLIED_VERIFIED_NO_REAPPLY_REQUIRED',
 'PRODUCTION_FIREWALL_APPLY_VERIFY_ROLLBACK_EVIDENCE_READY',
}
mutation_keys=('mutation_performed','db_mutation_performed','firewall_apply_performed','conn'+'track_flush_performed','docker_restart_performed','systemd_restart_performed')
if data.get('production_firewall_apply_verify_rollback')!='production_firewall_apply_verify_rollback_ready':
    raise SystemExit(fail('firewall_completion_readiness_json_invalid'))
if data.get('final_decision') not in safe_decisions:
    raise SystemExit(fail('firewall_completion_readiness_json_invalid'))
if data.get('blockers') not in ([], None):
    raise SystemExit(fail('firewall_completion_readiness_json_invalid'))
if data.get('phase12_start_allowed') is not False:
    raise SystemExit(fail('firewall_completion_readiness_json_unsafe'))
if any(data.get(k) is True for k in mutation_keys):
    raise SystemExit(fail('firewall_completion_readiness_json_unsafe'))
for k in mutation_keys:
    data.setdefault(k, False)
data.setdefault('blockers', [])
data.setdefault('phase12_start_allowed', False)
out.write_text(json.dumps(data, indent=2, sort_keys=True), encoding='utf-8')
PY
}
if [[ -n "${FIREWALL_COMPLETION_EVIDENCE_DIR}" ]]; then
  if [[ ! -d "${FIREWALL_COMPLETION_EVIDENCE_DIR}" ]]; then
    echo "firewall completion evidence dir not found: ${FIREWALL_COMPLETION_EVIDENCE_DIR}" >&2
    exit 2
  fi
  FIREWALL_COMPLETION_EVIDENCE_ARG=(--firewall-completion-evidence-dir "${FIREWALL_COMPLETION_EVIDENCE_DIR}")
  if [[ -f "${FIREWALL_COMPLETION_EVIDENCE_DIR}/production-firewall-apply-verify-rollback-readiness.json" ]]; then
    FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED="${FIREWALL_COMPLETION_EVIDENCE_DIR}"
    FIREWALL_COMPLETION_READINESS_SOURCE="copied_readiness_json"
    if ! validate_or_fail_closed_firewall_readiness "${FIREWALL_COMPLETION_EVIDENCE_DIR}/production-firewall-apply-verify-rollback-readiness.json" "${OUT_DIR}/production-firewall-apply-verify-rollback-readiness.json"; then
      FIREWALL_COMPLETION_READINESS_SOURCE="invalid_readiness_json"
    fi
  elif [[ -f "${FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence/production-firewall-apply-verify-rollback-readiness.json" ]]; then
    FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED="${FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence"
    FIREWALL_COMPLETION_READINESS_SOURCE="copied_nested_readiness_json"
    if ! validate_or_fail_closed_firewall_readiness "${FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence/production-firewall-apply-verify-rollback-readiness.json" "${OUT_DIR}/production-firewall-apply-verify-rollback-readiness.json"; then
      FIREWALL_COMPLETION_READINESS_SOURCE="invalid_readiness_json"
    fi
  elif [[ -d "${FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence" ]] && find "${FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence" -maxdepth 1 -type f | read -r _; then
    FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED="${FIREWALL_COMPLETION_EVIDENCE_DIR}/firewall-completion-evidence"
    FIREWALL_COMPLETION_READINESS_SOURCE="recomputed_nested_raw_evidence"
    run_json "${OUT_DIR}/production-firewall-apply-verify-rollback-readiness.json" "${MPF_BIN}" production production-firewall-apply-verify-rollback-readiness --evidence-dir "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}" --output json
  else
    FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED="${FIREWALL_COMPLETION_EVIDENCE_DIR}"
    FIREWALL_COMPLETION_READINESS_SOURCE="recomputed_raw_evidence"
    if ! run_json "${OUT_DIR}/production-firewall-apply-verify-rollback-readiness.json" "${MPF_BIN}" production production-firewall-apply-verify-rollback-readiness --evidence-dir "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}" --output json; then
      FIREWALL_COMPLETION_READINESS_SOURCE="missing_or_failed"
    fi
  fi
  if [[ -f "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}/manifest.json" ]]; then
    cp "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}/manifest.json" "${OUT_DIR}/firewall-completion-evidence-manifest.json"
  fi
  if [[ -f "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}/manifest.sha256" ]]; then
    cp "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}/manifest.sha256" "${OUT_DIR}/firewall-completion-evidence-manifest.sha256"
  fi
  if [[ -f "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}/SHA256SUMS.txt" ]]; then
    cp "${FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED}/SHA256SUMS.txt" "${OUT_DIR}/firewall-completion-evidence-SHA256SUMS.txt"
  fi
fi
export FIREWALL_COMPLETION_EVIDENCE_DIR_ORIGINAL FIREWALL_COMPLETION_EVIDENCE_DIR_RESOLVED FIREWALL_COMPLETION_READINESS_SOURCE
run_json "${OUT_DIR}/production-onboarding-flow-readiness.json" "${MPF_BIN}" production production-onboarding-flow-readiness --output json
run_json "${OUT_DIR}/production-abuse-runner-readiness.json" "${MPF_BIN}" production production-abuse-runner-readiness --output json
run_json "${OUT_DIR}/production-controls-pause-block-expire-readiness.json" "${MPF_BIN}" production production-controls-pause-block-expire-readiness --output json

"${MPF_BIN}" db status > "${OUT_DIR}/db-status.txt" 2>&1 || true
"${MPF_BIN}" lanes list > "${OUT_DIR}/lanes.txt" 2>&1 || true
"${MPF_BIN}" customer list > "${OUT_DIR}/customer-list.txt" 2>&1 || true
if "${MPF_BIN}" abuse status --output json > "${OUT_DIR}/abuse-status.json" 2> "${OUT_DIR}/abuse-status.stderr"; then
  python3 -m json.tool "${OUT_DIR}/abuse-status.json" >/dev/null
else
  "${MPF_BIN}" abuse status > "${OUT_DIR}/abuse-status.txt" 2>&1 || true
fi

write_collector_metadata
run_json "${OUT_DIR}/backup-restore-drill-readiness.json" "${MPF_BIN}" production backup-restore-drill-readiness --evidence-dir "${OUT_DIR}" --output json
run_json "${OUT_DIR}/phase11-operational-completion-gap-inventory.json" env MPF_EXPECTED_BACKEND_TARGET="${EXPECTED_BACKEND_TARGET}" "${MPF_BIN}" production phase11-operational-completion-gap-inventory --evidence-dir "${OUT_DIR}" "${LIFECYCLE_EVIDENCE_ARG[@]}" "${FIREWALL_COMPLETION_EVIDENCE_ARG[@]}" --output json
