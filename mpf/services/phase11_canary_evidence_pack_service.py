from __future__ import annotations

import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import (
    phase11_canary_abuse_coverage_visibility_service,
    phase11_canary_acceptance_review_service,
    phase11_canary_final_check_report_visibility_service,
    phase11_canary_reject_counters_visibility_service,
    phase11_canary_reject_session_ip_evidence_capture_service,
    phase11_canary_rollback_restore_visibility_service,
    phase11_canary_runtime_path_evidence_service,
    phase11_canary_usage_evidence_capture_service,
    phase11_canary_usage_visibility_service,
    phase11_canary_visibility_bundle_service,
    phase11_canary_worker_stratum_evidence_capture_service,
    phase11_external_canary_stratum_transcript_import_service,
    phase11_live_canary_evidence_collector_service,
)

FILES = {
    "live": "live-canary-evidence.json",
    "runtime": "runtime-path-evidence.json",
    "usage_evidence": "usage-evidence.json",
    "usage_visibility": "usage-visibility.json",
    "reject_evidence": "reject-session-ip-evidence.json",
    "reject_visibility": "reject-counters-visibility.json",
    "worker": "worker-stratum-evidence.json",
    "external": "external-stratum-transcript-import.json",
    "abuse": "abuse-coverage-visibility.json",
    "final_check": "final-check-report-visibility.json",
    "rollback": "rollback-restore-visibility.json",
    "bundle": "visibility-bundle.json",
    "acceptance": "acceptance-review.json",
    "manifest": "manifest.json",
}


def _safe_prepare_out_dir(out_dir: Path, overwrite: bool) -> None:
    p = out_dir.resolve()
    if p.exists() and not overwrite:
        raise ValueError("out-dir already exists; pass --overwrite-out-dir")
    forbidden = {Path("/"), Path("/tmp"), Path("/var"), Path("/opt"), Path("/opt/mpf-py-src")}
    if p in forbidden or len(p.parts) < 3:
        raise ValueError("unsafe out-dir path rejected")
    p.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        return
    for name in FILES.values():
        f = p / name
        if f.exists() and f.is_file():
            f.unlink()


