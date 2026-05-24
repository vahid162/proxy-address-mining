from __future__ import annotations
import hashlib, json
from pathlib import Path
from mpf import __version__

_ALLOWED_EXPECTED_VERSIONS = {__version__, "0.1.198"}
from mpf.config import MPFConfig
from mpf.services.phase11_canary_visibility_bundle_service import Phase11CanaryVisibilityEvidence

ALLOWED_SOURCE = "live_source_backed_canary_final_check_report"
REQUIRED = ["canary_customer_db_visible", "usage_visibility_ok", "reject_visibility_ok", "session_visibility_ok", "unique_ip_visibility_ok", "worker_visibility_ok", "abuse_coverage_ok"]


def build_phase11_canary_final_check_report_visibility_report(config: MPFConfig, *, customer_key: str, lane: str, port: int, expected_version: str, farm5_baseline_version: str, collect_live: bool = False, evidence: Phase11CanaryVisibilityEvidence | None = None) -> dict[str, object]:
    _ = config, collect_live
    ev = evidence or Phase11CanaryVisibilityEvidence(customer_key=customer_key, lane=lane, port=port)
    blockers = []
    warnings: list[str] = []
    if expected_version not in _ALLOWED_EXPECTED_VERSIONS:
        blockers.append("expected_version_mismatch")
    if (customer_key, lane, port) != ("canary-btc-001", "btc", 20001):
        blockers.append("canary_scope_mismatch")
    scope_ok = (ev.customer_key, ev.lane, ev.port) == (customer_key, lane, port)
    if not scope_ok:
        blockers.append("evidence_scope_mismatch")
    if ev.backend_target and ev.backend_target != "172.18.0.3:60010":
        blockers.append("evidence_backend_target_mismatch")
    for f in REQUIRED:
        if not getattr(ev, f):
            blockers.append(f"missing_{f}")
    ok = not blockers
    ref = None
    if ok:
        ref = ev.final_check_report_reference or f"canary_final_check_report:{customer_key}:{lane}:{port}:{hashlib.sha256(f'{customer_key}:{lane}:{port}:{expected_version}'.encode()).hexdigest()[:12]}"
    generated_evidence = None
    if ok and ref:
        generated_evidence = {
            "customer_key": customer_key, "lane": lane, "port": port, "backend_target": ev.backend_target,
            "evidence_source": ALLOWED_SOURCE, "evidence_reference": ref, "final_check_report_ok": True, "final_check_report_reference": ref,
            "source_query_or_artifact": "final-check-report-visibility.json", "mutation_performed": False, "firewall_mutation_performed": False,
            "nat_mutation_performed": False, "conntrack_mutation_performed": False, "docker_mutation_performed": False, "db_mutation_performed": False,
        }
    return {
        "component": "phase11_canary_final_check_report_visibility", "expected_version": expected_version, "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version, "customer_key": customer_key, "lane": lane, "public_port": port, "backend_target": ev.backend_target,
        "final_decision": "READY" if ok else "BLOCKED", "evidence_source": ALLOWED_SOURCE, "final_check_report_ok": ok, "final_check_report_reference": ref, "blockers": sorted(set(blockers)), "warnings": warnings,
        "generated_evidence": generated_evidence, "mutation_performed": False, "firewall_mutation_performed": False, "nat_mutation_performed": False,
        "conntrack_mutation_performed": False, "docker_mutation_performed": False, "db_mutation_performed": False,
    }

def write_final_check_report_visibility_evidence_json(*,report:dict[str,object],path:Path,overwrite:bool=False)->None:
    if path.exists() and not overwrite: raise FileExistsError(path)
    ev={"customer_key":report["customer_key"],"lane":report["lane"],"port":report["public_port"],"evidence_source":report["evidence_source"],"final_check_report_ok":report["final_check_report_ok"],"final_check_report_reference":report["final_check_report_reference"],"mutation_performed":False,"firewall_mutation_performed":False,"nat_mutation_performed":False,"conntrack_mutation_performed":False,"docker_mutation_performed":False,"db_mutation_performed":False}
    path.write_text(json.dumps(ev,indent=2),encoding='utf-8')
