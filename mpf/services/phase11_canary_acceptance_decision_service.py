from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig

_REQUIRED_FILES = [
    "manifest.json",
    "runtime-path-evidence.json",
    "visibility-bundle.json",
    "acceptance-review.json",
]


def _get(d: dict[str, object], path: str) -> object:
    cur: object = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def _is_false(v: object) -> bool:
    return v is False


def build_phase11_canary_acceptance_decision_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    warnings: list[str] = []

    customer_key = str(kwargs.get("customer_key", "canary-btc-001"))
    lane = str(kwargs.get("lane", "btc"))
    port = int(kwargs.get("port", 20001))
    backend_target = str(kwargs.get("backend_target", "172.18.0.3:60010"))
    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    evidence_pack_dir = Path(str(kwargs.get("evidence_pack_dir")))
    evidence_archive_path = kwargs.get("evidence_archive_path")
    expected_archive_sha256 = kwargs.get("expected_archive_sha256")
    operator = str(kwargs.get("operator", "")).strip()
    reason = str(kwargs.get("reason", "")).strip()

    if not (customer_key == "canary-btc-001" and lane == "btc" and port == 20001 and backend_target == "172.18.0.3:60010" and expected_version == __version__ and farm5_baseline_version == "0.1.168"):
        blockers.append("canary_acceptance_scope_mismatch")

    if not evidence_pack_dir.exists() or not evidence_pack_dir.is_dir():
        blockers.append("evidence_pack_dir_missing")

    if not operator or not reason or kwargs.get("operator_confirmed") is not True:
        blockers.append("operator_not_confirmed")
    if kwargs.get("i_have_reviewed_evidence_pack") is not True:
        blockers.append("evidence_pack_not_reviewed")
    if kwargs.get("i_confirm_no_real_customer_onboarding") is not True:
        blockers.append("real_customer_onboarding_not_explicitly_forbidden")
    if kwargs.get("i_confirm_no_production_traffic_authorized") is not True:
        blockers.append("production_traffic_not_explicitly_forbidden")
    if kwargs.get("i_confirm_phase11_not_final_accepted") is not True:
        blockers.append("phase11_final_acceptance_boundary_not_confirmed")

    archive_actual = None
    if expected_archive_sha256:
        if evidence_archive_path is None:
            blockers.append("evidence_archive_missing")
        else:
            p = Path(str(evidence_archive_path))
            if not p.exists():
                blockers.append("evidence_archive_missing")
            else:
                archive_actual = hashlib.sha256(p.read_bytes()).hexdigest()
                if archive_actual != str(expected_archive_sha256):
                    blockers.append("evidence_archive_sha256_mismatch")

    parsed: dict[str, dict[str, object]] = {}
    if "evidence_pack_dir_missing" not in blockers:
        for name in _REQUIRED_FILES:
            p = evidence_pack_dir / name
            if not p.exists():
                blockers.append(f"evidence_file_missing:{name}")
                continue
            try:
                parsed[name] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                blockers.append(f"evidence_file_invalid_json:{name}")

    manifest = parsed.get("manifest.json", {})
    runtime = parsed.get("runtime-path-evidence.json", {})
    vis = parsed.get("visibility-bundle.json", {})
    review = parsed.get("acceptance-review.json", {})

    if parsed:
        manifest_ok = (
            (manifest.get("expected_version") == "0.1.195" or manifest.get("evidence_repository_version") == "0.1.195")
            and manifest.get("repository_version") == "0.1.195"
            and manifest.get("farm5_baseline_version") == "0.1.168"
            and manifest.get("customer_key") == "canary-btc-001"
            and manifest.get("lane") == "btc"
            and manifest.get("public_port") == 20001
            and manifest.get("backend_target") == "172.18.0.3:60010"
            and manifest.get("runtime_path_final_decision") == "RUNTIME_PATH_EVIDENCE_READY"
            and manifest.get("visibility_bundle_final_decision") == "VISIBILITY_READY"
            and manifest.get("acceptance_review_final_decision") == "ACCEPTANCE_REVIEW_READY"
            and manifest.get("missing_visibility_primitives") == []
            and manifest.get("missing_evidence_primitives") == []
            and manifest.get("next_required_step") == "none"
            and manifest.get("failed_collectors") == []
            and manifest.get("skipped_files") == []
        )
        if not manifest_ok:
            blockers.append("manifest_not_ready")

        if not (runtime.get("final_decision") == "RUNTIME_PATH_EVIDENCE_READY" and runtime.get("blockers") == []):
            blockers.append("runtime_path_not_ready")
        if not (vis.get("final_decision") == "VISIBILITY_READY" and vis.get("blockers") == [] and vis.get("warnings") == []):
            blockers.append("visibility_bundle_not_ready")
        if not (review.get("final_decision") == "ACCEPTANCE_REVIEW_READY" and review.get("blockers") == [] and review.get("warnings") == []):
            blockers.append("acceptance_review_not_ready")

        for obj in (manifest, runtime, vis, review):
            if any(obj.get(k) is True for k in ("mutation_performed", "production_traffic_enabled", "phase11_accepted", "limited_onboarding_allowed")) or obj.get("no_onboarding_authorized") is not True:
                if "evidence_mutation_flag_detected" not in blockers:
                    blockers.append("evidence_mutation_flag_detected")
                break

        rt = runtime.get("generated_evidence", {}) if isinstance(runtime.get("generated_evidence"), dict) else {}
        if not all(rt.get(k) is True for k in ("conntrack_assured", "forwarder_pool_seen", "bridge_loopback_seen")):
            blockers.append("canary_runtime_primitive_missing")
        if not rt.get("evidence_reference") or not rt.get("source_query_or_artifact") or rt.get("evidence_source") != "live_source_backed_canary_runtime_path":
            blockers.append("canary_runtime_primitive_missing")

        rv = vis.get("runtime_evidence", {}) if isinstance(vis.get("runtime_evidence"), dict) else {}
        if not all(rv.get(k) is True for k in ("conntrack_assured", "forwarder_pool_seen", "bridge_loopback_seen", "stratum_subscribe_ok", "stratum_authorize_ok", "stratum_set_difficulty_seen", "stratum_notify_seen", "canary_nat_rule_present", "no_extra_customer_nat_rules", "no_unexpected_mpf_firewall_references")) or rv.get("canary_nat_rule_count") != 1 or rv.get("canary_nat_target") != "172.18.0.3:60010":
            blockers.append("canary_visibility_primitive_missing")

        sflags = review.get("safety_flags", {}) if isinstance(review.get("safety_flags"), dict) else {}
        if any(sflags.get(k) is not False for k in ("production_traffic_allowed", "firewall_apply_allowed", "abuse_automation_allowed", "ui_allowed", "telegram_allowed", "scheduler_allowed", "worker_enforcement_allowed")):
            blockers.append("acceptance_safety_flag_open")

    blockers = sorted(set(blockers))
    accepted = len(blockers) == 0
    return {
        "component": "phase11_canary_acceptance_decision",
        "expected_version": expected_version,
        "repository_version": __version__,
        "farm5_baseline_version": farm5_baseline_version,
        "customer_key": customer_key,
        "lane": lane,
        "public_port": port,
        "backend_target": backend_target,
        "evidence_pack_dir": str(evidence_pack_dir),
        "evidence_archive_path": str(evidence_archive_path) if evidence_archive_path else None,
        "archive_sha256_expected": expected_archive_sha256,
        "archive_sha256_actual": archive_actual,
        "operator": operator,
        "reason": reason,
        "phase11d_canary_accepted": accepted,
        "phase11_accepted": False,
        "limited_onboarding_allowed": False,
        "production_traffic_enabled": False,
        "no_onboarding_authorized": True,
        "mutation_performed": False,
        "firewall_mutation_performed": False,
        "nat_mutation_performed": False,
        "conntrack_mutation_performed": False,
        "docker_mutation_performed": False,
        "db_mutation_performed": False,
        "accepted_evidence_summary": {
            "runtime_path_final_decision": runtime.get("final_decision"),
            "visibility_bundle_final_decision": vis.get("final_decision"),
            "acceptance_review_final_decision": review.get("final_decision"),
            "conntrack_assured": _get(vis, "runtime_evidence.conntrack_assured"),
            "forwarder_pool_seen": _get(vis, "runtime_evidence.forwarder_pool_seen"),
            "bridge_loopback_seen": _get(vis, "runtime_evidence.bridge_loopback_seen"),
            "stratum_subscribe_ok": _get(vis, "runtime_evidence.stratum_subscribe_ok"),
            "stratum_authorize_ok": _get(vis, "runtime_evidence.stratum_authorize_ok"),
            "stratum_set_difficulty_seen": _get(vis, "runtime_evidence.stratum_set_difficulty_seen"),
            "stratum_notify_seen": _get(vis, "runtime_evidence.stratum_notify_seen"),
        },
        "blockers": blockers,
        "warnings": warnings,
        "next_required_step": "phase11e_limited_onboarding_gate_design" if accepted else "none",
        "final_decision": "CANARY_ACCEPTANCE_DECISION_ACCEPTED" if accepted else "BLOCKED",
    }