def _write(path: Path, obj: dict[str, object]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_phase11_canary_evidence_pack_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    started = datetime.now(UTC)
    out_dir = Path(str(kwargs["out_dir"]))
    _safe_prepare_out_dir(out_dir, bool(kwargs.get("overwrite_out_dir", False)))

    customer_key = str(kwargs.get("customer_key", "canary-btc-001")); lane = str(kwargs.get("lane", "btc")); port = int(kwargs.get("port", 20001))
    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    collect_live = bool(kwargs.get("collect_live", True))
    observation_seconds = min(int(kwargs.get("observation_seconds", 60)), int(kwargs.get("max_observation_seconds", 300)))
    observation_interval_seconds = int(kwargs.get("observation_interval_seconds", 2))
    backend_target = kwargs.get("backend_target")
    generated_files: list[str] = []
    skipped_files: list[dict[str, str]] = []
    failed_collectors: list[str] = []
    visibility_evs: list[phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence] = []
    acceptance_ev = phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence()

    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version)
        _write(out_dir / FILES["live"], live); generated_files.append(FILES["live"])
        acceptance_ev = phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))
        if not backend_target:
            backend_target = acceptance_ev.canary_nat_target

    samples = max(1, observation_seconds // max(1, observation_interval_seconds))
    runtime_reports = []
    for i in range(samples):
        rep = phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report(
            config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version,
            source_ip=kwargs.get("source_ip"), source_port=kwargs.get("source_port"), pool_host=str(kwargs.get("pool_host", "bitcoin.viabtc.io")), pool_port=int(kwargs.get("pool_port", 3333)),
            backend_target=backend_target, bridge_target=str(kwargs.get("bridge_target", "127.0.0.1:20170")), collect_live=collect_live,
        )
        runtime_reports.append(rep)
        if i < samples - 1:
            time.sleep(0)

    agg = {"conntrack_assured": False, "forwarder_pool_seen": False, "bridge_loopback_seen": False}
    blockers = set()
    first_seen: dict[str, str] = {}
    refs: dict[str, str] = {}
    for rep in runtime_reports:
        ev = rep.get("generated_evidence", {})
        for k in agg:
            if ev.get(k) is True and not agg[k]:
                agg[k] = True
                first_seen[k] = str(ev.get("captured_at") or "")
                refs[k] = str(ev.get("evidence_reference") or "")
        blockers.update(rep.get("blockers", []))
    for k, b in (("conntrack_assured", "missing_conntrack_assured_canary_flow"), ("forwarder_pool_seen", "missing_forwarder_pool_correlation"), ("bridge_loopback_seen", "missing_bridge_loopback_correlation")):
        if agg[k] and b in blockers:
            blockers.remove(b)
    runtime_final = {
        **runtime_reports[-1],
        "generated_evidence": {**runtime_reports[-1].get("generated_evidence", {}), **agg, "sample_count": samples, "first_seen_at": first_seen, "evidence_references": refs},
        "blockers": sorted(blockers),
        "final_decision": "RUNTIME_PATH_EVIDENCE_READY" if all(agg.values()) and not blockers else "BLOCKED",
    }
    _write(out_dir / FILES["runtime"], runtime_final); generated_files.append(FILES["runtime"])
    visibility_evs.append(phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence.from_dict(runtime_final["generated_evidence"]))
    for k in agg:
        if agg[k]: setattr(acceptance_ev, k, True)

    def _collector(name: str, fn, key: str, ev_key: str | None = None):
        nonlocal acceptance_ev
        try:
            report = fn()
            _write(out_dir / FILES[key], report); generated_files.append(FILES[key])
            if ev_key and report.get(ev_key):
                visibility_evs.append(phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence.from_dict(report[ev_key]))
            return report
        except Exception:
            failed_collectors.append(name)
            skipped_files.append({"file": FILES[key], "status": "FAILED", "reason": f"{name}_failed"})
            return None

    usage_e = _collector("usage_evidence", lambda: phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), "usage_evidence")
    if usage_e:
        usage_v = _collector("usage_visibility", lambda: phase11_canary_usage_visibility_service.build_phase11_canary_usage_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=False, evidence=phase11_canary_usage_visibility_service.Phase11CanaryUsageVisibilityEvidence.from_dict(usage_e.get("generated_evidence", {}))), "usage_visibility", "generated_evidence")
        if usage_v and usage_v.get("final_decision") != "BLOCKED": acceptance_ev.usage_visibility_ok = True

    rej = _collector("reject_session_ip", lambda: phase11_canary_reject_session_ip_evidence_capture_service.build_phase11_canary_reject_session_ip_evidence_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), "reject_evidence")
    if rej:
        rej_v = _collector("reject_visibility", lambda: phase11_canary_reject_counters_visibility_service.build_phase11_canary_reject_counters_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=False, evidence=phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence.from_dict(rej.get("generated_evidence", {}))), "reject_visibility", "generated_evidence")
        if rej_v and rej_v.get("final_decision") != "BLOCKED": acceptance_ev.reject_visibility_ok = True

    tr_json = kwargs.get("external_stratum_transcript_json") or []
    if tr_json:
        tr = _collector("external_stratum_transcript", lambda: phase11_external_canary_stratum_transcript_import_service.build_phase11_external_canary_stratum_transcript_import_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, transcript_json=tr_json, collect_live=collect_live), "external", "generated_evidence")
        if tr:
            _write(out_dir / FILES["worker"], tr); generated_files.append(FILES["worker"]); acceptance_ev.worker_visibility_ok = True
    elif not bool(kwargs.get("skip_worker_probe", True)) and kwargs.get("connect_host") and kwargs.get("worker_name"):
        w = _collector("worker_probe", lambda: phase11_canary_worker_stratum_evidence_capture_service.build_phase11_canary_worker_stratum_evidence_capture_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, connect_host=kwargs.get("connect_host"), connect_port=int(kwargs.get("connect_port", port)), worker_name=kwargs.get("worker_name"), worker_password=kwargs.get("worker_password", "x"), collect_live=collect_live), "worker", "generated_evidence")
        if w: acceptance_ev.worker_visibility_ok = True
    else:
        skipped_files.append({"file": FILES["worker"], "status": "SKIPPED", "reason": "worker_probe_skipped_or_missing_inputs"})

    for name, svc, k in [
        ("abuse", phase11_canary_abuse_coverage_visibility_service.build_phase11_canary_abuse_coverage_visibility_report, "abuse"),
        ("final_check", phase11_canary_final_check_report_visibility_service.build_phase11_canary_final_check_report_visibility_report, "final_check"),
        ("rollback", phase11_canary_rollback_restore_visibility_service.build_phase11_canary_rollback_restore_visibility_report, "rollback"),
    ]:
        r = _collector(name, lambda s=svc: s(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), k, "generated_evidence")
        if r and r.get("final_decision") != "BLOCKED":
            if name == "abuse": acceptance_ev.abuse_coverage_ok = True
            if name == "final_check": acceptance_ev.final_check_report_ok = True
            if name == "rollback": acceptance_ev.rollback_reference = "rollback_or_restore_present"

    merged = phase11_canary_visibility_bundle_service.merge_phase11_canary_visibility_evidence(visibility_evs, customer_key=customer_key, lane=lane, port=port, expected_backend_target=str(backend_target) if backend_target else None)
    bundle = phase11_canary_visibility_bundle_service.build_phase11_canary_visibility_bundle_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=merged)
    _write(out_dir / FILES["bundle"], bundle); generated_files.append(FILES["bundle"])

    for p in bundle.get("missing_visibility_primitives", []):
        if p == "canary_customer_db_visibility": acceptance_ev.canary_customer_db_visible = False
    for fld in ("canary_customer_db_visible", "session_visibility_ok", "unique_ip_visibility_ok"):
        setattr(acceptance_ev, fld, True if fld.replace("_ok", "_visibility").replace("canary_customer_db_visible", "canary_customer_db_visibility") not in bundle.get("missing_visibility_primitives", []) else getattr(acceptance_ev, fld))

    ar = phase11_canary_acceptance_review_service.build_phase11_canary_acceptance_review_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, evidence=acceptance_ev)
    _write(out_dir / FILES["acceptance"], ar); generated_files.append(FILES["acceptance"])

    manifest = {"component": "phase11_canary_evidence_pack", "expected_version": expected_version, "repository_version": __version__, "farm5_baseline_version": farm5_baseline_version, "customer_key": customer_key, "lane": lane, "public_port": port, "backend_target": backend_target, "out_dir": str(out_dir), "observation_seconds": observation_seconds, "observation_interval_seconds": observation_interval_seconds, "started_at": started.isoformat(), "completed_at": datetime.now(UTC).isoformat(), "generated_files": generated_files, "skipped_files": skipped_files, "failed_collectors": failed_collectors, "sub_reports_summary": {"runtime_final_decision": runtime_final.get("final_decision"), "visibility_bundle_final_decision": bundle.get("final_decision"), "acceptance_review_final_decision": ar.get("final_decision")}, "visibility_bundle_final_decision": bundle.get("final_decision"), "acceptance_review_final_decision": ar.get("final_decision"), "missing_visibility_primitives": bundle.get("missing_visibility_primitives", []), "missing_evidence_primitives": bundle.get("missing_evidence_primitives", []), "next_required_step": ar.get("next_required_step") or bundle.get("next_required_step"), "mutation_performed": False, "firewall_mutation_performed": False, "nat_mutation_performed": False, "conntrack_mutation_performed": False, "docker_mutation_performed": False, "db_mutation_performed": False, "production_traffic_enabled": False, "phase11_accepted": False, "limited_onboarding_allowed": False, "no_onboarding_authorized": True}
    _write(out_dir / FILES["manifest"], manifest)
    return manifest
