from __future__ import annotations

import json
import math
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

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
    if overwrite:
        for name in set(FILES.values()):
            f = p / name
            if f.exists() and f.is_file():
                f.unlink()
        for f in p.iterdir():
            if not f.is_file():
                continue
            if re.fullmatch(r"external-stratum-transcript-import-[0-9]+\.json", f.name):
                f.unlink()


def _write(path: Path, obj: dict[str, object]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _validate_obs(seconds: int, interval: int, max_seconds: int) -> tuple[int, int, int, int]:
    if seconds < 1 or interval < 1 or max_seconds < 1:
        raise ValueError("observation seconds/interval/max must be >= 1")
    effective = min(seconds, max_seconds)
    sample_count = max(1, math.ceil(effective / interval))
    return seconds, interval, max_seconds, effective, sample_count


def build_phase11_canary_evidence_pack_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    started = datetime.now(UTC)
    out_dir = Path(str(kwargs["out_dir"]))
    _safe_prepare_out_dir(out_dir, bool(kwargs.get("overwrite_out_dir", False)))
    sleep_fn: Callable[[float], None] = kwargs.get("sleep_fn", time.sleep)  # test-only injection

    customer_key = str(kwargs.get("customer_key", "canary-btc-001"))
    lane = str(kwargs.get("lane", "btc"))
    port = int(kwargs.get("port", 20001))
    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    collect_live = bool(kwargs.get("collect_live", True))
    requested_obs = int(kwargs.get("observation_seconds", 60))
    requested_interval = int(kwargs.get("observation_interval_seconds", 2))
    requested_max = int(kwargs.get("max_observation_seconds", 300))
    (_, interval, _, effective_obs, sample_count) = _validate_obs(requested_obs, requested_interval, requested_max)

    backend_target = kwargs.get("backend_target")
    generated_files: list[str] = []
    skipped_files: list[dict[str, str]] = []
    failed_collectors: list[str] = []
    visibility_evs: list[phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence] = []
    acceptance_ev = phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence()

    if collect_live:
        live = phase11_live_canary_evidence_collector_service.build_phase11_live_canary_evidence_collector_report(
            config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version
        )
        _write(out_dir / FILES["live"], live)
        generated_files.append(FILES["live"])
        acceptance_ev = phase11_canary_acceptance_review_service.Phase11CanaryAcceptanceEvidence.from_dict(live.get("evidence", {}))
        if not backend_target:
            backend_target = acceptance_ev.canary_nat_target

    runtime_reports: list[dict[str, object]] = []
    for idx in range(sample_count):
        rep = phase11_canary_runtime_path_evidence_service.build_phase11_canary_runtime_path_evidence_report(
            config,
            customer_key=customer_key,
            lane=lane,
            port=port,
            expected_version=expected_version,
            farm5_baseline_version=farm5_baseline_version,
            source_ip=kwargs.get("source_ip"),
            source_port=kwargs.get("source_port"),
            pool_host=str(kwargs.get("pool_host", "bitcoin.viabtc.io")),
            pool_port=int(kwargs.get("pool_port", 3333)),
            backend_target=backend_target,
            bridge_target=str(kwargs.get("bridge_target", "127.0.0.1:20170")),
            collect_live=collect_live,
        )
        runtime_reports.append(rep)
        if idx < sample_count - 1:
            sleep_fn(interval)

    agg = {"conntrack_assured": False, "forwarder_pool_seen": False, "bridge_loopback_seen": False}
    blockers: set[str] = set()
    first_seen: dict[str, str] = {}
    refs: dict[str, str] = {}
    for rep in runtime_reports:
        ev = rep.get("generated_evidence", {}) if isinstance(rep.get("generated_evidence", {}), dict) else {}
        for key in agg:
            if ev.get(key) is True and not agg[key]:
                agg[key] = True
                first_seen[key] = str(ev.get("captured_at") or "")
                refs[key] = str(ev.get("evidence_reference") or "")
        rep_blockers = rep.get("blockers", [])
        if isinstance(rep_blockers, list):
            blockers.update(str(x) for x in rep_blockers)
    for key, blocker in (("conntrack_assured", "missing_conntrack_assured_canary_flow"), ("forwarder_pool_seen", "missing_forwarder_pool_correlation"), ("bridge_loopback_seen", "missing_bridge_loopback_correlation")):
        if agg[key] and blocker in blockers:
            blockers.remove(blocker)

    runtime_final = {
        **runtime_reports[-1],
        "generated_evidence": {
            **(runtime_reports[-1].get("generated_evidence", {}) if isinstance(runtime_reports[-1].get("generated_evidence", {}), dict) else {}),
            **agg,
            "sample_count": sample_count,
            "first_seen_at": first_seen,
            "evidence_references": refs,
        },
        "blockers": sorted(blockers),
        "final_decision": "RUNTIME_PATH_EVIDENCE_READY" if all(agg.values()) and not blockers else "BLOCKED",
    }
    _write(out_dir / FILES["runtime"], runtime_final)
    generated_files.append(FILES["runtime"])
    visibility_evs.append(phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence.from_dict(runtime_final["generated_evidence"]))

    def _collector(name: str, filename: str, fn, ev_key: str | None = None) -> dict[str, object] | None:
        try:
            report = fn()
            _write(out_dir / filename, report)
            generated_files.append(filename)
            if ev_key and isinstance(report.get(ev_key), dict):
                visibility_evs.append(phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence.from_dict(report[ev_key]))
            return report
        except Exception:
            failed_collectors.append(name)
            skipped_files.append({"file": filename, "status": "FAILED", "reason": f"{name}_failed"})
            return None

    usage_capture = _collector("usage_evidence", FILES["usage_evidence"], lambda: phase11_canary_usage_evidence_capture_service.build_phase11_canary_usage_evidence_capture_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live))
    usage_visibility_input = None
    if usage_capture and isinstance(usage_capture.get("usage_evidence"), dict):
        usage_visibility_input = phase11_canary_usage_visibility_service.Phase11CanaryUsageVisibilityEvidence.from_dict(usage_capture["usage_evidence"])
    _collector("usage_visibility", FILES["usage_visibility"], lambda: phase11_canary_usage_visibility_service.build_phase11_canary_usage_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=usage_visibility_input), "generated_evidence")
    reject_session_ip = _collector("reject_session_ip", FILES["reject_evidence"], lambda: phase11_canary_reject_session_ip_evidence_capture_service.build_phase11_canary_reject_session_ip_evidence_capture_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live))
    if reject_session_ip and isinstance(reject_session_ip.get("generated_evidence"), dict):
        visibility_evs.append(phase11_canary_visibility_bundle_service.Phase11CanaryVisibilityEvidence.from_dict(reject_session_ip["generated_evidence"]))
    elif reject_session_ip:
        skipped_files.append({"file": FILES["reject_evidence"], "status": "SKIPPED", "reason": "session_ip_source_backed_evidence_not_available_yet"})
    _collector("reject_visibility", FILES["reject_visibility"], lambda: phase11_canary_reject_counters_visibility_service.build_phase11_canary_reject_counters_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), "generated_evidence")

    transcript_paths = [Path(p) for p in (kwargs.get("external_stratum_transcript_json") or [])]
    if transcript_paths:
        for i, tpath in enumerate(transcript_paths, start=1):
            filename = FILES["external"] if i == 1 else f"external-stratum-transcript-import-{i}.json"
            report = _collector(
                f"external_stratum_transcript_{i}",
                filename,
                lambda p=tpath: phase11_external_canary_stratum_transcript_import_service.build_phase11_external_canary_stratum_transcript_import_report(
                    config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, transcript_json=p, collect_live=collect_live
                ),
                "generated_evidence",
            )
            if report and i == 1:
                _write(out_dir / FILES["worker"], report)
                generated_files.append(FILES["worker"])
    elif not bool(kwargs.get("skip_worker_probe", True)) and kwargs.get("connect_host") and kwargs.get("worker_name"):
        _collector("worker_probe", FILES["worker"], lambda: phase11_canary_worker_stratum_evidence_capture_service.build_phase11_canary_worker_stratum_evidence_capture_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, connect_host=kwargs.get("connect_host"), connect_port=int(kwargs.get("connect_port", port)), worker_name=kwargs.get("worker_name"), collect_live=collect_live), "generated_evidence")
    else:
        skipped_files.append({"file": FILES["worker"], "status": "SKIPPED", "reason": "worker_probe_skipped_or_missing_inputs"})

    _collector("abuse", FILES["abuse"], lambda: phase11_canary_abuse_coverage_visibility_service.build_phase11_canary_abuse_coverage_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), "generated_evidence")
    _collector("final_check", FILES["final_check"], lambda: phase11_canary_final_check_report_visibility_service.build_phase11_canary_final_check_report_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), "generated_evidence")
    _collector("rollback", FILES["rollback"], lambda: phase11_canary_rollback_restore_visibility_service.build_phase11_canary_rollback_restore_visibility_report(config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live), "generated_evidence")

    merged = phase11_canary_visibility_bundle_service.merge_phase11_canary_visibility_evidence(
        visibility_evs, customer_key=customer_key, lane=lane, port=port, expected_backend_target=str(backend_target) if backend_target else None
    )
    bundle = phase11_canary_visibility_bundle_service.build_phase11_canary_visibility_bundle_report(
        config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, collect_live=collect_live, evidence=merged
    )
    _write(out_dir / FILES["bundle"], bundle)
    generated_files.append(FILES["bundle"])

    for k in ("conntrack_assured", "forwarder_pool_seen", "bridge_loopback_seen", "stratum_subscribe_ok", "stratum_authorize_ok", "stratum_set_difficulty_seen", "stratum_notify_seen"):
        setattr(acceptance_ev, k, getattr(merged, k, False))

    vis = bundle.get("visibility", {}) if isinstance(bundle.get("visibility"), dict) else {}
    def _present(name: str) -> bool:
        item = vis.get(name, {})
        return isinstance(item, dict) and item.get("status") == "PRESENT"

    acceptance_ev.canary_customer_db_visible = _present("canary_customer_db_visibility")
    acceptance_ev.usage_visibility_ok = _present("usage_counters_visibility")
    acceptance_ev.reject_visibility_ok = _present("reject_counters_visibility")
    acceptance_ev.session_visibility_ok = _present("active_recent_sessions_visibility")
    acceptance_ev.unique_ip_visibility_ok = _present("unique_ips_visibility")
    acceptance_ev.worker_visibility_ok = _present("unique_workers_visibility")
    acceptance_ev.abuse_coverage_ok = _present("abuse_coverage_visibility")
    acceptance_ev.final_check_report_ok = _present("final_check_report_visibility")
    rr = vis.get("rollback_or_restore_plan_visibility", {})
    if isinstance(rr, dict) and rr.get("status") == "PRESENT":
        ref = rr.get("reference")
        if isinstance(ref, str) and ref:
            if ref.startswith("rollback"):
                acceptance_ev.rollback_reference = ref
            else:
                acceptance_ev.restore_reference = ref

    acceptance_ev.evidence_source = merged.evidence_source or acceptance_ev.evidence_source
    acceptance_ev.evidence_reference = merged.evidence_reference or acceptance_ev.evidence_reference

    ar = phase11_canary_acceptance_review_service.build_phase11_canary_acceptance_review_report(
        config, customer_key=customer_key, lane=lane, port=port, expected_version=expected_version, farm5_baseline_version=farm5_baseline_version, evidence=acceptance_ev
    )
    _write(out_dir / FILES["acceptance"], ar)
    generated_files.append(FILES["acceptance"])

    manifest = {
        "component": "phase11_canary_evidence_pack",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": backend_target,
        "out_dir": str(out_dir),
        "observation_seconds_requested": requested_obs,
        "observation_interval_seconds_requested": requested_interval,
        "max_observation_seconds_requested": requested_max,
        "observation_seconds": effective_obs,
        "observation_interval_seconds": interval,
        "sample_count": sample_count,
        "runtime_path_final_decision": runtime_final.get("final_decision"),
        "runtime_path_blockers": runtime_final.get("blockers", []),
        "per_primitive_first_seen_at": first_seen,
        "per_primitive_evidence_references": refs,
        "started_at": started.isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "generated_files": generated_files,
        "skipped_files": skipped_files,
        "failed_collectors": failed_collectors,
        "sub_reports_summary": {"runtime_final_decision": runtime_final.get("final_decision"), "visibility_bundle_final_decision": bundle.get("final_decision"), "acceptance_review_final_decision": ar.get("final_decision")},
        "visibility_bundle_final_decision": bundle.get("final_decision"),
        "acceptance_review_final_decision": ar.get("final_decision"),
        "missing_visibility_primitives": bundle.get("missing_visibility_primitives", []),
        "missing_evidence_primitives": bundle.get("missing_evidence_primitives", []),
        "next_required_step": ar.get("next_required_step") or bundle.get("next_required_step"),
        "mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "db_mutation_performed": False,
        "production_traffic_enabled": False,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "no_onboarding_authorized": True,
    }
    _write(out_dir / FILES["manifest"], manifest)
    return manifest
