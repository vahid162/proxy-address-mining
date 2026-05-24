from __future__ import annotations

import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig


def build_phase11_limited_onboarding_gate_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    del config
    blockers: list[str] = []
    warnings: list[str] = []

    expected_version = str(kwargs.get("expected_version", __version__))
    farm5_baseline_version = str(kwargs.get("farm5_baseline_version", "0.1.168"))
    decision_json = Path(str(kwargs.get("canary_acceptance_decision_json", "")))
    operator = str(kwargs.get("operator", "")).strip()
    reason = str(kwargs.get("reason", "")).strip()

    data: dict[str, object] | None = None
    if not decision_json.exists() or not decision_json.is_file():
        blockers.append("canary_acceptance_decision_json_missing")
    else:
        try:
            data = json.loads(decision_json.read_text(encoding="utf-8"))
        except Exception:
            blockers.append("canary_acceptance_decision_json_invalid")

    if data is not None:
        if data.get("archive_sha256_expected") != data.get("archive_sha256_actual"):
            blockers.append("canary_acceptance_hash_mismatch")
        required_scope = {
            "component": "phase11_canary_acceptance_decision",
            "expected_version": "0.1.197",
            "repository_version": "0.1.197",
            "farm5_baseline_version": "0.1.168",
            "customer_key": "canary-btc-001",
            "lane": "btc",
            "public_port": 20001,
            "backend_target": "172.18.0.3:60010",
            "operator": "vahid",
            "final_decision": "CANARY_ACCEPTANCE_DECISION_ACCEPTED",
            "next_required_step": "phase11e_limited_onboarding_gate_design",
        }
        if any(data.get(k) != v for k, v in required_scope.items()):
            blockers.append("canary_acceptance_scope_mismatch")

        if data.get("phase11d_canary_accepted") is not True or data.get("final_decision") != "CANARY_ACCEPTANCE_DECISION_ACCEPTED":
            blockers.append("canary_acceptance_decision_not_accepted")

        if any(data.get(k) is not False for k in ("phase11_accepted", "limited_onboarding_allowed", "production_traffic_enabled")) or data.get("no_onboarding_authorized") is not True:
            blockers.append("canary_acceptance_safety_boundary_open")

        if any(data.get(k) is True for k in ("mutation_performed", "firewall_mutation_performed", "nat_mutation_performed", "conntrack_mutation_performed", "docker_mutation_performed", "db_mutation_performed")):
            blockers.append("canary_acceptance_mutation_flag_detected")

        if data.get("blockers") != [] or data.get("warnings") != []:
            blockers.append("canary_acceptance_decision_not_accepted")

        summary = data.get("accepted_evidence_summary") if isinstance(data.get("accepted_evidence_summary"), dict) else {}
        req_summary = {
            "runtime_path_final_decision": "RUNTIME_PATH_EVIDENCE_READY",
            "visibility_bundle_final_decision": "VISIBILITY_READY",
            "acceptance_review_final_decision": "ACCEPTANCE_REVIEW_READY",
            "conntrack_assured": True,
            "forwarder_pool_seen": True,
            "bridge_loopback_seen": True,
            "stratum_subscribe_ok": True,
            "stratum_authorize_ok": True,
            "stratum_set_difficulty_seen": True,
            "stratum_notify_seen": True,
        }
        if any(summary.get(k) != v for k, v in req_summary.items()):
            blockers.append("canary_acceptance_evidence_summary_incomplete")

    if expected_version != __version__:
        blockers.append("expected_version_mismatch")
    if farm5_baseline_version != "0.1.168":
        blockers.append("farm5_baseline_version_mismatch")

    if not operator or not reason or kwargs.get("operator_confirmed") is not True:
        blockers.append("operator_not_confirmed")
    if kwargs.get("i_understand_no_real_customer_onboarding_yet") is not True:
        blockers.append("no_real_customer_onboarding_boundary_not_confirmed")
    if kwargs.get("i_understand_no_production_traffic_yet") is not True:
        blockers.append("no_production_traffic_boundary_not_confirmed")
    if kwargs.get("i_understand_phase11e_requires_separate_execution_gate") is not True:
        blockers.append("phase11e_separate_execution_gate_not_confirmed")

    blockers = sorted(set(blockers))
    ready = not blockers

    return {
        "component": "phase11_limited_onboarding_gate",
        "expected_version": expected_version,
        "repository_version": __version__,
        "phase11d_canary_accepted": True if data and data.get("phase11d_canary_accepted") is True else False,
        "phase11e_gate_ready": ready,
        "phase11e_execution_allowed": False,
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
        "final_decision": "PHASE11E_LIMITED_ONBOARDING_GATE_READY" if ready else "BLOCKED",
        "next_required_step": "phase11e_limited_onboarding_execution_gate_pr" if ready else "none",
        "blockers": blockers,
        "warnings": warnings,
    }
