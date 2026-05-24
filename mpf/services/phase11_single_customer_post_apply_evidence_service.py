from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mpf import __version__
from mpf.config import MPFConfig
from mpf.services import customer_read_service
from mpf.services.phase11_single_customer_firewall_apply_gate_service import _read_live_snapshot

REQ_EXEC_SHA = "bd8f3900db3d3fb2647ead8cec47c870f4cd00ebaf52b68bc329a065a65b880b"
REQ_PRE_SHA = "3a493643f796f10f37443152e99adda928f30c82067fc98a4a748f52d2767494"
REQ_POST_SHA = "c6330a80954f7268ccec311750751b45464c84c2efd627509d1ecee274eec27b"
REQ_APPLY_SHA = "500978bf2b156a5da6a1b299e41d346cadf2b20b15280212c607c51c9a307b1a"
REQ_PLAN_SHA = "0893d1d63b7cb7f60a3473ad9f922c3f65bc9b3e6ff8d5b84aecfa701d45c438"

EXPECTED_SCOPE = {
    "customer_key": "limited-btc-001",
    "lane": "btc",
    "public_port": 20101,
    "backend_target": "172.18.0.3:60010",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_file(path: Path, missing_blocker: str, invalid_blocker: str, blockers: list[str]) -> dict[str, object] | None:
    if not path.exists() or not path.is_file():
        blockers.append(missing_blocker)
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        blockers.append(invalid_blocker)
        return None
    if not isinstance(data, dict):
        blockers.append(invalid_blocker)
        return None
    return data


def _parse_snapshot(snapshot: str) -> dict[str, object]:
    lines = snapshot.splitlines()
    dnat_20101 = [line for line in lines if "MPF_NAT_PRE" in line and "--dport 20101" in line and "-j DNAT" in line]
    connlimit_rules = [
        line
        for line in lines
        if "-A MPFC_20101" in line
        and "--dport 20101" in line
        and "mpf:limited-btc-001:customer_connlimit_reject" in line
        and "-j REJECT" in line
    ]
    hashlimit_rules = [
        line
        for line in lines
        if "-A MPFC_20101" in line
        and "--dport 20101" in line
        and "mpf:limited-btc-001:customer_hashlimit_reject" in line
        and "-j REJECT" in line
    ]
    return {
        "has_canary_20001": ":MPFC_20001" in snapshot and any("--dport 20001" in line and "canary-btc-001" in line for line in lines),
        "has_20101_chain": ":MPFC_20101" in snapshot,
        "has_20101_ref": "limited-btc-001" in snapshot,
        "dnat_20101_exact_target_count": len(
            [line for line in dnat_20101 if "--to-destination 172.18.0.3:60010" in line and "limited-btc-001" in line]
        ),
        "dnat_20101_loopback_count": len([line for line in dnat_20101 if "--to-destination 127.0.0.1:" in line]),
        "unrelated_customer_nat_rule_count": len(
            [line for line in lines if "-A MPF_NAT_PRE" in line and "mpf:" in line and "limited-btc-001" not in line and "canary-btc-001" not in line]
        ),
        "limited_20101_connlimit_reject_rule_count": len(connlimit_rules),
        "limited_20101_hashlimit_reject_rule_count": len(hashlimit_rules),
        "limited_20101_filter_primitives_verified": len(connlimit_rules) == 1 and len(hashlimit_rules) == 1,
    }


def _verify_confirmations(kwargs: dict[str, object], blockers: list[str]) -> None:
    confirmations = {
        "operator_confirmed": "operator_not_confirmed",
        "i_understand_post_apply_evidence_only": "post_apply_evidence_only_not_confirmed",
        "i_understand_no_additional_firewall_apply": "no_additional_firewall_apply_not_confirmed",
        "i_understand_no_production_traffic_acceptance": "no_production_traffic_not_confirmed",
        "i_understand_no_miner_traffic_acceptance": "no_miner_traffic_not_confirmed",
        "i_confirm_runtime_path_evidence_required_next": "runtime_path_required_not_confirmed",
        "i_confirm_stratum_transcript_required_next": "stratum_transcript_required_not_confirmed",
        "i_confirm_visibility_bundle_required_next": "visibility_bundle_required_not_confirmed",
        "i_confirm_abuse_1h_required_before_customer_traffic": "abuse_1h_required_not_confirmed",
        "i_confirm_restart_container_order_required_before_limited_acceptance": "restart_container_order_required_not_confirmed",
    }
    for field, blocker in confirmations.items():
        if kwargs.get(field) is not True:
            blockers.append(blocker)


def _base_result(expected_version: str, kwargs: dict[str, object]) -> dict[str, object]:
    return {
        "component": "phase11_single_customer_post_apply_evidence",
        "expected_version": expected_version,
        "repository_version": __version__,
        "candidate_customer_key": str(kwargs.get("candidate_customer_key", EXPECTED_SCOPE["customer_key"])),
        "candidate_lane": str(kwargs.get("candidate_lane", EXPECTED_SCOPE["lane"])),
        "candidate_public_port": int(kwargs.get("candidate_public_port", EXPECTED_SCOPE["public_port"])),
        "candidate_backend_target": str(kwargs.get("candidate_backend_target", EXPECTED_SCOPE["backend_target"])),
        "production_traffic_enabled": False,
        "miner_traffic_allowed": False,
        "phase11_accepted": False,
        "additional_firewall_apply_allowed": False,
        "db_activation_allowed": False,
        "mutation_performed": False,
    }


def build_phase11_single_customer_post_apply_evidence_report(config: MPFConfig, **kwargs: object) -> dict[str, object]:
    blockers: list[str] = []
    expected_version = str(kwargs.get("expected_version", "0.1.205"))
    result = _base_result(expected_version, kwargs)

    _verify_confirmations(kwargs, blockers)

    if (
        result["candidate_customer_key"] != EXPECTED_SCOPE["customer_key"]
        or str(result["candidate_lane"]).lower() != EXPECTED_SCOPE["lane"]
        or int(result["candidate_public_port"]) != EXPECTED_SCOPE["public_port"]
        or result["candidate_backend_target"] != EXPECTED_SCOPE["backend_target"]
    ):
        blockers.append("candidate_scope_mismatch")

    execution_json_path = Path(str(kwargs.get("execution_json", "")))
    execution_data = _read_json_file(execution_json_path, "execution_json_missing", "execution_json_invalid", blockers)
    if execution_data is not None and _sha256_file(execution_json_path) != str(kwargs.get("execution_json_sha256", REQ_EXEC_SHA)):
        blockers.append("execution_json_hash_mismatch")

    if execution_data is not None:
        expected_execution_fields = {
            "final_decision": "PHASE11_SINGLE_CUSTOMER_FIREWALL_APPLY_EXECUTED_PENDING_REVIEW",
            "execute_requested": True,
            "apply_execution_ready": True,
            "firewall_apply_execution_allowed": True,
            "iptables_restore_authorized": True,
            "mutation_performed": True,
            "firewall_mutation_performed": True,
            "nat_mutation_performed": True,
            "next_required_step": "phase11e_post_apply_runtime_evidence_pr",
            "production_traffic_enabled": False,
            "miner_traffic_allowed": False,
            "phase11_accepted": False,
        }
        if any(execution_data.get(k) != v for k, v in expected_execution_fields.items()):
            blockers.append("execution_json_not_success")
        if execution_data.get("blockers") != [] or execution_data.get("warnings") != []:
            blockers.append("execution_json_safety_boundary_open")
        if (
            execution_data.get("candidate_customer_key") != EXPECTED_SCOPE["customer_key"]
            or execution_data.get("candidate_lane") != EXPECTED_SCOPE["lane"]
            or execution_data.get("candidate_public_port") != EXPECTED_SCOPE["public_port"]
            or execution_data.get("candidate_backend_target") != EXPECTED_SCOPE["backend_target"]
        ):
            blockers.append("execution_json_scope_mismatch")

        post_apply_verification = execution_data.get("post_apply_verification")
        if not isinstance(post_apply_verification, dict):
            blockers.append("execution_json_post_apply_verification_missing")
        else:
            expected_post_apply = {
                "mpf_nat_pre_exists": True,
                "mpfc_20001_exists": True,
                "mpfc_20101_exists": True,
                "canary_20001_exact_artifact_preserved": True,
                "dnat_20101_exact_target_count": 1,
                "dnat_20101_loopback_count": 0,
                "unrelated_customer_nat_rule_count": 0,
                "limited_20101_connlimit_reject_rule_count": 1,
                "limited_20101_hashlimit_reject_rule_count": 1,
                "limited_20101_filter_primitives_verified": True,
            }
            if any(post_apply_verification.get(k) != v for k, v in expected_post_apply.items()):
                blockers.append("execution_json_post_apply_verification_failed")

    pre_path = Path(str(kwargs.get("pre_apply_snapshot_file", "")))
    post_path = Path(str(kwargs.get("post_apply_snapshot_file", "")))
    if not pre_path.exists() or not pre_path.is_file():
        blockers.append("pre_apply_snapshot_missing")
    elif _sha256_file(pre_path) != str(kwargs.get("pre_apply_snapshot_sha256", REQ_PRE_SHA)):
        blockers.append("pre_apply_snapshot_hash_mismatch")

    if not post_path.exists() or not post_path.is_file():
        blockers.append("post_apply_snapshot_missing")
    elif _sha256_file(post_path) != str(kwargs.get("post_apply_snapshot_sha256", REQ_POST_SHA)):
        blockers.append("post_apply_snapshot_hash_mismatch")

    apply_gate_path = Path(str(kwargs.get("apply_gate_json", "")))
    if not apply_gate_path.exists() or not apply_gate_path.is_file():
        blockers.append("apply_gate_json_missing")
    elif _sha256_file(apply_gate_path) != str(kwargs.get("apply_gate_json_sha256", REQ_APPLY_SHA)):
        blockers.append("apply_gate_json_hash_mismatch")

    plan_gate_path = Path(str(kwargs.get("plan_gate_json", "")))
    if not plan_gate_path.exists() or not plan_gate_path.is_file():
        blockers.append("plan_gate_json_missing")
    elif _sha256_file(plan_gate_path) != str(kwargs.get("plan_gate_json_sha256", REQ_PLAN_SHA)):
        blockers.append("plan_gate_json_hash_mismatch")

    post_snapshot_classification: dict[str, object] = {}
    if pre_path.exists() and pre_path.is_file() and post_path.exists() and post_path.is_file():
        pre_cls = _parse_snapshot(pre_path.read_text(encoding="utf-8"))
        post_cls = _parse_snapshot(post_path.read_text(encoding="utf-8"))
        post_snapshot_classification = post_cls

        if not pre_cls["has_canary_20001"]:
            blockers.append("pre_apply_snapshot_missing_canary_20001")
        if pre_cls["has_20101_chain"] or pre_cls["dnat_20101_exact_target_count"] > 0 or pre_cls["has_20101_ref"]:
            blockers.append("pre_apply_snapshot_unexpected_20101_present")

        if not post_cls["has_canary_20001"]:
            blockers.append("post_apply_snapshot_missing_canary_20001")
        if not post_cls["has_20101_chain"] or int(post_cls["dnat_20101_exact_target_count"]) < 1:
            blockers.append("post_apply_snapshot_missing_20101")
        if int(post_cls["dnat_20101_exact_target_count"]) > 1:
            blockers.append("post_apply_snapshot_duplicate_20101")
        if int(post_cls["dnat_20101_loopback_count"]) > 0:
            blockers.append("post_apply_snapshot_loopback_20101")
        if int(post_cls["unrelated_customer_nat_rule_count"]) > 0:
            blockers.append("post_apply_snapshot_unrelated_customer_nat")
        if post_cls["limited_20101_filter_primitives_verified"] is not True:
            blockers.append("post_apply_snapshot_missing_filter_primitives")

    try:
        db_rows = customer_read_service.list_customer_status(config, include_deleted=False, limit=5000)
    except Exception:
        db_rows = customer_read_service.CustomerList(ok=False, message="exception", customers=[])

    if not db_rows.ok:
        blockers.append("db_read_failed")
    else:
        staged = [row for row in db_rows.customers if row.customer_key == EXPECTED_SCOPE["customer_key"]]
        if len(staged) == 0:
            blockers.append("staged_customer_missing")
        elif len(staged) > 1:
            blockers.append("staged_customer_duplicate")
        else:
            customer = staged[0]
            if customer.lane != EXPECTED_SCOPE["lane"] or customer.port != EXPECTED_SCOPE["public_port"]:
                blockers.append("staged_customer_scope_mismatch")
            if str(customer.status).strip().lower() != "paused":
                blockers.append("staged_customer_not_paused")
        if [row for row in db_rows.customers if row.customer_key != EXPECTED_SCOPE["customer_key"] and row.port == EXPECTED_SCOPE["public_port"]]:
            blockers.append("candidate_port_collision")

    live_snapshot_file = kwargs.get("live_snapshot_file")
    collect_live = bool(kwargs.get("collect_live", False))
    if live_snapshot_file or collect_live:
        try:
            live_snapshot = _read_live_snapshot(Path(str(live_snapshot_file)) if live_snapshot_file else None, collect_live, kwargs.get("live_snapshot_reader"))
            live_cls = _parse_snapshot(live_snapshot)
            if post_snapshot_classification and live_cls != post_snapshot_classification:
                blockers.append("live_snapshot_mismatch")
        except Exception:
            blockers.append("live_firewall_read_failed")

    if blockers:
        return {
            **result,
            "post_apply_evidence_ready": False,
            "controlled_apply_recorded": False,
            "runtime_path_evidence_ready": False,
            "stratum_transcript_ready": False,
            "visibility_bundle_ready": False,
            "abuse_1h_coverage_ready": False,
            "restart_container_order_ready": False,
            "blockers": sorted(set(blockers)),
            "warnings": [],
            "next_required_step": "none",
            "final_decision": "BLOCKED",
        }

    return {
        **result,
        **post_snapshot_classification,
        "post_apply_evidence_ready": True,
        "controlled_apply_recorded": True,
        "runtime_path_evidence_ready": False,
        "stratum_transcript_ready": False,
        "visibility_bundle_ready": False,
        "abuse_1h_coverage_ready": False,
        "restart_container_order_ready": False,
        "blockers": [],
        "warnings": [],
        "next_required_step": "phase11e_single_customer_runtime_path_evidence_pr",
        "final_decision": "PHASE11_SINGLE_CUSTOMER_POST_APPLY_EVIDENCE_READY",
    }
